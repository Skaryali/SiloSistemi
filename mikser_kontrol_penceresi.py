from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QProgressBar, QComboBox, QDialog, QListWidget
from PyQt5.QtCore import QTimer, QTime, Qt
from PyQt5.QtGui import QPixmap
from db import sarf_yap, veritabani_baglan
from mola import MolaKontrol
from malzeme_giris_penceresi import MalzemeGirisPenceresi
from sarf_listesi_penceresi import SarfListesiPenceresi
from malzeme_listesi_penceresi import MalzemeListesiPenceresi
from db import stok_miktarlari_getir
from PyQt5.QtWidgets import QFrame
from kritik_stok import kritik_stok_kontrol_ve_mail
from PyQt5.QtWidgets import  QWidget
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import QTimer
from formuller import formul_oranlar
from PyQt5.QtWidgets import QMessageBox
from ayar_yukleyici import AyarYukleyici  
from AyarlarPenceresi import AyarlarPenceresi
from PyQt5.QtWidgets import QPushButton
from id_goster_penceresi import IdGosterPenceresi
from mail_ikonlari import UrunWidget
from db import stok_miktarlari_getir
from db import kritik_stok_kontrol, mail_gonder_grup, stok_kontrol_sifirla


def formatla_kg(miktar):
    return f"{miktar:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


class MikserKontrolPenceresi(QWidget):
    def __init__(self, ana_pencere=None):
        super().__init__()
        self.setWindowTitle("Mikser Kontrol Paneli")
        self.setGeometry(70, 80, 1800, 900)
        self.ana_pencere = ana_pencere

        self.ayar_yukleyici = AyarYukleyici()
        self.urun_widgetler = []

        # 🔽 Stok verilerini çekiyoruz
        urunler = stok_miktarlari_getir().items()

        # 🎞️ Animasyon ayarları
        silo_animasyon_ayarlar = {
            "Silo 1": {"dosya": "mail_gif.gif", "width": 50, "height": 50},
            "Silo 2": {"dosya": "mail_gif.gif", "width": 40, "height": 40},
            "Silo 3": {"dosya": "mail_gif.gif", "width": 40, "height": 40},
            "Silo 4": {"dosya": "mail_gif.gif", "width": 40, "height": 40},
        }

        y_pos = 10
        for ad, stok in urunler:
            animasyon_ayari = silo_animasyon_ayarlar.get(ad, {})
            uw = UrunWidget(
                ad,
                stok,
                parent=self,
                animasyon_dosyasi=animasyon_ayari.get("dosya"),
                animasyon_width=animasyon_ayari.get("width", 40),
                animasyon_height=animasyon_ayari.get("height", 40)
            )
            uw.setGeometry(10, y_pos, 400, 80)
            uw.show()
            self.urun_widgetler.append(uw)
            y_pos += 90

    def resizeEvent(self, event):
        y_pos = 50
        for uw in self.urun_widgetler:
            uw.setGeometry(30, y_pos, int(self.width() * 0.45), 80)
            y_pos += 90
        super().resizeEvent(event)

        
        
        # Elle yerleştirmek istediğin ürünler
        urun_bilgileri = [
            ("Silo 1", 120),
            ("Silo 2", 80),
            ("EVA", 50),
            ("DINP", 30),
            ("Rulo Naylon", 75),
            ("Yurt Dışı Naylon", 55)
        ]

        # Elle konumlandırma ayarları
        baslangic_x = 50
        baslangic_y = 80
        dikey_aralik = 70

        for i, (urun_adi, stok) in enumerate(urun_bilgileri):
            widget = UrunWidget(urun_adi, stok, self)
            widget.setGeometry(baslangic_x, baslangic_y + i * dikey_aralik, 300, 50)
            widget.show()
            self.urun_widgetler.append(widget)
    

        self.timer_mola_bilgi = QTimer()
        self.timer_mola_bilgi.timeout.connect(self._mola_sayac_guncelle)

        self.timer_kritik_stok = QTimer()
        self.timer_kritik_stok.timeout.connect(self.kritik_stok_ve_widget_guncelle)
        self.timer_kritik_stok.start(15 * 60 * 1000)  # 15 dakikada bir çalışır
        

        self.kritik_stok_ve_widget_guncelle()
    

        # Değişiklik sonrası ayarları yeniden oku
        self.sarfiyat_hizi = self.ayar_yukleyici.get("mikser_sarfiyat_hizi_saniye", 5)
        self.kritik_stok = self.ayar_yukleyici.get("kritik_stok", 100)


       
        # Mola kontrol nesnesi ÖNCELİKLİ
        self.molaKontrol = MolaKontrol()
        self.molaKontrol.molaBasladi.connect(self.mola_basladi_handler)
        self.molaKontrol.molaBitti.connect(self.mola_bitti_handler)
        self.molaSirasindaDurdurulanMikser1 = False
        self.molaSirasindaDurdurulanMikser2 = False



        

        self._arka_plani_ayarla()

        self.m1_toplam_kg = 1250
        self.m2_toplam_kg = 1250
        self.m1_aktif = False
        self.m2_aktif = False
        self.m1_adet = 0
        self.m2_adet = 0
        self.blink_state_m1 = False
        self.blink_state_m2 = False

        self.malzeme_id_map = {
            "Silo 1": 1,
            "Silo 2": 2,
            "Silo 3": 3,
            "Silo 4": 4,
            "EVA": 5,
            "DINP": 6,
            "Rulo Naylon": 7,
            "Turmet Dolomit": 8,
            "Yurt Dışı Naylon": 9,
        }

        self.formul_oranlar = formul_oranlar

        
        self.m1_durum = "durdu"  # veya "aktif", "mola"
        self.m2_durum = "durdu"
        self._ui_bilesenlerini_baslat()
        self._timerlari_ayarla()
        self.stil_yukle()
        self.stok_guncelle()

        

        self.sarfiyat_hizi = self.ayar_yukleyici.get("mikser_sarfiyat_hizi_saniye", 900)
        self.kritik_stok = self.ayar_yukleyici.get("kritik_stok", 1000)

        # mola saatleri gibi başka ayarları da alabilirsin
        self.mola_saatleri = self.ayar_yukleyici.get("mola_saatleri", [])
        print("Yüklenen mola saatleri:", self.mola_saatleri)
    
    def ayarlar_ac(self):
        pencere = AyarlarPenceresi(self)
        pencere.exec_()
  

 
    def kritik_stok_ve_widget_guncelle(self):
        kritik_urunler = kritik_stok_kontrol_ve_mail()  
        print("🔍 Kritik ürünler:", [ad for ad, _, _ in kritik_urunler])

        for widget in self.urun_widgetler:
            print("🔎 Kontrol edilen widget:", widget.urun_adi)

            if any(ad.strip().lower() == widget.urun_adi.strip().lower() for ad, _, _ in kritik_urunler):
                print(f"📩 Kritik stok! Mail animasyonu gösteriliyor: {widget.urun_adi}")
                widget.mail_durumuna_gore_guncelle(True)
            else:
                yeni_stok = self.stok_bilgisi_cek(widget.urun_adi)
                kritik_stok = self._kritik_degerini_getir(widget.urun_adi)
                widget.mail_durumuna_gore_guncelle(False)
                widget.stok_guncelle(yeni_stok)

                print(f"✅ Kritik değil — stok güncelleniyor: {widget.urun_adi} → {yeni_stok} kg")
                print(f"🧪 Eşik kontrolü: {widget.urun_adi} stok {yeni_stok} > kritik {kritik_stok}?")

                if yeni_stok > kritik_stok:
                    print(f"🔄 İkon sıfırlanıyor: {widget.urun_adi}")
                    widget.ikon_sifirla()

    def _arka_plani_ayarla(self):
        """Pencerenin arka plan resmini ayarlar."""
        self.bg_label = QLabel(self)
        pixmap = QPixmap("C:/Users/gokhan.yasar/Desktop/SILO SISTEMI KODLAR/resimler/silo takip sistemi arka plan  yenisi daha düzenli.jpg")
        self.bg_label.setPixmap(pixmap)
        self.bg_label.setScaledContents(True)
        self.bg_label.resize(self.size())

    def _ui_bilesenlerini_baslat(self):
       
        """Tüm UI bileşenlerini oluşturur ve konumlandırır."""
        w = self.width()
        h = self.height()

        # Mikser 1
        self.m1_saat = QLabel("🕒 Başlangıç Saati:", self)
        self.m1_saat.resize(200, 100)
        self.m1_saat.setObjectName("M1SaatLabel")
        self.m1_sayac = QLabel("📦 Üretilen Palet:", self)
        self.m1_sayac.resize(160, 100)
        self.m1_sayac.setObjectName("M1SayacLabel")
        self.btn_m1_baslat = QPushButton("✅ M1 Başlat", self)
        self.btn_m1_baslat.resize(150, 35)
        self.btn_m1_baslat.clicked.connect(self.Btn_M1_Baslat_Click)


        # Mikser 2
        self.m2_saat = QLabel("🕒 Başlangıç Saati:", self)
        self.m2_saat.resize(200, 100)
        self.m2_saat.setObjectName("M2SaatLabel")
        self.m2_sayac = QLabel("📦 Üretilen Palet:", self)
        self.m2_sayac.resize(160, 100)
        self.m2_sayac.setObjectName("M2SayacLabel")
        self.btn_m2_baslat = QPushButton("✅ M2 Başlat", self)
        self.btn_m2_baslat.resize(150, 35)
        self.btn_m2_baslat.clicked.connect(self.Btn_M2_Baslat_Click)

        # QLabel oluştur
        # self.lbl_gokhan = QLabel(self)
        # self.lbl_gokhan.setGeometry(int(w * 0.08), int(h * 0.51), 50, 50)
        # self.lbl_gokhan.setStyleSheet("background-color: black;")
        # self.lbl_gokhan.show()
        # self.lbl_gokhan.raise_()
      
        # QMovie ile GIF'i bağla
        # self.movie_gokhan = QMovie("mail_gif.gif")  
        # self.lbl_gokhan.setMovie(self.movie_gokhan)
        # self.movie_gokhan.start()

        # Eva Frame
        self.frame_eva = QFrame(self)
        self.frame_eva.setObjectName("EvaFrame")
        self.frame_eva.setGeometry(int(w * 0.02), int(h * 0.50), 190, 65)
 
        self.lbl_Eva = QLabel("🧪 Eva", self.frame_eva)
        self.lbl_Eva.move(8, 5)
        self.lbl_Eva.setObjectName("EvaStok")

        self.lbl_Eva_stok = QLabel("0 kg", self.frame_eva)
        self.lbl_Eva_stok.move(10, 30)
        self.lbl_Eva_stok.setObjectName("EvaStokDeger")

        # Turmet Dolomit Frame
        self.frame_dolomit = QFrame(self)
        self.frame_dolomit.setObjectName("DolomitFrame")
        self.frame_dolomit.setGeometry(int(w * 0.02), int(h * 0.60), 190, 60)

        self.lbl_TurmetDolomit = QLabel("🔘 Turmet Dolomit", self.frame_dolomit)
        self.lbl_TurmetDolomit.move(8, 5)
        self.lbl_TurmetDolomit.setObjectName("DolomitStok")

        self.lbl_TurmetDolomit_stok = QLabel("0 kg", self.frame_dolomit)
        self.lbl_TurmetDolomit_stok.move(10, 30)
        self.lbl_TurmetDolomit_stok.setObjectName("DolomitStokDeger")

        # DINP Frame
        self.frame_dinp = QFrame(self)
        self.frame_dinp.setObjectName("DINPFrame")
        self.frame_dinp.setGeometry(int(w * 0.02), int(h * 0.70), 190, 60)

        self.lbl_DINP = QLabel("🧴 DINP", self.frame_dinp)
        self.lbl_DINP.move(8, 5)
        self.lbl_DINP.setObjectName("DINPStok")

        self.lbl_DINP_stok = QLabel("0 kg", self.frame_dinp)
        self.lbl_DINP_stok.move(10, 30)
        self.lbl_DINP_stok.setObjectName("DINPStokDeger")

        # Yurt Dışı Naylon Frame
        self.frame_yurtdisi = QFrame(self)
        self.frame_yurtdisi.setObjectName("YurtDisiFrame")
        self.frame_yurtdisi.setGeometry(int(w * 0.02), int(h * 0.80), 190, 60)

        self.lbl_YurtDısıNaylon = QLabel("🛍️ Yurt Dışı Naylon", self.frame_yurtdisi)
        self.lbl_YurtDısıNaylon.move(8, 5)
        self.lbl_YurtDısıNaylon.setObjectName("YurtDisiStok")
        

        self.lbl_YurtDısıNaylon_stok = QLabel("0 kg", self.frame_yurtdisi)
        self.lbl_YurtDısıNaylon_stok.move(10, 30)
        self.lbl_YurtDısıNaylon_stok.setObjectName("YurtDisiStokDeger")


        # Rulo Naylon Frame
        self.frame_rulo = QFrame(self)
        self.frame_rulo.setObjectName("RuloFrame")
        self.frame_rulo.setGeometry(int(w * 0.02), int(h * 0.90), 190, 60)

        self.lbl_RuloNaylon = QLabel("🧻 Rulo Naylon", self.frame_rulo)
        self.lbl_RuloNaylon.move(8, 5)
        self.lbl_RuloNaylon.setObjectName("RuloStok")

        self.lbl_RuloNaylon_stok = QLabel("0 kg", self.frame_rulo)
        self.lbl_RuloNaylon_stok.move(10, 30)
        self.lbl_RuloNaylon_stok.setObjectName("RuloStokDeger")


            # Mola Bilgi
        self.lbl_mola_bilgi = QLabel("", self)
        self.lbl_mola_bilgi.setStyleSheet("color: yellow; font-size: 18px; background-color: rgba(0,0,0,150);")
        self.lbl_mola_bilgi.resize(280, 30)
        self.lbl_mola_bilgi.move(int(w * 0.42), int(h * 0.05)) 
        self.lbl_mola_bilgi.hide()
        self.lbl_mola_bilgi.raise_()

        # Formül seçimleri
        self.lbl_m1_formul = QLabel("Formül :", self)
        self.lbl_m1_formul.setObjectName("formulm1")
        self.cmb_m1_formul = QComboBox(self)
        self.cmb_m1_formul.addItems(self.formul_oranlar.keys())

        self.lbl_m2_formul = QLabel("Formül :", self)
        self.lbl_m2_formul.setObjectName("formulm2")
        self.cmb_m2_formul = QComboBox(self)
        self.cmb_m2_formul.addItems(self.formul_oranlar.keys())

        # Geri Al butonları
        self.btn_m1_geri_al = QPushButton("⬅ M1 Geri Al", self)
        self.btn_m1_geri_al.clicked.connect(self.geri_al_m1)
        self.btn_m2_geri_al = QPushButton("⬅ M2 Geri Al", self)
        self.btn_m2_geri_al.clicked.connect(self.geri_al_m2)

        # Durum butonları
        self.btn_m1_durum = QPushButton("M1", self)
        self.btn_m1_durum.setEnabled(False)
        self.btn_m2_durum = QPushButton("M2", self)
        self.btn_m2_durum.setEnabled(False)

        # Silo barları ve etiketleri
        self.silo_bars = []
        self.silo_labels = []
        for i in range(4):
            bar = QProgressBar(self)
            bar.setMaximum(100)
            bar.setOrientation(Qt.Vertical)
            bar.setTextVisible(True)
            self.silo_bars.append(bar)

            label = QLabel("%0", self)
            label.setAlignment(Qt.AlignCenter)
            self.silo_labels.append(label)

        self.btn_m1_baslat.setObjectName("m1Baslat")
        self.btn_m2_baslat.setObjectName("m2Baslat")
        self.btn_m1_durum.setObjectName("mikserDurum")
        self.btn_m2_durum.setObjectName("mikserDurum")

        # Konumlandırma
        self.m1_saat.move(int(w * 0.01), int(h * 0.01))
        self.m1_sayac.move(int(w * 0.01), int(h * 0.05))
        self.btn_m1_baslat.move(int(w * 0.37), int(h * 0.26))

        self.lbl_m1_formul.move(int(w * 0.25), int(h * 0.02))
        self.cmb_m1_formul.move(int(w * 0.25), int(h * 0.05))

        self.m2_saat.move(int(w * 0.89), int(h * 0.01))
        self.m2_sayac.move(int(w * 0.89), int(h * 0.04))
        self.btn_m2_baslat.move(int(w * 0.55), int(h * 0.26))

        self.lbl_m2_formul.move(int(w * 0.71), int(h * 0.02))
        self.cmb_m2_formul.move(int(w * 0.71), int(h * 0.05))

        self.btn_m1_durum.setObjectName("m1Durum")
        self.btn_m2_durum.setObjectName("m2Durum")
        self.btn_m1_durum.move(int(w * 0.19), int(h * 0.05))
        self.btn_m2_durum.move(int(w * 0.77), int(h * 0.05))
        self.btn_m1_durum.setFixedSize(70, 29)
        self.btn_m2_durum.setFixedSize(70, 29)

        self.btn_m1_geri_al.move(int(w * 0.37), int(h * 0.32))
        self.btn_m2_geri_al.move(int(w * 0.55), int(h * 0.32))

        silo_positions = [
            (int(w * 0.19), int(h * 0.44)),
            (int(w * 0.39), int(h * 0.44)),
            (int(w * 0.58), int(h * 0.44)),
            (int(w * 0.77), int(h * 0.44))
        ]
        self.silo_bar_width = 70
        self.silo_bar_height = int(h * 0.39)

        for i, (bar, label) in enumerate(zip(self.silo_bars, self.silo_labels)):
            x, y = silo_positions[i]
            bar.move(x, y)
            bar.resize(self.silo_bar_width, self.silo_bar_height)
            # Label'ı barın üstünde konumlandırıyoruz, değeri gösteriyor
            label.move(x, y - 50) # Barın hemen üstüne
            label.resize(self.silo_bar_width, 20)
            label.setText(f"%{bar.value()}")


       
    
        # Ana pencereye dönüş butonu
        self.btn_don = QPushButton("🔙 Ürün Kontrol", self)
        self.btn_don.clicked.connect(self.ana_pencereye_don)
        self.btn_don.move(int(w * 0.88), int(h * 0.65))
        
        # Çıkış Butonu
        self.btn_cikis = QPushButton("❌ Çıkış", self)
        self.btn_cikis.clicked.connect(self.close)
        self.btn_cikis.move(int(w * 0.88), int(h * 0.85))
        
         # Giriş Butonu
        self.btn_giris = QPushButton("📥 Ürün Giriş", self)
        self.btn_giris.clicked.connect(self.giris_listesi_ac)
        self.btn_giris.move(int(w * 0.88), int(h * 0.70))

        # Sarf Edilen Ürün Butonu
        self.btn_sarf = QPushButton("🧱 Sarf Edilen Ürün", self)
        self.btn_sarf.clicked.connect(self.SarfKontrolPenceresi)
        self.btn_sarf.move(int(w * 0.88), int(h * 0.80))

        # Malzeme Stok Butonu
        self.btn_sarf = QPushButton("📦 Güncel Stok", self)
        self.btn_sarf.clicked.connect(self.StokKontrol)
        self.btn_sarf.move(int(w * 0.88), int(h * 0.75))

        
        self.btn_ayarlar = QPushButton("⚙️ Ayarlar", self)  
        self.btn_ayarlar.clicked.connect(self.ayarlar_ac)
        self.btn_ayarlar.move(int(w * 0.88), int(h * 0.90))

        self.btn_id_goster = QPushButton("📋 ID'leri Göster", self)
        self.btn_id_goster.move(int(w * 0.88), int(h * 0.95))
        self.btn_id_goster.clicked.connect(self.idleri_goster)

    def _kritik_degerini_getir(self, urun_adi):
            kritik_degerler = {
                "Silo 1": 100,
                "Silo 2": 150,
                "EVA": 80,
                "DINP": 70,
                "Rulo Naylon": 90,
                "Turmet Dolomit": 50,
                "Yurt Dışı Naylon": 120
            }
            return kritik_degerler.get(urun_adi, 0)  # varsayılan kritik değer: 0


    def idleri_goster(self):
        self.pencere = IdGosterPenceresi(self.malzeme_id_map)
        self.pencere.exec_()

        # Malzeme Stok Fonksiyonu 

    def StokKontrol(self):
        self.StokKontrol = MalzemeListesiPenceresi()
        self.StokKontrol.show()        

    def _timerlari_ayarla(self):
        """Uygulama için gerekli QTimer'ları ayarlar."""
        self.timer_m1 = QTimer()
        self.timer_m1.timeout.connect(self.sarf_m1)

        self.timer_m2 = QTimer()
        self.timer_m2.timeout.connect(self.sarf_m2)

        self.timer_stok_guncelle = QTimer()
        self.timer_stok_guncelle.timeout.connect(self.stok_guncelle)
        self.timer_stok_guncelle.start(5000) # Her 5 saniyede bir stokları güncelle

        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink_buttons)
        self.blink_timer.start(1000) # Her saniyede bir yanıp sönme durumunu değiştir

    def blink_buttons(self):
        self.blink_on = not getattr(self, "blink_on", False)  # True/False toggle

            # M1 Durumuna göre yanıp sönme
        if  self.m1_durum == "aktif":
            self._blink_btn(self.btn_m1_durum, "green", is_on=self.blink_on)
        elif    self.m1_durum == "mola":
                self._blink_btn(self.btn_m1_durum, "gray", is_on=self.blink_on)
        elif    self.m1_durum == "durdu":
                self._blink_btn(self.btn_m1_durum, "red", is_on=self.blink_on)

            # M2 Durumuna göre yanıp sönme
        if self.m2_durum == "aktif":
           self._blink_btn(self.btn_m2_durum, "green", is_on=self.blink_on)
        elif self.m2_durum == "mola":
             self._blink_btn(self.btn_m2_durum, "gray", is_on=self.blink_on)
        elif self.m2_durum == "durdu":
             self._blink_btn(self.btn_m2_durum, "red", is_on=self.blink_on)

    def _blink_btn(self, button, color, is_on):
        if is_on:
            button.setStyleSheet(f"background-color: {color}; color: white; border-radius: 10px;")
            button.setText("M1" if button == self.btn_m1_durum else "M2")
        else:
            button.setStyleSheet("background-color: none; color: transparent; border-radius: 10px;")
            button.setText("")

    # Malzeme Giriş Penceresi Fonksiyonu 

    def giris_listesi_ac(self):
        self.giris_penceresi = MalzemeGirisPenceresi()
        self.giris_penceresi.show()   

    # Malzeme Sarf Penceresi Fonksiyonu 

    def SarfKontrolPenceresi(self):
        self.SarfKontrolPenceresi = SarfListesiPenceresi()
        self.SarfKontrolPenceresi.show()   

    def stil_yukle(self):
        """Harici bir stil dosyasından (stil.qss) stil yükler."""
        try:
            with open("stil.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("❌ stil.qss dosyası bulunamadı.")

    def toggle_m1(self):
        """Mikser 1'i başlatır veya durdurur."""
        self.m1_aktif = not self.m1_aktif
        self.btn_m1_baslat.setText("❌ M1 Durdur" if self.m1_aktif else "✅M1 Başlat")
        self.btn_m1_baslat.setProperty("aktif", str(self.m1_aktif).lower())
        self.btn_m1_baslat.style().unpolish(self.btn_m1_baslat)
        self.btn_m1_baslat.style().polish(self.btn_m1_baslat)




        if self.m1_aktif:
            self.m1_durum = "aktif"
            self.m1_saat.setText("🕒 Başlangıç Saati:" + QTime.currentTime().toString(" hh:mm"))
            self.timer_m1.start(900000)  # 15 dakikada bir sarfiyat yap
            
        else:
            self.m1_durum = "durdu"
            self.timer_m1.stop()
        self.guncelle_durum_renk() # Durum butonunun rengini hemen güncelle

    def toggle_m2(self):
        """Mikser 2'yi başlatır veya durdurur."""
        self.m2_aktif = not self.m2_aktif
        self.btn_m2_baslat.setText("❌M2 Durdur" if self.m2_aktif else "✅M2 Başlat ")
        self.btn_m2_baslat.setProperty("aktif", str(self.m2_aktif).lower())
        self.btn_m2_baslat.style().unpolish(self.btn_m2_baslat)
        self.btn_m2_baslat.style().polish(self.btn_m2_baslat)

        if self.m2_aktif:
            self.m2_durum = "aktif"
            self.m2_saat.setText("🕒 Başlangıç Saati:" + QTime.currentTime().toString(" hh:mm"))
            self.timer_m2.start(5000)  # 5 saniyede bir sarfiyat yap
        else:
            self.m2_durum = "durdu"
            self.timer_m2.stop()
        self.guncelle_durum_renk() # Durum butonunun rengini hemen güncelle

    def Btn_M1_Baslat_Click(self):
        if self.molaKontrol.isMola:
            QMessageBox.information(self, "Mola", "Şu anda mola zamanı. Mikser başlatılamaz.")
            return
        self.toggle_m1()

    def Btn_M2_Baslat_Click(self):
        if self.molaKontrol.isMola:
            QMessageBox.information(self, "Mola", "Şu anda mola zamanı. Mikser başlatılamaz.")
            return
        self.toggle_m2()    

    def sarf_m1(self):
        """Mikser 1 için sarfiyat işlemini gerçekleştirir."""
        self.m1_adet += 1
        self.m1_sayac.setText(f"📦 Üretilen Palet: {self.m1_adet}")
        secilen_formul = self.cmb_m1_formul.currentText()
        self.mikser_sarf_yap("M1", secilen_formul, self.m1_toplam_kg)
        self.stok_guncelle()  # Sarfiyat sonrası stokları güncelle
        kritik_urunler = kritik_stok_kontrol()
        mail_gonder_grup(kritik_urunler)
        stok_kontrol_sifirla(kritik_urunler)

    def sarf_m2(self):
        """Mikser 2 için sarfiyat işlemini gerçekleştirir."""
        self.m2_adet += 1
        self.m2_sayac.setText(f"📦 Üretilen Palet: {self.m2_adet}")
        secilen_formul = self.cmb_m2_formul.currentText()
        self.mikser_sarf_yap("M2", secilen_formul, self.m2_toplam_kg)
        self.stok_guncelle()  # Sarfiyat sonrası stokları güncelle
        kritik_urunler = kritik_stok_kontrol()
        mail_gonder_grup(kritik_urunler)
        stok_kontrol_sifirla(kritik_urunler)

    def mikser_sarf_yap(self, mikser_adi, formulkodu, toplamKg, geri_al=False):
        """Belirtilen formül ve mikser için sarfiyat veya geri alma işlemi yapar."""
        oranlar = self.formul_oranlar.get(formulkodu, {})
        for urun, oran in oranlar.items():
            miktar = toplamKg * oran
            if miktar <= 0:
                continue
            malzeme_id = self.malzeme_id_map.get(urun)
            if malzeme_id:
                # Geri alma durumunda miktarı negatif yap
                miktar = -miktar if geri_al else miktar
                sarf_yap(malzeme_id, miktar, mikser_adi)

    def stok_guncelle(self):
        oranlar = self._stok_doluluk_oranlari_db()
        if oranlar:
            for i, oran in enumerate(oranlar):
                if i < len(self.silo_bars):
                    self.silo_bars[i].setValue(oran)
                    bar = self.silo_bars[i]
                    label = self.silo_labels[i]
                    y_offset = int(self.silo_bar_height * (1 - oran / 100))
                    label.move(bar.x(), bar.y() + y_offset - 50)
                    label.setText(f"%{oran}")
                    label.setVisible(True)

        stok_miktarlari = stok_miktarlari_getir()
        self.lbl_Eva_stok.setText(f"{formatla_kg(stok_miktarlari.get('EVA', 0))} kg")
        self.lbl_TurmetDolomit_stok.setText(f"{formatla_kg(stok_miktarlari.get('Turmet Dolomit', 0))} kg")
        self.lbl_DINP_stok.setText(f"{formatla_kg(stok_miktarlari.get('DINP', 0))} kg")
        self.lbl_YurtDısıNaylon_stok.setText(f"{formatla_kg(stok_miktarlari.get('Yurt Dışı Naylon', 0))} kg")
        self.lbl_RuloNaylon_stok.setText(f"{formatla_kg(stok_miktarlari.get('Rulo Naylon', 0))} kg")
    
        
    def _stok_doluluk_oranlari_db(self):
        """Veritabanından silo doluluk oranlarını çeker."""
        conn = veritabani_baglan()
        if not conn:
            print("❌ Veritabanı bağlantısı kurulamadı.")
            return []

        cursor = conn.cursor()
        silo_isimleri = ["Silo 1", "Silo 2", "Silo 3", "Silo 4"]
        oranlar = []
        kapasite = 60000  # Örnek kapasite (kg)

        for isim in silo_isimleri:
            try:
                # Malzeme ID'sini doğrudan map'ten al
                mid = self.malzeme_id_map.get(isim)
                if mid is None:
                    print(f"Malzeme ID haritasında '{isim}' bulunamadı. Stok 0 olarak ayarlandı.")
                    oranlar.append(0)
                    continue

                cursor.execute("SELECT baslangic_stok FROM malzemeler WHERE id = ?", (mid,))
                sonuc = cursor.fetchone()
                if not sonuc:
                    print(f"Veritabanında ID {mid} ile eşleşen '{isim}' malzemesi bulunamadı.")
                    oranlar.append(0)
                    continue
                bas_stok = sonuc[0]

                cursor.execute("SELECT SUM(miktar) FROM girisler WHERE malzeme_id = ?", (mid,))
                giris = cursor.fetchone()[0] or 0

                cursor.execute("SELECT SUM(miktar) FROM sarf WHERE malzeme_id = ?", (mid,))
                sarf = cursor.fetchone()[0] or 0

                mevcut = bas_stok + giris - sarf
                oran = int((mevcut / kapasite) * 100)
                oran = max(0, min(oran, 100)) # Oranın 0-100 arasında kalmasını sağla
                oranlar.append(oran)
            except Exception as e:
                print(f"Veritabanından '{isim}' (ID: {mid if 'mid' in locals() else 'Bilinmiyor'}) stoğu çekilirken hata oluştu: {e}")
                oranlar.append(0) # Hata durumunda 0 ekle
        conn.close()
        return tuple(oranlar)

    def geri_al_m1(self):
        """Mikser 1 için son sarfiyatı geri alır."""
        if self.m1_adet > 0:
            self.m1_adet -= 1
            self.m1_sayac.setText(f"📦 Üretilen Palet: {self.m1_adet}")
            secilen_formul = self.cmb_m1_formul.currentText()
            self.mikser_sarf_yap("M1", secilen_formul, self.m1_toplam_kg, geri_al=True)
            self.stok_guncelle() # Geri alma sonrası stokları güncelle

    def geri_al_m2(self):
        """Mikser 2 için son sarfiyatı geri alır."""
        if self.m2_adet > 0:
            self.m2_adet -= 1
            self.m2_sayac.setText(f"📦 Üretilen Palet: {self.m2_adet}")
            secilen_formul = self.cmb_m2_formul.currentText()
            self.mikser_sarf_yap("M2", secilen_formul, self.m2_toplam_kg, geri_al=True)
            self.stok_guncelle() # Geri alma sonrası stokları güncelle

    def ana_pencereye_don(self):
        """Ana pencereye geri döner ve bu pencereyi gizler."""
        if self.ana_pencere:
            self.ana_pencere.show()
        self.hide()

    def mola_basladi_handler(self, mola_tipi):
        """Mola başladığında mikserleri durdurur ve bilgi gösterir."""

        if self.m1_aktif:
            self.toggle_m1()
            self.molaSirasindaDurdurulanMikser1 = True
        if self.m2_aktif:
            self.toggle_m2()
            self.molaSirasindaDurdurulanMikser2 = True
        
        if mola_tipi == "Cuma Namazı Saati":
            sure_saniye = (14 - QTime.currentTime().hour()) * 3600 + (0 - QTime.currentTime().minute()) * 60
        elif mola_tipi == "Yemek Molası":
            sure_saniye = (13 - QTime.currentTime().hour()) * 3600
        else:  # Çay Molası ve diğer molalar için 15 dk sabit
            sure_saniye = 15 * 60

        self.mola_bitis_saati = QTime.currentTime().addSecs(sure_saniye)
        self.lbl_mola_bilgi.show()
        self.timer_mola_bilgi.start(1000)  # Her saniye kontrol et

    def mola_bitti_handler(self):
        """Mola bittiğinde durdurulan mikserleri tekrar başlatır ve bilgi gizlenir."""
        if self.molaSirasindaDurdurulanMikser1:
            self.toggle_m1()
            self.molaSirasindaDurdurulanMikser1 = False
        if self.molaSirasindaDurdurulanMikser2:
            self.toggle_m2()
            self.molaSirasindaDurdurulanMikser2 = False

        self.lbl_mola_bilgi.hide()
        self.timer_mola_bilgi.stop()
        self.guncelle_durum_renk()

    def _mola_sayac_guncelle(self):
        kalan = QTime.currentTime().secsTo(self.mola_bitis_saati)
        if kalan <= 0:
            self.lbl_mola_bilgi.setText("🟢 Mola bitti.")
            self.timer_mola_bilgi.stop()
        else:
            dakika = kalan // 60
            saniye = kalan % 60
            self.lbl_mola_bilgi.setText(f"⏳ Mola sürüyor... {dakika:02}:{saniye:02} kaldı.")

    def guncelle_durum_renk(self):
        """Mikser durum butonlarının rengini günceller."""
        pass # Bu fonksiyon artık doğrudan yanıp sönme mantığını yönetmiyor.

    def stok_bilgisi_cek(self, malzeme_adi):
        stoklar = stok_miktarlari_getir()  # bu fonksiyon zaten dışarıda tanımlı
        return stoklar.get(malzeme_adi, 0)