"""
Sajz GarageX — Automated Video Assembly Service v2
No AI API needed — hardcoded weekly content, 100% reliable
Uses FFmpeg + Pexels free stock footage
"""
 
from flask import Flask, request, jsonify
import subprocess, requests, os, tempfile, uuid, logging, re, base64
from datetime import datetime
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Flask(__name__)
 
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
 
WEEKLY_CONTENT = {
    0: {
        "topic": "Ferrari vs Lamborghini Last V12 War",
        "pexels_search": "supercar ferrari lamborghini",
        "hook": "THE LAST V12s ALIVE",
        "cta": "Follow @sajzgaragex",
        "youtube_title": "Ferrari vs Lamborghini Last V12 War | Sajz GarageX",
        "youtube_description": "Ferrari 12Cilindri vs Lamborghini Revuelto. Two V12 legends. Sajz GarageX breaks down the specs, sound, and soul.\n\n🔔 Subscribe to Sajz GarageX!\n📸 @sajzgaragex | @thesajz\n💛 linktr.ee/thesajz",
        "youtube_tags": "cars,supercars,Ferrari,Lamborghini,V12,car review,automotive,sports car,exotic cars,Sajz GarageX,petrolhead,horsepower,naturally aspirated,car culture,luxury cars",
        "pinned_comment": "🔥 Ferrari or Lamborghini? Drop your vote! Follow @sajzgaragex 💛 linktr.ee/thesajz",
        "ig_thesajz": "Ferrari vs Lamborghini — THE LAST V12 WAR 🔴🟡\n\nOne screams at 9,000rpm. One hits 1,015hp.\nBoth naturally aspirated. Both about to be history.\n\nDrop 🔴 Ferrari or 🟡 Lambo 👇\n\n💛 linktr.ee/thesajz\n\n#cars #supercars #carporn #carlife #carsofinstagram #automotive #Ferrari #Lamborghini #sportscar #exoticcars #luxurycars #carculture #motorhead #petrolhead #carenthusiast #carlovers #dreamcar #v12 #horsepower #racecar #carshow #modified #stance #turbo #v8",
        "ig_sajzgaragex": "The V12 is dying. These two are the eulogy. 🖤\n\nFerrari 12Cilindri — 830hp, 9,000rpm.\nLamborghini Revuelto — 1,015hp hybrid V12.\n\n🎬 Full breakdown → Sajz GarageX YouTube\n💛 linktr.ee/thesajz\n\n#sajzgaragex #ferrari #lamborghini #v12 #supercar #cargram #bmwm #carguy #garagelife #motorsport #carsandcoffee #trackday #petrolhead #exoticcars #carporn #bmwlife #autodetailing #drifting #bmwcommunity #automotivephotography #bmwmotorsport #bmwlovers #garagebuild #carmod #projectcar"
    },
    1: {
        "topic": "Top 5 Underrated Cars Nobody Talks About",
        "pexels_search": "classic vintage car street",
        "hook": "SLEPT ON FOREVER",
        "cta": "Follow @sajzgaragex",
        "youtube_title": "Top 5 Underrated Cars Nobody Buys | Sajz GarageX",
        "youtube_description": "These 5 cars are criminally underrated. Sajz GarageX reveals the hidden gems real petrolheads actually drive.\n\n🔔 Subscribe to Sajz GarageX!\n📸 @sajzgaragex | @thesajz\n💛 linktr.ee/thesajz",
        "youtube_tags": "underrated cars,hidden gem cars,best used cars,car review,automotive,sports car,Sajz GarageX,petrolhead,car buying guide,best cars 2026,overlooked cars,luxury cars",
        "pinned_comment": "💬 Which underrated car would YOU buy? Comment! Follow @sajzgaragex 💛 linktr.ee/thesajz",
        "ig_thesajz": "5 cars the internet SLEPT on 😤\n\nWhile everyone buys the same thing, real petrolheads know better.\n\nDrop yours 👇\n\n💛 linktr.ee/thesajz\n\n#cars #carporn #carlife #carsofinstagram #automotive #sportscar #exoticcars #luxurycars #carculture #motorhead #petrolhead #carenthusiast #carlovers #dreamcar #horsepower #racecar #carshow #modified #stance #turbo #v8 #instacars #cargram #bmw #supercars",
        "ig_sajzgaragex": "The cars everyone ignored. The cars real drivers know. 🔑\n\n🎬 Full list → Sajz GarageX YouTube\n💛 linktr.ee/thesajz\n\n#sajzgaragex #bmwm #carguy #garagelife #carmod #cargram #bmwlovers #garagebuild #automotivephotography #bmwlife #carsandcoffee #motorsport #trackday #petrolhead #bmwcommunity #drifting #autodetailing #bmwmotorsport #projectcar #carreview #bmwm3 #bmwm4 #mpower #carculture #stance"
    },
    2: {
        "topic": "BMW M3 vs M4 Which One Actually Wins",
        "pexels_search": "BMW sports car M series",
        "hook": "M3 OR M4 SETTLE IT",
        "cta": "Follow @sajzgaragex",
        "youtube_title": "BMW M3 vs M4 Which One Actually Wins | Sajz GarageX",
        "youtube_description": "BMW M3 vs M4 — same engine, completely different experience. Sajz GarageX settles the debate every BMW fan has.\n\n🔔 Subscribe to Sajz GarageX!\n📸 @sajzgaragex | @thesajz\n💛 linktr.ee/thesajz",
        "youtube_tags": "BMW M3,BMW M4,BMW M series,BMW review,car comparison,automotive,sports car,Sajz GarageX,petrolhead,BMW,M power,best BMW,car review,luxury cars,track car",
        "pinned_comment": "🚗 M3 or M4? Drop your answer! Follow @sajzgaragex 💛 linktr.ee/thesajz",
        "ig_thesajz": "BMW M3 vs M4. Same engine. Different soul. 🔵⚪\n\nOne is a sedan. One is a coupe.\nBoth will ruin every other car for you.\n\nWhich one? 👇\n\n💛 linktr.ee/thesajz\n\n#BMW #BMWM3 #BMWM4 #carporn #carlife #carsofinstagram #automotive #sportscar #luxurycars #carculture #motorhead #petrolhead #carenthusiast #carlovers #dreamcar #horsepower #racecar #modified #bmwmpower #bmwlovers #stance #turbo #bmwclub #mpower #supercars",
        "ig_sajzgaragex": "The BMW debate that never ends 🔥\n\nM3 — four doors, all practicality, same savage engine.\nM4 — two doors, pure driver focus.\n\n🎬 Full breakdown → Sajz GarageX YouTube\n💛 linktr.ee/thesajz\n\n#sajzgaragex #bmwm3 #bmwm4 #bmwm #mpower #bmwlovers #garagebuild #carmod #cargram #bmwcommunity #automotivephotography #bmwlife #carsandcoffee #motorsport #carguy #garagelife #drifting #trackday #petrolhead #bmwmotorsport #autodetailing #projectcar #bmwclub #carreview #stance"
    },
    3: {
        "topic": "Craziest Car Moments of 2026 So Far",
        "pexels_search": "sports car drift race burnout",
        "hook": "2026 IS INSANE FOR CARS",
        "cta": "Follow @sajzgaragex",
        "youtube_title": "Craziest Car Moments of 2026 So Far | Sajz GarageX",
        "youtube_description": "2026 has already delivered insane car moments. Sajz GarageX recaps the moments every petrolhead needs to see.\n\n🔔 Subscribe to Sajz GarageX!\n📸 @sajzgaragex | @thesajz\n💛 linktr.ee/thesajz",
        "youtube_tags": "best cars 2026,car moments 2026,crazy car videos,car review,automotive,sports car,Sajz GarageX,petrolhead,viral car,drag race,car meet,fastest cars,supercar,luxury cars",
        "pinned_comment": "🔥 Which moment was your favourite? Follow @sajzgaragex 💛 linktr.ee/thesajz",
        "ig_thesajz": "2026 is already an all-timer for cars 🏎️🔥\n\nThe launches. The records. The reveals.\nPetrolheads are eating good this year.\n\nFavourite moment so far? 👇\n\n💛 linktr.ee/thesajz\n\n#cars #supercars #carporn #carlife #carsofinstagram #automotive #sportscar #exoticcars #luxurycars #carculture #motorhead #petrolhead #carenthusiast #carlovers #dreamcar #horsepower #racecar #carshow #modified #stance #turbo #v8 #instacars #2026cars #viral",
        "ig_sajzgaragex": "The car world in 2026 is not playing games 💀\n\n🎬 Full recap → Sajz GarageX YouTube\n💛 linktr.ee/thesajz\n\n#sajzgaragex #bmwm #carguy #garagelife #carmod #cargram #bmwlovers #automotivephotography #carsandcoffee #motorsport #trackday #petrolhead #bmwcommunity #drifting #autodetailing #bmwmotorsport #projectcar #carreview #stance #mpower #bmwm3 #bmwm4 #supercar #exoticcars #carporn"
    },
    4: {
        "topic": "Build Your Dream 3 Car Garage",
        "pexels_search": "luxury car garage exotic",
        "hook": "YOUR DREAM 3 CAR GARAGE",
        "cta": "Follow @sajzgaragex",
        "youtube_title": "Build Your Dream 3 Car Garage Sajz Edition | Sajz GarageX",
        "youtube_description": "If you could only have 3 cars, what would they be? Sajz GarageX builds the ultimate dream garage. What is in yours?\n\n🔔 Subscribe to Sajz GarageX!\n📸 @sajzgaragex | @thesajz\n💛 linktr.ee/thesajz",
        "youtube_tags": "dream garage,best cars,car collection,automotive,sports car,Sajz GarageX,petrolhead,luxury cars,exotic cars,garage build,dream car,BMW,supercar,best 3 cars",
        "pinned_comment": "🏎️ What 3 cars in YOUR dream garage? Follow @sajzgaragex 💛 linktr.ee/thesajz",
        "ig_thesajz": "3 cars. That is all you get. Choose wisely 🏎️🏎️🏎️\n\nOne for the track. One for the daily. One for the show.\n\nDrop your 3 👇\n\n💛 linktr.ee/thesajz\n\n#cars #supercars #carporn #carlife #carsofinstagram #dreamcar #automotive #sportscar #exoticcars #luxurycars #carculture #motorhead #petrolhead #carenthusiast #carlovers #horsepower #carshow #modified #stance #turbo #v8 #instacars #garage #dreamgarage #BMW",
        "ig_sajzgaragex": "The Sajz GarageX dream garage. 3 cars. No compromises. 🖤\n\n🎬 Sajz builds his on YouTube → Sajz GarageX\n💛 linktr.ee/thesajz\n\n#sajzgaragex #bmwm #carguy #garagelife #garagebuild #carmod #cargram #bmwlovers #automotivephotography #bmwlife #carsandcoffee #motorsport #drifting #trackday #petrolhead #bmwcommunity #autodetailing #bmwmotorsport #projectcar #carreview #dreamgarage #exoticcars #carporn #stance #mpower"
    },
    5: {
        "topic": "Best BMW Mods Under 1000 Dollars",
        "pexels_search": "BMW car modified custom",
        "hook": "1000 BUCKS TRANSFORMS YOUR BMW",
        "cta": "Follow @sajzgaragex",
        "youtube_title": "Best BMW Mods Under 1000 That Actually Work | Sajz GarageX",
        "youtube_description": "You do not need to spend a fortune to transform your BMW. Sajz GarageX breaks down the best mods under $1000.\n\n🔔 Subscribe to Sajz GarageX!\n📸 @sajzgaragex | @thesajz\n💛 linktr.ee/thesajz",
        "youtube_tags": "BMW mods,best BMW modifications,cheap BMW mods,BMW upgrade,car modification,automotive,BMW M series,Sajz GarageX,petrolhead,BMW tuning,car mods under 1000,BMW performance",
        "pinned_comment": "🔧 Favourite BMW mod? Drop it! Follow @sajzgaragex 💛 linktr.ee/thesajz",
        "ig_thesajz": "1000 dollars and your BMW will never be the same 🔧🔥\n\nSajz GarageX has the list that actually works.\n\nSave this post 👇\n\n💛 linktr.ee/thesajz\n\n#BMW #carporn #carlife #carsofinstagram #automotive #bmwmods #sportscar #luxurycars #carculture #motorhead #petrolhead #carenthusiast #carlovers #modified #bmwmpower #bmwlovers #stance #turbo #bmwclub #mpower #carmod #bmwm #garagelife #carshow #instacars",
        "ig_sajzgaragex": "The $1000 BMW transformation guide 💰🔧\n\nExhaust. Intake. Suspension. Interior.\nOnly real mods that work.\n\n🎬 Full list → Sajz GarageX YouTube\n💛 linktr.ee/thesajz\n\n#sajzgaragex #bmwm #bmwmods #garagebuild #carmod #cargram #bmwlovers #automotivephotography #bmwlife #carsandcoffee #motorsport #carguy #garagelife #drifting #trackday #petrolhead #bmwcommunity #autodetailing #bmwmotorsport #projectcar #carreview #mpower #bmwm3 #bmwm4 #stance"
    },
    6: {
        "topic": "Why the Porsche 911 Beats Everything",
        "pexels_search": "Porsche sports car highway",
        "hook": "WHY 911 BEATS EVERYTHING",
        "cta": "Follow @sajzgaragex",
        "youtube_title": "Why the Porsche 911 Beats Every Sports Car | Sajz GarageX",
        "youtube_description": "The Porsche 911 has been the benchmark for over 60 years. Sajz GarageX explains why no car has managed to dethrone it.\n\n🔔 Subscribe to Sajz GarageX!\n📸 @sajzgaragex | @thesajz\n💛 linktr.ee/thesajz",
        "youtube_tags": "Porsche 911,best sports car,Porsche review,car review,automotive,sports car,Sajz GarageX,petrolhead,luxury cars,Porsche GT3,911 Turbo S,best car ever,sports car comparison",
        "pinned_comment": "🏆 Is the 911 the GOAT? Comment! Follow @sajzgaragex 💛 linktr.ee/thesajz",
        "ig_thesajz": "60 years. Still undefeated. The Porsche 911 🏆\n\nEvery generation tries to beat it. None can.\n\nAm I wrong? 👇\n\n💛 linktr.ee/thesajz\n\n#Porsche #Porsche911 #carporn #carlife #carsofinstagram #automotive #sportscar #exoticcars #luxurycars #carculture #motorhead #petrolhead #carenthusiast #carlovers #dreamcar #horsepower #racecar #carshow #stance #turbo #instacars #supercar #GT3 #911TurboS #BMW",
        "ig_sajzgaragex": "The 911 is not a car. It is a religion 🙏\n\n🎬 Full breakdown → Sajz GarageX YouTube\n💛 linktr.ee/thesajz\n\n#sajzgaragex #porsche911 #porsche #bmwm #carguy #garagelife #carmod #cargram #automotivephotography #carsandcoffee #motorsport #trackday #petrolhead #bmwcommunity #drifting #autodetailing #bmwmotorsport #projectcar #carreview #supercar #exoticcars #carporn #stance #mpower #GT3"
    }
}
 
 
def get_pexels_videos(query: str, count: int = 4) -> list:
    if not PEXELS_API_KEY:
        return []
    headers = {"Authorization": PEXELS_API_KEY}
    params  = {"query": query, "per_page": count, "orientation": "portrait", "size": "medium"}
    try:
        r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=15)
        r.raise_for_status()
        urls = []
        for v in r.json().get("videos", []):
            files = sorted(v.get("video_files", []), key=lambda x: x.get("width", 0), reverse=True)
            for f in files:
                if f.get("width", 0) >= 720:
                    urls.append(f["link"])
                    break
        return urls[:count]
    except Exception as e:
        logger.error(f"Pexels error: {e}")
        return []
 
 
def download_file(url: str, dest: str) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=45)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=16384):
                f.write(chunk)
        return True
    except Exception as e:
        logger.warning(f"Download failed: {e}")
        return False
 
 
def safe_text(text: str) -> str:
    return re.sub(r"[:'\\]", "", text)[:50]
 
 
def process_clip(src: str, dst: str) -> bool:
    cmd = ["ffmpeg", "-i", src,
           "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
           "-c:v", "libx264", "-preset", "fast", "-crf", "24", "-an", "-t", "8",
           dst, "-y"]
    return subprocess.run(cmd, capture_output=True, timeout=120).returncode == 0
 
 
def concat_clips(clips: list, out: str) -> bool:
    cf = os.path.join(os.path.dirname(out), "concat.txt")
    with open(cf, "w") as f:
        for p in clips:
            f.write(f"file '{p}'\n")
    return subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", cf, "-c", "copy", out, "-y"],
                          capture_output=True, timeout=120).returncode == 0
 
 
def add_overlays(src: str, dst: str, hook: str, cta: str) -> bool:
    vf = (f"drawtext=text='{safe_text(hook)}':fontsize=54:fontcolor=white:x=(w-tw)/2:y=90:box=1:boxcolor=black@0.65:boxborderw=14,"
          f"drawtext=text='{safe_text(cta)}':fontsize=40:fontcolor=white:x=(w-tw)/2:y=h-110:box=1:boxcolor=black@0.65:boxborderw=10")
    return subprocess.run(["ffmpeg", "-i", src, "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-crf", "23", dst, "-y"],
                          capture_output=True, timeout=180).returncode == 0
 
 
@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Sajz GarageX v2 — no Gemini needed"})
 
 
@app.route("/generate", methods=["POST"])
def generate():
    data    = request.json or {}
    weekday = data.get("weekday", datetime.now().weekday())
    content = WEEKLY_CONTENT[int(weekday) % 7]
    day_names = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    logger.info(f"Generating: {content['topic']}")
 
    video_urls = get_pexels_videos(content["pexels_search"], 4) or get_pexels_videos("sports car driving", 4)
    if not video_urls:
        return jsonify({"error": "No Pexels videos — check PEXELS_API_KEY"}), 500
 
    tmpdir = tempfile.mkdtemp()
    job_id = str(uuid.uuid4())[:8]
    processed = []
 
    for i, url in enumerate(video_urls):
        raw = os.path.join(tmpdir, f"raw_{i}.mp4")
        proc = os.path.join(tmpdir, f"clip_{i}.mp4")
        if download_file(url, raw) and process_clip(raw, proc):
            processed.append(proc)
 
    if not processed:
        return jsonify({"error": "Video processing failed"}), 500
 
    merged = os.path.join(tmpdir, "merged.mp4")
    final  = os.path.join(tmpdir, f"final_{job_id}.mp4")
 
    if not concat_clips(processed, merged) or not add_overlays(merged, final, content["hook"], content["cta"]):
        return jsonify({"error": "Video assembly failed"}), 500
 
    with open(final, "rb") as vf:
        video_b64 = base64.b64encode(vf.read()).decode()
 
    return jsonify({
        "status": "success",
        "day": day_names[int(weekday) % 7],
        "topic": content["topic"],
        "content": content,
        "video_b64": video_b64,
        "filename": f"sajz_{day_names[int(weekday)%7].lower()}_{job_id}.mp4"
    })
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
 
