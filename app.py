import streamlit as st
import fitz
import re
import pandas as pd


# =========================================================
# SAYFA AYARLARI
# =========================================================

st.set_page_config(
    page_title="Çalışan Sayısı Belge Asistanı",
    page_icon="📄",
    layout="wide"
)


# =========================================================
# TASARIM
# =========================================================

st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

h1 {
    font-size: 2.4rem !important;
    font-weight: 700 !important;
}

h2, h3 {
    font-weight: 600 !important;
}

[data-testid="stFileUploader"] {
    border: 1px solid #d9d9d9;
    border-radius: 12px;
    padding: 18px;
}

[data-testid="stAlert"] {
    border-radius: 10px;
}

[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# BAŞLIK
# =========================================================

st.title("📄 Çalışan Sayısı Belge Asistanı")

st.write(
    "Muhtasar beyannamelerden firma, VKN, dönem ve çalışan sayısı "
    "bilgilerini otomatik olarak çıkarır, belgeleri kontrol eder "
    "ve çalışan ortalamasını hesaplar."
)

st.caption(
    "Eksik dönemleri, tekrar eden belgeleri ve farklı firmaya ait "
    "beyannameleri otomatik olarak kontrol eder."
)

st.divider()


# =========================================================
# AY İSİMLERİ
# =========================================================

ay_isimleri = {
    1: "Ocak",
    2: "Şubat",
    3: "Mart",
    4: "Nisan",
    5: "Mayıs",
    6: "Haziran",
    7: "Temmuz",
    8: "Ağustos",
    9: "Eylül",
    10: "Ekim",
    11: "Kasım",
    12: "Aralık"
}


# =========================================================
# DOSYA YÜKLEME
# =========================================================

dosyalar = st.file_uploader(
    "Muhtasar beyannamelerini yükleyin",
    type=["pdf"],
    accept_multiple_files=True
)


if dosyalar:

    belgeler = []
    okunamayanlar = []


    # =====================================================
    # PDF BELGELERİNİ OKU
    # =====================================================

    for dosya in dosyalar:

        try:

            pdf = fitz.open(
                stream=dosya.getvalue(),
                filetype="pdf"
            )

            metin = ""

            for sayfa in pdf:
                metin += sayfa.get_text() + "\n"

            pdf.close()


            # Firma adı
            firma = re.search(
                r"Mükellef\s*/\s*Firma:?\s*([^\n]+)",
                metin,
                re.IGNORECASE
            )


            # Vergi Kimlik Numarası
            vkn = re.search(
                r"Vergi Kimlik No:?\s*(\d{10})",
                metin,
                re.IGNORECASE
            )


            # Beyanname dönemi
            donem = re.search(
                r"Beyanname Dönemi:?\s*(\d{2})/(\d{4})",
                metin,
                re.IGNORECASE
            )


            # Çalışan sayısı
            calisan = re.search(
                r"Aylık hizmet bildirimi\s+(\d+)",
                metin,
                re.IGNORECASE
            )


            # Gerekli bilgiler bulunduysa kaydet
            if firma and vkn and donem and calisan:

                belgeler.append({

                    "Dosya": dosya.name,

                    "Firma":
                        firma.group(1).strip(),

                    "VKN":
                        vkn.group(1).strip(),

                    "Yıl":
                        int(donem.group(2)),

                    "Ay":
                        int(donem.group(1)),

                    "Çalışan Sayısı":
                        int(calisan.group(1))
                })

            else:

                okunamayanlar.append(
                    dosya.name
                )


        except Exception:

            okunamayanlar.append(
                dosya.name
            )


    # =====================================================
    # BELGELER OKUNDUYSA
    # =====================================================

    if belgeler:

        tum_df = pd.DataFrame(belgeler)


        # =================================================
        # ANA FİRMAYI BELİRLE
        # En fazla belgeye sahip VKN ana firma kabul edilir
        # =================================================

        vkn_sayilari = (
            tum_df["VKN"]
            .value_counts()
        )

        ana_vkn = vkn_sayilari.index[0]


        ana_df = tum_df[
            tum_df["VKN"] == ana_vkn
        ].copy()


        yabanci_df = tum_df[
            tum_df["VKN"] != ana_vkn
        ].copy()


        ana_firma = (
            ana_df.iloc[0]["Firma"]
        )


        # =================================================
        # FİRMA BİLGİLERİ
        # =================================================

        st.subheader("🏢 Firma Bilgileri")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Firma",
                ana_firma
            )

        with col2:
            st.metric(
                "VKN",
                ana_vkn
            )

        with col3:
            st.metric(
                "Geçerli Belge",
                len(ana_df)
            )


        # =================================================
        # FARKLI FİRMA KONTROLÜ
        # =================================================

        if not yabanci_df.empty:

            for _, belge in yabanci_df.iterrows():

                st.warning(
                    f"⚠️ Farklı firmaya ait belge tespit edildi: "
                    f"{belge['Firma']} — "
                    f"VKN: {belge['VKN']} — "
                    f"{belge['Dosya']}. "
                    f"Bu belge hesaplamaya dahil edilmedi."
                )


        # =================================================
        # OKUNAMAYAN BELGE KONTROLÜ
        # =================================================

        for dosya_adi in okunamayanlar:

            st.warning(
                f"⚠️ {dosya_adi} okunamadı. "
                f"Bu belge hesaplamaya dahil edilmedi."
            )


        # =================================================
        # ANA FİRMA BELGELERİNİ SIRALA
        # =================================================

        ana_df = ana_df.sort_values(
            ["Yıl", "Ay"]
        )


        st.success(
            f"✅ {len(ana_df)} belge ana firmaya ait "
            f"olarak başarıyla işlendi."
        )


        # =================================================
        # AYLIK ÇALIŞAN SAYILARI
        # =================================================

        st.subheader(
            "📊 Aylık Çalışan Sayıları"
        )


        tablo_df = ana_df[
            [
                "Yıl",
                "Ay",
                "Çalışan Sayısı"
            ]
        ].copy()


        tablo_df["Ay"] = (
            tablo_df["Ay"]
            .map(ay_isimleri)
        )


        st.dataframe(
            tablo_df,
            use_container_width=True,
            hide_index=True
        )


        # =================================================
        # DÖNEM KONTROLÜ VE ORTALAMA
        # =================================================

        st.subheader(
            "📈 Dönem Kontrolü ve Ortalama"
        )


        for yil in sorted(
            ana_df["Yıl"].unique()
        ):

            yil_df = ana_df[
                ana_df["Yıl"] == yil
            ].copy()


            # Demo senaryosu:
            # 2025 = Ocak-Aralık
            # 2026 = Ocak-Ağustos

            if yil == 2026:

                beklenen_aylar = list(
                    range(1, 9)
                )

            else:

                beklenen_aylar = list(
                    range(1, 13)
                )


            bulunan_aylar = (
                yil_df["Ay"]
                .tolist()
            )


            # =================================================
            # TEKRAR EDEN AY KONTROLÜ
            # =================================================

            tekrar_eden_aylar = (
                yil_df[
                    yil_df.duplicated(
                        subset=["Ay"],
                        keep=False
                    )
                ]["Ay"]
                .unique()
                .tolist()
            )


            if tekrar_eden_aylar:

                tekrarlar = ", ".join(
                    ay_isimleri[ay]
                    for ay in tekrar_eden_aylar
                )

                st.warning(
                    f"⚠️ {yil} döneminde tekrar eden "
                    f"belge tespit edildi: {tekrarlar}. "
                    f"Ortalama hesaplanmadı."
                )

                continue


            # =================================================
            # EKSİK AY KONTROLÜ
            # =================================================

            eksik_aylar = [

                ay

                for ay in beklenen_aylar

                if ay not in bulunan_aylar
            ]


            if eksik_aylar:

                eksikler = ", ".join(
                    ay_isimleri[ay]
                    for ay in eksik_aylar
                )

                st.warning(
                    f"⚠️ {yil} dönemi eksik. "
                    f"Eksik dönem: {eksikler} {yil}. "
                    f"Ortalama hesaplanmadı."
                )

                continue


            # =================================================
            # ORTALAMA
            # =================================================

            ortalama = (
                yil_df[
                    "Çalışan Sayısı"
                ]
                .mean()
            )


            st.success(
                f"✅ {yil}: "
                f"{len(yil_df)}/{len(beklenen_aylar)} "
                f"dönem tamamlandı — "
                f"Çalışan Ortalaması: {ortalama:.2f}"
            )


            st.metric(
                f"{yil} Çalışan Ortalaması",
                f"{ortalama:.2f}"
            )


    # =====================================================
    # HİÇBİR BELGE OKUNAMADIYSA
    # =====================================================

    else:

        st.error(
            "Belgelerden firma, VKN, dönem veya "
            "çalışan sayısı bilgileri okunamadı."
        )