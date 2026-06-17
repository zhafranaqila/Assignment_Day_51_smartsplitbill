import os
import time
import json
from PIL import Image
from google import genai
from google.genai import types
from transformers import DonutProcessor, VisionEncoderDecoderModel
import torch

if os.path.exists(".streamlit/secrets.toml"):
    with open(".streamlit/secrets.toml", "r") as f:
        for line in f:
            if "GEMINI_API_KEY" in line:
                # Mengambil string di dalam tanda petik
                api_key = line.split("=")[1].strip().strip('"').strip("'")
                os.environ["GEMINI_API_KEY"] = api_key

#set up path buat gambar
IMG_1 = "data/pic1.jpeg"
IMG_2 = "data/pic2.png"

# Schema JSON untuk konsistensi output Gemini
SCHEMA_PROMPT = {
    "type": "OBJECT",
    "properties": {
        "items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "nama_item": {"type": "STRING"},
                    "jumlah": {"type": "INTEGER"},
                    "harga_per_item": {"type": "NUMBER"},
                    "total_harga_item": {"type": "NUMBER"}
                },
                "required": ["nama_item", "jumlah", "harga_per_item", "total_harga_item"]
            }
        },
        "subtotal": {"type": "NUMBER"},
        "pajak": {"type": "NUMBER"},
        "service_charge": {"type": "NUMBER"},
        "total_harga_bill": {"type": "NUMBER"}
    },
    "required": ["items", "subtotal", "pajak", "service_charge", "total_harga_bill"]
}

def test_gemini(image_path):
    print(f"\n--- [MODEL 1] Menguji Gemini 1.5 Flash pada: {image_path} ---")
    start_time = time.time()
    
    try:
        client = genai.Client()
        img = Image.open(image_path)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[img, "Extract all transaction items, quantities, prices, subtotal, tax, service charge, and grand total from this receipt image strictly into the requested JSON schema."],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SCHEMA_PROMPT,
                temperature=0.1,
            ),
        )
        inference_time = time.time() - start_time
        print(f"⏱️ Inference Time: {inference_time:.2f} detik")
        print("📝 Hasil Ekstraksi:")
        print(json.dumps(json.loads(response.text), indent=4))
        return inference_time, response.text
    except Exception as e:
        print(f"❌ Error Gemini: {e}")
        return None, None

def test_donut(image_path):
    print(f"\n--- [MODEL 2] Menguji Hugging Face Donut pada: {image_path} ---")
    print("⏳ Loading Model Donut (Proses awal mungkin agak lama mendownload weights ~800MB)...")
    
    start_time = time.time()
    try:
        # Load model & processor Donut yang di-finetune untuk resit (CORD dataset)
        processor = DonutProcessor.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")
        model = VisionEncoderDecoderModel.from_pretrained("naver-clova-ix/donut-base-finetuned-cord-v2")
        
        # Pindahkan ke GPU jika tersedia
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model.to(device)
        
        img = Image.open(image_path).convert("RGB")
        
        # Preprocessing gambar
        pixel_values = processor(img, return_tensors="pt").pixel_values
        pixel_values = pixel_values.to(device)
        
        # Generate token kuliner / teks struktur
        task_prompt = "<s_cord-v2>"
        decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids
        decoder_input_ids = decoder_input_ids.to(device)
        
        outputs = model.generate(
            pixel_values,
            decoder_input_ids=decoder_input_ids,
            max_length=model.config.decoder.max_position_embeddings,
            pad_token_id=processor.tokenizer.pad_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
            use_cache=True,
            bad_words_ids=[[processor.tokenizer.unk_token_id]],
            return_dict_in_generate=True,
        )
        
        # Decode hasil ke bentuk JSON-like text
        sequence = processor.batch_decode(outputs.sequences)[0]
        sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
        clean_json = processor.token2json(sequence)
        
        inference_time = time.time() - start_time
        print(f"⏱️ Inference Time: {inference_time:.2f} detik")
        print("📝 Hasil Ekstraksi:")
        print(json.dumps(clean_json, indent=4))
        return inference_time, clean_json
    except Exception as e:
        print(f"❌ Error Donut: {e}")
        return None, None

if __name__ == "__main__":
    # Jalankan pengujian untuk pic1
    if os.path.exists(IMG_1):
        test_gemini(IMG_1)
        test_donut(IMG_1)
    else:
        print(f"File {IMG_1} tidak ditemukan. Cek kembali nama ekstensi file kamu.")