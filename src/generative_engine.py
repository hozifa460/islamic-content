import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-3B-Instruct"

class GenerativeIslamicEngine:
    """Generative LLM Engine using PyTorch Transformers Qwen2.5 for Fluid Understanding & Intelligent Responses."""

    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.is_ready = False
        self.load_model()

    def load_model(self):
        print(f"[*] Initializing PyTorch Qwen2.5 Generative Engine ({MODEL_NAME})...")
        try:
            hf_token = os.environ.get("HF_TOKEN")
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=hf_token)
            self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype="auto",
                device_map="cpu",
                low_cpu_mem_usage=True,
                token=hf_token
            )
            self.is_ready = True
            print(f"[+] Generative Engine ({MODEL_NAME}) initialized and ready!")
        except Exception as e:
            print(f"[!] Qwen2.5 PyTorch load notice: {e}")
            self.is_ready = False

    def generate_response(self, user_query: str, retrieved_context: str = "") -> str | None:
        if not self.is_ready or self.model is None or self.tokenizer is None:
            return None

        system_prompt = (
            "أنت رَفِيق، المستشار الإسلامي الذكي والصديق اللطيف المتحدث بالعربية الفصيحة والميسرة. "
            "تفهم وتستوعب جميع الأسئلة واللهجات العربية (المصرية، الخليجية، الشامية) بسلاسة فائقة، وتجيب بذكاء وود كصديق ومستشار أمين."
        )

        if retrieved_context:
            user_prompt = f"السؤال: {user_query}\n\nالمعلومات المعتمدة:\n{retrieved_context}\n\nأجب بأسلوب سلس وميسر ومطابق للمعلومات أعلاه."
        else:
            user_prompt = f"السؤال أو المحادثة: {user_query}\n\nأجب بأسلوبك الذكي الودود اللطيف الشبيه بالرفيق والصديق."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            model_inputs = self.tokenizer([text], return_tensors="pt")

            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=250,
                do_sample=True,
                temperature=0.6,
                top_p=0.9
            )
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]

            response_text = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
            return response_text
        except Exception as e:
            print(f"[!] Generative response error: {e}")
            return None

if __name__ == "__main__":
    engine = GenerativeIslamicEngine()
    if engine.is_ready:
        print("Testing Generative Query 'انت اي نموذج':")
        print(engine.generate_response("انت اي نموذج"))

