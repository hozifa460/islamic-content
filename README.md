# 🤖 بوت المزامنة السحابية لليوتيوب (YouTube 24/7 Auto-Sync Bot)

[![GitHub Actions Status](https://img.shields.io/badge/24%2F7%20Auto%20Sync-Active-22c55e?style=for-the-badge&logo=githubactions)](https://github.com/hozifa460/islamic-content/actions)
[![Hugging Face Dataset](https://img.shields.io/badge/Hugging%20Face-Telewat__Daawa__And__Channels-ffbf00?style=for-the-badge&logo=huggingface)](https://huggingface.co/datasets/hozifa1/Telewat_Daawa_And_Channels)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python)](https://python.org)

هذا المستودع مخصص حصرياً لعملية **المزامنة السحابية الآلية 24/7** لجلب التلاوات والمقاطع الإسلامية والدعوية من **33 قناة يوتيوب موثقة** وتصنيفها ونشرها تلقائياً على منصة **Hugging Face** كل 60 دقيقة عبر **GitHub Actions** بدون أي تدخل بشري.

---

## ⚙️ كيف يعمل النظام السحابي؟ (24/7 Automated Pipeline)

```text
  [ 🎥 33 قناة يوتيوب (RSS Feeds) ]
                │
                ▼ (كل 60 دقيقة عبر GitHub Actions)
  [ 🤖 tools/sync_youtube.py ]
                │
                ├── 1. جلب أحدث المقاطع والتلاوات المرفوعة
                ├── 2. تصنيف المادة: (Videos 🎥 / Shorts ⚡ / Live 🔴)
                └── 3. معالجة وتحديث الفهرس الشامل index.json
                │
                ▼ (رفع تلقائي سحابي)
  [ 🤗 Hugging Face: hozifa1/Telewat_Daawa_And_Channels ]
```

---

## 📂 محتويات المستودع (Repository Structure)

```text
islamic-content/
├── .github/
│   └── workflows/
│       └── youtube-sync.yml       # ملف الجدولة السحابية الآلية 24/7 لـ GitHub Actions
├── tools/
│   ├── sync_youtube.py           # المحرك الرئيسي المباشر لجلب RSS وتحديث Hugging Face
│   └── youtube_channels.json     # قائمة الـ 33 قناة يوتيوب المعرفة ومعرفاتها
├── requirements.txt              # المكتبيات المطلوبة (huggingface_hub)
└── README.md                     # الدليل المرجعي والشرح التوضيحي للنظام
```

---

## 🔑 تفعيل المفتاح السري (GitHub Secrets Setup)

لتشغيل السكربت تلقائياً في السحاب بالصلاحية الكاملة للتحديث على Hugging Face:

1. اذهب إلى **Settings** ⬅️ **Secrets and variables** ⬅️ **Actions**.
2. انقر على **New repository secret**.
3. الاسم (Name): `HF_TOKEN`
4. القيمة (Secret): ضَع رمز الوصول الخاص بك في هاجينج فيس (`hf_...`).

---

## ➕ كيفية إضافة قناة جديدة (Adding New Channels)

عدّل ملف `tools/youtube_channels.json` وأضف القناة بالصيغة التالية:
```json
{
  "categoryId": "اسم_معرف_القناة",
  "channelId": "UCxxxxxxxxxxxxxxxxxxxxxx",
  "channelName": "اسم القناة بالكامل"
}
```

---

<div align="center">
  🔒 <b>بوت مزامنة سحابي مُؤتمت 100% • محدث 24/7 تلقائياً</b>
</div>
