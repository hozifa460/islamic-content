import urllib.request
import xml.etree.ElementTree as ET
import json
import os
import sys
import time
from huggingface_hub import HfApi

sys.stdout.reconfigure(encoding='utf-8')

HF_TOKEN = os.environ.get("HF_TOKEN")
DATASET_REPO = "hozifa1/Telewat_Daawa_And_Channels"

api = HfApi(token=HF_TOKEN)

def log(msg):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [AUTO-SYNC-WORKER] {msg}", flush=True)

def fetch_rss_entries(channel_id):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        xml_data = resp.read().decode('utf-8')
    
    root = ET.fromstring(xml_data)
    ns = {
        'atom': 'http://www.w3.org/2005/Atom',
        'yt': 'http://www.youtube.com/xml/schemas/2015'
    }
    
    entries = []
    for entry in root.findall('atom:entry', ns):
        video_id = entry.find('yt:videoId', ns).text
        title = entry.find('atom:title', ns).text
        published = entry.find('atom:published', ns).text
        entries.append({
            'videoId': video_id,
            'title': title,
            'published': published
        })
    return entries

def detect_video_bucket(video_id):
    # Check if Short
    try:
        req = urllib.request.Request(f"https://www.youtube.com/shorts/{video_id}", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if "/shorts/" in resp.geturl():
                return "shorts"
    except Exception:
        pass

    # Check if Live
    try:
        req = urllib.request.Request(f"https://www.youtube.com/watch?v={video_id}", headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            if '"isLive":true' in html or '"isLiveContent":true' in html:
                return "live"
    except Exception:
        pass

    return "videos"

def load_channels_config():
    # The tools copy is the single canonical local configuration.
    local_paths = [
        os.path.join(os.path.dirname(__file__), "youtube_channels.json")
    ]
    for p in local_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f).get("channels", [])

    # Priority 2: Hugging Face dataset online URL
    url = f"https://huggingface.co/datasets/{DATASET_REPO}/raw/main/Dawah_And_Channels/youtube_channels.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8')).get("channels", [])

def run_sync():
    log("🚀 Starting Full 24/7 Sync for Hugging Face Dataset...")

    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN is required for dataset synchronization.")

    channels = load_channels_config()
    log(f"Loaded {len(channels)} configured channels.")
    channel_ids = [ch.get("channelId") for ch in channels if ch.get("channelId")]
    category_ids = [ch.get("categoryId") for ch in channels if ch.get("categoryId")]
    if len(channel_ids) != len(set(channel_ids)):
        raise ValueError("Duplicate YouTube channelId values found in configuration.")
    if len(category_ids) != len(set(category_ids)):
        raise ValueError("Duplicate categoryId values found in configuration.")

    total_new_items = 0

    seen_cat_ids = set()
    for ch in channels:
        cat_id = ch.get("categoryId")
        channel_id = ch.get("channelId")
        channel_name = ch.get("channelName", cat_id)

        if not channel_id or not cat_id or cat_id in seen_cat_ids:
            continue
        seen_cat_ids.add(cat_id)

        try:
            entries = fetch_rss_entries(channel_id)
            buckets = {"live": [], "videos": [], "shorts": []}
            for e in entries:
                b = detect_video_bucket(e['videoId'])
                item = {
                    "title": e['title'],
                    "subtitle": channel_name,
                    "publishedAt": e.get("published", ""),
                    "audioUrl": f"https://www.youtube.com/watch?v={e['videoId']}",
                    "imageUrl": f"https://i.ytimg.com/vi/{e['videoId']}/hqdefault.jpg",
                    "videoUrl": f"https://www.youtube.com/watch?v={e['videoId']}"
                }
                buckets[b].append(item)

            for b_type, items in buckets.items():
                if not items:
                    continue

                file_rel_path = f"Dawah_And_Channels/{cat_id}/{cat_id}.{b_type}.json"
                existing_items = []
                existing_meta = {}

                try:
                    f_url = f"https://huggingface.co/datasets/{DATASET_REPO}/raw/main/{file_rel_path}"
                    req_f = urllib.request.Request(f_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_f) as resp_f:
                        f_data = json.loads(resp_f.read().decode('utf-8'))
                        existing_meta = f_data
                        existing_items = f_data.get("items", [])
                except Exception:
                    pass

                existing_urls = {it.get("videoUrl") for it in existing_items if isinstance(it, dict)}
                new_to_add = [it for it in items if it["videoUrl"] not in existing_urls]

                if new_to_add:
                    log(f"  -> Adding {len(new_to_add)} NEW items to {b_type} for {channel_name}")
                    total_new_items += len(new_to_add)
                    merged_items = new_to_add + existing_items
                    payload = {
                        "id": cat_id,
                        "title": channel_name,
                        "emoji": "🎥" if b_type == "videos" else ("🔴" if b_type == "live" else "⚡"),
                        "description": f"{channel_name} - {b_type.upper()}",
                        "gradientColors": ["#111827", "#1f2937"],
                        "imageUrl": existing_meta.get("imageUrl", f"https://i.ytimg.com/vi/{items[0]['audioUrl'].split('=')[-1]}/hqdefault.jpg"),
                        "items": merged_items
                    }
                    api.upload_file(
                        path_or_fileobj=json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8'),
                        path_in_repo=file_rel_path,
                        repo_id=DATASET_REPO,
                        repo_type="dataset",
                        commit_message=f"auto-sync {cat_id}.{b_type}.json"
                    )

        except Exception as err:
            log(f"Notice for {cat_id}: {err}")

    # Rebuild Dawah_And_Channels/index.json
    log("\nRebuilding Dawah_And_Channels/index.json...")
    tree = api.list_repo_tree(repo_id=DATASET_REPO, repo_type="dataset", recursive=True)
    all_paths = [item.path for item in tree if item.path.startswith("Dawah_And_Channels/") and item.path.endswith(".json")]
    idx_files = [p.replace("Dawah_And_Channels/", "") for p in sorted(all_paths) if not p.endswith("index.json") and not p.endswith("youtube_channels.json")]

    api.upload_file(
        path_or_fileobj=json.dumps({"files": idx_files}, ensure_ascii=False, indent=2).encode('utf-8'),
        path_in_repo="Dawah_And_Channels/index.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
        commit_message="rebuild index.json"
    )
    log(f"🎯 Sync Completed Successfully! ({total_new_items} new items added).")

if __name__ == "__main__":
    run_sync()
