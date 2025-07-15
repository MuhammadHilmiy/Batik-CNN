from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import bcrypt

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np

app = Flask(__name__)
app.secret_key = "membuatLOginFlask1"

# ------------ KONFIGURASI MySQL ------------
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="flaskdb"
    )

dic = {0 : 'Batik Betawi',  
       1 : 'Batik Bokor Kencono',
       2 : 'Batik Boraspati', 
       3 : 'Batik Buketan',
       4 : 'Batik Ikat Celup',
       5 : 'Batik Kawung',
       6 : 'Batik Mega Mendung',
       7 : 'Batik Parang',
       8 : 'Batik Rumah Minang',
       9 : 'Batik Sidomukti',
       10 : 'Batik Tuntrum',
       11 : 'Batik Wahyu Tumurun',
       12 : 'Batik Wirasat'}
       
model = load_model('MobileNetV2-v1-Batik-91.11.h5')

model.make_predict_function()

def predict_label(img_path):
	i = image.load_img(img_path, target_size=(224,224))
	i = image.img_to_array(i)/255.0
	i = i.reshape(1, 224,224,3)
	p = np.argmax(model.predict(i), axis=-1)
	return dic[p[0]]


# routes
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        pwd_raw  = request.form['password'].encode('utf-8')

        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close(); conn.close()

        if user and bcrypt.checkpw(pwd_raw, user['password'].encode()):
            session['name']  = user['name']
            session['email'] = user['email']
            return redirect(url_for('classification'))

        flash("Email atau password salah", "danger")
        return redirect(url_for('login'))

    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name   = request.form['name']
        email  = request.form['email']
        pw1    = request.form['password'].encode('utf-8')
        pw2    = request.form['repassword'].encode('utf-8')

        if pw1 != pw2:
            flash("Password tidak sama", "warning")
            return redirect(url_for('register'))

        hash_pw = bcrypt.hashpw(pw1, bcrypt.gensalt())

        conn = get_db()                           # mysql‑connector helper
        cur  = conn.cursor(dictionary=True)

        cur.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            flash("Email sudah terdaftar, silakan login", "warning")
            cur.close(); conn.close()
            return redirect(url_for('login'))

        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s,%s,%s)",
            (name, email, hash_pw)
        )
        conn.commit()
        cur.close(); conn.close()

        flash("Registrasi berhasil, silakan login", "success")
        return redirect(url_for('login'))

    # GET: tampilkan form
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/classification")
def classification():
    # menampilkan form upload gambar
    return render_template("classification.html")


# ---------------- HALAMAN CONFUSION MATRIX ----------------
@app.route("/cnn")
def cnn():
    # menampilkan matrix (cnn.html)
    return render_template("cnn.html")


@app.route("/submit", methods = ['GET', 'POST'])
def get_output():
	if request.method == 'POST':
		img = request.files['my_image']

		img_path = "static/" + img.filename	
		img.save(img_path)

		p = predict_label(img_path)

	return render_template("classification.html", prediction = p, img_path = img_path)

if __name__ =='__main__':
	#app.debug = True
	app.run(debug = True)