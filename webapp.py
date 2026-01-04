import streamlit as st
import json
import os
import glob
import requests
import re
from gtts import gTTS
import base64

# --- SAYFA AYARLARI (MENÜ AÇIK BAŞLASIN) ---
st.set_page_config(
    page_title="Kelime Kulesi", 
    page_icon="🏰", 
    layout="wide", 
    initial_sidebar_state="expanded"  # <-- Bu ayar menüyü açık tutmaya zorlar
)

# --- CSS TASARIM ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    header {visibility: hidden;}
    
    .flashcard {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        text-align: center;
        border: 2px solid #f0f0f0;
        height: 350px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .english-word { font-size: 60px !important; font-weight: 800; color: #2c3e50; margin: 0; line-height: 1.2; }
    .turkish-word { font-size: 40px !important; font-weight: normal; color: #e67e22; margin-top: 10px; animation: fadeIn 0.5s; }
    
    .stButton>button { width: 100%; border-radius: 10px; height: 50px; font-size: 16px; font-weight: bold; margin-top: 10px; }
    
    .video-container {
        border-radius: 15px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        max-height: 400px; display: flex; justify-content: center; align-items: center; background-color: #000;
    }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    """, unsafe_allow_html=True)

# --- AYARLAR ---
KLASOR = "kelime_kutusu"
VIDEO_KLASOR = "kelime_kutusu/videolar"
PEXELS_API_KEY = "coY2VaGe3OeYlTWs4AL0fWITB1RNk1k25jH2HFJoJ9dDtkqzg00tol5x"

if not os.path.exists(KLASOR): os.makedirs(KLASOR)
if not os.path.exists(VIDEO_KLASOR): os.makedirs(VIDEO_KLASOR)

# --- FONKSİYONLAR ---
def ses_cal_gtts(metin):
    try:
        tts = gTTS(text=metin, lang='en')
        tts.save("temp_audio.mp3")
        with open("temp_audio.mp3", "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>"""
        st.markdown(md, unsafe_allow_html=True)
    except: pass

def video_bul(kelime):
    temiz_eng = "".join([c for c in kelime if c.isalnum() or c in (' ', '-', '_')]).strip().lower()
    yerel_yol = os.path.join(VIDEO_KLASOR, f"{temiz_eng}.mp4")
    if os.path.exists(yerel_yol): return yerel_yol
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={kelime}&per_page=1&orientation=landscape"
        r = requests.get(url, headers=headers, timeout=3)
        data = r.json()
        if data.get('videos'):
            link = data['videos'][0]['video_files'][0]['link']
            with open(yerel_yol, "wb") as f: f.write(requests.get(link).content)
            return yerel_yol
    except: pass
    return None

def dosya_oku(isim):
    try:
        with open(os.path.join(KLASOR, f"{isim}.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def dosya_listesi():
    return [os.path.splitext(os.path.basename(d))[0] for d in glob.glob(os.path.join(KLASOR, "*.json"))]

# --- STATE ---
if 'index' not in st.session_state: st.session_state.index = 0
if 'kart_acik' not in st.session_state: st.session_state.kart_acik = False
if 'aktif_dosya' not in st.session_state: st.session_state.aktif_dosya = ""

# =========================================================
# SOL MENÜ (SIDEBAR) - BURASI ÖNEMLİ
# =========================================================
with st.sidebar:
    st.title("📂 Dosyalar")
    dosyalar = dosya_listesi()
    if not dosyalar:
        st.error("Dosya yok!")
    else:
        secilen_dosya = st.selectbox("Seçiniz:", dosyalar)
        if secilen_dosya != st.session_state.aktif_dosya:
            st.session_state.aktif_dosya = secilen_dosya
            st.session_state.index = 0
            st.session_state.kart_acik = False
    
    st.divider()
    st.info("Menüyü kapatmak için sol üstteki çarpıya basabilirsin.")

# =========================================================
# ANA EKRAN
# =========================================================
if not st.session_state.aktif_dosya:
    st.title("👈 Lütfen Soldan Dosya Seçin")
    st.stop()

veri = dosya_oku(st.session_state.aktif_dosya)
tur = "hikaye" if isinstance(veri, dict) else "kelime"

if tur == "kelime":
    if not veri:
        st.warning("Bu dosya boş.")
    else:
        idx = st.session_state.index
        if idx >= len(veri): st.session_state.index = 0
        kelime = veri[st.session_state.index]

        # --- EKRAN DÜZENİ ---
        col_sol, col_sag = st.columns([5, 4]) 

        with col_sol:
            # 1. KELİME KARTI
            html_content = f"""<div class="flashcard"><p class="english-word">{kelime['eng']}</p>"""
            
            if st.session_state.kart_acik:
                html_content += f'<p class="turkish-word">{kelime["tr"]}</p></div>'
            else:
                html_content += '</div>'
                ses_cal_gtts(kelime['eng']) # SES: KART KAPALIYKEN (İLK AÇILIŞTA) ÇALAR
            
            st.markdown(html_content, unsafe_allow_html=True)
            
            # 2. BUTONLAR
            c1, c2, c3 = st.columns([1, 2, 1])
            with c1:
                if st.button("⬅️ Geri"):
                    st.session_state.index = (st.session_state.index - 1) % len(veri)
                    st.session_state.kart_acik = False
                    st.rerun()
            with c2:
                lbl = "GİZLE 🙈" if st.session_state.kart_acik else "GÖSTER (Alt Ok) 👁️"
                if st.button(lbl, type="primary"): 
                    st.session_state.kart_acik = not st.session_state.kart_acik
                    st.rerun()
            with c3:
                if st.button("İleri ➡️"):
                    st.session_state.index = (st.session_state.index + 1) % len(veri)
                    st.session_state.kart_acik = False
                    st.rerun()
            
            st.progress((idx + 1) / len(veri))

        with col_sag:
            # 3. VİDEO ALANI
            st.markdown('<div class="video-container">', unsafe_allow_html=True)
            video_yolu = video_bul(kelime["eng"])
            if video_yolu:
                st.video(video_yolu, autoplay=True, loop=True, muted=True)
            else:
                st.info("Video bulunamadı.")
            st.markdown('</div>', unsafe_allow_html=True)

else:
    st.subheader(f"📖 {secilen_dosya}")
    sayfalar = veri.get("sayfalar", [])
    if sayfalar:
        st.write(sayfalar[0])
    else:
        st.write("Sayfa yok.")
