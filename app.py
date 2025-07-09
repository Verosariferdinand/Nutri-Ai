import os, re
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///nutri_ai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # Ganti dengan secret key yang lebih kuat
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# Tentukan folder untuk menyimpan gambar
UPLOAD_FOLDER = os.path.join('static', 'images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Memeriksa ekstensi file yang diizinkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route untuk mengakses gambar yang sudah di-upload                                                                                                                                                                         
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    print(f"Request for file: {filename}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    umur = db.Column(db.Integer, nullable=False)
    tb = db.Column(db.Integer, nullable=False)
    bb = db.Column(db.Integer, nullable=False)
    profile_picture = db.Column(db.String(200), nullable=True)
    tujuan = db.Column(db.String(50), nullable=False)
    aktivitas = db.Column(db.String(50), nullable=False)
    tipe_tubuh = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    bmr = db.Column(db.Float, nullable=True)
    tdee = db.Column(db.Float, nullable=True)
    foods = db.relationship('Food', backref='user', lazy=True)


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_makanan = db.Column(db.String(120), nullable=False)
    porsi = db.Column(db.Integer, default=1)
    protein = db.Column(db.Integer, nullable=False)
    kalori = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    input_from = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "nama_makanan": self.nama_makanan,
            "porsi": self.porsi,
            "protein": self.protein,
            "kalori": self.kalori,
            "image": self.image,
            "input_from": self.input_from
        }

class WaktuMakan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    waktu_makan = db.Column(db.String(50), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id', name='fk_food_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_user_id'), nullable=False)
    food = db.relationship('Food', backref='waktu_makan', lazy=True)
    user = db.relationship('User', backref='waktu_makan', lazy=True)

    def __repr__(self):
        return f'<WaktuMakan {self.waktu_makan}>'
    
# Model untuk Laporan
class Laporan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id', name='fk_food_id'), nullable=True)
    waktu_makan = db.Column(db.String(50), nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    total_protein = db.Column(db.Integer, nullable=False)
    total_kalori = db.Column(db.Integer, nullable=False)

    food = db.relationship('Food', backref='laporan', lazy=True)
    user = db.relationship('User', backref='laporan', lazy=True)

    def __repr__(self):
        return f'<Laporan {self.id} - {self.tanggal}>'

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('register.html')

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', user=user)

@app.route('/update_profile_picture', methods=['POST'])
def update_profile_picture():
    if 'profile_picture' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    file = request.files['profile_picture']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            # Menyimpan file
            file.save(file_path)
            print(f"File saved to: {file_path}")  # Debug: Tampilkan path penyimpanan file

            # Update foto profil di database
            user = User.query.filter_by(username=session.get('username')).first_or_404()
            user.profile_picture = filename
            db.session.commit()

            # Kembalikan URL gambar yang baru
            return jsonify({'status': 'success', 'profile_picture_url': url_for('uploaded_file', filename=filename)})

        except Exception as e:
            db.session.rollback()
            return jsonify({'status': 'error', 'message': f'Error uploading file: {str(e)}'}), 500

    return jsonify({'status': 'error', 'message': 'File type not allowed'}), 400

@app.route('/register', methods=['POST'])
def register():
    # Ambil data dari form
    umur = int(request.form['umur'])
    tb = int(request.form['tb'])
    bb = int(request.form['bb'])
    gender = request.form['gender']
    aktivitas = request.form['aktivitas']
    tujuan = request.form['tujuan']
    tipe_tubuh = request.form.get('body_type')

    # Hitung BMR menggunakan rumus Mifflin-St Jeor
    if gender == 'laki_laki':
        bmr = 10 * bb + 6.25 * tb - 5 * umur + 5
    else:
        bmr = 10 * bb + 6.25 * tb - 5 * umur - 161

    # Menentukan faktor aktivitas berdasarkan pilihan pengguna
    if aktivitas == 'sangat_tidak_aktif':
        tdee = bmr * 1.2  # Sedentary
    elif aktivitas == 'aktivitas_ringan':
        tdee = bmr * 1.375  # Lightly active
    elif aktivitas == 'aktivitas_sedang':
        tdee = bmr * 1.55  # Moderately active
    elif aktivitas == 'aktivitas_berat':
        tdee = bmr * 1.725  # Very active

    # Penyesuaian berdasarkan tipe tubuh
    if tipe_tubuh == 'ectomorph':
        tdee *= 1.2  # Ectomorph membutuhkan lebih banyak kalori
    elif tipe_tubuh == 'mesomorph':
        tdee *= 1.55  # Mesomorph tetap dengan faktor standar
    elif tipe_tubuh == 'endomorph':
        tdee *= 1.8  # Endomorph membutuhkan kalori lebih sedikit untuk diet

    # Membuat objek user dengan data dari form dan hasil perhitungan BMR dan TDEE
    user = User(
        username=request.form['username'],
        password=generate_password_hash(request.form['password']),
        umur=umur,
        tb=tb,
        bb=bb,
        tujuan=tujuan,
        aktivitas=aktivitas,
        gender=gender,
        tipe_tubuh=tipe_tubuh,
        bmr=bmr,
        tdee=tdee
    )
    
    # Menambahkan user ke dalam database
    db.session.add(user)
    db.session.commit()

    # Menyimpan username ke session agar pengguna tetap login tanpa perlu login ulang
    session['username'] = user.username

    # Mengalihkan ke halaman dashboard pengguna
    return redirect(url_for('dashboard', username=user.username))

# Fungsi untuk menambahkan pemisah ribuan
@app.template_filter('format_number')
def format_number(value):
    try:
        return "{:,.0f}".format(value)
    except ValueError:
        return value
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['username'] = user.username
            return redirect(url_for('dashboard', username=user.username))
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/dashboard/<username>')
def dashboard(username):
    user = User.query.filter_by(username=username).first_or_404()

    # Ambil BMR dan TDEE dari database
    bmr = user.bmr
    tdee = user.tdee

    # Menentukan target kalori berdasarkan tujuan
    if user.tujuan == 'bulking':
        target_calories = tdee + 500  # Menambah 500 kalori untuk bulking
        target_protein = user.bb * 2  # Asumsi protein 15% dari total kalori
    elif user.tujuan == 'cutting':
        target_calories = tdee - 500  # Mengurangi 500 kalori untuk cutting
        target_protein = user.bb * 2  # Asumsi protein 15% dari total kalori
    else:
        target_calories = tdee  # Target kalori tetap di TDEE untuk maintain
        target_protein = user.bb * 1.6  # Asumsi protein 15% dari total kalori
    
    # Mendapatkan makanan berdasarkan waktu makan
    makanan_pagi = WaktuMakan.query.filter_by(waktu_makan='Pagi', user_id=user.id).all()
    makanan_siang = WaktuMakan.query.filter_by(waktu_makan='Siang', user_id=user.id).all()
    makanan_sore = WaktuMakan.query.filter_by(waktu_makan='Sore', user_id=user.id).all()
    makanan_malam = WaktuMakan.query.filter_by(waktu_makan='Malam', user_id=user.id).all()

    # Fungsi untuk menghitung total protein dan kalori berdasarkan waktu makan
    def total(waktu_list):
        return sum(w.food.protein for w in waktu_list if w.food.input_from == 'input makanan'), \
               sum(w.food.kalori  for w in waktu_list if w.food.input_from == 'input makanan')

    # Total keseluruhan dari semua makanan yang diinput
    total_protein_input = sum(f.protein for f in user.foods if f.input_from == 'input makanan')
    total_kalori_input = sum(f.kalori  for f in user.foods if f.input_from == 'input makanan')

    # Total per waktu makan
    total_protein_pagi, total_kalori_pagi = total(makanan_pagi)
    total_protein_siang, total_kalori_siang = total(makanan_siang)
    total_protein_sore, total_kalori_sore = total(makanan_sore)
    total_protein_malam, total_kalori_malam = total(makanan_malam)
    
     # Menghitung progress terhadap target kalori dan protein
    progress_calories = round((total_kalori_input / target_calories) * 100, 1)  # Round to 1 decimal
    progress_protein = round((total_protein_input / target_protein) * 100, 1)  # Round to 1 decimal

    # Status apakah target tercapai atau belum
    target_status_calories = "Sudah tercapai" if total_kalori_input >= target_calories else "Belum tercapai"
    target_status_protein = "Sudah tercapai" if total_protein_input >= target_protein else "Belum tercapai"

    return render_template('dashboard.html',
                           user=user,
                           bmr=round(bmr),  # Menampilkan BMR dengan pembulatan
                           tdee=round(tdee),  # Menampilkan TDEE dengan pembulatan
                           target_calories=round(target_calories),  # Menampilkan target kalori dengan pembulatan
                           target_protein=round(target_protein),  # Menampilkan target protein dengan pembulatan
                           total_protein_input_makanan=total_protein_input,
                           total_kalori_input_makanan=total_kalori_input,
                           total_protein_pagi=total_protein_pagi,
                           total_kalori_pagi=total_kalori_pagi,
                           total_protein_siang=total_protein_siang,
                           total_kalori_siang=total_kalori_siang,
                           total_protein_sore=total_protein_sore,
                           total_kalori_sore=total_kalori_sore,
                           total_protein_malam=total_protein_malam,
                           total_kalori_malam=total_kalori_malam,
                           makanan_pagi=makanan_pagi,
                           makanan_siang=makanan_siang,
                           makanan_sore=makanan_sore,
                           makanan_malam=makanan_malam,
                           progress_calories=progress_calories,
                           progress_protein=progress_protein,
                           target_status_calories=target_status_calories,
                           target_status_protein=target_status_protein)


@app.route('/input_makanan/<username>', methods=['GET', 'POST'])
def input_makanan(username):
    if 'username' not in session:
        return redirect(url_for('home'))  # Pastikan user sudah login

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        nama_makanan = request.form['nama_makanan']
        porsi = request.form['porsi']
        if not nama_makanan or not porsi or int(porsi) <= 0:
            # Jika nama makanan kosong atau porsi kurang dari 1, tampilkan pesan error
            return jsonify({'status': 'error', 'message': 'Pastikan nama makanan valid dan porsi lebih dari 0.'}), 400

        f = Food(
            nama_makanan=nama_makanan,
            porsi=int(porsi),
            protein=int(request.form['protein']),
            kalori=int(request.form['kalori']),
            user_id=user.id,
            input_from="input makanan"
        )
        db.session.add(f)
        db.session.commit()

        db.session.add(WaktuMakan(
            waktu_makan=request.form['waktu_makan'],
            food_id=f.id,
            user_id=user.id
        ))
        db.session.commit()

        return redirect(url_for('dashboard', username=username))

    # Mengambil semua data makanan berdasarkan user yang sedang login
    foods_data = [f.to_dict() for f in Food.query.filter_by(input_from="tambah data").all()]
    
    return render_template('input_makanan.html', user=user, foods_data=foods_data)

@app.route('/submit_to_dashboard', methods=['POST'])
def submit_to_dashboard():
    try:
        # Mendapatkan data JSON dari request
        data = request.get_json(force=True)
        # Mengambil pengguna berdasarkan session yang login
        user = User.query.filter_by(username=session.get('username')).first_or_404()

        for item in data:
            # Memastikan data makanan dimasukkan dengan benar
            f = Food(
                nama_makanan=item['nama_makanan'],
                porsi=int(item['porsi']),
                protein=int(re.sub(r'\D', '', item['protein'])),  # Mengambil angka saja dari input
                kalori=int(re.sub(r'\D', '', item['kalori'])),    # Mengambil angka saja dari input
                user_id=user.id,  # Menambahkan user_id
                input_from="input makanan",
                image=item['image']  # Menyimpan gambar makanan jika ada
            )
            db.session.add(f)
            db.session.commit()  # Commit setelah menambah food

            # Memasukkan data waktu makan untuk makanan yang diinput
            db.session.add(WaktuMakan(
                waktu_makan=item['waktu_makan'],
                food_id=f.id,  # Referensi ke food yang baru saja ditambahkan
                user_id=user.id  # Menambahkan user_id ke waktu_makan untuk mengaitkan ke pengguna
            ))
        
        # Commit perubahan
        db.session.commit()
        return jsonify({'status': 'success'}), 200

    except Exception as e:
        # Jika terjadi error, rollback untuk membatalkan perubahan
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/tambah_data/<username>', methods=['GET', 'POST'])
def tambah_data(username):
    user = User.query.filter_by(username=username).first_or_404()

    if request.method == 'POST':
        nama_makanan = request.form['nama_makanan']
        protein = int(request.form['protein'])
        kalori = int(request.form['kalori'])
        file = request.files['food_image']

        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        f = Food(
            nama_makanan=nama_makanan,
            protein=protein,
            kalori=kalori,
            image=filename,
            user_id=None,
            input_from="tambah data"
        )
        db.session.add(f)
        db.session.commit()

        return redirect(url_for('input_makanan', username=username))

    return render_template('tambah_data.html', user=user)

# Route untuk Laporan
@app.route('/laporan/<username>', methods=['GET'])
def laporan(username):
    # Menemukan pengguna berdasarkan username
    user = User.query.filter_by(username=username).first_or_404()

    # Mengambil laporan berdasarkan user_id dan urutkan berdasarkan tanggal
    laporan_data = Laporan.query.filter_by(user_id=user.id).order_by(Laporan.tanggal.desc()).all()

    # Jika tidak ada laporan, beri pesan atau tampilkan halaman kosong
    if laporan_data is None:
        return render_template('laporan.html', user=user, laporan_data=None, message="Tidak ada laporan yang tersedia.")
    
    # Menampilkan laporan dalam bentuk tabel
    return render_template('laporan.html', user=user, laporan_data=laporan_data)


@app.route('/submit_laporan/<username>', methods=['POST'])
def submit_laporan(username):
    # Logika untuk submit laporan
    user = User.query.filter_by(username=username).first_or_404()

    # Ambil data makanan berdasarkan waktu makan
    makanan_pagi = WaktuMakan.query.filter_by(waktu_makan='Pagi').all()
    makanan_siang = WaktuMakan.query.filter_by(waktu_makan='Siang').all()
    makanan_sore = WaktuMakan.query.filter_by(waktu_makan='Sore').all()
    makanan_malam = WaktuMakan.query.filter_by(waktu_makan='Malam').all()

    # Hitung total protein dan kalori per waktu makan
    def total(waktu_list):
        return sum(w.food.protein for w in waktu_list if w.food.input_from == 'input makanan'), \
               sum(w.food.kalori for w in waktu_list if w.food.input_from == 'input makanan')

    total_protein_pagi, total_kalori_pagi = total(makanan_pagi)
    total_protein_siang, total_kalori_siang = total(makanan_siang)
    total_protein_sore, total_kalori_sore = total(makanan_sore)
    total_protein_malam, total_kalori_malam = total(makanan_malam)

    # Hitung total keseluruhan
    total_protein = total_protein_pagi + total_protein_siang + total_protein_sore + total_protein_malam
    total_kalori = total_kalori_pagi + total_kalori_siang + total_kalori_sore + total_kalori_malam

    # Menyimpan data laporan ke database
    laporan = Laporan(
        user_id=user.id,
        waktu_makan='Hari Ini',  # Bisa diperinci berdasarkan waktu makan
        total_protein=total_protein,
        total_kalori=total_kalori
    )

    db.session.add(laporan)
    db.session.commit()

    # Redirect setelah data laporan disubmit
    return redirect(url_for('laporan', username=username))

@app.route('/reset_and_report', methods=['POST'])
def reset_and_report():
    today = datetime.utcnow().date()

    # Ambil semua data makanan hari ini (untuk user yang login)
    user = User.query.filter_by(username=session['username']).first_or_404()

    # Mengambil makanan yang dimasukkan hari ini
    makanan_hari_ini = WaktuMakan.query.join(Food).filter(Food.user_id == user.id, Food.input_from == 'input makanan').all()

    # Menghitung total protein dan kalori untuk laporan
    total_protein = sum(w.food.protein * w.food.porsi for w in makanan_hari_ini)
    total_kalori = sum(w.food.kalori * w.food.porsi for w in makanan_hari_ini)

    # Menambahkan laporan ke dalam database
    laporan = Laporan(
        user_id=user.id,
        waktu_makan='Hari Ini',  # Bisa lebih spesifik jika diinginkan
        total_protein=total_protein,
        total_kalori=total_kalori
    )
    db.session.add(laporan)
    db.session.commit()

    # Hapus data makanan hari ini
    db.session.query(WaktuMakan).filter(Food.user_id == user.id).delete()
    db.session.query(Food).filter(Food.user_id == user.id, Food.input_from == 'input makanan').delete()
    db.session.commit()

    # Redirect ke halaman laporan atau dashboard setelah reset
    return redirect(url_for('laporan', username=user.username))

# Fungsi reset otomatis setiap 24 jam
def reset_daily():
    today = datetime.utcnow().date()

    # Ambil semua data makanan hari ini (untuk user yang login)
    user = User.query.filter_by(username=session['username']).first_or_404()

    # Mengambil makanan yang dimasukkan hari ini
    makanan_hari_ini = WaktuMakan.query.join(Food).filter(Food.user_id == user.id, Food.input_from == 'input makanan').all()

    # Menghitung total protein dan kalori untuk laporan
    total_protein = sum(w.food.protein * w.food.porsi for w in makanan_hari_ini)
    total_kalori = sum(w.food.kalori * w.food.porsi for w in makanan_hari_ini)

    # Menambahkan laporan ke dalam database
    laporan = Laporan(
        user_id=user.id,
        waktu_makan='Hari Ini',  # Bisa lebih spesifik jika diinginkan
        total_protein=total_protein,
        total_kalori=total_kalori
    )
    db.session.add(laporan)
    db.session.commit()

    # Hapus data makanan hari ini
    db.session.query(WaktuMakan).filter(Food.user_id == user.id).delete()
    db.session.query(Food).filter(Food.user_id == user.id, Food.input_from == 'input makanan').delete()
    db.session.commit()

    # Redirect ke halaman laporan atau dashboard setelah reset
    return redirect(url_for('laporan', username=user.username))

# Scheduler untuk reset otomatis setiap 24 jam
scheduler = BackgroundScheduler()
scheduler.add_job(func=reset_daily, trigger="interval", hours=24)
scheduler.start()


if __name__ == '__main__':
    app.run(debug=True)
