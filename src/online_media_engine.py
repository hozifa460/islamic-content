import os
import re
import json
import urllib.request
import threading
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.vector_store import normalize_arabic

MEDIA_CACHE_FILE = "data/online_media_cache.json"

DIALECT_MEDIA_PREFIXES = [
    'جيبلي', 'جيب لي', 'جيب', 'هاتلي', 'هات لي', 'هات', 'شغللي', 'شغل لي', 'شغل', 
    'سمعني', 'سمعني تلاوة', 'عايز', 'عايز استمع', 'اريد', 'أريد', 'ابحث عن', 'اسمها', 'اسمه',
    'احدث', 'أحدث', 'اخر', 'أخر', 'جديد', 'فيديوهات', 'فيديو', 'شورتس', 'بث', 'مباشر'
]

SPEAKER_ALIASES = {
    'يوسف جو': ['يوسف جو', 'جديد يوسف جو', 'ypusef_joe', 'yusef_joe', 'yousef_joe'],
    'زين خير الله': ['زين خير الله', 'zein_khair_allah'],
    'المنشاوي': ['المنشاوي', 'منشاوي', 'minshawi', 'tajweed_menshawy'],
    'عبد الباسط': ['عبد الباسط', 'عبدالباسط', 'baset'],
    'الشعراوي': ['الشعراوي', 'shaarawy', 'alshaarawy'],
    'إياد القنيبي': ['القنيبي', 'إياد القنيبي', 'اياد القنيبي', 'iyad_alqunibi'],
    'عثمان الخميس': ['عثمان الخميس', 'الشيخ عثمان الخميس', 'عثمان الخمس', 'othman_alkhames'],
    'هيثم طلعت': ['هيثم طلعت', 'دكتور هيثم طلعت', 'الدكتور هيثم طلعت', 'haytham_talaat'],
    'مصطفى العدوي': ['مصطفى العدوي', 'الشيخ مصطفى العدوي', 'mostafa_aladawy'],
    'الحويني': ['الحويني', 'أبو إسحاق الحويني', 'ابو اسحاق الحويني', 'howini'],
    'عبد الله رشدي': ['عبد الله رشدي', 'عبدالله رشدي', 'دكتور عبدالله رشدي', 'abdallah_roshdi'],
    'ذاكر نايك': ['ذاكر نايك', 'دكتور ذاكر نايك', 'dr_zaker_naik'],
    'معاذ عليان': ['معاذ عليان', 'moaz_alian'],
    'ياسر ممدوح': ['ياسر ممدوح', 'yasser_mamdouh'],
    'محمد الغليظ': ['محمد الغليظ', 'mohamed_algaleez'],
    'عاصم هيثم': ['عاصم هيثم', 'دكتور عاصم هيثم', 'asem_haythem'],
    'بدون ورق': ['بدون ورق', 'bedon_waraq'],
    'كان زهوقا': ['كان زهوقا', 'kan_zahoka'],
    'تاريخنا': ['تاريخنا', 'tarekhna'],
    'سراج حياني': ['سراج حياني', 'siraj_hyani'],
    'محمد غنايم': ['محمد غنايم', 'mohamed_ghanayem'],
    'إبراهيم عبد الغني': ['إبراهيم عبد الغني', 'ابراهيم عبد الغني', 'ibrahem_abdel_ghany'],
    'مناظرات': ['مناظرات', 'monazarat'],
    'الساخر الهادف': ['الساخر الهادف', 'alsakher_alhadef'],
    'وليد إسماعيل': ['وليد إسماعيل', 'وليد اسماعيل', 'waleed_ismaeel'],
    'يوسف القط': ['يوسف القط', 'yousef_alkott'],
    'Towards Eternity': ['towards eternity', 'eternity'],
    'البحبحاني': ['البحبحاني', 'albahbhany'],
    'أنس أكشن': ['أنس أكشن', 'انس اكشن', 'anas_action'],
    'شريف علي': ['شريف علي', 'شريف على', 'sherif_ali'],
    'عبد الدائم كحيل': ['عبد الدائم كحيل', 'abd_aldem_kaheel'],
    'محمود داوود': ['محمود داوود', 'mahmoud_dawood'],
    'محمود نصار': ['محمود نصار', 'mahmoud_nassar'],
    'علاء إبراهيم': ['علاء إبراهيم', 'علاء ابراهيم', 'alaa_ibrahim'],
    'محمد فرماوي': ['محمد فرماوي', 'mohamed_faramawy']
}

def clean_media_query(query: str) -> str:
    """Strip dialect verbs while keeping core search terms."""
    q = normalize_arabic(query)
    for p in DIALECT_MEDIA_PREFIXES:
        norm_p = normalize_arabic(p)
        q = re.sub(rf'\b{norm_p}\b', '', q)
    q = re.sub(r'[ \t]+', ' ', q).strip()
    return q if q else normalize_arabic(query)

class OnlineMediaEngine:
    """Live Master Media Search Engine for 33 YouTube Channels & Quran Recitations."""

    HF_INDEX_URL = "https://huggingface.co/datasets/hozifa1/Telewat_Daawa_And_Channels/raw/main/Dawah_And_Channels/index.json"

    def __init__(self):
        self.media_items = []
        self.corpus_normalized = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.is_loaded = False
        
        if os.path.exists(MEDIA_CACHE_FILE):
            self.load_from_cache()
        else:
            threading.Thread(target=self.fetch_and_cache_media, daemon=True).start()

    def load_from_cache(self):
        try:
            with open(MEDIA_CACHE_FILE, "r", encoding="utf-8") as f:
                self.media_items = json.load(f)
            self.build_index()
            print(f"[+] Loaded {len(self.media_items)} master media items!")
        except Exception as e:
            print(f"[!] Media cache load error: {e}")
            threading.Thread(target=self.fetch_and_cache_media, daemon=True).start()

    def fetch_and_cache_media(self):
        try:
            print("[*] Fetching media index from Hugging Face...")
            req = urllib.request.Request(self.HF_INDEX_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=15) as res:
                self.media_items = json.loads(res.read().decode('utf-8'))
                os.makedirs(os.path.dirname(MEDIA_CACHE_FILE), exist_ok=True)
                with open(MEDIA_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.media_items, f, ensure_ascii=False)
                self.build_index()
        except Exception as e:
            print(f"[!] Media fetch error: {e}")

    def build_index(self):
        if not self.media_items:
            return
        raw_texts = [f"{m['title']} {m['speaker']} {m['category']}" for m in self.media_items]
        self.corpus_normalized = [normalize_arabic(t) for t in raw_texts]

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            analyzer="word",
            min_df=1
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_normalized)
        self.is_loaded = True

    def is_shorts(self, item: dict) -> bool:
        url = (item.get('video_url', '') or item.get('audio_url', '')).lower()
        title = item.get('title', '').lower()
        return ('/shorts/' in url or '#shorts' in title or '#short' in title or 'شورت' in title or 'مقطع قصير' in title)

    def is_live_or_podcast(self, item: dict) -> bool:
        url = (item.get('video_url', '') or item.get('audio_url', '')).lower()
        title = item.get('title', '').lower()
        norm_t = normalize_arabic(title)
        return ('بث' in norm_t or 'مباشر' in norm_t or 'بودكاست' in norm_t or 'حوار' in norm_t or 'لقاء' in norm_t or 'live' in url or 'stream' in url or 'podcast' in title or 'podcast' in url)

    def search(self, query: str, top_k=3):
        if not self.is_loaded or not self.media_items or self.tfidf_matrix is None:
            return []

        clean_q = clean_media_query(query)
        norm_raw_q = normalize_arabic(query)

        # Detect intent flags
        recency_keywords = ['احدث', 'أحدث', 'اخر', 'أخر', 'جديد', 'الجديدة', 'الجديد', 'الحديثة', 'اخيرة', 'أخيرة', 'مؤخرا', 'مؤخراً']
        is_recency = any(k in norm_raw_q for k in recency_keywords)

        shorts_keywords = ['شورتس', 'شورت', 'قصيرة', 'قصار', 'shorts', 'short']
        is_shorts_req = any(k in norm_raw_q for k in shorts_keywords)

        live_keywords = ['بث', 'مباشر', 'بودكاست', 'حوار', 'لقاء', 'مباشرة', 'live', 'stream', 'podcast']
        is_live_req = any(k in norm_raw_q for k in live_keywords)

        is_explicit_video = any(k in query for k in ['فيديو', 'مرئي', 'يوتيوب', 'مقطع'])
        is_explicit_audio = any(k in query for k in ['صوت', 'صوتي', 'تلاوة', 'mp3'])

        # Strict Target Speaker Detection
        target_speaker_keywords = []
        for speaker_label, kw_list in SPEAKER_ALIASES.items():
            if any(normalize_arabic(k) in norm_raw_q for k in kw_list):
                target_speaker_keywords.extend([normalize_arabic(k) for k in kw_list])
                break

        query_vec = self.vectorizer.transform([clean_q])
        sims = cosine_similarity(query_vec, self.tfidf_matrix)[0].copy()

        # Track relative speaker match count to prioritize newest videos (lower index = newer)
        speaker_match_counters = {}

        for idx in range(len(self.media_items)):
            if idx < len(self.corpus_normalized):
                item = self.media_items[idx]
                url = item.get('video_url', '') or item.get('audio_url', '')
                spk_norm = normalize_arabic(item.get('speaker', ''))
                cat_norm = normalize_arabic(item.get('category', ''))
                doc_norm = self.corpus_normalized[idx]

                # Link Health Validation: Must have valid URL
                if not url or url.strip() == "":
                    sims[idx] = -999.0
                    continue

                # STRICT SPEAKER MANDATORY FILTER: Strict Channel matching (Zero Leak Policy)
                if target_speaker_keywords:
                    speaker_matched = any(kw in spk_norm or kw in cat_norm for kw in target_speaker_keywords)
                    if speaker_matched:
                        sims[idx] += 50.0

                        # Counter for relative channel index
                        rel_idx = speaker_match_counters.get(spk_norm, 0)
                        speaker_match_counters[spk_norm] = rel_idx + 1

                        # Recency Boosting: lower index in channel list = newest video!
                        if is_recency:
                            sims[idx] += max(0.0, 100.0 - (rel_idx * 5.0))
                    else:
                        sims[idx] = -999.0 # ZERO LEAK: Eliminate other speakers!
                        continue

                # Type Filtering (Shorts vs Live vs Video)
                item_is_shorts = self.is_shorts(item)
                item_is_live = self.is_live_or_podcast(item)

                if is_shorts_req:
                    if item_is_shorts:
                        sims[idx] += 300.0
                    else:
                        sims[idx] -= 200.0
                elif is_live_req:
                    if item_is_live:
                        sims[idx] += 300.0
                    else:
                        sims[idx] -= 200.0
                else:
                    # Regular video request: penalize shorts so full videos come first
                    if item_is_shorts:
                        sims[idx] -= 30.0

                if clean_q in doc_norm:
                    sims[idx] += 10.0

                if is_explicit_video and ('youtube.com' in url.lower() or 'youtu.be' in url.lower()):
                    sims[idx] += 15.0
                elif is_explicit_audio and ('.mp3' in url.lower() or 'archive.org' in url.lower()):
                    sims[idx] += 10.0

        top_indices = list(sims.argsort()[::-1])
        results = []
        seen_titles = set()
        seen_urls = set()

        for idx in top_indices:
            if idx < len(self.media_items) and sims[idx] > -100.0:
                item = self.media_items[idx]
                t_norm = normalize_arabic(item.get('title', ''))
                u_norm = (item.get('video_url', '') or item.get('audio_url', '')).strip().lower()
                
                if t_norm in seen_titles or u_norm in seen_urls:
                    continue
                seen_titles.add(t_norm)
                seen_urls.add(u_norm)
                
                results.append(item)
                if len(results) >= top_k:
                    break

        # Graceful fallback: If specific type filter (e.g. shorts) returned no items, fallback to speaker videos
        if not results and target_speaker_keywords:
            for idx in range(len(self.media_items)):
                item = self.media_items[idx]
                spk_norm = normalize_arabic(item.get('speaker', ''))
                cat_norm = normalize_arabic(item.get('category', ''))
                if any(kw in spk_norm or kw in cat_norm for kw in target_speaker_keywords):
                    t_norm = normalize_arabic(item.get('title', ''))
                    if t_norm not in seen_titles:
                        seen_titles.add(t_norm)
                        results.append(item)
                        if len(results) >= top_k:
                            break

        return results

if __name__ == "__main__":
    engine = OnlineMediaEngine()
    engine.load_from_cache()
    print("Testing 'احدث فيديوهات هيثم طلعت':")
    res = engine.search("احدث فيديوهات هيثم طلعت", top_k=3)
    for i, r in enumerate(res):
        print(f" ({i+1})", r['title'], "-> Speaker:", r['speaker'])
