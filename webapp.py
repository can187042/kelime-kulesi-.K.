import streamlit as st
import json
import os
import glob
import random
import requests
import time
import re
from gtts import gTTS
from deep_translator import GoogleTranslator
import base64

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kelime Kulesi", page_icon="🏰", layout="wide", initial_sidebar_state="expanded")

# --- ÖZEL CSS (GÖRÜNÜM AYARLARI) ---
st.markdown("""
    <style>
    /* Kelime Kartı Tasarımı */
    .flashcard {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
        border: 2px solid #f0f0f0;
    }
    .english-word {
        font-size: 70px !important;
        font-weight: 800;
        color: #2c3e50;
        margin: 0;
        padding: 0;
    }
    .turkish-word {
        font-size: 45px !important;
        font-weight: normal;
        color: #e67e22; /* Turuncu */
        margin-top: 10px;
        animation: fadeIn 0.5s;
    }
    
    /* Buton Tasarımları */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 55px;
        font-size: 18px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    /* Video Alanı */
    .video-container {
        margin-top: 20px;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- SABİTLER ---
KLASOR = "kelime_kutusu"
VIDEO_KLASOR = "kelime_kutusu/videolar"
PEXELS_API_KEY = "coY2VaGe3OeYlTWs4AL0fWITB1RNk1k25jH2HFJoJ9dDtkqzg00tol5x"

if not os.path.exists(KLASOR): os.makedirs(KLASOR)
if not os.path.exists(VIDEO_KLASOR): os.makedirs(VIDEO_KLASOR)

# --- FONKSİYONLAR ---
def ses_cal_gtts(metin):
    """Metni seslendirir"""
    try:
        tts = gTTS(text=metin, lang='en')
        # Geçici dosya yerine byte stream kullanabiliriz ama dosya daha stabil
        tts.save("temp_audio.mp3")
        with open("temp_audio.mp3", "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True)
    except:
        pass

def video_bul(kelime):
    """Videoyu bulur veya indirir"""
    temiz_eng = "".join([c for c in kelime if c.isalnum() or c in (' ', '-', '_')]).strip().lower()
    yerel_yol = os.path.join(VIDEO_KLASOR, f"{temiz_eng}.mp4")
    
    if os.path.exists(yerel_yol):
        return yerel_yol
    
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
# SOL MENÜ (SIDEBAR)
# =========================================================
with st.sidebar:
    st.header("📂 Dosya Yöneticisi")
    dosyalar = dosya_listesi()
    
    if not dosyalar:
        st.warning("Hiç dosya bulunamadı.")
    else:
        secilen_dosya = st.selectbox("Çalışılacak Dosya:", dosyalar)
        
        # Dosya değişince index'i sıfırla
        if secilen_dosya != st.session_state.aktif_dosya:
            st.session_state.aktif_dosya = secilen_dosya
            st.session_state.index = 0
            st.session_state.kart_acik = False
    
    st.divider()
    st.info("💡 İpucu: 'GÖSTER' butonuna basarak kelimenin anlamını görebilirsin.")

# =========================================================
# ANA EKRAN
# =========================================================

if not st.session_state.aktif_dosya:
    st.title("🏰 Kelime Kulesi")
    st.write("Lütfen sol menüden bir dosya seçin.")
    st.stop()

veri = dosya_oku(st.session_state.aktif_dosya)
tur = "hikaye" if isinstance(veri, dict) else "kelime"

# --- KELİME MODU ---
if tur == "kelime":
    if not veri:
        st.warning("Bu dosya boş.")
    else:
        # Index güvenliği
        idx = st.session_state.index
        if idx >= len(veri): st.session_state.index = 0
        kelime = veri[st.session_state.index]

        # 1. KELİME ALANI (ÜSTTE)
        # HTML ile özel tasarım kutusu
        html_content = f"""
        <div class="flashcard">
            <p class="english-word">{kelime['eng']}</p>
        """
        
        # Eğer kart açıksa Türkçe anlamı ekle
        if st.session_state.kart_acik:
            html_content += f'<p class="turkish-word">{kelime["tr"]}</p></div>'
            ses_cal_gtts(kelime['eng']) # Sadece açılınca oku
        else:
            html_content += '</div>' # Türkçe yok
            
        st.markdown(html_content, unsafe_allow_html=True)

        # 2. KONTROL BUTONLARI (ORTADA)
        c1, c2, c3 = st.columns([1, 2, 1])
        
        with c1:
            if st.button("⬅️ Önceki"):
                st.session_state.index = (st.session_state.index - 1) % len(veri)
                st.session_state.kart_acik = False # Yeni kelimeye geçince kapat
                st.rerun()
                
        with c2:
            # Burası senin "Alt Ok" işlevini görecek ana buton
            lbl = "GİZLE 🙈" if st.session_state.kart_acik else "GÖSTER (Alt Ok) 👁️"
            # Butona basınca durumu tersine çevir
            if st.button(lbl, type="primary"): 
                st.session_state.kart_acik = not st.session_state.kart_acik
                st.rerun()
                
        with c3:
            if st.button("Sonraki ➡️"):
                st.session_state.index = (st.session_state.index + 1) % len(veri)
                st.session_state.kart_acik = False # Yeni kelimeye geçince kapat
                st.rerun()

        # 3. VİDEO ALANI (EN ALTTA VE SÜREKLİ AÇIK)
        st.markdown('<div class="video-container">', unsafe_allow_html=True)
        video_yolu = video_bul(kelime["eng"])
        if video_yolu:
            # Video her zaman görünür, kartın açık/kapalı olmasından etkilenmez
            st.video(video_yolu, autoplay=True, loop=True, muted=True)
        else:
            st.info("Video aranıyor veya bulunamadı...")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # İlerleme çubuğu en altta şık durur
        st.progress((idx + 1) / len(veri))

# --- HİKAYE MODU (DEĞİŞMEDİ, AYNI KALDI) ---
else:
    st.subheader(f"📖 {secilen_dosya}")
    # Hikaye kodu buraya eklenebilir (önceki kodun aynısı)
    # Şimdilik yer tutucu:
    sayfalar = veri.get("sayfalar", [])
    if sayfalar:
        st.write(sayfalar[0])
    else:
        st.write("Sayfa yok.")
