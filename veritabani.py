import sqlite3

baglanti = sqlite3.connect('kayamakina.db')
islemci = baglanti.cursor()

islemci.execute("DROP TABLE IF EXISTS makineler")
islemci.execute("DROP TABLE IF EXISTS kategoriler")

islemci.execute('''CREATE TABLE kategoriler (id INTEGER PRIMARY KEY, kategori_adi TEXT)''')
islemci.execute('''CREATE TABLE makineler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    kategori_id INTEGER, 
                    makine_adi TEXT, 
                    fiyat REAL, 
                    para_birimi TEXT,
                    model_yili TEXT,
                    durum TEXT,
                    motor_gucu TEXT,
                    kapasite TEXT,
                    devir_araligi TEXT,
                    teknik_aciklama TEXT,
                    neden_almalisiniz TEXT)''')

islemci.execute("INSERT INTO kategoriler VALUES (1, 'Torna (Manuel)')")
islemci.execute("INSERT INTO kategoriler VALUES (2, 'Freze')")
islemci.execute("INSERT INTO kategoriler VALUES (3, 'Pres')")

# 10 MAKİNELİK DEV LİSTE
makineler = [
    (1, 'Bulgar Tornası - CU320 Model', 260000, 'TL', '2020', 'Sıfıra Yakın', '4.5 kW', '320 mm Çap / 1000 mm Boy', '45 - 2000 RPM', 
     'Fener mili ve dişli kutusu kusursuzdur. Gövde yataklarında derin aşınma yoktur. Hassas kalıp ve parça işleri için idealdir.', 
     'Bulgar döküm kalitesiyle ömürlük bir makinedir. Parça bulma sorunu yaşatmaz, dükkanın demirbaşı olur.'),
    
    (2, 'Phoebus PBM 4 Kalıpçı Freze', 240000, 'TL', '2010', 'Temiz / Çalışır', '3.7 kW', '1370 x 254 mm Tabla', '60 - 4500 RPM', 
     'Tayvan üretimi, ağır sanayi tipi döküm gövde. Titreşimsiz çalışma performansı. Dijital ölçü sistemi (DRO) ve aksesuarlı.', 
     'Hassas kalıp üretimi için profesyonellerin ilk tercihidir. Uygun maliyetle yüksek performans sunar.'),

    (1, '2 Metre Tires Torna Tezgahı', 14850, 'EUR', '2008', 'Güçlü Kondisyon', '7.5 kW', '2000 mm Punta Arası', '20 - 1600 RPM', 
     'Ağır iş tornasıdır. 2 metre işleme boyu ile mil ve büyük parçalar için yüksek stabilite ve hassasiyet sağlar.', 
     'Geniş işleme kapasitesiyle ağır sanayi operasyonlarında sarsılmaz sonuçlar almanızı sağlar.'),

    (1, 'ZMM Bulgaria C11MSM Torna', 620000, 'TL', '2008', 'Sorunsuz / Tam Takım', '11 kW', '600 mm Çap Kapasite', '250 - 1100 RPM', 
     'Metrik, Whitworth, Modül ve Inch diş açma kapasitesi tamdır. 3 kollu devir sistemi ve yağ basınç göstergesi mevcuttur.', 
     'Büyük çaplı profesyonel işler için piyasanın en çok aranan ve değerini koruyan efsane Bulgar modelidir.'),

    (3, '30 Ton Derinler Pres', 88000, 'TL', '2005', 'Aktif Çalışır Durumda', '5.5 kW', '30 Ton Basma Kapasitesi', 'Sabit Hız', 
     'Ağır sanayi tipi çelik konstrüksiyon gövde. Sac şekillendirme, kesme ve delme işlemleri için yüksek verimlilik sağlar.', 
     'Seri üretim hatları için dayanıklı ve güvenilir bir çözüm. Bakımları düzenli yapılmış, masrafsız bir makinedir.'),

    (1, 'TOS SN50C Torna Tezgahı', 425000, 'TL', '1989', 'Full Seri / Bakımlı', '5.5 kW', '500 Çap / 1.5 Metre Boy', '22 - 2000 RPM', 
     'Piyasanın en çok tutulan TOS modelidir. Sertleştirilmiş taşlanmış banko, 52 mm fener mili deliği ve Norton dişli kutusu aktiftir.', 
     'Hem kaba hem hassas işleme için ideal devir aralığı. Yatırım değeri yüksek, her zaman alıcısı olan bir makinedir.'),

    (2, 'Mikrokat 2 Numara Freze (Tayvan)', 92000, 'TL', '2003', 'Hassas ve Sağlam', '2.2 kW', 'Hassas Kızaklı Tabla', 'Manuel Kontrol', 
     'Tayvan üretimi kalitesi. Kalıp işleme ve kanal açma işleri için ideal titreşimsiz gövde. Tüm hareketler ve kızaklar sorunsuzdur.', 
     'Fiyat/performans oranı çok yüksektir. Kalıpçılar ve küçük ölçekli hassas atölyeler için kaçırılmayacak fırsat.'),

    (2, '5 No Kalıpçı Freze (Büyük Tip)', 225000, 'TL', '2016', 'Modern ve Yeni', '5.5 kW', 'Geniş Yüzeyli Ağır İş Tablası', 'Geniş Devir Aralığı', 
     '2016 model, düşük yıpranma oranına sahip modern makinedir. Büyük parçaların hassas işlenmesi için tasarlanmış ağır döküm gövde.', 
     'Yeni model avantajıyla daha az aşınma ve daha uzun ömür. Büyük kalıp işleme işleri için yüksek performans.'),

    (2, '3 Numara Dijitallİ Kalıpçı Freze', 165000, 'TL', '2012', 'DRO Dijital Ekranlı', '3.0 kW', 'Hassas Kızaklı Standart Tabla', 'Kademeli Hız', 
     'Üzerindeki dijital ölçü ekranı (DRO) ile hatasız ve hızlı ölçü alma imkanı. X-Y-Z eksen hareketleri sağlıklı ve akıcıdır.', 
     'Dengeli çalışma yapısı ve pratik kullanımıyla atölyelerin en çok tercih edilen 3 numara modelidir.'),

    (2, '3 Numara Kalıpçı Freze Tezgahı', 185000, 'TL', '2015', 'Temiz Kullanılmış', '3.5 kW', 'Standart Kalıpçı Tablası', 'Yüksek Devir', 
     'Genel kalıpçılık ve hassas talaşlı imalat için uygun, stabil çalışan makinedir. Güçlü motor yapısı ile yüksek verim sunar.', 
     '2015 model temiz kullanılmış makine. Prototip üretimi ve metal işleme atölyeleri için ideal, sağlam yatırım.')
]

islemci.executemany("INSERT INTO makineler (kategori_id, makine_adi, fiyat, para_birimi, model_yili, durum, motor_gucu, kapasite, devir_araligi, teknik_aciklama, neden_almalisiniz) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", makineler)

baglanti.commit()
baglanti.close()
print("Kaya Makina'nın 10'luk dev kadrosu sahada!")
