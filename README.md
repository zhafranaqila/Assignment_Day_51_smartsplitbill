# 🧾 SmartSplit Bill AI — Proof of Concept (PoC)

Aplikasi prototype berbasis Python dan Streamlit untuk ekstraksi data struk belanja secara otomatis menggunakan Generative AI, dilengkapi fitur pembagian tagihan (*split bill*) secara proporsional dan adil.

---

## 🏗️ Arsitektur Sistem

Aplikasi ini dibangun menggunakan arsitektur *VLM-based Information Extraction* yang memotong jalur OCR konvensional untuk efisiensi data:

[Foto Struk] ➔ [Streamlit UI] ➔ [Gemini API (2.5-Flash)] ➔ [JSON Structured Output]
│
[Hasil Split Bill] 💡 [Kalkulasi Proporsional] ➔ [Validasi User] ◄┘

**Tech Stack:**
- **Frontend & UI:** Streamlit
- **Core Engine AI:** Google GenAI SDK (`gemini-2.5-flash` / `gemini-1.5-flash`)
- **Format Data:** JSON Structured Outputs

---

## 🔬 Hasil Riset & Perbandingan Model AI

Sesuai instruksi assignment, dilakukan eksperimen mandiri terhadap dua jenis model *OCR-Free / Document Information Extraction* menggunakan sampel struk belanja (*Sushi Tei*):

| Kriteria Penilaian | Model 1: Gemini (API-Based) | Model 2: HF Donut (Local Model) |
| :--- | :--- | :--- |
| **Waktu Inference** | **~10.05 detik** (Lebih Cepat) | **~21.43 detik** (Lebih Lambat) |
| **Konsistensi Format**| **Sempurna**. Output otomatis berupa JSON sesuai skema. | **Kurang**. Struktur default model (`nm`, `cnt`, `price`). |
| **Akurasi Teks & Angka**| **Sangat Tinggi**. Nominal angka bersih dari teks sampah. | **Cukup**. Berhasil baca item, tapi *halusinasi* di area footer. |
| **Dependensi Hardware**| Ringan (Komputasi berbasis Cloud). | Berat (Sangat bergantung pada CPU/GPU lokal). |

**Kesimpulan Pemilihan Model:** Model **Gemini** dipilih sebagai engine utama prototype karena fitur *Structured Output*-nya memastikan tipe data (integer/float) konsisten sehingga aman saat diproses oleh fungsi kalkulator matematika Python tanpa risiko error `ValueError`.

---

## 🛠️ Troubleshooting & Dependency Management

Selama fase pengembangan prototype, ditemukan beberapa kendala teknis dari template dasar dan dependensi eksternal. Berikut adalah log dokumentasi penyelesaian masalah (*troubleshooting*):

### 1. Isu Dependensi Modul Tambahan (`babel`)
- **Masalah:** Saat pertama kali menjalankan perintah `streamlit run app.py`, aplikasi mengalami *crash* dengan pesan error `ModuleNotFoundError: No module named 'babel'`.
- **Penyebab:** Modul `babel.numbers` digunakan di dalam arsitektur utilitas template untuk memformat mata uang rupiah (`format_currency`), namun library tersebut belum terdaftar di instalasi dasar.
- **Solusi:** Melakukan instalasi manual terhadap library penunjang lokal tersebut di dalam environment aktif menggunakan perintah `pip install babel`.

### 2. Sinkronisasi Ekstensi Berkas Gambar (*File Extension Handling*)
- **Masalah:** Script penguji sempat mendeteksi error file tidak ditemukan: `File data/pic1.jpg tidak ditemukan. Cek kembali nama ekstensi file kamu.`
- **Penyebab:** Perbedaan penulisan ekstensi fisik antara `.jpg` dan `.jpeg` pada sistem operasi Windows.
- **Solusi:** Menyesuaikan variabel pencarian path gambar di dalam kode agar membaca `data/pic1.jpeg` secara presisi sesuai format berkas asli struk belanja.

---

## 🚧 Kelemahan Sistem & Ide Improvisasi

### 1. Sisi Model AI
- **Kelemahan:** Jika kualitas foto struk terlalu miring, buram (*blur*), atau pencahayaan minim, AI terkadang salah membaca angka (misal angka 0 terbaca 8) atau melewatkan karakter kecil. Selain itu, model API gratisan rentan terkena error `503 Service Unavailable` saat traffic padat.
- **Ide Improvisasi:** Menambahkan pipeline preprocessing gambar menggunakan **OpenCV** (seperti *Grayscale* dan *Adaptive Thresholding*) sebelum dikirim ke API untuk mempertegas karakter teks, serta menerapkan mekanisme *retries/back-off* jika API mendeteksi error 503.

### 2. Sisi Produk & UI/UX
- **Kelemahan (Utang Teknis):** Aplikasi memunculkan log peringatan *deprecation* karena menggunakan parameter `use_container_width=True` pada fungsi penampilan gambar (`st.image`), yang mana parameter ini sudah tidak didukung pada versi Streamlit terbaru pasca Desember 2025. Input nama anggota patungan juga masih bersifat manual (dipisahkan koma), dan proses alokasi item harus dicentang satu per satu.
- **Ide Improvisasi:** Melakukan *refactoring* kode UI pada rilis berikutnya dengan mengganti sintaks lama menjadi `width='stretch'` untuk menjamin kompatibilitas Streamlit. Mengembangkan fitur UI berbasis *Drag-and-Drop* kartu nama ke baris item menu, atau menambahkan fitur *Auto-split* cerdas berbasis kecerdasan buatan.

---

## 🚀 Cara Menjalankan Aplikasi Secara Lokal

1. **Clone Repository:**
```bash
   git clone <link-repo-github-kamu>
   cd smartsplit-bill-ai