# 🤖 نظام المزامنة التلقائية والبحث الإسلامي الذكي (Islamic Content & Auto-Sync Engine)

[![GitHub Actions Status](https://img.shields.io/badge/24%2F7%20Auto%20Sync-Active-22c55e?style=for-the-badge&logo=githubactions)](https://github.com/hozifa460/islamic-content/actions)
[![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Telewat__Daawa__And__Channels-ffbf00?style=for-the-badge&logo=huggingface)](https://huggingface.co/datasets/hozifa1/Telewat_Daawa_And_Channels)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python)](https://python.org)

نظام متكامل ومُؤتمت 100% لمزامنة الفيديوهات والتلاوات الإسلامية من 33+ قناة يوتيوب موثوقة ونشرها تلقائياً على منصة **Hugging Face** كل 60 دقيقة عبر **GitHub Actions** بدون أي تدخل بشري، مقترن بمحرك بحث معكوس فائق الذكاء ومجرد من العشوائية.

---

## 🌟 مميزات النظام والحل الذهبي (Golden Features)

### 1. 🤖 مزامنة آلية سحابية 24/7 (Cloud Auto-Sync)
- يعمل بجدولة آلية سحابية على **GitHub Actions** تفحص موجزات RSS لـ **33 قناة يوتيوب** كل 60 دقيقة.
- يقوم بتصنيف المادة تلقائياً إلى ثلاثة أقسام:
  - 🎥 **فيديوهات طويلة (`videos`)**
  - ⚡ **مقاطع قصيرة (`shorts`)**
  - 🔴 **بث مباشر ولقاءات (`live`)**
- يرفع المحتوى المحدث فورياً لمستودع بيانات هاتفينغ فيس: [`hozifa1/Telewat_Daawa_And_Channels`](https://huggingface.co/datasets/hozifa1/Telewat_Daawa_And_Channels).

### 2. 🔒 سياسة منع التسريب المطلقة (Zero Leak Policy)
- عند طلب المحتوى الخاطئ بشرط قنوات معينة (مثل الدكتور هيثم طلعت، الشيخ عثمان الخميس، يوسف جو، الشيخ محمد الغليظ، إلخ)، يتم عزل القناة 100% واستبعاد نتائج أي قنوات أخرى.

### 3. ⏱️ الترتيب الزمني الذكي بحسب التاريخ (Recency Order)
- عند استخدام كلمات استعلامية مثل (`أحدث`, `أخير`, `جديد`), يرتب المحرك النتائج بحسب التاريخ ليُظهر **أحدث المقاطع والفيديوهات المرفوعة أولاً**.

### 4. 📚 التمييز الدقيق بين الكتب والفيديو (Smart Intent Classifier)
- يتم التمييز الفوري بين طلبات الكتب والأحاديث (مثل "كتاب صحيح البخاري") وطلبات الميديا.
- طلبات الكتب تُجلب من فهرس الأحاديث والكتب الفقهية (55,454 حاديثاً ونصاً) خلال أقل من 0.05 ثانية وبدون ميديا.

---

## 📂 هيكلية المستودع (Repository Architecture)

```text
islamic-content/
├── .github/
│   └── workflows/
│       └── youtube-sync.yml       # ملف الجدولة السحابية الآلية 24/7 لـ GitHub Actions
├── tools/
│   ├── sync_youtube.py           # المحرك الرئيسي المباشر لجلب RSS وتحديث Hugging Face
│   └── youtube_channels.json     # قائمة الـ 33 قناة يوتيوب المعرفة وتفريعاتها
├── radio_database/
│   └── youtube_channels.json     # نسق التكوين المصدري للقنوات
├── requirements.txt              # المكتبيات المطلوبة (huggingface_hub)
└── README.md                     # الدليل المرجعي والشرح التوضيحي للنظام
```

---

## 📡 القنوات المشمولة بالمزامنة المباشرة (33 Channel Catalog)

يتابع النظام أحدث إصدارات القنوات الإسلامية والدعوية والتلاوات، ومنها:

- 🟢 الدكتور هيثم طلعت
- 🟢 جديد الشيخ عثمان الخميس
- 🟢 جديد يوسف جو
- 🟢 جديد الشيخ محمد الغليظ
- 🟢 جديد الدكتور إياد القنيبي
- 🟢 جديد التجويد والشيخ المنشاوي
- 🟢 جديد الشيخ عبد الباسط عبد الصمد
- 🟢 جديد الشيخ مصطفى العدوي
- 🟢 جديد الشيخ أبو إسحاق الحويني
- 🟢 جديد الدكتور عبد الله رشدي
- 🟢 جديد الدكتور ذاكر نايك
- 🟢 جديد الشيخ معاذ عليان
- 🟢 جديد بودكاست بدون ورق
- 🟢 جديد محمود داوود
- 🟢 جديد البحبحاني
- *(بالإضافة لجميع القنوات الـ 33 الموثقة في `youtube_channels.json`)*

---

## 🔑 كيفية تفعيل التشغيل الآلي على حسابك (Setup Guide)

1. **قم برفع هذا المستودع إلى حسابك على GitHub**:
   ```bash
   git add .
   git commit -m "feat: add 24/7 automated youtube sync workflow"
   git push origin main
   ```

2. **إضافة المفتاح السري (`HF_TOKEN`)**:
   - افتح مستودعك على موقع GitHub.
   - اذهب إلى **Settings** ⬅️ **Secrets and variables** ⬅️ **Actions**.
   - انقر على **New repository secret**.
   - الاسم (Name): `HF_TOKEN`
   - القيمة (Secret): ضع رمز وصول Hugging Face الخاص بك (`hf_...`).

---

## 🛠️ التشغيل اليدوي والمحلي (Local Execution)

إذا أردت تشغيل المزامنة فورياً من جهازك الشخصي:

```bash
pip install -r requirements.txt
python tools/sync_youtube.py
```

---

<div align="center">
  🔒 <b>نظام موثق • دقيق • مجرد من العشوائية • محدث 24/7 تلقائياً</b>
</div>
