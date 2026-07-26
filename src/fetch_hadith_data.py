import os
import json
import urllib.request

def fetch_bukhari_hadiths():
    url = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-bukhari.json"
    print(f"[*] Downloading Sahih al-Bukhari dataset from {url}...")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
        hadiths = data.get("hadiths", [])
        print(f"[+] Downloaded {len(hadiths)} Hadiths successfully!")
        
        bukhari_chunks = []
        for idx, h in enumerate(hadiths):
            text = h.get("text", "").strip()
            hadith_number = h.get("hadithnumber", idx + 1)
            
            if len(text) > 20:
                bukhari_chunks.append({
                    "id": f"sahih_bukhari_h{hadith_number}",
                    "book_name": "صحيح البخاري (المصدر الحرفي)",
                    "page_number": hadith_number,  # Storing Hadith number as page/ref
                    "content": f"حديث رقم ({hadith_number}): {text}"
                })
                
        # Merge with existing processed_chunks.json if it exists
        chunks_file = "data/processed_chunks.json"
        existing_chunks = []
        if os.path.exists(chunks_file):
            with open(chunks_file, "r", encoding="utf-8") as f:
                existing_chunks = json.load(f)
                
        combined_chunks = existing_chunks + bukhari_chunks
        
        with open(chunks_file, "w", encoding="utf-8") as f:
            json.dump(combined_chunks, f, ensure_ascii=False, indent=2)
            
        print(f"[+] Merged Sahih al-Bukhari ({len(bukhari_chunks)} hadiths). Total dataset chunks: {len(combined_chunks)}")
        return combined_chunks
        
    except Exception as e:
        print(f"[!] Error downloading Sahih al-Bukhari: {e}")
        return []

if __name__ == "__main__":
    fetch_bukhari_hadiths()
