import os
import torch

class LoRACompanionLoader:
    """Seamless Loader for Fine-Tuned Arabic LoRA Adapter."""

    ADAPTER_DIR = "models/arabic_companion_lora_adapter"

    def __init__(self, base_model_id="Qwen/Qwen2.5-3B-Instruct"):
        self.base_model_id = base_model_id
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.check_and_load_adapter()

    def check_and_load_adapter(self):
        if not os.path.exists(self.ADAPTER_DIR):
            print(f"[*] LoRA Adapter directory ({self.ADAPTER_DIR}) not found. Engine using Extractive RAG mode.")
            return

        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            from peft import PeftModel

            print(f"[*] Loading Fine-Tuned Arabic LoRA Adapter from {self.ADAPTER_DIR}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.ADAPTER_DIR, trust_remote_code=True)
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_id,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            self.model = PeftModel.from_pretrained(base_model, self.ADAPTER_DIR)
            self.is_loaded = True
            print("[+] Fine-Tuned Arabic LoRA Adapter loaded successfully!")
        except Exception as e:
            print(f"[!] LoRA Adapter load notice: {e}")

    def generate_friendly_response(self, user_query: str, retrieved_context: str) -> str | None:
        if not self.is_loaded or self.model is None or self.tokenizer is None:
            return None

        prompt = f"<|im_start|>system\nأنت رَفِيق، المستشار الإسلامي الذكي. أجب بسلاسة ووضوح وبلسان عربي فصيح وميسر بناءً على المصادر المرفقة.<|im_end|>\n<|im_start|>user\nالسؤال: {user_query}\n\nالمصادر المعتمدة:\n{retrieved_context}<|im_end|>\n<|im_start|>assistant\n"
        
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=350,
                    temperature=0.3,
                    top_p=0.9,
                    do_sample=True
                )
            generated = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
            return generated.strip()
        except Exception as e:
            print(f"[!] LoRA Generation notice: {e}")
            return None
