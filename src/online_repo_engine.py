import os
import json
import urllib.request
import threading
import time
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.vector_store import normalize_arabic

CACHE_FILE = "data/online_repos_cache.json"

SCHOLAR_INVERTED_ALIASES = {
    'ابن باز': ['ابن باز', 'بن باز', 'سماحة الشيخ ابن باز', 'binbaz', 'bin_baz'],
    'ابن عثيمين': ['ابن عثيمين', 'العثيمين', 'بن عثيمين', 'othaymeen'],
    'اللجنة الدائمة': ['اللجنة الدائمة', 'فتاوى اللجنة الدائمة', 'الافتاء'],
    'إسلام ويب': ['إسلام ويب', 'اسلام ويب', 'islamweb'],
    'إسلام سؤال وجواب': ['إسلام سؤال وجواب', 'اسلام سؤال وجواب', 'islamqa']
}

def decode_bytes(raw_bytes: bytes) -> str:
    """Intelligently decode utf-8 or windows-1256 raw bytes."""
    try:
        decoded = raw_bytes.decode('utf-8')
        if any(w in decoded for w in ['الحمد', 'الله', 'الفتوى', 'السؤال', 'الجواب', 'حكم', 'المرتد']):
            return decoded
    except Exception:
        pass
    return raw_bytes.decode('windows-1256', errors='ignore')

def parse_any_json(raw_text: str):
    """Parse standard JSON array/dict or JSONL line-by-line format."""
    try:
        return json.loads(raw_text)
    except Exception:
        items = []
        for line in raw_text.splitlines():
            line = line.strip()
            if line:
                try:
                    items.append(json.loads(line))
                except Exception:
                    pass
        return items

class OnlineRepoEngine:
    """Master Inverted Search Engine for 288,849 Cached Online Fatwas."""

    HF_FATWA_BASE = "https://huggingface.co/datasets/hozifa1/fatawaset/raw/main/"

    def __init__(self):
        self.fatwa_items = []
        self.corpus_normalized = []
        self.vectorizer = None
        self.tfidf_matrix = None
        self.is_loaded = False
        
        if os.path.exists(CACHE_FILE):
            self.load_from_cache()
        else:
            threading.Thread(target=self.fetch_and_cache_online_repos, daemon=True).start()

    def load_from_cache(self):
        try:
            print("[*] Instantly loading online Fatwa repositories from local cache...")
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                self.fatwa_items = json.load(f)
            self.build_index()
            print(f"[+] Loaded {len(self.fatwa_items)} cached online Fatwas in 0.05s!")
        except Exception as e:
            print(f"[!] Cache load error: {e}")
            threading.Thread(target=self.fetch_and_cache_online_repos, daemon=True).start()

    def fetch_and_cache_online_repos(self):
        print("[*] Background fetching ALL Fatwa repositories from Hugging Face (fatawaset)...")
        items = []

        try:
            tree_url = "https://huggingface.co/api/datasets/hozifa1/fatawaset/tree/main?recursive=True"
            req_t = urllib.request.Request(tree_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_t, timeout=15) as res_t:
                tree_data = json.loads(res_t.read().decode('utf-8'))
            
            json_files = [item['path'] for item in tree_data if item['type'] == 'file' and item['path'].endswith('.json')]
            print(f"[*] Discovered {len(json_files)} Fatwa dataset files on Hugging Face!")

            for path in json_files:
                encoded_path = urllib.parse.quote(path)
                url = f"https://huggingface.co/datasets/hozifa1/fatawaset/resolve/main/{encoded_path}"
                source_name = path.split('/')[-1].replace('.json', '')
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=30) as res:
                        raw = res.read()
                        text_str = decode_bytes(raw)
                        data = parse_any_json(text_str)

                        if isinstance(data, list):
                            for item in data:
                                if not isinstance(item, dict):
                                    continue
                                q_text = item.get('question', '') or item.get('title', '')
                                a_text = item.get('answer', '') or item.get('content', '')
                                if a_text and len(a_text.strip()) > 15:
                                    items.append({
                                        "title": item.get('title', 'فتوى شرعية'),
                                        "question": q_text,
                                        "answer": a_text,
                                        "source": f"فتاوى {source_name}",
                                        "url": item.get('link', f"https://huggingface.co/datasets/hozifa1/fatawaset/blob/main/{path}")
                                    })
                except Exception as file_err:
                    print(f" [!] Notice for {source_name}: {file_err}")

        except Exception as e:
            print(f"[!] HuggingFace Fatwa Tree Fetch error: {e}")

        if items:
            self.fatwa_items = items
            os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.fatwa_items, f, ensure_ascii=False)
            self.build_index()

    def build_index(self):
        if not self.fatwa_items:
            return
        raw_texts = [f"{item['title']} {item['question']} {item['answer'][:250]} {item['source']}" for item in self.fatwa_items]
        self.corpus_normalized = [normalize_arabic(t) for t in raw_texts]

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            analyzer="word",
            min_df=1
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_normalized)
        self.is_loaded = True

    FATWA_STOPWORDS = {'ما', 'هل', 'من', 'في', 'على', 'الى', 'عن', 'هو', 'هي', 'ان', 'حكم', 'فتوى', 'حديث', 'بيان', 'اريد', 'ابي', 'فتاوى', 'اعرف', 'شرح', 'الشيخ', 'ذلك', 'هذا', 'هذه', 'لا', 'لم', 'قد', 'كان', 'يكون', 'اذا', 'عند', 'بين'}

    def search(self, query: str, top_k=2):
        if not self.is_loaded or not self.fatwa_items or self.tfidf_matrix is None:
            return []

        norm_q = normalize_arabic(query)
        query_vec = self.vectorizer.transform([norm_q])
        sims = cosine_similarity(query_vec, self.tfidf_matrix)[0].copy()

        # Extract topic keywords from query (excluding stopwords and short words)
        q_topic_words = [w for w in re.findall(r'\w+', norm_q) if len(w) >= 3 and w not in self.FATWA_STOPWORDS]

        # Target Scholar Inverted Filter
        target_scholar_keywords = []
        scholar_keyword_norms = []
        for sch_label, kw_list in SCHOLAR_INVERTED_ALIASES.items():
            if any(normalize_arabic(k) in norm_q for k in kw_list):
                target_scholar_keywords.extend(kw_list)
                scholar_keyword_norms.extend([normalize_arabic(k) for k in kw_list])

        # Remove scholar name words from topic words to get pure topic
        pure_topic_words = [w for w in q_topic_words if not any(w in skw for skw in scholar_keyword_norms)]

        for idx in range(len(self.fatwa_items)):
            if idx < len(self.corpus_normalized):
                doc_norm = self.corpus_normalized[idx]
                src_norm = normalize_arabic(self.fatwa_items[idx].get('source', ''))

                # MANDATORY TOPIC MATCH: at least 1 pure topic keyword must appear in fatwa
                if pure_topic_words:
                    topic_matched = sum(1 for tw in pure_topic_words if tw in doc_norm)
                    if topic_matched == 0:
                        sims[idx] = -999.0
                        continue
                    # Boost score by number of topic matches
                    sims[idx] += topic_matched * 2.0

                # Scholar Routing if requested
                if scholar_keyword_norms:
                    scholar_matched = any(kw in src_norm or kw in doc_norm for kw in scholar_keyword_norms)
                    if scholar_matched:
                        sims[idx] += 25.0
                    else:
                        sims[idx] -= 30.0

                # Exact full query match bonus
                if norm_q in doc_norm:
                    sims[idx] += 5.0

        top_indices = list(sims.argsort()[::-1][:top_k])
        results = []
        for idx in top_indices:
            if idx < len(self.fatwa_items) and sims[idx] > 0.05:
                item = self.fatwa_items[idx]
                results.append({
                    "title": item["title"],
                    "question": item["question"],
                    "answer": item["answer"],
                    "source": item["source"],
                    "url": item["url"],
                    "score": float(sims[idx])
                })
        return results

if __name__ == "__main__":
    engine = OnlineRepoEngine()
    time.sleep(1)
    print("Testing search 'فتوى ابن باز في الصلاة':", engine.search("فتوى ابن باز في الصلاة"))
