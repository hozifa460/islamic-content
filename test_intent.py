from src.extractive_engine import ExtractiveIslamicEngine

engine = ExtractiveIslamicEngine()
query = "تلاوة الحشر والقصار للشيخ المنشاوي"
print("Testing Query:", query)
res = engine.answer_query(query)
print("--- RESPONSE ---")
print(res)
