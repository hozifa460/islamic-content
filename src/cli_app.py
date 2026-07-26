import sys
import os

# Ensure src is in python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extractive_engine import ExtractiveIslamicEngine

def main():
    print("=" * 70)
    print("      نظام الذكاء الاصطناعي الإسلامي المستند الصارم للمصادر      ")
    print("   (إجابة نصية حرفية من صحيح البخاري والكتب المتاحة بدون تجويد)   ")
    print("=" * 70)
    print("\nجارٍ تحميل محرك الاسترجاع المتجهي والنموذج المحلي...")
    
    try:
        engine = ExtractiveIslamicEngine()
        print("\n[+] اكتمل التحميل بنجاح! يمكنك الآن طرح الأسئلة والحرية في الصيغ (عامية أو مبهمة).")
        print("اكتب 'خروج' أو 'exit' للإنهاء.\n")
        
        while True:
            try:
                query = input("❓ أدخل سؤالك الشرعي: ").strip()
                if not query:
                    continue
                if query.lower() in ["خروج", "exit", "quit"]:
                    print("شكراً لاستخدامك النظام. في أمان الله.")
                    break
                    
                print("\n🔍 جاري البحث والاستخراج الحرفي من المصادر الموثوقة...")
                answer = engine.answer_query(query)
                print("\n" + answer + "\n")
                print("-" * 70)
                
            except KeyboardInterrupt:
                print("\nتم إغلاق البرنامج.")
                break
            except Exception as e:
                print(f"\n[!] حدث خطأ أثناء المعالجة: {e}\n")
                
    except Exception as e:
        print(f"[!] خطأ في تشغيل المحرك: {e}")

if __name__ == "__main__":
    main()
