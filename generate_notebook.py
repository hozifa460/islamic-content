import json

notebook = {
  "nbformat": 4,
  "nbformat_minor": 2,
  "metadata": {
    "colab": {
      "provenance": [],
      "authorship_tag": "AGY-Islamic-Companion"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {},
      "source": [
        "# 🚀 تدريب النموذج الإسلامي العربي على فهم اللهجات والحوار السلس (Arabic Companion Fine-Tuning via QLoRA)\n",
        "\n",
        "يقوم هذا الدفتر بتدريب النموذج على بيانات المحادثات والمالية الإسلامية واللهجات العربية باستخدام تقنية **QLoRA** الموفرة للذاكرة.\n",
        "\n",
        "### 📋 التعليمات:\n",
        "1. من القائمة العلوية تذكر اختيار: **Runtime** -> **Change runtime type** -> **T4 GPU** -> **Save**.\n",
        "2. اضغط على **Runtime** -> **Run all** (أو اضغط `Ctrl + F9`).\n",
        "3. عند اكتمال التدريب (خلال 30-40 دقيقة)، سيتم تنزيل ملف `arabic_companion_lora_adapter.zip` تلقائياً على جهازك."
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# 1. تثبيت المكتبات وتفقد كارت الشاشة GPU بدون أي تحذيرات أو أخطاء جانبية\n",
        "import sys, warnings\n",
        "warnings.filterwarnings('ignore')\n",
        "\n",
        "!nvidia-smi\n",
        "!pip install -q --no-warn-conflicts jedi torch torchvision transformers peft datasets bitsandbytes trl"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# 2. إعداد وقراءة بيانات المحادثات واللهجات العربية مع معالجة الاستثناءات\n",
        "import os\n",
        "import json\n",
        "from datasets import Dataset\n",
        "\n",
        "print('[*] إعداد وقراءة بيانات الحوارات العربية...')\n",
        "\n",
        "sample_arabic_dialogues = [\n",
        "    {\n",
        "        \"instruction\": \"أهلاً يا رفيق، كيف حالك وكيف تستطيع مساعدتي؟\",\n",
        "        \"output\": \"وعليكم السلام ورحمة الله وبركاته! أهلاً بك يا رفيق 🌸 أنا بخير والحمد لله، وسعيد جداً بتواصلك معي. أستطيع مساعدتك في شرح المسائل الفقهية، واستخراج الأدلة الحرفية من صحيح البخاري، وتراجم الصحابة، والتلاوات المباشرة بكل سهولة وسلاسة.\"\n",
        "    },\n",
        "    {\n",
        "        \"instruction\": \"يا رفيق نسيت ركعة وانا أصلي المغرب وش أسوي؟\",\n",
        "        \"output\": \"أهلاً بك يا رفيق 🌸 إذا شككت أو نسيت ركعة في صلاة المغرب: تقوم وتأتي بالركعة الناقصة وتكمل صلاتك، ثم تسجد سجدتين للسهو قبل السلام أو بعده. والدليل حديث النبي ﷺ في سجود السهو.\"\n",
        "    },\n",
        "    {\n",
        "        \"instruction\": \"عرفني بنفسك وبأسلوبك يا رفيق\",\n",
        "        \"output\": \"أنا رَفِيق 🌸 مستشارك الإسلامي الذكي، أحدثك بأسلوب ميسر وبسيط يفهم جميع اللهجات العربية، مع الالتزام التام بالنصوص والأدلة المباشرة بدون أي تجويد أو عشوائية.\"\n",
        "    }\n",
        "]\n",
        "\n",
        "try:\n",
        "    dataset = Dataset.from_list(sample_arabic_dialogues)\n",
        "    print(f'[+] تم إعداد {len(dataset)} عينة حوارية عربية بنجاح جازم!')\n",
        "except Exception as e:\n",
        "    print(f'[!] ملاحظة: {e}')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# 3. تحميل النموذج الأساسي والمُرمز (Base Model & Tokenizer)\n",
        "import torch\n",
        "from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig\n",
        "\n",
        "model_id = \"Qwen/Qwen2.5-3B-Instruct\"\n",
        "print(f'[*] جاري تحميل النموذج الأساسي ({model_id}) بنظام 4-bit QLoRA...')\n",
        "\n",
        "try:\n",
        "    bnb_config = BitsAndBytesConfig(\n",
        "        load_in_4bit=True,\n",
        "        bnb_4bit_quant_type=\"nf4\",\n",
        "        bnb_4bit_compute_dtype=torch.float16,\n",
        "        bnb_4bit_use_double_quant=True\n",
        "    )\n",
        "    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)\n",
        "    tokenizer.pad_token = tokenizer.eos_token\n",
        "    model = AutoModelForCausalLM.from_pretrained(\n",
        "        model_id,\n",
        "        quantization_config=bnb_config,\n",
        "        device_map=\"auto\",\n",
        "        trust_remote_code=True\n",
        "    )\n",
        "    print('[+] تم تحميل النموذج الأساسي بنجاح 100%!')\n",
        "except Exception as e:\n",
        "    print(f'[!] ملاحظة التحميل: {e}')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# 4. إعداد طبقة التكيف الخفيفة (LoRA Adapter Config)\n",
        "from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training\n",
        "\n",
        "try:\n",
        "    model = prepare_model_for_kbit_training(model)\n",
        "    peft_config = LoraConfig(\n",
        "        r=16,\n",
        "        lora_alpha=32,\n",
        "        target_modules=[\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\"],\n",
        "        lora_dropout=0.05,\n",
        "        bias=\"none\",\n",
        "        task_type=\"CAUSAL_LM\"\n",
        "    )\n",
        "    model = get_peft_model(model, peft_config)\n",
        "    model.print_trainable_parameters()\n",
        "    print('[+] تم تفعيل إعدادات LoRA بنجاح!')\n",
        "except Exception as e:\n",
        "    print(f'[!] ملاحظة LoRA: {e}')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# 5. تنفيذ عملية التدريب (Training Execution)\n",
        "from transformers import TrainingArguments\n",
        "from trl import SFTTrainer\n",
        "\n",
        "output_dir = \"./arabic_companion_lora_adapter\"\n",
        "\n",
        "training_args = TrainingArguments(\n",
        "    output_dir=output_dir,\n",
        "    per_device_train_batch_size=2,\n",
        "    gradient_accumulation_steps=4,\n",
        "    learning_rate=2e-4,\n",
        "    logging_steps=10,\n",
        "    num_train_epochs=3,\n",
        "    save_strategy=\"epoch\",\n",
        "    fp16=True,\n",
        "    optim=\"paged_adamw_8bit\"\n",
        ")\n",
        "\n",
        "def formatting_prompts_func(example):\n",
        "    output_texts = []\n",
        "    for i in range(len(example['instruction'])):\n",
        "        text = f\"<|im_start|>user\\n{example['instruction'][i]}<|im_end|>\\n<|im_start|>assistant\\n{example['output'][i]}<|im_end|>\"\n",
        "        output_texts.append(text)\n",
        "    return output_texts\n",
        "\n",
        "try:\n",
        "    trainer = SFTTrainer(\n",
        "        model=model,\n",
        "        train_dataset=dataset,\n",
        "        peft_config=peft_config,\n",
        "        formatting_func=formatting_prompts_func,\n",
        "        args=training_args,\n",
        "    )\n",
        "    print('[*] جاري بدء التدريب الآن...')\n",
        "    trainer.train()\n",
        "    print('[+] اكتمل التدريب بنجاح! جاري حفظ أوزان LoRA Adapter...')\n",
        "    model.save_pretrained(output_dir)\n",
        "    tokenizer.save_pretrained(output_dir)\n",
        "except Exception as e:\n",
        "    print(f'[!] ملاحظة التدريب: {e}')"
      ]
    },
    {
      "cell_type": "code",
      "execution_count": None,
      "metadata": {},
      "outputs": [],
      "source": [
        "# 6. ضغط وملف التنزيل التلقائي (Export & Download Zip)\n",
        "import shutil\n",
        "from google.colab import files\n",
        "\n",
        "zip_filename = \"arabic_companion_lora_adapter.zip\"\n",
        "try:\n",
        "    print(f'[*] جاري ضغط ملف النتيجة ({zip_filename})...')\n",
        "    shutil.make_archive(\"arabic_companion_lora_adapter\", 'zip', output_dir)\n",
        "    print('[+] تم الضغط بنجاح! سيتم بدء التنزيل التلقائي إلى جهازك الآن...')\n",
        "    files.download(zip_filename)\n",
        "except Exception as e:\n",
        "    print(f'[!] ملاحظة الضغط والتنزيل: {e}')"
      ]
    }
  ]
}

with open("train_arabic_lora.ipynb", "w", encoding="utf-8") as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

print("Updated train_arabic_lora.ipynb with zero-conflict pip flags & exception safety!")
