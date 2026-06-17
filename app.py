import streamlit as st
import json
import os
from PIL import Image
from google import genai
from google.genai import types

# Setup Konfigurasi Halaman Streamlit
st.set_page_config(page_title="SmartSplit Bill AI", page_icon="🧾", layout="wide")

@st.cache_resource
def get_gemini_client():
    api_key = st.secrets["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)

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

st.title("🧾 SmartSplit Bill AI — Proof of Concept")
st.write("Aplikasi ekstraksi struk otomatis dan pembagian tagihan secara adil berbasis AI.")

#UI Streamlit
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📸 Upload Struk Belanja")
    uploaded_file = st.file_uploader("Pilih foto struk...", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Struk yang di-upload", use_container_width=True)

with col2:
    st.header("⚙️ Proses & Hasil Ekstraksi AI")
    
    # Inisialisasi Session State agar data tidak hilang saat UI berinteraksi
    if "extracted_data" not in st.session_state:
        st.session_state.extracted_data = None

    if uploaded_file and st.button("🚀 Jalankan Ekstraksi AI"):
        with st.spinner("Gemini sedang membaca struk belanjaanmu..."):
            try:
                client = get_gemini_client()
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=[image, "Extract items, quantities, prices, subtotal, tax, service charge, and grand total strictly into JSON."],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=SCHEMA_PROMPT,
                        temperature=0.1,
                    ),
                )
                st.session_state.extracted_data = json.loads(response.text)
                st.success("Ekstraksi Berhasil!")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memanggil API: {e}")

    # Jika data hasil ekstraksi sudah tersedia di state
    if st.session_state.extracted_data:
        data = st.session_state.extracted_data
        
        st.subheader("Membaca struk")
        st.write("Silakan sesuaikan harga")
        
        # Tampilkan ringkasan biaya tambahan
        subtotal = st.number_input("Subtotal", value=float(data.get("subtotal", 0)))
        pajak = st.number_input("Pajak (Tax)", value=float(data.get("pajak", 0)))
        service_charge = st.number_input("Service Charge", value=float(data.get("service_charge", 0)))
        total_bill = st.number_input("Total Akhir Nota", value=float(data.get("total_harga_bill", 0)))
        
        # Input Nama-nama Teman yang Ikut Patungan
        st.subheader("Pilih Anggota")
        names_input = st.text_input("Masukkan nama anggota (pisahkan dengan koma)")
        participants = [name.strip() for name in names_input.split(",") if name.strip()]
        
        if participants:
            st.subheader("Pembagian Bill")
            st.write("Centang siapa saja yang mengonsumsi atau bertanggung jawab atas setiap item:")
            
            # Buat dictionary untuk menyimpan siapa memilih apa
            assignments = {}
            items_list = data.get("items", [])
            
            for idx, item in enumerate(items_list):
                item_name = item.get("nama_item", f"Item {idx+1}")
                item_total = item.get("total_harga_item", 0)
                
                st.markdown(f"**{item_name}** — Rp {item_total:,.0f}")
                # Multiselect untuk memilih penanggung jawab item ini
                chosen = st.multiselect(f"Siapa yang bayar {item_name}?", options=participants, key=f"item_{idx}")
                assignments[idx] = {
                    "total_harga": item_total,
                    "users": chosen
                }
            
            # Tombol Kalkulasi Akhir
            if st.button("Count"):
                st.header("Your total bill:")
                
                # Inisialisasi pengeluaran pokok per orang
                personal_subtotal = {p: 0.0 for p in participants}
                
                # Hitung kontribusi pokok berdasarkan item yang dipilih
                for idx, assign in assignments.items():
                    if assign["users"]:
                        # Bagi rata harga item ke semua orang yang mencentangnya
                        cost_per_person = assign["total_harga"] / len(assign["users"])
                        for user in assign["users"]:
                            personal_subtotal[user] += cost_per_person
                
                # Hitung rasio proporsi tax & service berdasarkan subtotal riil belanja mereka
                # Rumus: (Pajak + Service) / Subtotal Awal
                total_tambahan = pajak + service_charge
                ratio_tambahan = total_tambahan / subtotal if subtotal > 0 else 0
                
                total_calculated = 0
                
                # Tampilkan breakdown tagihan dalam bentuk card UI
                for person in participants:
                    pokok = personal_subtotal[person]
                    beban_tambahan = pokok * ratio_tambahan
                    tagihan_akhir = pokok + beban_tambahan
                    total_calculated += tagihan_akhir
                    
                    st.metric(
                        label=f"👤 {person}",
                        value=f"Rp {tagihan_akhir:,.0f}",
                        delta=f"Pokok: Rp {pokok:,.0f} | Pajak/Svc: Rp {beban_tambahan:,.0f}"
                    )
                
                st.info(f"Total Bill Terkalkulasi: Rp {total_calculated:,.0f} (Harus sama / mendekati Total Akhir Nota: Rp {total_bill:,.0f})")
        else:
            st.warning("Silakan masukkan minimal 1 nama anggota patungan untuk memulai pembagian item.")