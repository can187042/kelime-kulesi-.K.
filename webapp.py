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
from io import BytesIO
import base64

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kelime Kulesi", page_icon="🏰", layout="centered")

# --- CSS İLE TASARIM ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 50px;
        font-weight: bold;
    }
    .story-text {
        background-color: #fff9c4;
        padding: 25px;
        border-radius: 10px;
        font-size: 20px;
        line-height: 1.8;
        color: #333;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
    }
    .word-span {
        cursor: help;
        border-bottom: 2px dotted #aaa;
        padding-bottom: 1px;
        transition: all 0.2s;
    }
    .word-span:hover {
        background-color: #ffeb3b;
        color: #000;
        border-bottom: 2px solid #000;
    }
    .known-word {
        color: #1565C0; /* Mavi */
        font-weight: bold;
        border-bottom: 2px solid #90CAF9;
    }
    .unknown-word {
        color: #424242; /* Koyu Gri */
    }
    </style>
    """, unsafe_allow_html=True)

# --- SABİTLER ---
KLASOR = "kelime_kutusu"
VIDEO_KLASOR = "kelime_kutusu/videolar"
PEXELS_API_KEY = "coY2VaGe3OeYlTWs4AL0fWITB1RNk1k25jH2HFJoJ9dDtkqzg00tol5x"

if not os.path.exists(KLASOR): os.makedirs(KLASOR)
if not os.path.exists(VIDEO_KLASOR): os.makedirs(VIDEO_KLASOR)

# --- YARDIMCI FONKSİYONLAR ---
def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    md = f"""
        <audio autoplay="true">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(md, unsafe_allow_html=True)

def ses_cal_gtts(metin):
    try:
        tts = gTTS(text=metin, lang='en')
        tts.save("temp_audio.mp3")
        autoplay_audio("temp_audio.mp3")
    except:
        pass

def dosya_oku(isim):
    try:
        with open(os.path.join(KLASOR, f"{isim}.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except: return []

def dosya_yaz(isim, veri):
    with open(os.path.join(KLASOR, f"{isim}.json"), "w", encoding="utf-8") as f:
        json.dump(veri, f, indent=4, ensure_ascii=False)

def dosya_listesi():
    return [os.path.splitext(os.path.basename(d))[0] for d in glob.glob(os.path.join(KLASOR, "*.json"))]

def kelime_temizle(kelime):
    return "".join(filter(str.isalnum, kelime.lower()))

def video_bul(kelime):
    temiz = kelime_temizle(kelime)
    yerel_yol = os.path.join(VIDEO_KLASOR, f"{temiz}.mp4")
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

# --- STATE YÖNETİMİ ---
if 'index' not in st.session_state: st.session_state.index = 0
if 'kart_acik' not in st.session_state: st.session_state.kart_acik = False
if 'sayfa_no' not in st.session_state: st.session_state.sayfa_no = 0

# --- ANA UYGULAMA ---
st.title("🏰 Kelime Kulesi")

dosyalar = dosya_listesi()
if not dosyalar:
    st.warning("Henüz dosya yok. GitHub'a kelime dosyalarını yükleyin.")
    st.stop()

secilen_dosya = st.selectbox("Dosya Seç:", dosyalar)
veri = dosya_oku(secilen_dosya)
tur = "hikaye" if isinstance(veri, dict) else "kelime"

# =========================================================
# MOD 1: KELİME KARTLARI (FLASHCARD)
# =========================================================
if tur == "kelime":
    if not veri:
        st.info("Bu dosya boş.")
    else:
        idx = st.session_state.index
        if idx >= len(veri): st.session_state.index = 0
        kelime = veri[st.session_state.index]
        
        st.progress((idx + 1) / len(veri))
        
        c1, c2 = st.columns([1, 1])
        with c1:
            vid = video_bul(kelime["eng"])
            if st.session_state.kart_acik and vid:
                st.video(vid, autoplay=True, loop=True, muted=True)
            else:
                st.info("🔒 Video Gizli")
        
        with c2:
            st.markdown(f"<h1 style='text-align:center;'>{kelime['eng']}</h1>", unsafe_allow_html=True)
            if st.session_state.kart_acik:
                st.markdown(f"<h2 style='text-align:center; color:orange;'>{kelime['tr']}</h2>", unsafe_allow_html=True)
                ses_cal_gtts(kelime["eng"])
            else:
                st.markdown("<h2 style='text-align:center; color:gray;'>???</h2>", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            if st.button("⬅️"):
                st.session_state.index = (st.session_state.index - 1) % len(veri)
                st.session_state.kart_acik = False
                st.rerun()
        with col2:
            lbl = "GİZLE 🙈" if st.session_state.kart_acik else "GÖSTER 👁️"
            if st.button(lbl):
                st.session_state.kart_acik = not st.session_state.kart_acik
                st.rerun()
        with col3:
            if st.button("➡️"):
                st.session_state.index = (st.session_state.index + 1) % len(veri)
                st.session_state.kart_acik = False
                st.rerun()

# =========================================================
# MOD 2: HİKAYE OKUMA (STORY MODE) - GÜNCELLENDİ!
# =========================================================
else:
    sayfalar = veri.get("sayfalar", [])
    sozluk = veri.get("sozluk", {})
    
    if not sayfalar:
        st.warning("Bu hikayede sayfa yok.")
    else:
        # Sayfa Kontrolü
        if st.session_state.sayfa_no >= len(sayfalar): st.session_state.sayfa_no = 0
        aktif_metin = sayfalar[st.session_state.sayfa_no]
        
        st.caption(f"Sayfa {st.session_state.sayfa_no + 1} / {len(sayfalar)}")

        # 1. HTML OLUŞTURMA (Her kelime için tooltip)
        html_cikti = []
        eksik_kelime_var_mi = False
        
        for kelime_ham in aktif_metin.split():
            temiz = kelime_temizle(kelime_ham)
            if not temiz:
                html_cikti.append(kelime_ham)
                continue
            
            if temiz in sozluk:
                # Sözlükte var: Mavi ve Anlamlı
                anlam = sozluk[temiz]
                span = f'<span class="word-span known-word" title="{anlam}">{kelime_ham}</span>'
                html_cikti.append(span)
            else:
                # Sözlükte yok: Gri ve Anlamsız (Ama tıklanabilir görünür)
                span = f'<span class="word-span unknown-word" title="Çeviri yok">{kelime_ham}</span>'
                html_cikti.append(span)
                if len(temiz) > 1: # 1 harften büyükse eksik say
                    eksik_kelime_var_mi = True
        
        # Hikayeyi Ekrana Bas
        st.markdown(f'<div class="story-text">{" ".join(html_cikti)}</div>', unsafe_allow_html=True)
        st.caption("ℹ️ Kelimelerin üzerine gelerek (telefonda tıklayarak) anlamını görebilirsin.")

        # 2. BUTONLAR VE SES
        col_nav1, col_audio, col_nav2 = st.columns([1, 2, 1])
        with col_nav1:
            if st.button("⬅️ Geri"):
                if st.session_state.sayfa_no > 0:
                    st.session_state.sayfa_no -= 1
                    st.rerun()
        with col_audio:
            if st.button("🔊 Sayfayı Dinle"):
                ses_cal_gtts(aktif_metin)
        with col_nav2:
            if st.button("İleri ➡️"):
                if st.session_state.sayfa_no < len(sayfalar) - 1:
                    st.session_state.sayfa_no += 1
                    st.rerun()

        st.divider()

        # 3. EKSİK KELİMELERİ TAMAMLAMA (OTOMATİK)
        if eksik_kelime_var_mi:
            st.warning("⚠️ Bu sayfada sözlükte olmayan kelimeler var. Anlamlarını görmek için aşağıdaki butona bas.")
            if st.button("✨ TÜM SAYFAYI ÇEVİR VE KAYDET ✨"):
                progress_text = "Kelimeler analiz ediliyor..."
                my_bar = st.progress(0, text=progress_text)
                
                translator = GoogleTranslator(source='auto', target='tr')
                kelimeler_set = set(re.findall(r'\w+', aktif_metin.lower()))
                eklenen = 0
                toplam = len(kelimeler_set)
                
                for i, k in enumerate(kelimeler_set):
                    if len(k) > 1 and k not in sozluk:
                        try:
                            tr = translator.translate(k)
                            sozluk[k] = tr
                            eklenen += 1
                        except: pass
                    my_bar.progress((i + 1) / toplam)
                
                my_bar.empty()
                if eklenen > 0:
                    veri["sozluk"] = sozluk
                    dosya_yaz(secilen_dosya, veri)
                    st.success(f"{eklenen} yeni kelime sözlüğe eklendi! Sayfa yenileniyor...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("Eklenecek yeni kelime bulunamadı.")

        # 4. KELİME DÜZENLEME (HATA DÜZELTME)
        with st.expander("✍️ Kelime Anlamı Düzenle / Düzelt"):
            tum_kelimeler = sorted(list(sozluk.keys()))
            duzenlenecek = st.selectbox("Düzenlenecek kelimeyi seç:", tum_kelimeler)
            if duzenlenecek:
                yeni_anlam = st.text_input("Türkçe Anlamı:", value=sozluk[duzenlenecek])
                if st.button("Kaydet ve Düzelt"):
                    sozluk[duzenlenecek] = yeni_anlam
                    veri["sozluk"] = sozluk
                    dosya_yaz(secilen_dosya, veri)
                    st.success(f"'{duzenlenecek}' kelimesi güncellendi!")
                    time.sleep(1)
                    st.rerun()
