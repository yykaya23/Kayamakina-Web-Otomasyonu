import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import requests  # YENİ: Google kütüphanelerini devreden çıkarıp saf bağlantı kuruyoruz!
from werkzeug.security import generate_password_hash, check_password_hash

# DİKKAT: Fotoğraftaki çalışan AQ. anahtarını buraya ekledim!
API_KEY = "AQ.Ab8RN6IVYzCfLVDBdLvcrlsr0MsWHweleDOMCK_f2sqLHAlzkQ"

def gemini_istek_at(prompt):
    """Google kütüphaneleri hata verdiği için sunucuya doğrudan (saf) istek atan fonksiyon"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status() # Hata varsa yakalar
    json_veri = response.json()
    return json_veri['candidates'][0]['content']['parts'][0]['text'].strip()

def uzman_yorumu_uret(makine_adi, yil):
    prompt = f"""
    Sen endüstriyel ağır sanayi makineleri (torna, freze, pres) konusunda 30 yıllık tecrübeye sahip bir uzmansın. 
    Müşteriyi ikna edecek, teknik ve tok bir dille şu makine için en fazla 2 cümlelik bir 'Uzman Yorumu' yaz. 
    Makine: {makine_adi}, Üretim Yılı: {yil}.
    Sadece yorumu yaz, giriş veya selamlama yapma.
    """
    try:
        return gemini_istek_at(prompt)
    except Exception as hata:
        print(f"Uzman Yorumu Hatası: {hata}")
        return "Güçlü performansı ve dayanıklı gövdesiyle sanayi operasyonlarınız için uzun ömürlü ve ideal bir yatırımdır."

def akilli_asistan_yaniti(sorgu, makineler):
    if len(sorgu) < 5: 
        return None

    makine_katalogu = ""
    for m in makineler:
        makine_katalogu += f"ID: {m['id']} | Adı: {m['makine_adi']} | Fiyat: {m['fiyat']} {m['para_birimi']} | Kategori: {m['kategori_adi']}\n"

    prompt = f"""
    Sen 'Kaya Makina' şirketinin yetenekli ve kibar yapay zeka satış asistanısın.
    Müşteri arama motorumuza şu talebi yazdı: "{sorgu}"
    Şu an stokta olan makinelerimiz şunlar:
    {makine_katalogu}

    Görev: Müşterinin talebini (bütçe, iş tipi vb.) analiz et ve stoktaki makinelerden ona en uygun olanı öner. Nedenini 2-3 cümleyle samimi ve profesyonel bir dille açıkla. Eğer bütçesine veya işine uygun makine yoksa dürüstçe belirt.
    """
    try:
        return gemini_istek_at(prompt)
    except Exception as hata:
        print(f"Akıllı Asistan Hatası: {hata}")
        return None

app = Flask(__name__)
app.secret_key = 'harvey_specter_gizli_anahtari' 

def veritabani_baglan():
    baglanti = sqlite3.connect('kayamakina.db')
    baglanti.row_factory = sqlite3.Row
    return baglanti

@app.route('/')
def ana_sayfa():
    arama_kelimesi = request.args.get('q', '') 
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    
    sorgu_baz = '''
        SELECT m.id, m.makine_adi, m.fiyat, m.para_birimi, k.kategori_adi, u.ad_soyad as satici_adi 
        FROM makineler m 
        JOIN kategoriler k ON m.kategori_id = k.id 
        LEFT JOIN kullanicilar u ON m.kullanici_id = u.id
    '''
    
    islemci.execute(sorgu_baz + ' ORDER BY m.id DESC')
    tum_makineler = islemci.fetchall()

    ai_mesaji = None
    if arama_kelimesi:
        ai_mesaji = akilli_asistan_yaniti(arama_kelimesi, tum_makineler)
        sorgu = sorgu_baz + ' WHERE m.makine_adi LIKE ? OR k.kategori_adi LIKE ? ORDER BY m.id DESC'
        arama_formatli = f"%{arama_kelimesi}%" 
        islemci.execute(sorgu, (arama_formatli, arama_formatli))
        gosterilecek_makineler = islemci.fetchall()
        
        if len(gosterilecek_makineler) == 0 and len(arama_kelimesi) > 5:
            gosterilecek_makineler = tum_makineler
    else:
        gosterilecek_makineler = tum_makineler
        
    baglanti.close()
    return render_template('index.html', makineler=gosterilecek_makineler, arama_kelimesi=arama_kelimesi, topluluk_modu=False, ai_mesaji=ai_mesaji)

@app.route('/topluluk')
def topluluk_vitrini():
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    
    islemci.execute('''
        SELECT m.id, m.makine_adi, m.fiyat, m.para_birimi, k.kategori_adi, u.ad_soyad as satici_adi 
        FROM makineler m 
        JOIN kategoriler k ON m.kategori_id = k.id 
        LEFT JOIN kullanicilar u ON m.kullanici_id = u.id
        WHERE m.kullanici_id != 0 
        ORDER BY m.id DESC
    ''')
    makineler = islemci.fetchall()
    baglanti.close()
    return render_template('index.html', makineler=makineler, arama_kelimesi='', topluluk_modu=True)

@app.route('/tarihce')
def tarihce_sayfasi():
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    islemci.execute('SELECT * FROM oneriler ORDER BY id DESC')
    kayitli_oneriler = islemci.fetchall()
    baglanti.close()
    return render_template('tarihce.html', oneriler=kayitli_oneriler)

@app.route('/api/oneriler/ekle', methods=['POST'])
def oneriler_ekle():
    veri = request.get_json()
    metin = veri.get('metin', '').strip()
    
    if not metin:
        return jsonify({'durum': 'hata', 'mesaj': 'Lütfen boş bırakmayın!'}), 400
        
    kullanici_id = -1
    if session.get('admin_girisi'):
        isim = "Sistem Yöneticisi (Admin)"
        kullanici_id = 0
    elif session.get('satici_girisi'):
        isim = session.get('ad_soyad', 'Kayıtlı Satıcı')
        kullanici_id = session.get('kullanici_id', -1)
    else:
        isim = veri.get('isim', '').strip() or 'Ziyaretçi'
        
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    islemci.execute('INSERT INTO oneriler (isim, metin, kullanici_id) VALUES (?, ?, ?)', (isim, metin, kullanici_id))
    baglanti.commit()
    baglanti.close()
    
    return jsonify({'durum': 'basarili', 'isim': isim, 'metin': metin})

@app.route('/api/tarihce_chat', methods=['POST'])
def api_tarihce_chat():
    veri = request.get_json()
    sorgu = veri.get('mesaj', '')
    
    prompt = f"""
    Sen ağır sanayi, talaşlı imalat ve fabrika makineleri konusunda uzman bir makine mühendisisin.
    Kullanıcı sana şu teknik soruyu sordu veya terimi sordu: "{sorgu}"
    
    Görev: Tamamen teknik verilere dayalı, öğretici, net ve anlaşılır bir cevap ver.
    Cevabın en fazla 3 cümle olsun. Profesyonel ve tok bir sanayi ustası üslubu kullan.
    """
    try:
        cevap = gemini_istek_at(prompt)
        return jsonify({'cevap': cevap})
    except Exception as hata:
        print(f"Tarihçe Asistan Hatası: {hata}")
        return jsonify({'cevap': 'Teknik asistan motoruna şu an bağlanılamadı. Lütfen terminaldeki hata kodunu kontrol edin.'})

@app.route('/makine/<int:makine_id>')
def makine_detay(makine_id):
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    
    islemci.execute('''
        SELECT m.*, k.kategori_adi, u.ad_soyad as satici_adi, u.telefon as satici_telefon
        FROM makineler m 
        JOIN kategoriler k ON m.kategori_id = k.id 
        LEFT JOIN kullanicilar u ON m.kullanici_id = u.id 
        WHERE m.id = ?
    ''', (makine_id,))
    makine = islemci.fetchone()
    
    islemci.execute('SELECT * FROM yedek_parcalar WHERE makine_id = ?', (makine_id,))
    yedek_parcalar = islemci.fetchall()
    
    baglanti.close()
    return render_template('detay.html', makine=makine, yedek_parcalar=yedek_parcalar)

@app.route('/kayit', methods=['GET', 'POST'])
def kayit_ol():
    if request.method == 'POST':
        ad_soyad = request.form.get('ad_soyad')
        email = request.form.get('email')
        telefon = request.form.get('telefon', '') 
        sifre = request.form.get('sifre')
        kriptolu_sifre = generate_password_hash(sifre)
        
        telefon = telefon.replace(" ", "").replace("+", "")
        if telefon and not telefon.startswith("90"):
            telefon = "90" + telefon.lstrip("0")
        elif not telefon:
            telefon = "905324876093"
            
        baglanti = veritabani_baglan()
        islemci = baglanti.cursor()
        try:
            islemci.execute('INSERT INTO kullanicilar (ad_soyad, email, sifre, telefon) VALUES (?, ?, ?, ?)', (ad_soyad, email, kriptolu_sifre, telefon))
            baglanti.commit()
            flash('Satıcı hesabınız başarıyla oluşturuldu! Şimdi giriş yapabilirsiniz.', 'success')
            return redirect(url_for('giris_yap'))
        except sqlite3.IntegrityError:
            flash('Bu e-posta adresi zaten sistemde kayıtlı!', 'error')
        finally:
            baglanti.close()
    return render_template('kayit.html')

@app.route('/giris', methods=['GET', 'POST'])
def giris_yap():
    hata = None
    if request.method == 'POST':
        email = request.form.get('email')
        sifre = request.form.get('sifre')
        
        if email == 'yusuf@kayamakina.com' and sifre == 'patron123':
            session['admin_girisi'] = True 
            session['kullanici_id'] = 0 
            session['ad_soyad'] = "Admin Yusuf"
            return redirect(url_for('admin_panel'))
        
        baglanti = veritabani_baglan()
        islemci = baglanti.cursor()
        islemci.execute('SELECT * FROM kullanicilar WHERE email = ?', (email,))
        kullanici = islemci.fetchone()
        baglanti.close()
        
        if kullanici and check_password_hash(kullanici['sifre'], sifre):
            session['satici_girisi'] = True
            session['kullanici_id'] = kullanici['id']
            session['ad_soyad'] = kullanici['ad_soyad']
            flash(f'Tekrar hoş geldin, {kullanici["ad_soyad"]}!', 'success')
            return redirect(url_for('satici_paneli')) 
        else:
            hata = "Hatalı e-posta veya şifre! Lütfen tekrar deneyin."
            
    return render_template('giris.html', hata=hata)

@app.route('/cikis')
def cikis_yap():
    session.clear() 
    flash('Güvenli bir şekilde çıkış yaptınız.', 'success')
    return redirect(url_for('ana_sayfa'))

@app.route('/admin')
def admin_panel():
    if not session.get('admin_girisi'): return redirect(url_for('giris_yap'))

    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    islemci.execute('SELECT * FROM kategoriler')
    kategoriler = islemci.fetchall()
    
    islemci.execute('''
        SELECT m.id, m.makine_adi, m.fiyat, m.para_birimi, k.kategori_adi, m.kullanici_id, u.ad_soyad as satici_adi
        FROM makineler m 
        JOIN kategoriler k ON m.kategori_id = k.id 
        LEFT JOIN kullanicilar u ON m.kullanici_id = u.id
        ORDER BY m.id DESC
    ''')
    makineler = islemci.fetchall()
    baglanti.close()
    return render_template('admin.html', makineler=makineler, kategoriler=kategoriler)

@app.route('/admin/ekle', methods=['POST'])
def makine_ekle():
    if not session.get('admin_girisi'): return redirect(url_for('giris_yap'))
    
    kategori_id = request.form.get('kategori_id')
    makine_adi = request.form.get('makine_adi')
    fiyat = request.form.get('fiyat')
    para_birimi = request.form.get('para_birimi')
    model_yili = request.form.get('model_yili')
    foto = request.files.get('foto')
    
    akilli_yorum = uzman_yorumu_uret(makine_adi, model_yili)
    
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    sorgu = '''INSERT INTO makineler (kategori_id, kullanici_id, makine_adi, fiyat, para_birimi, model_yili, durum, motor_gucu, kapasite, devir_araligi, teknik_aciklama, neden_almalisiniz) VALUES (?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    
    islemci.execute(sorgu, (kategori_id, makine_adi, fiyat, para_birimi, model_yili, 'Yeni Eklendi', '-', '-', '-', 'Sisteme yeni girildi.', akilli_yorum))
    yeni_id = islemci.lastrowid 
    baglanti.commit()
    baglanti.close()

    if foto and foto.filename != '':
        os.makedirs(os.path.join('static', 'images'), exist_ok=True)
        foto.save(os.path.join('static', 'images', f"{yeni_id}.jpg"))

    flash(f'"{makine_adi}" başarıyla eklendi.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/sil/<int:makine_id>', methods=['POST'])
def makine_sil(makine_id):
    if not session.get('admin_girisi'): return redirect(url_for('giris_yap'))
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    
    islemci.execute('DELETE FROM makineler WHERE id = ?', (makine_id,))
    baglanti.commit()
    baglanti.close()
    
    foto_yolu = os.path.join('static', 'images', f"{makine_id}.jpg")
    if os.path.exists(foto_yolu): os.remove(foto_yolu)
        
    flash('Seçili ilan sistemden başarıyla silindi.', 'error')
    return redirect(url_for('admin_panel'))

@app.route('/admin/foto_guncelle/<int:makine_id>', methods=['POST'])
def foto_guncelle(makine_id):
    if not session.get('admin_girisi'): return redirect(url_for('giris_yap'))
    foto = request.files.get('foto_guncel')
    if foto and foto.filename != '':
        os.makedirs(os.path.join('static', 'images'), exist_ok=True)
        foto.save(os.path.join('static', 'images', f"{makine_id}.jpg"))
        flash('Fotoğraf başarıyla güncellendi!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/yedek_ekle', methods=['POST'])
def yedek_ekle():
    if not session.get('admin_girisi'): return redirect(url_for('giris_yap'))
    makine_id = request.form.get('makine_id')
    parca_adi = request.form.get('parca_adi')
    fiyat = request.form.get('fiyat')
    para_birimi = request.form.get('para_birimi')
    stok_durumu = request.form.get('stok_durumu')
    
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    islemci.execute('INSERT INTO yedek_parcalar (makine_id, parca_adi, fiyat, para_birimi, stok_durumu) VALUES (?, ?, ?, ?, ?)', 
                   (makine_id, parca_adi, fiyat, para_birimi, stok_durumu))
    baglanti.commit()
    baglanti.close()
    flash(f'Yedek parça eklendi!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/satici')
def satici_paneli():
    if not session.get('satici_girisi'): return redirect(url_for('giris_yap'))
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    islemci.execute('SELECT * FROM kategoriler')
    kategoriler = islemci.fetchall()
    islemci.execute('''
        SELECT m.id, m.makine_adi, m.fiyat, m.para_birimi, k.kategori_adi 
        FROM makineler m JOIN kategoriler k ON m.kategori_id = k.id 
        WHERE m.kullanici_id = ? ORDER BY m.id DESC
    ''', (session['kullanici_id'],))
    makineler = islemci.fetchall()
    baglanti.close()
    return render_template('satici.html', makineler=makineler, kategoriler=kategoriler)

@app.route('/satici/ekle', methods=['POST'])
def satici_makine_ekle():
    if not session.get('satici_girisi'): return redirect(url_for('giris_yap'))
    kategori_id = request.form.get('kategori_id')
    makine_adi = request.form.get('makine_adi')
    fiyat = request.form.get('fiyat')
    para_birimi = request.form.get('para_birimi')
    model_yili = request.form.get('model_yili')
    foto = request.files.get('foto')
    
    akilli_yorum = uzman_yorumu_uret(makine_adi, model_yili)
    
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    sorgu = '''INSERT INTO makineler (kategori_id, kullanici_id, makine_adi, fiyat, para_birimi, model_yili, durum, motor_gucu, kapasite, devir_araligi, teknik_aciklama, neden_almalisiniz) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
    
    islemci.execute(sorgu, (kategori_id, session['kullanici_id'], makine_adi, fiyat, para_birimi, model_yili, 'İkinci El', '-', '-', '-', 'Satıcı tarafından yüklendi.', akilli_yorum))
    yeni_id = islemci.lastrowid 
    baglanti.commit()
    baglanti.close()
    
    if foto and foto.filename != '':
        os.makedirs(os.path.join('static', 'images'), exist_ok=True)
        foto.save(os.path.join('static', 'images', f"{yeni_id}.jpg"))
        
    flash('İlanınız başarıyla vitrine eklendi!', 'success')
    return redirect(url_for('satici_paneli'))

@app.route('/satici/sil/<int:makine_id>', methods=['POST'])
def satici_makine_sil(makine_id):
    if not session.get('satici_girisi'): return redirect(url_for('giris_yap'))
    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    islemci.execute('DELETE FROM makineler WHERE id = ? AND kullanici_id = ?', (makine_id, session['kullanici_id']))
    if islemci.rowcount > 0: 
        foto_yolu = os.path.join('static', 'images', f"{makine_id}.jpg")
        if os.path.exists(foto_yolu): os.remove(foto_yolu)
        flash('İlanınız yayından kaldırıldı.', 'success')
    else:
        flash('Güvenlik İhlali: Yetkisiz silme!', 'error')
    baglanti.commit()
    baglanti.close()
    return redirect(url_for('satici_paneli'))

@app.route('/api/chat', methods=['POST'])
def api_chat():
    veri = request.get_json()
    sorgu = veri.get('mesaj', '')
    
    if len(sorgu) < 3:
        return jsonify({'cevap': 'Lütfen size daha iyi yardımcı olabilmem için detay verin.'})

    baglanti = veritabani_baglan()
    islemci = baglanti.cursor()
    islemci.execute('SELECT id, makine_adi, fiyat, para_birimi FROM makineler')
    makineler = islemci.fetchall()
    baglanti.close()

    makine_katalogu = ""
    for m in makineler:
        makine_katalogu += f"Makine: {m['makine_adi']} | Fiyat: {m['fiyat']} {m['para_birimi']}\n"

    prompt = f"""
    Sen 'Kaya Makina' şirketinin cana yakın ve uzman yapay zeka satış asistanısın. 
    Müşteri sohbet kutusundan sana şunu yazdı: "{sorgu}"
    Stoktaki makinelerimiz şunlar:
    {makine_katalogu}
    Görev: Müşterinin talebini analiz et ve stoktan en uygun makineyi bul. Karşında bir dostun varmış gibi samimi, kısa ve net (en fazla 2-3 cümle) bir cevap ver. Makine önerirken fiyatını da belirt.
    """
    try:
        cevap = gemini_istek_at(prompt)
        return jsonify({'cevap': cevap})
    except Exception as hata:
        print(f"Sohbet Yapay Zeka Hatası: {hata}")
        return jsonify({'cevap': 'Sistemde anlık bir yoğunluk var, lütfen birazdan tekrar yazın.'})

def veritabani_tamir_et():
    baglanti = sqlite3.connect('kayamakina.db')
    islemci = baglanti.cursor()
    try:
        islemci.execute('SELECT makine_id FROM yedek_parcalar LIMIT 1')
    except sqlite3.OperationalError:
        islemci.execute('DROP TABLE IF EXISTS yedek_parcalar')
        islemci.execute('''CREATE TABLE yedek_parcalar (id INTEGER PRIMARY KEY AUTOINCREMENT, makine_id INTEGER, parca_adi TEXT, fiyat REAL, para_birimi TEXT, stok_durumu TEXT, FOREIGN KEY(makine_id) REFERENCES makineler(id))''')
        baglanti.commit()
        
    islemci.execute('''CREATE TABLE IF NOT EXISTS kullanicilar (id INTEGER PRIMARY KEY AUTOINCREMENT, ad_soyad TEXT NOT NULL, email TEXT UNIQUE NOT NULL, sifre TEXT NOT NULL, rol TEXT DEFAULT 'satici')''')
    
    try:
        islemci.execute('SELECT kullanici_id FROM makineler LIMIT 1')
    except sqlite3.OperationalError:
        islemci.execute('ALTER TABLE makineler ADD COLUMN kullanici_id INTEGER DEFAULT 0')
        baglanti.commit()

    try:
        islemci.execute('SELECT telefon FROM kullanicilar LIMIT 1')
    except sqlite3.OperationalError:
        islemci.execute('ALTER TABLE kullanicilar ADD COLUMN telefon TEXT DEFAULT "905324876093"')
        baglanti.commit()

    try:
        islemci.execute('SELECT id FROM oneriler LIMIT 1')
    except sqlite3.OperationalError:
        islemci.execute('''CREATE TABLE oneriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isim TEXT,
            metin TEXT,
            kullanici_id INTEGER DEFAULT -1
        )''')
        baglanti.commit()

    baglanti.close()

veritabani_tamir_et()
if __name__ == '__main__':
    app.run(debug=True)
