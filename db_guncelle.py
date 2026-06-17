import sqlite3

baglanti = sqlite3.connect('kayamakina.db')
islemci = baglanti.cursor()

# 1. HAMLE: Eski, bozuk veya eksik tabloyu kökünden sil (DROP)
islemci.execute('DROP TABLE IF EXISTS yedek_parcalar')

# 2. HAMLE: Yepyeni, jilet gibi tabloyu tüm sütunlarıyla baştan kur
islemci.execute('''
CREATE TABLE yedek_parcalar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    makine_id INTEGER,
    parca_adi TEXT,
    fiyat REAL,
    para_birimi TEXT,
    stok_durumu TEXT,
    FOREIGN KEY(makine_id) REFERENCES makineler(id)
)
''')

baglanti.commit()
baglanti.close()

print("Eski ve hatalı tablo imha edildi. Yeni yedek parça deposu kusursuz şekilde kuruldu patron!")
