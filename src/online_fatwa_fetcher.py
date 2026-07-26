import urllib.request
import urllib.parse
import re
from bs4 import BeautifulSoup

def decode_arabic_html(raw_bytes: bytes) -> str:
    """Intelligently decode HTML bytes into valid Arabic text (utf-8 or windows-1256)."""
    try:
        decoded = raw_bytes.decode('utf-8')
        if any(w in decoded for w in ['الحمد', 'الله', 'الفتوى', 'السؤال', 'الجواب', 'حكم']):
            return decoded
    except Exception:
        pass
    return raw_bytes.decode('windows-1256', errors='ignore')

class OnlineFatwaFetcher:
    """Live Real-Time Fetcher for trusted Islamic Fatwa databases (IslamWeb)."""

    BASE_SEARCH_URL = "https://www.islamweb.net/ar/fatawa/index.php?page=search&query="
    BASE_FATWA_URL = "https://www.islamweb.net"

    @classmethod
    def fetch_fatwa(cls, query: str, timeout: float = 4.0) -> dict | None:
        if not query or len(query.strip()) < 3:
            return None

        clean_q = query.strip()
        try:
            # 1. Search IslamWeb with windows-1256 encoded query
            encoded_query = urllib.parse.quote(clean_q, encoding='windows-1256')
            search_url = cls.BASE_SEARCH_URL + encoded_query
            
            req = urllib.request.Request(
                search_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as res:
                raw_search = res.read()
                search_html = decode_arabic_html(raw_search)
                
            soup_search = BeautifulSoup(search_html, 'html.parser')
            
            # Find candidate Fatwa links matching /ar/fatwa/<number>/
            fatwa_candidates = []
            for a in soup_search.find_all('a', href=True):
                href = a['href']
                match = re.search(r'/fatwa/(\d+)/', href)
                if match:
                    fatwa_num = match.group(1)
                    title = a.get_text().strip()
                    full_url = cls.BASE_FATWA_URL + href if href.startswith('/') else href
                    fatwa_candidates.append((fatwa_num, title, full_url))

            if not fatwa_candidates:
                return None

            # Pick the top candidate Fatwa
            target_num, target_title, target_url = fatwa_candidates[0]
            safe_target_url = urllib.parse.quote(target_url, safe=':/?&=#')
            
            # 2. Fetch the specific Fatwa page
            req_fatwa = urllib.request.Request(
                safe_target_url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            with urllib.request.urlopen(req_fatwa, timeout=timeout) as res_f:
                raw_fatwa = res_f.read()
                fatwa_html = decode_arabic_html(raw_fatwa)
                
            soup_fatwa = BeautifulSoup(fatwa_html, 'html.parser')
            
            # Extract paragraphs
            all_paragraphs = [p.get_text().strip() for p in soup_fatwa.find_all('p') if len(p.get_text().strip()) > 30]
            
            if not all_paragraphs:
                return None
                
            question_text = all_paragraphs[0]
            answer_paragraphs = [p for p in all_paragraphs[1:] if "حقوق الطبع" not in p and "جميع الحقوق" not in p]
            
            if not answer_paragraphs:
                answer_paragraphs = all_paragraphs
                
            full_answer = "\n\n".join(answer_paragraphs[:4]) # Limit to top 4 clean paragraphs
            
            return {
                "fatwa_number": target_num,
                "title": target_title if target_title and len(target_title) > 3 else clean_q,
                "question": question_text,
                "answer": full_answer,
                "source": "موقع إسلام ويب (IslamWeb)",
                "url": target_url
            }

        except Exception as e:
            print(f"[!] Online Fatwa Fetcher notice: {e}")
            return None

if __name__ == "__main__":
    print("[*] Testing Online Fatwa Fetcher...")
    res = OnlineFatwaFetcher.fetch_fatwa("قطرة العين في الصيام")
    if res:
        print(f"[+] Success! Fatwa #{res['fatwa_number']}: {res['title']}")
        print(f"Source: {res['source']} - {res['url']}")
        print(f"Answer snippet: {res['answer'][:200]}...")
    else:
        print("[!] No Fatwa fetched.")
