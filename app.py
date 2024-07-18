from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from pymongo import MongoClient
import jwt
from jwt.exceptions import ExpiredSignatureError
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from functools import wraps
from bson import ObjectId
import os
import pytz
from os.path import join, dirname
from dotenv import load_dotenv
import certifi
ca = certifi.where()


app = Flask(__name__)
dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

ADMIN_KEY = "NUSAACADEMY"
SECRET_KEY = "NUSAACADEMY" 
MONGODB_URI = ("mongodb+srv://ncc1477:Qwedsa123!@cluster0.kkwb2cl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
app.config["UPLOAD_FOLDER"] = "./static/images"
app.secret_key = SECRET_KEY

client = MongoClient(MONGODB_URI,tlsCAFile=ca)
db = client.nusa_academy
TOKEN_KEY = "mytoken"


# untuk menentukan laman admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token_receive = request.cookies.get("mytoken")
        if token_receive is not None:
            try:
                payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
                if payload["role"] == "admin":
                    return f(*args, **kwargs)
                else:
                    return redirect(
                        url_for("home", msg="Only admin can access this page")
                    )
            except (jwt.ExpiredSignatureError, jwt.DecodeError):
                return redirect(
                    url_for("login", msg="Your token is invalid or has expired")
                )
        else:
            return redirect(url_for("login", msg="Please login to view this page"))

    return decorated_function


@app.route("/")
def home():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
        else:
            user_info = None

        articles = db.articles.find().sort("tanggal", -1).limit(3)

        return render_template("Myhome.html", user_info=user_info)

    except jwt.ExpiredSignatureError:
        return render_template("Myhome.html")


@app.route("/about")
def about():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
        else:
            user_info = None

        articles = db.articles.find().sort("tanggal", -1).limit(3)

        return render_template("AboutNew.html", user_info=user_info)

    except jwt.ExpiredSignatureError:
        return render_template("Myhome.html")


@app.route("/mentor")
def mentor():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            mentors = db.mentor.find()
            return render_template(
                "MyMentor.html", mentors=mentors, user_info=user_info
            )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/mentor_kami", methods=["GET", "POST"])
def mentor_kami():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.mentor.find_one({"username": payload["id"]})
        else:
            user_info = None

        if request.method == "POST":
            mentor_name = request.form.get("name")
            mentor_file = request.files["file"]

            # Check if 'file' exists in the form data
            if mentor_file:
                mentor_description = request.form.get("description")
                timezone = pytz.timezone("Asia/Jakarta")
                current_datetime = datetime.now(timezone)
                tanggal_kirim = current_datetime.strftime("%d/%m/%y - %H:%M")
                timestamp = current_datetime.timestamp()

                # Securely save the file with a unique filename
                mentor_file.save(
                    os.path.join(app.config["UPLOAD_FOLDER"], mentor_file.filename)
                )

                # Save mentor data to the database
                new_mentor = {
                    "name": mentor_name,
                    "file": mentor_file.filename,
                    "description": mentor_description,
                    "tanggal_kirim": tanggal_kirim,
                    "timestamp": timestamp,
                }
                db.mentor.insert_one(new_mentor)

                return redirect(url_for("mentor", user_info=user_info))

            else:
                # Handle the case where 'file' is not present in the form data
                flash("No file part", "error")
                return redirect(request.url)

        # Add a return statement for cases where the method is not 'POST'
        return render_template("MyMentor.html", user_info=user_info)

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("mentor_kami"))


@app.route("/administrator/forum")
@admin_required
def admin_forum():
    forums = db.forums.find()
    return render_template("administrator/forum.html", forums=forums)


@app.route("/administrator/dashboard/<username>")
@admin_required
def admin_home(username):
    token_receive = request.cookies.get("mytoken")
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    status = username == payload["id"]
    user_info = db.user.find_one({"username": payload["id"]})
    user_data = db.user.find_one({"username": username}, {"_id": False})
    page = request.args.get("page", 1, type=int)
    contacts_per_page = 20
    contacts = (
        db.hubungi.find().skip((page - 1) * contacts_per_page).limit(contacts_per_page)
    )
    total_contacts = db.hubungi.count_documents({})
    if user_info is not None:
        return render_template(
            "administrator/dashboardAdmin.html",
            status=status,
            user_data=user_data,
            user_info=user_info,
            is_admin=True,
            contacts=contacts,
            page=page,
            total_contacts=total_contacts,
            contacts_per_page=contacts_per_page,
        )
    else:
        return redirect(url_for("login", msg="User not found"))


@app.route("/administrator/hubungi/<username>")
@admin_required
def admin_hubungi(username):
    page = request.args.get("page", 1, type=int)
    contacts_per_page = 20
    contacts = (
        db.hubungi.find().skip((page - 1) * contacts_per_page).limit(contacts_per_page)
    )
    total_contacts = db.hubungi.count_documents({})
    token_receive = request.cookies.get("mytoken")
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    status = username == payload["id"]
    user_data = db.user.find_one({"username": username}, {"_id": False})
    user_info = db.user.find_one({"username": payload["id"]})
    page = request.args.get("page", 1, type=int)
    contacts_per_page = 20
    contacts = (
        db.hubungi.find().skip((page - 1) * contacts_per_page).limit(contacts_per_page)
    )
    return render_template(
        "administrator/dashboardAdmin.html",
        status=status,
        user_data=user_data,
        contacts=contacts,
        page=page,
        total_contacts=total_contacts,
        user_info=user_info,
        contacts_per_page=contacts_per_page,
    )


# regis admin
@app.route("/admin_reg")
def admin_register():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            if user_info:
                # Jika pengguna sudah login, arahkan ke halaman lain
                return redirect(url_for("home"))

        # Jika pengguna belum login, tampilkan halaman registrasi admin
        return render_template("admin_register.html")

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template("admin_register.html")


# admin login
@app.route("/admin_signup", methods=["POST"])
def admin_signup():
    username_receive = request.form["username"]
    nama_receive = request.form["nama_lengkap"]
    pw_receive = request.form["password"]
    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()
    adminkey_receive = request.form["admin_key"]
    user_exists = bool(db.user.find_one({"username": username_receive}))
    if user_exists:
        return jsonify(
            {
                "result": "error_uname",
                "msg": f"An account with username {username_receive} is already exists. Please Login!",
            }
        )
    elif adminkey_receive != ADMIN_KEY:
        return jsonify(
            {"result": "error_akey", "msg": f"Admin key yang anda masukkan salah!"}
        )
    else:
        doc = {
            "username": username_receive,
            "name": nama_receive,
            "password": pw_hash,
            "profile_pic_real": "profile_pics/profile_placeholder.png",
            "profile_info": "",
            "role": "admin",
        }
        db.user.insert_one(doc)
        return jsonify({"result": "success"})


# user regis
@app.route("/user_signup", methods=["POST"])
def user_signup():
    username_receive = request.form["username"]
    nama_receive = request.form["nama_lengkap"]
    pw_receive = request.form["password"]
    pw_hash = hashlib.sha256(pw_receive.encode("utf-8")).hexdigest()

    user_exists = bool(db.user.find_one({"username": username_receive}))
    if user_exists:
        return jsonify(
            {
                "result": "error_uname",
                "msg": f"An account with username {username_receive} is already exists. Please Login!",
            }
        )
    else:
        doc = {
            "username": username_receive,
            "name": nama_receive,
            "password": pw_hash,
            "profile_pic_real": "profile_pics/profile_placeholder.png",
            "profile_info": "",
            "role": "member",
        }
        db.user.insert_one(doc)
        return jsonify({"result": "success"})


# user login
@app.route("/sign_in", methods=["POST"])
def sign_in():
    # Sign in
    username_receive = request.form["username_give"]
    password_receive = request.form["password_give"]
    pw_hash = hashlib.sha256(password_receive.encode("utf-8")).hexdigest()
    result = db.user.find_one(
        {
            "username": username_receive,
            "password": pw_hash,
        }
    )
    print(result)
    if result:
        payload = {
            "id": username_receive,
            # the token will be valid for 24 hours
            "exp": datetime.utcnow() + timedelta(seconds=60 * 60 * 24),
            "role": result["role"],
        }
        print(payload)
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")

        return jsonify(
            {
                "result": "success",
                "token": token,
            }
        )
    # Let's also handle the case where the id and
    # password combination cannot be found
    else:
        return jsonify(
            {
                "result": "fail",
                "msg": "Kami tidak dapat menemukan pengguna dengan kombinasi username/password tersebut.",
            }
        )


@app.route("/login")
def login():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            if user_info:
                return redirect(url_for("home"))

        return render_template("login.html")

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return render_template("login.html")


@app.route("/user_count", methods=["GET"])
def user_count():
    user_count = db.user.count_documents({})
    return jsonify({"user_count": user_count})


@app.route("/user_transaksi", methods=["GET"])
def user_transaksi():
    user_transaksi = db.transactions.count_documents({})
    return jsonify({"user_transaksi": user_transaksi})


@app.route("/administrator/materi")
def admin_kelas():
    classes = db.classes.find()
    # for class in classes
    # kelas = class['nama_kelas']
    return render_template("administrator/materi.html", classes=classes)


@app.route("/hubungi_kami", methods=["GET", "POST"])
def hubungi():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
        else:
            user_info = None

        if request.method == "POST":
            nama_lengkap = request.form["nama_lengkap"]
            email = request.form["email"]
            pesan = request.form["message"]
            timezone = pytz.timezone("Asia/Jakarta")
            current_datetime = datetime.now(timezone)
            tanggal_kirim = current_datetime.strftime("%d/%m/%y - %H:%M")
            timestamp = current_datetime.timestamp()
            doc = {
                "nama_lengkap": nama_lengkap,
                "email": email,
                "pesan": pesan,
                "tanggal_kirim": tanggal_kirim,
                "timestamp": timestamp,
            }
            db.hubungi.insert_one(doc)
            return jsonify({"msg": "Pesan Anda Berhasil Dikirim"})
        else:
            return render_template("hubungiNEW.html", user_info=user_info)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/profil/<username>")
def user(username):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        status = username == payload["id"]
        user_info = db.user.find_one({"username": payload["id"]})
        user_data = db.user.find_one({"username": username}, {"_id": False})
        return render_template(
            "profile_mem.html", user_info=user_info, user_data=user_data, status=status
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/update_user", methods=["POST"])
def save_user():
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        username = payload["id"]
        name_receive = request.form["name_give"]
        updated_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        doc = {
            "name": name_receive,
        }

        if "file_give" in request.files:
            # nama_wisata = request.form['nama_wisata']
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/.{username}.{extension}"
            file.save("./static/" + file_path)
            doc["profile_pic"] = filename
            doc["profile_pic_real"] = file_path

        # Perbarui informasi nama pengguna dan profil di basis data
        db.user.update_one({"username": payload["id"]}, {"$set": doc})

        response = jsonify({"result": "success", "msg": "Profil Anda telah diperbarui"})
        response.set_cookie("mytoken", updated_token)
        return response
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/forum/<username>", methods=["GET", "POST"])
def forum(username):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.user.find_one({"username": payload["id"]})

        if request.method == "POST":
            konten = request.form.get("konten")
            post_id = request.form.get("post_id")
            action = request.form.get("action")

            timezone = pytz.timezone("Asia/Jakarta")
            current_datetime = datetime.now(timezone)
            post_date = current_datetime.strftime("%d/%m/%y - %H:%M")
            timestamp = current_datetime.timestamp()

            doc = {
                "username": user_info["username"],
                "nama_lengkap": user_info["name"],
                "foto_profil": user_info["profile_pic_real"],
                "role": user_info["role"],
                "konten": konten,
                "post_data": post_date,
                "isCompleted": "false",
                "timestamp": timestamp,
                "action": action,
                "likes": 0,
            }
            db.forum.insert_one(doc)
            return jsonify({"msg": "Komentar berhasil ditambahkan"})
        else:
            forums = list(db.forum.find().sort("timestamp", -1))
            return render_template("forum.html", user_info=user_info, forums=forums)

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/forum/<username>/comment", methods=["GET", "POST"])
def forum_comment(username):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.user.find_one({"username": payload["id"]})

        if request.method == "POST":
            konten = request.form.get("konten")
            post_id = request.form.get("post_id")

            timezone = pytz.timezone("Asia/Jakarta")
            current_datetime = datetime.now(timezone)
            post_date = current_datetime.strftime("%d/%m/%y - %H:%M")
            timestamp = current_datetime.timestamp()
            # Simpan komentar ke database, hubungkan dengan postingan menggunakan post_id
            db.forum.update_one(
                {"_id": ObjectId(post_id)},
                {
                    "$push": {
                        "comments": {
                            "username": user_info["username"],
                            "konten": konten,
                            "timestamp": timestamp,
                            "foto_profil": user_info["profile_pic_real"],
                            "role": user_info["role"],
                            "post_data": post_date,
                            # "status": "false", > "status":"True"
                            # if "status" == "True" "redirect_url('front-end')
                        }
                    }
                },
            )

            return jsonify({"success": True, "msg": "Komentar berhasil ditambahkan"})

        forums = list(db.forum.find().sort("timestamp", -1))
        return render_template("forum.html", user_info=user_info, forums=forums)

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/administrator/profile/<username>")
@admin_required
def admin(username):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        status = username == payload["id"]
        user_info = db.user.find_one({"username": payload["id"]})
        user_data = db.user.find_one({"username": username}, {"_id": False})
        return render_template(
            "administrator/profile.html",
            is_admin=True,
            user_info=user_info,
            user_data=user_data,
            status=status,
        )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/update_admin", methods=["POST"])
def save_img():
    token_receive = request.cookies.get(TOKEN_KEY)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        username = payload["id"]
        name_receive = request.form["name_give"]
        updated_token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
        doc = {
            "name": name_receive,
        }

        if "file_give" in request.files:
            file = request.files.get("file_give")
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/.{username}{extension}"
            file.save("./static/" + file_path)
            doc["file"] = file_path
            doc["profile_pic"] = filename
            doc["profile_pic_real"] = file_path

        # Perbarui informasi nama pengguna dan profil di basis data
        db.user.update_one({"username": payload["id"]}, {"$set": doc})

        # Kembalikan token yang sudah diperbarui dalam respons
        response = jsonify({"result": "success", "msg": "Profil Anda telah diperbarui"})
        response.set_cookie(TOKEN_KEY, updated_token)
        return response

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


@app.route("/fetch_notifications", methods=["GET"])
def fetch_notifications():
    try:
        # Implement your logic to fetch notification counts
        contact_count = db.hubungi.count_documents({})
        new_user_count = db.user.count_documents({"role": "member"})

        return jsonify(
            {"contact_count": contact_count, "new_user_count": new_user_count}
        )

    except Exception as e:
        # Handle exceptions as needed
        return jsonify({"error": str(e)})


# Logic to fetch detailed notifications
@app.route("/get_notifications", methods=["GET"])
def get_notifications():
    try:
        # Implement your logic to fetch detailed notifications
        # For example, fetch the latest contact messages or new user registrations
        contact_messages = list(db.hubungi.find().sort("timestamp", -1).limit(5))
        new_users = list(
            db.user.find({"role": "member"}).sort("timestamp", -1).limit(5)
        )

        # Create a list of notification messages
        notifications = []
        for message in contact_messages:
            notifications.append(f"New contact message from {message['nama_lengkap']}")
        for user in new_users:
            notifications.append(f"New user registered: {user['name']}")

        return jsonify(notifications)
    except Exception as e:
        # Handle exceptions as needed
        return jsonify({"error": str(e)})


@app.route("/temp")
def temp():
    return render_template("templateNavbar.html")


@app.route("/materi")
def materi():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            transactions = list(db.transactions.find({"user_id": payload["id"]}))
            frontend_classes = list(db.materi.find({"category": "Front-end"}))
            backend_classes = list(db.materi.find({"category": "Back-end"}))
            fullstack_classes = list(db.materi.find({"category": "Fullstack"}))

            for transaction in transactions:
                transaction["class_id"] = str(transaction["class_id"])
            for materi in frontend_classes:
                materi["_id"] = str(materi["_id"])
                # _id = ObjectId("dsakjhldshajkdhjskahdjksahdjksa")
            for materi in backend_classes:
                materi["_id"] = str(materi["_id"])
            for materi in fullstack_classes:
                materi["_id"] = str(materi["_id"])
            return render_template(
                "CLASSBARU.html",
                transactions=transactions,
                frontend_classes=frontend_classes,
                backend_classes=backend_classes,
                fullstack_classes=fullstack_classes,
                user_info=user_info,
            )
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/tambah_kelas", methods=["POST"])
def tambah_kelas():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.materi.find_one({"username": payload["id"]})
        else:
            user_info = None
        if request.method == "POST":
            nama_kelas = request.form.get("nama_kelas")
            category = request.form.get("category")
            gambar_kelas = request.files[
                "gambar_kelas"
            ]  # handle file upload appropriately
            deskripsi_kelas = request.form.get("deskripsi_kelas")
            harga_kelas = request.form.get("harga_kelas")
            judul_kelas1 = request.form.get("judul_kelas1")
            judul_kelas2 = request.form.get("judul_kelas2")
            judul_kelas3 = request.form.get("judul_kelas3")
            isi_kelas1 = request.form.get("isi_kelas1")
            isi_kelas2 = request.form.get("isi_kelas2")
            isi_kelas3 = request.form.get("isi_kelas3")
            url_kelas1 = request.form.get("url_kelas1")
            url_kelas2 = request.form.get("url_kelas2")
            url_kelas3 = request.form.get("url_kelas3")

            new_class = {
                "nama_kelas": nama_kelas,
                "category": category,
                "gambar_kelas": gambar_kelas.filename,
                "deskripsi_kelas": deskripsi_kelas,
                "harga_kelas": harga_kelas,
                "judul_kelas1": judul_kelas1,
                "judul_kelas2": judul_kelas2,
                "judul_kelas3": judul_kelas3,
                "isi_kelas1": isi_kelas1,
                "isi_kelas2": isi_kelas2,
                "isi_kelas3": isi_kelas3,
                "url_kelas1": url_kelas1,
                "url_kelas2": url_kelas2,
                "url_kelas3": url_kelas3,
            }

            db.materi.insert_one(new_class)
            gambar_kelas.save(
                os.path.join(app.config["UPLOAD_FOLDER"], gambar_kelas.filename)
            )
            return redirect(url_for("materi", user_info=user_info))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("materi"))


@app.route("/transaksi/<materi_id>")
def transaksi(materi_id):
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            materi = db.materi.find_one({"_id": ObjectId(materi_id)})
            user_data = db.user.find_one({"username": payload["id"]}, {"_id": False})
            return render_template(
                "Transaction.html",
                user_info=user_info,
                materi=materi,
                user_data=user_data,
            )
        else:
            return redirect(url_for("login"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/create_transaction", methods=["POST"])
def create_transaction():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.materi.find_one({"username": payload["id"]})
        else:
            user_info = None
        if request.method == "POST":
            user_id = payload["id"]
            class_id = request.form.get("class_id")
            email = request.form.get("email")
            kartu_bank = request.form.get("card")
            penerima = request.form.get("penerima")
            profinsi = request.form.get("provinsi")
            kota = request.form.get("kota")
            kodepos = request.form.get("kodepos")
            harga = request.form.get("harga")
            kategori = request.form.get("category")
            nama_kelas = request.form.get("nama_kelas")
            username = request.form.get("username")

            new_transaction = {
                "user_id": user_id,
                "class_id": class_id,
                "transaction_date": datetime.now(),
                "status": False,
                "email": email,
                "kartu_bank": kartu_bank,
                "penerima": penerima,
                "profinsi": profinsi,
                "kota": kota,
                "postal_code": kodepos,
                "price": harga,
                "category": kategori,
                "class_name": nama_kelas,
                "username": username,
            }

            db.transactions.insert_one(new_transaction)
            return redirect(url_for("pembelian"))
        else:
            return redirect(url_for("login"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/accept_transaction/<transaction_id>", methods=["POST"])
@admin_required
def accept_transaction(transaction_id):
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            if user_info is None:
                return redirect(url_for("login"))
            username = user_info["username"]
            update = db.transactions.update_one(
                {"_id": ObjectId(transaction_id)}, {"$set": {"status": "True"}}
            )
            return redirect(url_for("admin_transaksi", username=username))
        else:
            return redirect(url_for("login"))

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/administrator/transaksi/<username>")
@admin_required
def admin_transaksi(username):
    token_receive = request.cookies.get("mytoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        status = username == payload["id"]
        user_info = db.user.find_one({"username": payload["id"]})
        user_data = db.user.find_one({"username": username}, {"_id": False})
        page = request.args.get("page", 1, type=int)
        transaction_per_page = 1000
        transactions = (
            db.transactions.find()
            .skip((page - 1) * transaction_per_page)
            .limit(transaction_per_page)
        )
        total_transaksi = db.transactions.count_documents({})
        if user_info is not None:
            return render_template(
                "administrator/AdminTransaction.html",
                status=status,
                user_data=user_data,
                user_info=user_info,
                is_admin=True,
                transaction_per_page=transaction_per_page,
                transactions=transactions,
                page=page,
                total_contacts=total_transaksi,
            )
        else:
            return redirect(url_for("login", msg="User not found"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login", msg="Token is invalid"))


@app.route("/pembelianku")
def pembelian():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            transactions = list(db.transactions.find({"user_id": payload["id"]}))
            materi = list(db.materi.find())
            frontend_classes = list(db.materi.find({"category": "Front-end"}))
            backend_classes = list(db.materi.find({"category": "Back-end"}))
            fullstack_classes = list(db.materi.find({"category": "Fullstack"}))
            all_classes = frontend_classes + backend_classes + fullstack_classes

            for transaction in transactions:
                transaction["class_id"] = str(transaction["class_id"])

            for materi in frontend_classes:
                materi["_id"] = str(materi["_id"])
                # _id = ObjectId("dsakjhldshajkdhjskahdjksahdjksa")
            for materi in backend_classes:
                materi["_id"] = str(materi["_id"])
            for materi in fullstack_classes:
                materi["_id"] = str(materi["_id"])
            return render_template(
                "pembelianku.html",
                user_info=user_info,
                transactions=transactions,
                materi=materi,
                frontend_classes=frontend_classes,
                backend_classes=backend_classes,
                fullstack_classes=fullstack_classes,
                all_classes=all_classes,
            )
        else:
            return redirect(url_for("login"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/mykonten")
def isikonten():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            transactions = list(db.transactions.find({"user_id": payload["id"]}))
            materi = list(db.materi.find())
            frontend_classes = list(db.materi.find({"category": "Front-end"}))
            backend_classes = list(db.materi.find({"category": "Back-end"}))
            fullstack_classes = list(db.materi.find({"category": "Fullstack"}))
            all_classes = frontend_classes + backend_classes + fullstack_classes

            for transaction in transactions:
                transaction["class_id"] = str(transaction["class_id"])

            for materi in frontend_classes:
                materi["_id"] = str(materi["_id"])
            for materi in backend_classes:
                materi["_id"] = str(materi["_id"])
            for materi in fullstack_classes:
                materi["_id"] = str(materi["_id"])
            return render_template(
                "MyContent.html",
                user_info=user_info,
                all_classes=all_classes,
                transactions=transactions,
                materi=materi,
                frontend_classes=frontend_classes,
                backend_classes=backend_classes,
                fullstack_classes=fullstack_classes,
            )
        else:
            return redirect(url_for("login"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))
@app.route("/mykonten2")
def isikonten2():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            transactions = list(db.transactions.find({"user_id": payload["id"]}))
            materi = list(db.materi.find())
            frontend_classes = list(db.materi.find({"category": "Front-end"}))
            backend_classes = list(db.materi.find({"category": "Back-end"}))
            fullstack_classes = list(db.materi.find({"category": "Fullstack"}))
            all_classes = frontend_classes + backend_classes + fullstack_classes

            for transaction in transactions:
                transaction["class_id"] = str(transaction["class_id"])

            for materi in frontend_classes:
                materi["_id"] = str(materi["_id"])
            for materi in backend_classes:
                materi["_id"] = str(materi["_id"])
            for materi in fullstack_classes:
                materi["_id"] = str(materi["_id"])
            return render_template(
                "MyContent1.html",
                user_info=user_info,
                all_classes=all_classes,
                transactions=transactions,
                materi=materi,
                frontend_classes=frontend_classes,
                backend_classes=backend_classes,
                fullstack_classes=fullstack_classes,
            )
        else:
            return redirect(url_for("login"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))
@app.route("/mykonten3")
def isikonten3():
    token_receive = request.cookies.get("mytoken")
    try:
        if token_receive:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
            user_info = db.user.find_one({"username": payload["id"]})
            transactions = list(db.transactions.find({"user_id": payload["id"]}))
            materi = list(db.materi.find())
            frontend_classes = list(db.materi.find({"category": "Front-end"}))
            backend_classes = list(db.materi.find({"category": "Back-end"}))
            fullstack_classes = list(db.materi.find({"category": "Fullstack"}))
            all_classes = frontend_classes + backend_classes + fullstack_classes

            for transaction in transactions:
                transaction["class_id"] = str(transaction["class_id"])

            for materi in frontend_classes:
                materi["_id"] = str(materi["_id"])
            for materi in backend_classes:
                materi["_id"] = str(materi["_id"])
            for materi in fullstack_classes:
                materi["_id"] = str(materi["_id"])
            return render_template(
                "MyContent2.html",
                user_info=user_info,
                all_classes=all_classes,
                transactions=transactions,
                materi=materi,
                frontend_classes=frontend_classes,
                backend_classes=backend_classes,
                fullstack_classes=fullstack_classes,
            )
        else:
            return redirect(url_for("login"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/delete_class", methods=["POST"])
@admin_required
def delete_class():
    try:
        token_receive = request.cookies.get("mytoken")
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.user.find_one({"username": payload["id"]})
        class_id = request.form.get("id")
        db.materi.delete_one({"_id": ObjectId(class_id)})
        return redirect(url_for("materi"))
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("login"))


@app.route("/delete_mentor", methods=["POST"])
@admin_required
def delete_mentor():
    try:
        token_receive = request.cookies.get("mytoken")
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.user.find_one({"username": payload["id"]})
        mentor_id = request.form.get("id")
        db.mentor.delete_one({"_id": ObjectId(mentor_id)})
        return jsonify({"status": "success"})

    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({"status": "error", "message": "Invalid token"})

    except Exception as e:
        app.logger.error(f"Error deleting mentor: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/like", methods=["POST"])
def like_post():
    token_receive = request.cookies.get("mytoken")
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    user_id = payload["id"]

    post_id = request.form.get("post_id")
    is_liked = request.form.get("is_liked") == "true"

    if not post_id:
        return jsonify({"success": False, "msg": "No post_id provided"}), 400

    post = db.forum.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"success": False, "msg": "No post found"}), 400

    if is_liked:
        new_likes_count = post["likes"] - 1
        db.forum.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"likes": new_likes_count}, "$pull": {"liked_by": user_id}},
        )
    else:
        if user_id in post.get("liked_by", []):
            return (
                jsonify({"success": False, "msg": "User has already liked this post"}),
                400,
            )
        new_likes_count = post["likes"] + 1
        db.forum.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"likes": new_likes_count}, "$push": {"liked_by": user_id}},
        )

    return jsonify({"success": True, "likes": new_likes_count})


@app.route("/get_like_status", methods=["GET"])
def get_like_status():
    post_id = request.args.get("post_id")
    token_receive = request.cookies.get("mytoken")
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
    user_id = payload["id"]  # Get the user ID from the session or a cookie

    post = db.forum.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"success": False, "msg": "No post found"}), 400

    is_liked = user_id in post.get("liked_by", [])
    return jsonify({"is_liked": is_liked})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5000, debug=True)
