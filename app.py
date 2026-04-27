"""
Sajz GarageX — Automated Video Assembly Service
Runs free on Render.com | Uses FFmpeg + Pexels stock footage
Assembles daily car content Reels for @thesajz, @sajzgaragex, Sajz GarageX YouTube
"""

from flask import Flask, request, jsonify, send_file
import subprocess
import requests
import os
import json
import tempfile
import uuid
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
PEXELS_API_KEY   = os.environ.get("PEXELS_API_KEY", "")
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
GEMINI_URL       = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Weekly content themes (Monday=0 ... Sunday=6)
WEEKLY_THEMES = {
    0: {"theme": "Supercar Spotlight",  "search": "supercar lamborghini ferrari driving"},
    1: {"theme": "Hidden Gems",         "search": "classic car vintage automobile street"},
    2: {"theme": "BMW M Series",        "search": "BMW sports car M series driving"},
    3: {"theme": "Viral Car Moment",    "search": "sports car burnout drift race"},
    4: {"theme": "Dream Garage",        "search": "luxury car garage exotic collection"},
    5: {"theme": "Mods & Builds",       "search": "car modification custom build workshop"},
    6: {"theme": "Petrolhead Reacts",   "search": "fast car highway exotic automobile"},
}

# ─── Helpers ────────────────────────────────────────────────────────────────────

def safe_text(text: str) -> str:
    """Escape text for FFmpeg drawtext filter"""
    return re.sub(r"[:'\\]", "", text)[:60]


def download_file(url: str, dest: str, timeout: int = 45) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=timeout)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=16384):
                f.write(chunk)
        return True
    except Exception as e:
        logger.warning(f"Download failed {url}: {e}")
        return False


def get_pexels_videos(query: str, count: int = 4) -> list:
    """Fetch free stock car video URLs from Pexels"""
    if not PEXELS_API_KEY:
        return []
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {"query": query, "per_page": count, "orientation": "portrait", "size": "medium"}
    try:
        r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
        r.raise_for_status()
        videos = r.json().get("videos", [])
        urls = []
        for v in videos:
            # Pick HD file
            files = sorted(v.get("video_files", []), key=lambda x: x.get("width", 0), reverse=True)
            for f in files:
                if f.get("width", 0) >= 720:
                    urls.append(f["link"])
                    break
        return urls[:count]
    except Exception as e:
        logger.error(f"Pexels error: {e}")
        return []


def generate_content_with_gemini(theme: str, day_name: str) -> dict:
    """Call Gemini 1.5 Flash (free) to generate full daily content package"""
    if not GEMINI_API_KEY:
        return {}

    prompt = f"""
You are the content brain for Sajz GarageX — a passionate BMW and supercar YouTube/Instagram channel run by Sajjad.

Today is {day_name}. Theme: {theme}.

Generate a complete daily car content package. Return ONLY valid JSON, no markdown, no extra text.

JSON structure:
{{
  "video_topic": "Short punchy topic title (e.g. Ferrari 12Cilindri vs Revuelto)",
  "pexels_search": "3-5 word search query for Pexels car stock footage",
  "hook": "One punchy scroll-stopping line under 8 words for text overlay",
  "cta": "Short CTA under 6 words for text overlay",
  "youtube_title": "SEO title mentioning Sajz GarageX, max 70 chars",
  "youtube_description": "Full YT description 3 paragraphs, include: Subscribe to Sajz GarageX, Instagram @sajzgaragex and @thesajz, Support: linktr.ee/thesajz",
  "youtube_tags": ["tag1","tag2",...] (30 tags, common automobile search terms),
  "pinned_comment": "Short pinned comment asking engagement + follow @sajzgaragex",
  "thumbnail_text": "Max 4 bold words for thumbnail",
  "instagram_thesajz_caption": "Full Instagram caption for @thesajz: punchy attitude, emojis, CTA, support links (linktr.ee/thesajz), 25 mega-viral hashtags like #cars #supercars #carporn",
  "instagram_sajzgaragex_caption": "Full Instagram caption for @sajzgaragex: technical, BMW/garage angle, mention Sajz GarageX YouTube, support links, 25 niche hashtags like #sajzgaragex #bmwm #garagelife"
}}

Rules:
- Voice: Confident petrolhead, short punchy sentences, authentic
- Always reference cars/automobiles/BMW
- YouTube tags: simple, commonly searched words only (no hashtags, no #)
- Keep hook and cta short enough to fit as text overlay on video
""".strip()

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1500}
    }

    try:
        r = requests.post(
            f"{GEMINI_URL}?key={GEMINI_API_KEY}",
            json=payload, timeout=30
        )
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        # Strip any markdown code fences
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return {}


def process_clip(input_path: str, output_path: str, duration: int = 8):
    """Resize clip to 1080x1920 vertical format"""
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", (
            "scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920"
        ),
        "-c:v", "libx264", "-preset", "fast", "-crf", "24",
        "-an", "-t", str(duration),
        output_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    return result.returncode == 0


def concat_clips(clip_paths: list, output_path: str) -> bool:
    """Concatenate processed clips"""
    tmpdir = os.path.dirname(output_path)
    concat_file = os.path.join(tmpdir, "concat.txt")
    with open(concat_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p}'\n")
    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0",
        "-i", concat_file,
        "-c", "copy",
        output_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    return result.returncode == 0


def add_overlays(input_path: str, output_path: str, hook: str, cta: str) -> bool:
    """Add hook text at top and CTA at bottom using FFmpeg drawtext"""
    hook_safe = safe_text(hook)
    cta_safe  = safe_text(cta)

    vf = (
        f"drawtext=text='{hook_safe}':"
        f"fontsize=54:fontcolor=white:x=(w-tw)/2:y=90:"
        f"box=1:boxcolor=black@0.65:boxborderw=14,"

        f"drawtext=text='{cta_safe}':"
        f"fontsize=40:fontcolor=white:x=(w-tw)/2:y=h-110:"
        f"box=1:boxcolor=black@0.65:boxborderw=10"
    )

    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        output_path, "-y"
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=180)
    return result.returncode == 0


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Sajz GarageX Video Assembler"})


@app.route("/generate", methods=["POST"])
def generate():
    """
    Main endpoint — called by Make.com daily at 8 AM.
    Accepts: { "weekday": 0-6 }  (0=Monday)
    Returns: JSON with all content + assembled video as base64
    """
    import base64
    from datetime import datetime

    data = request.json or {}
    weekday = data.get("weekday", datetime.now().weekday())
    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_name  = day_names[weekday % 7]

    theme_info = WEEKLY_THEMES[weekday % 7]
    theme      = theme_info["theme"]
    fallback_search = theme_info["search"]

    logger.info(f"Generating content for {day_name} — {theme}")

    # 1. Generate content with Gemini
    content = generate_content_with_gemini(theme, day_name)
    if not content:
        return jsonify({"error": "Gemini content generation failed"}), 500

    pexels_query = content.get("pexels_search", fallback_search)
    hook = content.get("hook", "This changes everything")
    cta  = content.get("cta", "Follow @sajzgaragex")

    # 2. Fetch Pexels videos
    video_urls = get_pexels_videos(pexels_query, count=4)
    if not video_urls:
        # Fallback search
        video_urls = get_pexels_videos(fallback_search, count=4)
    if not video_urls:
        return jsonify({"error": "No Pexels videos found"}), 500

    # 3. Assemble video
    tmpdir = tempfile.mkdtemp()
    job_id = str(uuid.uuid4())[:8]

    processed = []
    for i, url in enumerate(video_urls):
        raw  = os.path.join(tmpdir, f"raw_{i}.mp4")
        proc = os.path.join(tmpdir, f"clip_{i}.mp4")
        if download_file(url, raw) and process_clip(raw, proc):
            processed.append(proc)

    if not processed:
        return jsonify({"error": "Failed to process video clips"}), 500

    merged = os.path.join(tmpdir, "merged.mp4")
    final  = os.path.join(tmpdir, f"final_{job_id}.mp4")

    if not concat_clips(processed, merged):
        return jsonify({"error": "Failed to concat clips"}), 500

    if not add_overlays(merged, final, hook, cta):
        return jsonify({"error": "Failed to add overlays"}), 500

    # 4. Return video + all content as JSON
    with open(final, "rb") as vf:
        video_b64 = base64.b64encode(vf.read()).decode()

    return jsonify({
        "status":   "success",
        "day":      day_name,
        "theme":    theme,
        "content":  content,
        "video_b64": video_b64,
        "filename": f"sajz_garagex_{day_name.lower()}_{job_id}.mp4"
    })


@app.route("/assemble-only", methods=["POST"])
def assemble_only():
    """
    Lightweight endpoint: provide your own video_urls + hook + cta.
    Returns the assembled MP4 file directly.
    """
    data = request.json or {}
    video_urls = data.get("video_urls", [])
    hook = data.get("hook", "Watch This")
    cta  = data.get("cta", "Follow @sajzgaragex")

    if not video_urls:
        return jsonify({"error": "Provide video_urls"}), 400

    tmpdir = tempfile.mkdtemp()
    job_id = str(uuid.uuid4())[:8]

    processed = []
    for i, url in enumerate(video_urls[:4]):
        raw  = os.path.join(tmpdir, f"raw_{i}.mp4")
        proc = os.path.join(tmpdir, f"clip_{i}.mp4")
        if download_file(url, raw) and process_clip(raw, proc):
            processed.append(proc)

    if not processed:
        return jsonify({"error": "No clips processed"}), 500

    merged = os.path.join(tmpdir, "merged.mp4")
    final  = os.path.join(tmpdir, f"final_{job_id}.mp4")

    concat_clips(processed, merged)
    add_overlays(merged, final, hook, cta)

    return send_file(final, mimetype="video/mp4",
                     as_attachment=True,
                     download_name=f"sajz_{job_id}.mp4")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
