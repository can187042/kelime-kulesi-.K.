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

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Kelime Kulesi", page_icon="🏰", layout="wide")

# --- SABİTLER VE YÖNETİCİLER ---
KLASOR = "kelime_kutusu"
VIDEO_KLASOR = "kelime_kutusu/videolar"
PEXELS_API_KEY = "coY2VaGe3OeYlTWs4AL0fWITB1RNk1k25jH2HFJoJ9dDtkqzg00tol5x"

if not os.path.exists(KLASOR): os.makedirs(KLASOR)
if not os.path.exists(VIDEO_KLASOR): os.makedirs(VIDEO_KLASOR)
if not glob.glob(os.path.join(KLASOR, "*.json")):
    with open(os.path.join(KLASOR, "tekrar_et.json"), "w", encoding="utf-8") as f:
        json.dump([], f)


# --- FONKSİYONLAR ---
def ses_olustur(metin, lang='en'):
    """Metni sese çevirir ve Streamlit oynatıcısına gönderir"""
    try:
        tts = gTTS(text=metin, lang=lang, slow=False)
        fp = BytesIO()
        tts.write_to_fp(fp)
        return fp
    except:
        return None


def video_bul_ve_getir(kelime):
    """Pexels'den video bulur veya yerelden getirir"""
    temiz_eng = "".join([c for c in kelime if c.isalnum() or c in (' ', '-', '_')]).strip().lower()
    yerel_yol = os.path.join(VIDEO_KLASOR, f"{temiz_eng}.mp4")

    # Önce yerelde var mı bakalım
    if os.path.exists(yerel_yol):
        return yerel_yol

    # Yoksa indirelim
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={kelime}&per_page=1&orientation=landscape"
        r = requests.get(url, headers=headers, timeout=5)
        data = r.json()
        if data.get('videos'):
            video_url = data['videos'][0]['video_files'][0]['link']
            video_data = requests.get(video_url).content
            with open(yerel_yol, "wb") as f:
                f.write(video_data)
            return yerel_yol
    except:
        pass
    return None


def dosya_listesi():
    return [os.path.splitext(os.path.basename(d))[0] for d in glob.glob(os.path.join(KLASOR, "*.json"))]


def dosya_oku(isim):
    yol = os.path.join(KLASOR, f"{isim}.json")
    with open(yol, "r", encoding="utf-8") as f:
        return json.load(f)


def dosya_yaz(isim, veri):
    yol = os.path.join(KLASOR, f"{isim}.json")
    with open(yol, "w", encoding="utf-8") as f:
        json.dump(veri, f, indent=4, ensure_ascii=False)


def kelime_analiz_et(metin, mevcut_sozluk):
    kelimeler = set(re.findall(r'\w+', metin.lower()))
    yeni = {}
    translator = GoogleTranslator(source='auto', target='tr')
    for k in kelimeler:
        if len(k) > 2 and k not in mevcut_sozluk:
            try:
                tr = translator.translate(k)
                yeni[k] = tr
            except:
                pass
    return yeni


# --- SESSION STATE (DURUM YÖNETİMİ) ---
if 'index' not in st.session_state: st.session_state.index = 0
if 'kart_yonu' not in st.session_state: st.session_state.kart_yonu = 'eng'  # eng veya tr
if 'sayfa_no' not in st.session_state: st.session_state.sayfa_no = 0
if 'aktif_dosya' not in st.session_state: st.session_state.aktif_dosya = ""

# --- ARAYÜZ ---
st.title("🏰 Kelime Kulesi - Web Modu")

# YAN MENÜ (SIDEBAR)
with st.sidebar:
    st.header("📂 Dosyalar")
    dosyalar = dosya_listesi()
    secilen_dosya = st.selectbox("Çalışılacak Dosya", dosyalar)

    st.divider()

    st.subheader("➕ Yeni Ekle")
    yeni_isim = st.text_input("Dosya Adı")
    yeni_tur = st.radio("Tür", ["Kelime", "Hikaye"])
    if st.button("Oluştur"):
        if yeni_isim:
            icerik = {"tip": "hikaye", "sayfalar": [], "sozluk": {}} if yeni_tur == "Hikaye" else []
            dosya_yaz(yeni_isim, icerik)
            st.success("Oluşturuldu! Sayfayı yenile.")
            time.sleep(1)
            st.rerun()

    st.divider()

    # İçerik Ekleme Alanı
    st.subheader("📝 İçerik Ekle")
    hedef_ekle = st.selectbox("Hangi Dosyaya?", dosyalar, key="ekle_hedef")
    metin_ekle = st.text_area("Metin / Kelimeler (Alt alta)")
    if st.button("Kaydet ve Analiz Et"):
        veri = dosya_oku(hedef_ekle)
        if isinstance(veri, dict):  # Hikaye
            veri["sayfalar"].append(metin_ekle)
            yeni_sozluk = kelime_analiz_et(metin_ekle, veri["sozluk"])
            veri["sozluk"].update(yeni_sozluk)
            dosya_yaz(hedef_ekle, veri)
            st.success("Hikaye sayfası eklendi!")
        else:  # Kelime
            satirlar = metin_ekle.strip().split("\n")
            eklenen = 0
            for s in satirlar:
                p = s.split("–") if "–" in s else s.split("-")
                if len(p) >= 2:
                    veri.append({"eng": p[0].strip(), "tr": p[1].strip()})
                    eklenen += 1
            dosya_yaz(hedef_ekle, veri)
            st.success(f"{eklenen} kelime eklendi!")

# --- ANA EKRAN ---

# Dosya Yükle
if secilen_dosya != st.session_state.aktif_dosya:
    st.session_state.aktif_dosya = secilen_dosya
    st.session_state.index = 0
    st.session_state.sayfa_no = 0
    st.session_state.kart_yonu = 'eng'

veri = dosya_oku(secilen_dosya)
tur = "hikaye" if isinstance(veri, dict) else "kelime"

if tur == "kelime":
    # --- KELİME KARTLARI MODU ---
    if not veri:
        st.warning("Bu dosya boş! Yan menüden kelime ekle.")
    else:
        kelime = veri[st.session_state.index]

        # İlerleme Çubuğu
        st.progress((st.session_state.index + 1) / len(veri))
        st.caption(f"Kart {st.session_state.index + 1} / {len(veri)}")

        col1, col2, col3 = st.columns([1, 6, 1])

        with col1:
            st.write("")
            st.write("")
            if st.button("⬅️", use_container_width=True):
                st.session_state.index = (st.session_state.index - 1) % len(veri)
                st.session_state.kart_yonu = 'eng'
                st.rerun()

        with col3:
            st.write("")
            st.write("")
            if st.button("➡️", use_container_width=True):
                st.session_state.index = (st.session_state.index + 1) % len(veri)
                st.session_state.kart_yonu = 'eng'
                st.rerun()

        with col2:
            # VİDEO ALANI
            video_yolu = video_bul_ve_getir(kelime["eng"])
            if video_yolu:
                st.video(video_yolu, autoplay=True, loop=True, muted=True)

            # KART ALANI
            gosterilecek = kelime["eng"] if st.session_state.kart_yonu == 'eng' else kelime["tr"]
            renk = "blue" if st.session_state.kart_yonu == 'eng' else "orange"

            st.markdown(
                f"""
                <div style="background-color:black; padding:20px; border-radius:15px; text-align:center; border: 2px solid {renk};">
                    <h1 style="color:white; font-size:60px;">{gosterilecek}</h1>
                </div>
                """,
                unsafe_allow_html=True
            )

            # BUTONLAR (Çevir ve Ses)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 ÇEVİR (Space)", use_container_width=True):
                    st.session_state.kart_yonu = 'tr' if st.session_state.kart_yonu == 'eng' else 'eng'
                    st.rerun()
            with c2:
                ses_dosyasi = ses_olustur(kelime["eng"])
                if ses_dosyasi:
                    st.audio(ses_dosyasi, format="audio/mp3")

            # Tekrar Et Listesine Ekle/Çıkar
            if st.button("⭐ Tekrar Listesine Ekle/Çıkar"):
                tekrar_veri = dosya_oku("tekrar_et")
                var_mi = any(k["eng"] == kelime["eng"] for k in tekrar_veri)
                if var_mi:
                    tekrar_veri = [k for k in tekrar_veri if k["eng"] != kelime["eng"]]
                    st.toast("Listeden Çıkarıldı", icon="🗑️")
                else:
                    tekrar_veri.append(kelime)
                    st.toast("Listeye Eklendi", icon="✅")
                dosya_yaz("tekrar_et", tekrar_veri)

else:
    # --- HİKAYE MODU ---
    sayfalar = veri.get("sayfalar", [])
    sozluk = veri.get("sozluk", {})

    if not sayfalar:
        st.warning("Bu hikayede henüz sayfa yok. Yan menüden ekle.")
    else:
        st.subheader(f"📖 Sayfa {st.session_state.sayfa_no + 1} / {len(sayfalar)}")

        aktif_metin = sayfalar[st.session_state.sayfa_no]

        # Kelimeye Tıklama Simülasyonu (Tooltip ile)
        html_metin = ""
        for kelime in aktif_metin.split():
            temiz = "".join(filter(str.isalnum, kelime.lower()))
            if temiz in sozluk:
                # Bildiğimiz kelime ise üzerine gelince anlamı çıksın
                html_metin += f'<span title="{sozluk[temiz]}" style="color:blue; font-weight:bold; cursor:help;">{kelime}</span> '
            else:
                html_metin += f"{kelime} "

        st.markdown(
            f"""
            <div style="background-color:#FFF9C4; padding:25px; border-radius:10px; font-size:22px; color:black; line-height:1.6;">
                {html_metin}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.info(
            "💡 İpucu: Mavi renkli kelimelerin üzerine fare ile gelirsen (veya mobilde basılı tutarsan) anlamını görebilirsin.")

        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("⬅️ Önceki Sayfa"):
                if st.session_state.sayfa_no > 0:
                    st.session_state.sayfa_no -= 1
                    st.rerun()
        with c2:
            ses_dosyasi = ses_olustur(aktif_metin)
            if ses_dosyasi:
                st.audio(ses_dosyasi, format="audio/mp3")
        with c3:
            if st.button("Sonraki Sayfa ➡️"):
                if st.session_state.sayfa_no < len(sayfalar) - 1:
                    st.session_state.sayfa_no += 1
                    st.rerun()