import re
from src.vector_store import VectorStoreManager, normalize_arabic
from src.online_fatwa_fetcher import OnlineFatwaFetcher
from src.online_repo_engine import OnlineRepoEngine
from src.online_media_engine import OnlineMediaEngine
from src.generative_engine import GenerativeIslamicEngine

SAHABA_BIOS = {
    "عمر بن الخطاب": {
        "full_name": "عمر بن الخطاب بن نفيل القرشي العدوي (أبو حفص)",
        "title": "الفاروق - ثاني الخلفاء الراشدين ومن العشرة المبشرين بالجنة",
        "bio": "أعز الله به الإسلام، كان عادلاً حازماً، قُتل في محرابه وهو يصلي بالمسلمين. شهد المشاهد كلها مع رسول الله ﷺ، وتولى الخلافة (من 13 هـ إلى 23 هـ) وفُتحت في عهده الشام ومصر والقدس وفارس، وتوفي شهيداً سنة 23 هـ.",
        "keywords": ["عمر بن الخطاب", "عمر", "الفاروق"]
    },
    "أبو بكر الصديق": {
        "full_name": "عبد الله بن أبي قحافة عثمان القرشي التيمي (أبو بكر)",
        "title": "الصديق - أول الخلفاء الراشدين وأفضل الأمة بعد نبيها",
        "bio": "أول من أسلم من الرجال الأحرار، وصاحب النبي ﷺ في الهجرة وفي الغار، ووالد أم المؤمنين عائشة. تولى الخلافة بعد وفاة النبي ﷺ، وحارب أهل الردة وجمع القرآن الكريم، وتوفي سنة 13 هـ.",
        "keywords": ["أبو بكر", "ابو بكر", "الصديق", "عتيق"]
    },
    "عثمان بن عفان": {
        "full_name": "عثمان بن عفان بن أبي العاص القرشي الأموي (أبو عبد الله)",
        "title": "ذو النورين - ثالث الخلفاء الراشدين ومن العشرة المبشرين بالجنة",
        "bio": "تزوج ابنتي النبي ﷺ (رقية ثم أم كلثوم). صاحب الحياء والإنفاق العظيم، جهز جيش العسرة واشترى بئر رومة، وجمع المصحف الشريف على قراءة واحدة. استشهد سنة 35 هـ.",
        "keywords": ["عثمان بن عفان", "عثمان", "ذو النورين"]
    },
    "علي بن أبي طالب": {
        "full_name": "علي بن أبي طالب بن عبد المطلب القرشي الهاشمي (أبو الحسن)",
        "title": "أمير المؤمنين - رابع الخلفاء الراشدين وابن عم النبي ﷺ وزوج فاطمة",
        "bio": "أول من أسلم من الصبيان، فدى النبي ﷺ بنومه في فراشه ليلة الهجرة. كان من شجعان الصحابة وحكمائهم وقضاتهم المشهود لهم بالعلم والفصاحة.",
        "keywords": ["علي بن أبي طالب", "علي بن ابي طالب", "أبو تراب"]
    }
}

class ArabicSpellCorrector:
    """Smart Arabic Spell Corrector & Fuzzy Typo Tolerance Engine."""
    
    # Names of speakers, scholars, channels that must NEVER be spell-corrected
    PROTECTED_NAMES = {
        'يوسف', 'جو', 'هيثم', 'طلعت', 'عثمان', 'الخميس', 'إياد', 'اياد', 'القنيبي',
        'رشدي', 'محمود', 'داوود', 'معاذ', 'عليان', 'ذاكر', 'نايك', 'البحبحاني',
        'زهوقا', 'أنس', 'انس', 'أكشن', 'اكشن', 'شريف', 'علي', 'القط', 'الغليظ',
        'وليد', 'إسماعيل', 'اسماعيل', 'نصار', 'علاء', 'إبراهيم', 'ابراهيم', 'عاصم',
        'تاريخنا', 'سراج', 'حياني', 'غنايم', 'فرماوي', 'كحيل', 'الدائم',
        'العدوي', 'مصطفى', 'المنشاوي', 'منشاوي', 'عبدالباسط', 'الشعراوي',
        'الحويني', 'اسحاق', 'ممدوح', 'ياسر', 'باز', 'عثيمين', 'العثيمين',
        'الفوزان', 'الألباني', 'الالباني', 'البخاري', 'الترمذي', 'النسائي',
        'ماجه', 'مالك', 'أحمد', 'احمد', 'الدارمي', 'النواوي', 'القرطبي',
        'ابن', 'بن', 'عبد', 'الله', 'الدكتور', 'دكتور', 'الشيخ', 'شيخ',
        'بدون', 'ورق', 'كان', 'الساخر', 'الهادف', 'مناظرات'
    }

    DICTIONARY = [
        "صلاة", "تارك", "ترك", "حكم", "مرتد", "وضوء", "طهارة", "زكاة", "صيام",
        "حج", "عمرة", "مسح", "خفين", "سهو", "ركعة", "سجدة", "سجود", "جنابة",
        "حيض", "نفاس", "تيمم", "طلاق", "زواج", "ربا", "ميراث", "يمين", "نذر",
        "كفارة", "أضحية", "عقيقة", "شرك", "كفر", "توحيد", "عقيدة", "إيمان", "تلاوة",
        "سورة", "المنشاوي", "عبد الباسط", "البخاري", "مسلم", "الترمذي", "أبو داود"
    ]
    
    TYPO_MAP = {
        "صلة": "صلاة",
        "صلات": "صلاة",
        "صلوات": "صلاة",
        "تاركم": "تارك",
        "تاركا": "تارك",
        "تاركك": "تارك",
        "اتوضا": "توضأ",
        "اتوضأ": "توضأ",
        "مرتدد": "مرتد",
        "احكام": "أحكام",
        "احاحام": "أحكام",
        "منشوي": "المنشاوي",
        "عبدالباسط": "عبد الباسط",
        "عبدالبسيط": "عبد الباسط"
    }

    @classmethod
    def levenshtein_distance(cls, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return cls.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    @classmethod
    def correct_query(cls, query: str) -> str:
        words = query.strip().split()
        corrected_words = []
        
        for w in words:
            norm_w = normalize_arabic(w)
            
            # NEVER correct protected names (speakers, scholars, channels)
            if norm_w in cls.PROTECTED_NAMES or w in cls.PROTECTED_NAMES:
                corrected_words.append(w)
                continue
                
            if w in cls.TYPO_MAP:
                corrected_words.append(cls.TYPO_MAP[w])
            elif norm_w in cls.TYPO_MAP:
                corrected_words.append(cls.TYPO_MAP[norm_w])
            else:
                best_match = w
                best_dist = 99
                # Only correct words >= 4 chars, and require dist <= 1 for short words
                if len(norm_w) >= 4:
                    max_dist = 1 if len(norm_w) <= 5 else 2
                    for dict_w in cls.DICTIONARY:
                        norm_dict = normalize_arabic(dict_w)
                        dist = cls.levenshtein_distance(norm_w, norm_dict)
                        if dist <= max_dist and dist < best_dist:
                            best_dist = dist
                            best_match = dict_w
                corrected_words.append(best_match if best_dist <= 2 else w)
                
        return " ".join(corrected_words)

class FiqhQueryExpander:
    """Smart Fiqh Intent, Capabilities & Smalltalk Handler."""
    
    CAPABILITIES_REPLY = """أهلاً بك يا رفيق! 🌸 أنا **رَفِيق**، مستشارك الذكي في العلوم والآثار الشرعية والتلاوات المباشرة.

💡 **إليك ما أقوم به بالتنسيق والتوضيح الفوري**:
1. 🎙️ **خيارات التلاوات والمقاطع المباشرة**: تقديم قائمة بالخيارات والتلاوات المتطابقة المتاحة مع مشغل الصوت والتحميل لكل خيار.
2. 🌐 **الربط الحي بالفتاوى**: البحث الفوري في قواعد فتاوى ابن باز، وابن عثيمين، وإسلام ويب، وإسلام سؤال وجواب.
3. 👤 **تراجم وسير الصحابة**: تقديم البطاقة التعريفية الكاملة مدعمة بالأحاديث.
4. 📜 **الدليل الشرعي**: التذييل بالحديث المباشر المطابق من **صحيح البخاري**.
5. 🤖 **التوليد الفصيح الميسر (Generative Engine)**: التعبير بسلاسة تامة وتفهم لجميع اللهجات العربية.

تفضل بطرح سؤالك أو طلب التلاوة التي تريدها!"""

    SMALLTALK = [
        (r"(ماذا|ما|كيف|ايش|وش).*(تفعل|تستطيع|قدراتك|قدرتك|تعمل|تساعدني|تفيدني|الكتب|المصادر)", CAPABILITIES_REPLY),
        (r"(عرفني|عرفنا|مين|من).*(بنفسك|عنك|قدراتك|مهامك|عملك)", CAPABILITIES_REPLY),
        
        (r"(عامل ايه|عامل إيه|ازيك|إزيك|شلونك|كيفك|اخبارك|أخبارك|شخبارك|عساك بخير|شخبار|كيف الحال)", 
         "الحمد لله بأفضل حال يا رفيق! 🌸 يسعدني جداً تواصلك معي. كيف يمكنني مساعدتك اليوم في الأسئلة الشرعية أو التلاوات؟"),
          
        (r"(كيف|أخبار|اخبار|شلون|ازيك|علومك).*(حالك|صحتك|الأخبار|الاخبار|العلوم)", 
         "الحمد لله بأفضل حال يا رفيق! 🌸 يسعدني جداً تواصلك معي. كيف يمكنني مساعدتك اليوم في الأسئلة الشرعية أو التلاوات؟"),
        
        (r"(السلام عليكم|سلام عليكم|مرحبا|أهلا|اهلا|صباح الخير|مساء الخير)", 
         "وعليكم السلام ورحمة الله وبركاته! أهلاً بك يا رفيق 🌸 تفضل بطرح سؤالك الشرعي أو طلب التلاوة."),
        
        (r"(من|ما|مين).*(انت|أنت|اسمك)", CAPABILITIES_REPLY),
        (r"(شكرا|شكراً|يعطيك العافية|تسلم|جزاك الله)", "على الرحب والسعة يا رفيق! 🌸 أسعد بخدمتك دائماً."),
        (r"(ممتاز|رائع|جميل|طيب|حسنا)", "شكراً لك يا رفيق! يسعدني ذلك 🌸 تفضل إذا كان لديك استفسار آخر.")
    ]

    PATTERNS = [
        (r"(نسيت|سهوت|شككت|نسي|سهى).*(ركعة|صلاة|المغرب|العشاء|الظهر|العصر|الفجر)", 
         ["السهو في الصلاة", "سجود السهو", "صلى ركعتين ثم سلم", "سجد سجدتين وهو جالس", "إذا شك أحدكم في صلاته"]),
        
        (r"(ماء|اتوضأ|اتوضا|وضوء).*(حار|ساخن|سخن|حرارة)", 
         ["الوضوء بالماء الحار", "الماء المشمس", "طهارة", "الوضوء"]),

        (r"(مسح|مسيح).*(خف|خفين|شراب|جورب)", 
         ["المسح على الخفين", "الخفين", "طهور"]),
          
        (r"(نية|النية).*(صلاة|وضوء|صيام|عمرة|حج)", 
         ["إنما الأعمال بالنيات", "النية في الصلاة", "النية"]),
          
        (r"(حسن الظن|أظن|اقلق|رحمة الله)", 
         ["حسن الظن بالله", "أنا عند ظن عبدي بي", "الرجاء"])
    ]

    @classmethod
    def check_smalltalk(cls, query: str):
        q = query.strip()
        for pattern, reply in cls.SMALLTALK:
            if re.search(pattern, q, re.IGNORECASE):
                return reply
        return None

    @classmethod
    def check_sahaba_bio(cls, query: str):
        norm_q = normalize_arabic(query)
        for key, info in SAHABA_BIOS.items():
            for kw in info["keywords"]:
                if normalize_arabic(kw) in norm_q:
                    return info
        return None

    # All known creator/channel names for auto-detecting media intent
    CREATOR_NAMES = [
        'يوسف جو', 'عثمان الخميس', 'هيثم طلعت', 'إياد القنيبي', 'اياد القنيبي',
        'عبد الله رشدي', 'عبدالله رشدي', 'محمود داوود', 'معاذ عليان', 'ذاكر نايك',
        'البحبحاني', 'كان زهوقا', 'أنس أكشن', 'انس اكشن', 'شريف علي', 'شريف على',
        'يوسف القط', 'محمد الغليظ', 'وليد إسماعيل', 'وليد اسماعيل', 'محمود نصار',
        'علاء إبراهيم', 'علاء ابراهيم', 'عاصم هيثم', 'بدون ورق', 'تاريخنا',
        'سراج حياني', 'محمد غنايم', 'إبراهيم عبد الغني', 'ابراهيم عبد الغني',
        'الساخر الهادف', 'محمد فرماوي', 'مناظرات', 'عبد الدائم كحيل',
        'مصطفى العدوي', 'المنشاوي', 'عبد الباسط', 'عبدالباسط', 'الشعراوي',
        'الحويني', 'ابو اسحاق', 'ياسر ممدوح'
    ]

    @classmethod
    def detect_intent(cls, query: str) -> str:
        corrected_q = ArabicSpellCorrector.correct_query(query)
        norm_q = normalize_arabic(corrected_q)
        norm_original = normalize_arabic(query)

        # 1. Book & Hadith keywords check
        book_hadith_keywords = [
            'كتاب', 'كتب', 'مجلد', 'مؤلف', 'شرح', 'تفسير', 'صحيح', 'البخاري', 'بخاري', 'مسلم',
            'الترمذي', 'ترمذي', 'أبو داود', 'ابو داود', 'النسائي', 'نسائي', 'ابن ماجه',
            'ماجه', 'مالك', 'أحمد', 'احمد', 'الدارمي', 'المصنف', 'رياض الصالحين',
            'الأربعين النواوية', 'الأربعون النواوية', 'بلوغ المرام', 'الشمائل', 'حديث',
            'أحاديث', 'سنن', 'مسند', 'تخريج', 'جامع', 'فتح الباري', 'عمدة القاري'
        ]
        has_book_kw = any(k in norm_q or k in norm_original for k in book_hadith_keywords)

        # Check if query mentions a known creator/channel name -> media intent
        # (Unless explicitly asking for a book/hadith, e.g. "كتاب عثمان الخميس" vs "فيديو عثمان الخميس")
        for name in cls.CREATOR_NAMES:
            norm_name = normalize_arabic(name)
            if norm_name in norm_q or norm_name in norm_original:
                if not (has_book_kw and ('كتاب' in norm_original or 'حديث' in norm_original)):
                    return "media"

        # Explicit Media keywords ONLY (dialect verbs like 'جيبلي' and 'عايز' removed)
        media_keywords = [
            'تلاوة', 'سورة', 'قصار', 'الحشر', 'صوت', 'فيديو', 'فيديوهات',
            'استماع', 'تحميل', 'راديو', 'مقطع', 'شورتس', 'انشيد', 'انشودة', 'يوتيوب', 'قناة'
        ]
        if any(k in norm_q for k in media_keywords):
            if not (has_book_kw and 'كتاب' in norm_original):
                return "media"

        if has_book_kw:
            return "book"

        if any(k in norm_q for k in ['من هو', 'نسب', 'ترجمة', 'سيرة']):
            return "bio"

        fiqh_keywords = [
            'حكم', 'فتوى', 'يجوز', 'يصح', 'حلال', 'حرام', 'واجب', 'سنة', 'بدعة', 'مكروه', 'مستحب', 'فرض',
            'صلاة', 'وضوء', 'صيام', 'زكاة', 'حج', 'عمرة', 'طهارة', 'جنابة', 'حيض', 'نفاس', 'تيمم', 'مسح',
            'سهو', 'ركعة', 'سجدة', 'سجود', 'طلاق', 'خالع', 'عداء', 'زواج', 'نكان', 'ربا', 'ميراث', 'تركة',
            'يمين', 'نذر', 'صوم', 'فدية', 'كفارة', 'ذبيحة', 'اضحية', 'أضحية', 'عقيقة', 'صيد', 'خمر', 'ميسر',
            'شرك', 'كفر', 'توحيد', 'عقيدة', 'إيمان', 'قدر', 'جنة', 'نار', 'قبر', 'عذاب', 'قيامة', 'شفاعة'
        ]
        if any(k in norm_q for k in fiqh_keywords):
            return "fatwa"

        return "general"

    @classmethod
    def expand_query(cls, query: str) -> list[str]:
        corrected = ArabicSpellCorrector.correct_query(query)
        expanded = [query]
        if corrected != query:
            expanded.append(corrected)
        for pattern, terms in cls.PATTERNS:
            if re.search(pattern, query, re.IGNORECASE) or re.search(pattern, corrected, re.IGNORECASE):
                expanded.extend(terms)
        return expanded

def repair_arabic_text(text) -> str:
    """Repair PDF OCR spaces, broken letter connections, and garbled symbols."""
    if not text or str(text).strip() in ["None", "null", ""]:
        return ""
    text_str = str(text).strip()
    text_str = re.sub(r'\(\s*\d+\s*\)', '', text_str)
    text_str = re.sub(r'\(.*?(ساقط|حاشية|النسخ|طبعة).*?\)', '', text_str)
    text_str = re.sub(r'الل\s+ّه', 'الله', text_str)
    text_str = re.sub(r'الل\s+ه', 'الله', text_str)
    text_str = re.sub(r'ال\s+له', 'الله', text_str)
    text_str = re.sub(r'([.،؟:!])([^\s\d.،؟:!])', r'\1 \2', text_str)
    text_str = re.sub(r'\b[إأا]\s*ف\s*!\s*', '', text_str)
    text_str = re.sub(r'\b[ووا]\s*َ\s*و\b', '', text_str)
    text_str = re.sub(r'[ \t]+', ' ', text_str)
    return text_str.strip()

def format_fiqh_opinions(text: str) -> str:
    """Format Fatwa text into clean, structured bullet points if multiple opinions exist."""
    if not text:
        return ""
    clean = repair_arabic_text(text)
    clean = re.sub(r'\n{3,}', '\n\n', clean)
    
    # Format Fiqh school opinions & section headings
    clean = re.sub(r'(\s|^)(القول الأول|القسم الأول|الأول):', r'\1\n\n• **القول الأول**: ', clean)
    clean = re.sub(r'(\s|^)(القول الثاني|القسم الثاني|الثاني):', r'\1\n\n• **القول الثاني**: ', clean)
    clean = re.sub(r'(\s|^)(القول الثالث|القسم الثالث|الثالث):', r'\1\n\n• **القول الثالث**: ', clean)
    clean = re.sub(r'(\s|^)(ومن أدلة القول الأول):', r'\1\n\n  📌 **من أدلة القول الأول**:\n', clean)
    clean = re.sub(r'(\s|^)(ومن أدلة القول الثاني):', r'\1\n\n  📌 **من أدلة القول الثاني**:\n', clean)
    clean = re.sub(r'(\s|^)(فذهب|وذهب)\s+(الأمام|الإمام|أبو|مالك|الشافعي|أحمد|الحنفية|المالكية|الشافعية|الحنابلة)', r'\n\n• \1 \2', clean)
    clean = re.sub(r'(\s|^)(والمشهور|ورأي|وقال)\s+(عن|في|من|الإمام|أحمد|مالك|الشافعي)', r'\n\n• \1 \2', clean)

    clean = re.sub(r'\n{3,}', '\n\n', clean)
    return clean.strip()

STOPWORDS = {
    'ما', 'هل', 'من', 'في', 'على', 'إلى', 'عن', 'ماذا', 'كيف', 'متى', 'أين', 
    'هو', 'هي', 'أن', 'إن', 'هذا', 'هذه', 'كان', 'يكون', 'وانا', 'افعل', 'معنى', 'اليوم', 'حال', 'مصر',
    'حكم', 'مسألة', 'بيان', 'فصل', 'شرح', 'درجة', 'تخريج', 'قول', 'عايز', 'اريد', 'أريد', 'جيبلي', 'هات'
}

def validate_relevance(query: str, doc_text: str, score: float) -> bool:
    if not doc_text or doc_text == "None":
        return False
    norm_q = normalize_arabic(query)
    tokens = [w for w in re.findall(r'\w+', norm_q) if len(w) >= 3 and w not in STOPWORDS]
    
    if not tokens:
        return score >= 0.15
        
    norm_doc = normalize_arabic(doc_text)
    matched_tokens = [t for t in tokens if t in norm_doc]
    
    return len(matched_tokens) >= 1

def extract_valid_text(*texts) -> str:
    for t in texts:
        if t and str(t).strip() not in ["None", "null", ""]:
            return str(t).strip()
    return ""

class ExtractiveIslamicEngine:
    def __init__(self, min_similarity=0.35):
        self.vector_store = VectorStoreManager()
        self.online_repo = OnlineRepoEngine()
        self.media_engine = OnlineMediaEngine()
        self.generative_engine = GenerativeIslamicEngine()
        self.min_similarity = min_similarity

    def answer_query(self, query: str, top_k=4):
        query_clean = query.strip()
        if not query_clean:
            return "أهلاً بك يا رفيق! تفضل بطرح سؤالك الشرعي أو طلب التلاوة التي تريدها."
            
        # 1. Check smalltalk/greetings FIRST
        st_reply = FiqhQueryExpander.check_smalltalk(query_clean)
        if st_reply:
            return st_reply

        # Correct typos automatically
        corrected_query = ArabicSpellCorrector.correct_query(query_clean)

        # Detect Query Intent
        intent = FiqhQueryExpander.detect_intent(query_clean)

        # 2. Check Sahaba Biography FIRST for Sahaba queries
        sahaba_info = FiqhQueryExpander.check_sahaba_bio(corrected_query)

        # 3. IF INTENT IS MEDIA/RECITATION: Search for all top matching options
        media_matches = []
        if intent == "media":
            media_matches = self.media_engine.search(corrected_query, top_k=3)

        # 4. Search Cached Online Repositories for Fatwas
        online_repo_matches = []
        if intent in ["fatwa", "general"] and not sahaba_info:
            online_repo_matches = self.online_repo.search(corrected_query, top_k=2)

        # 5. Fast Online Fatwa Fetcher with strict 1.5s max timeout (only if no repo match and intent is fatwa)
        online_fatwa = None
        if intent == "fatwa" and not online_repo_matches and not sahaba_info:
            online_fatwa = OnlineFatwaFetcher.fetch_fatwa(corrected_query, timeout=1.5)

        # 6. Search Local Vector Store (Hadiths and Islamic Books) for all Knowledge Intents
        hadith_matches = []
        book_matches = []
        
        if intent in ["fatwa", "book", "hadith", "general"]:
            search_terms = FiqhQueryExpander.expand_query(corrected_query)
            all_matches = []
            for term in search_terms:
                matches = self.vector_store.search(term, top_k=6)
                all_matches.extend(matches)

            norm_q = normalize_arabic(corrected_query)
            q_keywords = [w for w in re.findall(r'\w+', norm_q) if len(w) >= 3 and w not in STOPWORDS]

            for m in all_matches:
                content = repair_arabic_text(m["content"])
                norm_c = normalize_arabic(content)
                matched_kws = [kw for kw in q_keywords if kw in norm_c]
                
                # Must contain at least ONE core topic keyword (excluding generic words)
                if not sahaba_info and intent != "book" and not matched_kws:
                    continue

                if not sahaba_info and intent != "book" and not validate_relevance(corrected_query, content, m.get("score", 0.0)):
                    continue
                    
                match_count = len(matched_kws)
                m_score = m.get("score", 0.0) + (match_count * 0.35)
                
                grade_str = str(m.get("grade", "")).lower()
                if "sahih" in grade_str or "صحيح" in grade_str or "hasan" in grade_str or "حسن" in grade_str:
                    m_score += 0.40
                elif "da'if" in grade_str or "ضعيف" in grade_str:
                    m_score -= 0.60
                m["final_score"] = m_score

                hadith_keywords = ['البخاري', 'مسلم', 'داود', 'الترمذي', 'النسائي', 'ماجه', 'مالك', 'أحمد', 'الدارمي', 'الصالحين', 'النواوية', 'القدسية', 'المصابيح', 'المفرد', 'المرام', 'الشمائل', 'الدهلوي', 'حديث']
                if any(hk in m["book_name"] for hk in hadith_keywords):
                    hadith_matches.append(m)
                else:
                    book_matches.append(m)
                    
            if sahaba_info:
                valid_h = [hm for hm in hadith_matches if any(normalize_arabic(kw) in normalize_arabic(hm["content"]) for kw in sahaba_info["keywords"])]
                valid_b = [bm for bm in book_matches if any(normalize_arabic(kw) in normalize_arabic(bm["content"]) for kw in sahaba_info["keywords"])]
                hadith_matches = valid_h
                book_matches = valid_b

        hadith_matches.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        book_matches.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)
        
        sections = []
        sections.append("أهلاً بك يا رفيق 🌸\n")

        # Render Quran Recitations Options List if retrieved
        if media_matches:
            sections.append(f"### 🎙️ وجد رفيق ({len(media_matches)}) خيارات تفاعلية متطابقة لطلبك، اختر المقطع واستمِع إليه مباشرة:")
            for i, med in enumerate(media_matches, 1):
                m_url = med['audio_url'] or med['video_url']
                sections.append(f"""📌 **الخيار ({i}): {med['title']}** — (*{med['speaker']}*)

[PLAYER:{m_url}]

[DOWNLOAD:{m_url}]""")

        # Render Sahaba Biography Profile if applicable
        if sahaba_info:
            sections.append(f"""### 👤 الترجمة والبطاقة التعريفية للصحابي الجليل

📌 **الاسم والنسب**: {sahaba_info['full_name']}
🌟 **اللقب والرتبة**: {sahaba_info['title']}

📖 **نبذة من سيرته العطرة**:
{sahaba_info['bio']}""")

        # Render Fatwa from Fast Cached Repositories if retrieved
        if online_repo_matches and intent != "media":
            best_fatwa = online_repo_matches[0]
            raw_ans = extract_valid_text(best_fatwa.get('answer'), best_fatwa.get('content'), best_fatwa.get('title'), best_fatwa.get('question'))
            clean_ans = format_fiqh_opinions(raw_ans)
            
            if clean_ans and validate_relevance(corrected_query, clean_ans, best_fatwa.get('score', 0.0)):
                sections.append(f"""### 🌐 فتوى شرعية موثقة من قواعد البيانات المباشرة

📌 **عنوان الفتوى والمصدر**: {best_fatwa['title']} — ({best_fatwa['source']})

> **"{clean_ans}"**

📌 **المصدر المرجعي**: [{best_fatwa['source']}]({best_fatwa['url']})""")

        # Render Live Online Fatwa if retrieved
        elif online_fatwa and intent != "media":
            raw_ans = extract_valid_text(online_fatwa.get('answer'), online_fatwa.get('content'))
            if raw_ans:
                clean_ans = format_fiqh_opinions(raw_ans)
                sections.append(f"""### 🌐 فتوى شرعية موثقة من موقع إسلام ويب

📌 **عنوان الفتوى**: {online_fatwa['title']} (فتوى رقم: {online_fatwa['fatwa_number']})

> **"{clean_ans}"**

📌 **المصدر المرجعي**: [{online_fatwa['source']}]({online_fatwa['url']})""")

        # Render Book Explanation / Text if retrieved
        if book_matches and intent != "media":
            best_book = book_matches[0]
            raw_b = extract_valid_text(best_book.get("content"))
            if raw_b:
                b_content = repair_arabic_text(raw_b)
                sections.append(f"""### 📖 النص والبيان من كتب العلم والسيرة

> **"{b_content}"**

📌 **المصدر المرجعي**: {best_book['book_name']} (الصفحة {best_book['page_number']})""")

        # Render Hadith Evidence / Book Passage if retrieved
        if hadith_matches and intent != "media":
            best_hadith = hadith_matches[0]
            raw_h = extract_valid_text(best_hadith.get("content"))
            if raw_h:
                h_content = repair_arabic_text(raw_h)
                b_title = best_hadith.get('book_name', 'السنة النبوية')
                grade_str = f"\n⭐ **درجة وتوثيق الحديث**: {best_hadith['grade']}" if best_hadith.get('grade') else ""
                sections.append(f"""### 📜 الدليل والحديث النبوي الشريف من ({b_title})

> **"{h_content}"**{grade_str}

📌 **المصدر المرجعي**: {b_title} (حديث رقم {best_hadith.get('page_number', 1)})""")

        if not sahaba_info and not media_matches and not online_repo_matches and not online_fatwa and not book_matches and not hadith_matches:
            gen_reply = self.generative_engine.generate_response(corrected_query) if self.generative_engine else None
            if gen_reply:
                return f"أهلاً بك يا رفيق 🌸\n\n{gen_reply}"
            return f"""أهلاً بك يا رفيق 🌸

أنا رفيق، مستشارك الصديق. يسعدني تواصلك معي! 

إذا كان لديك سؤال شرعي، أو تبحث عن كتاب إسلامي أو حديث نبوي، أو تلاوة قرآنية، تفضل بتوضيح سؤالك أو اسم الكتاب وسأجيبك بدقة كافية فورا!"""

        sections.append("🔒 **ضمان الدقة**: إجابة موثقة ومبسطة ومقترنة بالأدلة والنصوص المباشرة بدون أي عشوائية.")
        return "\n\n---\n\n".join(sections)

if __name__ == "__main__":
    engine = ExtractiveIslamicEngine()
