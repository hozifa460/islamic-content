import os
# Fix OpenBLAS / PyTorch memory allocation limit on Windows CPU
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import re
import json
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def normalize_arabic(text: str) -> str:
    """Normalize Arabic text by removing diacritics and unifying Alef/Hamza and Abi/Abu variants."""
    if not text:
        return ""
    tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = re.sub(tashkeel_pattern, '', text)
    text = re.sub(r'[إأآا]', 'ا', text)
    text = re.sub(r'ى', 'ي', text)
    text = re.sub(r'ؤ', 'و', text)
    text = re.sub(r'ئ', 'ي', text)
    text = re.sub(r'\b(ابي|ابا)\b', 'ابو', text)
    return text.strip()

def is_garbled_or_index(text: str) -> bool:
    """Detect broken/garbled OCR text or book index/table of contents pages."""
    if not text:
        return True
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    total_len = len(text)
    if total_len == 0 or (arabic_chars / total_len) < 0.65:
        return True
    numbers = re.findall(r'\b\d{2,4}\b', text)
    if len(numbers) >= 6:
        return True
    return False

SOURCE_INVERTED_ALIASES = {
    'البخاري': ['البخاري', 'صحيح البخاري', 'بخيري', 'bukhari'],
    'مسلم': ['مسلم', 'صحيح مسلم', 'muslim'],
    'أبو داود': ['أبو داود', 'ابو داود', 'سنن أبي داود', 'داود'],
    'الترمذي': ['الترمذي', 'جامع الترمذي', 'سنن الترمذي', 'tirmidhi'],
    'النسائي': ['النسائي', 'سنن النسائي', 'nasai'],
    'ابن ماجه': ['ابن ماجه', 'سنن ابن ماجه', 'ibn majah'],
    'أحمد': ['مسند أحمد', 'مسند احمد', 'الإمام أحمد', 'ahmad'],
    'المصنف': ['مصنف ابن أبي شيبة', 'مصنف عبد الرزاق', 'المصنف'],
    'مواقف وفوائد': ['مواقف وفوائد', 'الفوائد', 'الرياض'],
    'المحلى': ['المحلى', 'ابن حزم'],
    'موسوعة الأحاديث': ['موسوعة الأحاديث المشروحة', 'موسوعة الاحديث', 'hadeethenc']
}

class VectorStoreManager:
    """Master Inverted Search Index Manager for Hadiths, Tafsirs & Islamic Books."""
    
    def __init__(self, data_path="data/processed_chunks.json", model_dir="data/tfidf_model"):
        self.data_path = data_path
        self.model_dir = model_dir
        os.makedirs(self.model_dir, exist_ok=True)
        
        self.chunks = []
        self.corpus_normalized = []
        self.vectorizer = None
        self.tfidf_matrix = None
        print("[*] Initializing Fast Arabic N-Gram TF-IDF Vector Store Engine...")

        self.load_or_build_index()

    def load_or_build_index(self):
        if not os.path.exists(self.data_path):
            print(f"[!] Data path {self.data_path} does not exist yet.")
            return
            
        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_chunks = json.load(f)

        self.chunks = [c for c in raw_chunks if not is_garbled_or_index(c["content"])]
        print(f"[*] Clean dataset: {len(self.chunks)} valid passages (filtered {len(raw_chunks) - len(self.chunks)} garbled/index noise chunks).")

        if not self.chunks:
            return

        corpus_raw = [f"{c['content']} {c.get('book_name', '')}" for c in self.chunks]
        self.corpus_normalized = [normalize_arabic(c) for c in corpus_raw]
        
        vectorizer_path = os.path.join(self.model_dir, "tfidf_vectorizer.pkl")
        matrix_path = os.path.join(self.model_dir, "tfidf_matrix.pkl")
        
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3),
            sublinear_tf=True,
            analyzer="word",
            min_df=1
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_normalized)
        
        with open(vectorizer_path, "wb") as f:
            pickle.dump(self.vectorizer, f)
        with open(matrix_path, "wb") as f:
            pickle.dump(self.tfidf_matrix, f)

        print(f"[+] Master Vector Index built successfully for {len(self.chunks)} clean items!")

    def search(self, query: str, top_k=4):
        if not self.chunks or self.tfidf_matrix is None:
            return []
            
        norm_query = normalize_arabic(query)
        query_vec = self.vectorizer.transform([norm_query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix)[0].copy()

        # Strict Target Source/Book Inverted Routing
        target_source_keywords = []
        for src_label, kw_list in SOURCE_INVERTED_ALIASES.items():
            if any(normalize_arabic(k) in norm_query for k in kw_list):
                target_source_keywords.extend([normalize_arabic(k) for k in kw_list])

        for idx in range(len(self.chunks)):
            if idx < len(self.corpus_normalized):
                doc_norm = self.corpus_normalized[idx]
                book_norm = normalize_arabic(self.chunks[idx].get('book_name', ''))

                # Mandatory Source Filter if source is specified in query
                if target_source_keywords:
                    source_matched = any(kw in book_norm or kw in doc_norm for kw in target_source_keywords)
                    if source_matched:
                        sims[idx] += 30.0
                    else:
                        sims[idx] -= 50.0 # Strongly penalize non-matching sources

                if norm_query in doc_norm:
                    sims[idx] += 5.0

        top_indices = np.argsort(sims)[::-1][:min(top_k, len(self.chunks))]
            
        results = []
        for idx in top_indices:
            if idx < len(self.chunks) and sims[idx] > 0.0:
                results.append({
                    "content": self.chunks[idx]["content"],
                    "book_name": self.chunks[idx]["book_name"],
                    "page_number": self.chunks[idx].get("page_number", 1),
                    "grade": self.chunks[idx].get("grade", ""),
                    "score": float(sims[idx]),
                    "is_similarity": True
                })
        return results

if __name__ == "__main__":
    vm = VectorStoreManager()
    res = vm.search("حديث في البخاري عن الصلاة")
    print("Top match:", res[0]["book_name"], res[0]["content"][:150] if res else "None")
