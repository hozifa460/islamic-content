import os
import re
import json
import fitz  # PyMuPDF

class PDFProcessor:
    def __init__(self, books_dir="books", output_dir="data"):
        self.books_dir = books_dir
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted Arabic text."""
        if not text:
            return ""
        # Fix redundant newlines & multiple spaces
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def extract_text_from_pdf(self, pdf_path: str, min_chars_per_page=50):
        """Extract text page by page from digital PDF files."""
        filename = os.path.basename(pdf_path)
        doc = fitz.open(pdf_path)
        pages_data = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = self.clean_text(page.get_text("text"))
            if len(text) >= min_chars_per_page:
                pages_data.append({
                    "book_name": filename,
                    "page_number": page_num + 1,
                    "content": text
                })
        
        return pages_data

    def chunk_pages(self, pages_data, chunk_size=400, overlap=100):
        """Chunk page content into semantic overlapping text chunks for search."""
        chunks = []
        chunk_id = 0
        
        for item in pages_data:
            book_name = item["book_name"]
            page_num = item["page_number"]
            text = item["content"]
            
            # Simple word-based chunking
            words = text.split()
            if not words:
                continue
                
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                chunk_text = " ".join(chunk_words)
                
                if len(chunk_text.strip()) > 30:  # Skip tiny fragments
                    chunk_id += 1
                    chunks.append({
                        "id": f"{book_name}_p{page_num}_c{chunk_id}",
                        "book_name": book_name,
                        "page_number": page_num,
                        "content": chunk_text
                    })
                    
        return chunks

    def process_all_books(self):
        """Process all PDF books in books directory and save parsed JSON chunks."""
        all_chunks = []
        processed_stats = {}
        
        for file in os.listdir(self.books_dir):
            if file.endswith(".pdf"):
                path = os.path.join(self.books_dir, file)
                pages = self.extract_text_from_pdf(path)
                chunks = self.chunk_pages(pages)
                all_chunks.extend(chunks)
                processed_stats[file] = {
                    "valid_pages": len(pages),
                    "chunks_count": len(chunks)
                }
                print(f"[*] Processed '{file}': {len(pages)} readable pages -> {len(chunks)} text chunks.")

        out_path = os.path.join(self.output_dir, "processed_chunks.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
            
        print(f"\n[+] Total Chunks Extracted: {len(all_chunks)}")
        print(f"[+] Saved dataset to: {out_path}")
        return all_chunks, processed_stats

if __name__ == "__main__":
    processor = PDFProcessor()
    processor.process_all_books()
