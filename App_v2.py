from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
import sqlite3
from ecies.utils import generate_key
from ecies import encrypt, decrypt
import base64, os, sys
import hmac
import hashlib
import binascii
import random
import traceback
from cryptography.fernet import Fernet
from stegano import lsb
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders



app = Flask(__name__)
app.secret_key = 'a'

# ── EMAIL CREDENTIALS — change only here, applies everywhere ──
MAIL_FROM     = "indrayani.builds@gmail.com"   
MAIL_PASSWORD = "cwnlcdimfaipgqxy"             

# SQLite database file
DB_PATH = 'watermarkdata.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/ServerLogin')
def ServerLogin():
    return render_template('ServerLogin.html')

@app.route('/OwnerLogin')
def OwnerLogin():
    return render_template('OwnerLogin.html')

@app.route('/UserLogin')
def UserLogin():
    return render_template('UserLogin.html')

@app.route('/NewOwner')
def NewOwner():
    return render_template('NewOwner.html')

@app.route('/NewUser')
def NewUser():
    return render_template('NewUser.html')

@app.route('/PKGLogin')
def PKGLogin():
    return render_template('PKGLogin.html')

@app.route("/serverlogin", methods=['GET', 'POST'])
def serverlogin():
    if request.method == 'POST':
        if request.form['uname'] == 'server' and request.form['password'] == 'server':
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM ownertb WHERE status='waiting'")
            data = cur.fetchall()
            
            cur.execute("SELECT * FROM ownertb WHERE status='Active'")
            data1 = cur.fetchall()
            conn.close()
            return render_template('ServerHome.html', data=data, data1=data1)
        else:
            flash('Username or Password is wrong')
            return render_template('ServerLogin.html')

@app.route("/ServerHome")
def ServerHome():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ownertb WHERE status='waiting'")
    data = cur.fetchall()
    
    cur.execute("SELECT * FROM ownertb WHERE status='Active'")
    data1 = cur.fetchall()
    conn.close()
    return render_template('ServerHome.html', data=data, data1=data1)

@app.route("/SUserInfo")
def SUserInfo():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM regtb WHERE status='waiting'")
    data = cur.fetchall()
    
    cur.execute("SELECT * FROM regtb WHERE status='Active'")
    data1 = cur.fetchall()
    conn.close()
    return render_template('SUserInfo.html', data=data, data1=data1)

@app.route("/Approved11")
def Approved11():
    id = request.args.get('lid')
    email = request.args.get('email')
    loginkey = random.randint(1111, 9999)

    # ── 1. Save to DB FIRST so approval is never lost even if email fails ──
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE regtb SET status='Active', LoginKey=? WHERE id=?", (str(loginkey), id))
    conn.commit()

    # ── 2. Send email — wrapped so a mail error never breaks the approval ──
    try:
        message = "User Login Key :" + str(loginkey)
        sendmail(email, message)
    except Exception as e:
        print(f"[Approved11] Email failed for {email}: {e}")
        flash('User approved but email could not be sent. Login key: ' + str(loginkey))

    cur.execute("SELECT * FROM regtb WHERE status='waiting'")
    data = cur.fetchall()

    cur.execute("SELECT * FROM regtb WHERE status='Active'")
    data1 = cur.fetchall()
    conn.close()
    return render_template('SUserInfo.html', data=data, data1=data1)

@app.route("/Reject11")
def Reject11():
    id = request.args.get('lid')
    email = request.args.get('email')

    # ── 1. Save to DB FIRST ──
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE regtb SET status='reject' WHERE id=?", (id,))
    conn.commit()

    # ── 2. Send email safely ──
    try:
        message = "Your Request Rejected"
        sendmail(email, message)
    except Exception as e:
        print(f"[Reject11] Email failed for {email}: {e}")

    cur.execute("SELECT * FROM regtb WHERE status='waiting'")
    data = cur.fetchall()

    cur.execute("SELECT * FROM regtb WHERE status!='waiting'")
    data1 = cur.fetchall()
    conn.close()
    return render_template('SUserInfo.html', data=data, data1=data1)

@app.route('/SFileInfo')
def SFileInfo():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM filetb")
    data1 = cur.fetchall()
    conn.close()
    return render_template('SFileInfo.html', data=data1)

@app.route('/SRequestInfo')
def SRequestInfo():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM userfiletb")
    data1 = cur.fetchall()
    conn.close()
    return render_template('SRequestInfo.html', data=data1)

@app.route("/Approved")
def Approved():
    id = request.args.get('lid')
    email = request.args.get('email')
    loginkey = random.randint(1111, 9999)

    # ── 1. Save to DB FIRST ──
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE ownertb SET status='Active', LoginKey=? WHERE id=?", (str(loginkey), id))
    conn.commit()

    # ── 2. Send email safely ──
    try:
        message = "Owner Login Key :" + str(loginkey)
        sendmail(email, message)
    except Exception as e:
        print(f"[Approved] Email failed for {email}: {e}")
        flash('Owner approved but email could not be sent. Login key: ' + str(loginkey))

    cur.execute("SELECT * FROM ownertb WHERE status='waiting'")
    data = cur.fetchall()

    cur.execute("SELECT * FROM ownertb WHERE status='Active'")
    data1 = cur.fetchall()
    conn.close()
    return render_template('ServerHome.html', data=data, data1=data1)

@app.route("/Reject")
def Reject():
    id = request.args.get('lid')
    email = request.args.get('email')

    # ── 1. Save to DB FIRST ──
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE ownertb SET status='reject' WHERE id=?", (id,))
    conn.commit()

    # ── 2. Send email safely ──
    try:
        message = "Your Request Rejected"
        sendmail(email, message)
    except Exception as e:
        print(f"[Reject] Email failed for {email}: {e}")

    cur.execute("SELECT * FROM ownertb WHERE status='waiting'")
    data = cur.fetchall()

    cur.execute("SELECT * FROM ownertb WHERE status!='waiting'")
    data1 = cur.fetchall()
    conn.close()
    return render_template('ServerHome.html', data=data, data1=data1)

@app.route("/newowner", methods=['GET', 'POST'])
def newowner():
    if request.method == 'POST':
        uname = request.form['uname']
        mobile = request.form['mobile']
        email = request.form['email']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ownertb WHERE username=?", (username,))
        data = cur.fetchone()
        if data is None:
            cur.execute(
                "INSERT INTO ownertb (uname, mobile, email, address, username, password, status, LoginKey) VALUES (?, ?, ?, ?, ?, ?, 'waiting', '')",
                (uname, mobile, email, address, username, password)
            )
            conn.commit()
            conn.close()
            flash('Record Saved!')
            return render_template('NewOwner.html')
        else:
            conn.close()
            flash('Already Register This UserName!')
            return render_template('NewOwner.html')

@app.route("/ownerlogin", methods=['GET', 'POST'])
def ownerlogin():
    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['password']
        loginkey = request.form['loginkey']
        session['oname'] = request.form['uname']
        session['lk'] = loginkey

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ownertb WHERE username=? AND password=?", (username, password))
        data = cur.fetchone()
        if data is None:
            conn.close()
            flash('Username or Password is wrong')
            return render_template('OwnerLogin.html')
        else:
            Status = data['status']
            lkey = data['LoginKey']
            print(lkey)
            if Status == "waiting":
                conn.close()
                flash('Waiting For Server Approved!')
                return render_template('OwnerLogin.html')
            else:
                if lkey == loginkey:
                    cur.execute("SELECT * FROM ownertb WHERE username=?", (session['oname'],))
                    data1 = cur.fetchall()
                    conn.close()
                    return render_template('OwnerHome.html', data=data1)
                else:
                    conn.close()
                    flash('Login Key Incorrect')
                    return render_template('OwnerLogin.html')

@app.route('/OwnerHome')
def OwnerHome():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ownertb WHERE username=?", (session['oname'],))
    data1 = cur.fetchall()
    conn.close()
    return render_template('OwnerHome.html', data=data1)

@app.route("/newuser", methods=['GET', 'POST'])
def newuser():
    if request.method == 'POST':
        uname = request.form['uname']
        mobile = request.form['mobile']
        email = request.form['email']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM regtb WHERE username=?", (username,))
        data = cur.fetchone()
        if data is None:
            cur.execute(
                "INSERT INTO regtb (uname, mobile, email, address, username, password, status, LoginKey) VALUES (?, ?, ?, ?, ?, ?, 'waiting', '')",
                (uname, mobile, email, address, username, password)
            )
            conn.commit()
            conn.close()
            flash('Record Saved!')
            return render_template('NewUser.html')
        else:
            conn.close()
            flash('Already Register This UserName!')
            return render_template('NewUser.html')

@app.route('/OwnerFileUpload')
def OwnerFileUpload():
    return render_template('OwnerFileUpload.html', oname=session['oname'])

def create_sha256_signature(key, message):
    byte_key = binascii.unhexlify(key)
    message = message.encode()
    return hmac.new(byte_key, message, hashlib.sha256).hexdigest().upper()

@app.route("/owfileupload", methods=['GET', 'POST'])
def owfileupload():
    if request.method == 'POST':
        oname = session['oname']
        info = request.form['info']
        file = request.files['file']
        fnew = random.randint(111, 999)
        savename = str(fnew) + file.filename

        file.save("static/upload/" + savename)

        secp_k = generate_key()
        privhex = secp_k.to_hex()
        pubhex = secp_k.public_key.format(True).hex()

        filepath = "./static/upload/" + savename
        head, tail = os.path.split(filepath)

        newfilepath1 = './static/Encrypt/' + str(tail)
        newfilepath2 = './static/Decrypt/' + str(tail)

        data = 0
        with open(filepath, "rb") as File:
            data = base64.b64encode(File.read())

        print("Private_key:", privhex, "\nPublic_key:", pubhex, "Type: ", type(privhex))

        if privhex == 'null':
            flash('Please Choose Another File, file corrupted!')
            return render_template('OwnerFileUpload.html')

        else:
            print("Binary of the file:", data)
            encrypted_secp = encrypt(pubhex, data)
            print("Encrypted binary:", encrypted_secp)

            with open(newfilepath1, "wb") as EFile:
                EFile.write(base64.b64encode(encrypted_secp))

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM filetb")
            data2 = cur.fetchone()

            if data2:
                cur.execute("SELECT MAX(id) FROM filetb")
                da = cur.fetchone()
                if da:
                    d = da[0]
                    print(d)

                cur.execute("SELECT * FROM filetb WHERE id=?", (d,))
                data1 = cur.fetchone()
                if data1:
                    hash1 = data1['hash1']
                    num1 = random.randrange(1111, 9999)
                    hash2 = create_sha256_signature("E49756B4C8FAB4E48222A3E7F3B97CC3", str(num1))

                    cur.execute(
                        "INSERT INTO filetb (OwnerName, FileInfo, FileName, pubkey, privkey, hash1, hash2) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (oname, info, savename, pubhex, privhex, hash1, hash2)
                    )
                    conn.commit()
                    conn.close()
                    flash('File Upload And Encrypt Successfully')
                    return render_template('OwnerFileUpload.html', pkey=privhex, oname=oname)
            else:
                hash1 = '0'
                num1 = random.randrange(1111, 9999)
                hash2 = create_sha256_signature("E49756B4C8FAB4E48222A3E7F3B97CC3", str(num1))
                cur.execute(
                    "INSERT INTO filetb (OwnerName, FileInfo, FileName, pubkey, privkey, hash1, hash2) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (oname, info, savename, pubhex, privhex, hash1, hash2)
                )
                conn.commit()
                conn.close()
                flash('File Upload And Encrypt Successfully')
                return render_template('OwnerFileUpload.html', pkey=privhex, oname=oname)

@app.route("/owfileupload1", methods=['GET', 'POST'])
def owfileupload1():
    if request.method == 'POST':
        info = request.form['info']
        file = request.files['file']
        print(file)

        if file and file.filename.lower().endswith(('png', 'jpg', 'jpeg', 'gif')):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            print('pass')
            return render_template('OwnerFileUpload.html')
        else:
            return "Invalid file type. Only images are allowed.", 400

@app.route('/OwnerFileInfo')
def OwnerFileInfo():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM filetb WHERE OwnerName=?", (session['oname'],))
    data1 = cur.fetchall()
    conn.close()
    return render_template('OwnerFileInfo.html', data=data1)

@app.route("/ODownload")
def ODownload():
    fid = request.args.get('fid')

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM filetb WHERE id=?", (fid,))
    data = cur.fetchone()
    if data:
        prkey = data['privkey']
        fname = data['FileName']
    else:
        conn.close()
        return 'Incorrect username / password !'

    privhex = prkey

    filepath = "./static/Encrypt/" + fname
    head, tail = os.path.split(filepath)

    newfilepath1 = './static/Encrypt/' + str(tail)
    newfilepath2 = './static/Decrypt/' + str(tail)

    data = 0
    with open(newfilepath1, "rb") as File:
        data = base64.b64decode(File.read())

    print(data)
    decrypted_secp = decrypt(privhex, data)
    print("\nDecrypted:", decrypted_secp)
    with open(newfilepath2, "wb") as DFile:
        DFile.write(base64.b64decode(decrypted_secp))

    conn.close()
    return send_file(newfilepath2, as_attachment=True)

@app.route("/OwnerFileApproved")
def OwnerFileApproved():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM userfiletb WHERE status='waiting' AND OwnerName=?", (session['oname'],))
    data = cur.fetchall()
    
    cur.execute("SELECT * FROM userfiletb WHERE status='Approved' AND OwnerName=?", (session['oname'],))
    data1 = cur.fetchall()
    conn.close()
    return render_template('OwnerFileApproved.html', data=data, data1=data1)

@app.route("/OApproved")
def OApproved():
    rid = request.args.get('rid')
    fid = request.args.get('fid')

    session["fid"] = fid
    session["rid"] = rid

    return render_template('Hide.html')

@app.route("/hide", methods=['GET', 'POST'])
def hide():
    if request.method == 'POST':
        Unhidekey = request.form['hkey']
        file = request.files['file']
        fnew = random.randint(111, 999)
        savename = str(fnew) + file.filename
        file.save("static/upload/" + savename)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM userfiletb WHERE id=?", (session["rid"],))
        data = cur.fetchone()
        if data:
            prkey = data['prkey']
            UserName = data['Username']
        else:
            conn.close()
            return 'Incorrect username / password !'

        cur.execute("SELECT * FROM regtb WHERE UserName=?", (UserName,))
        data1 = cur.fetchone()
        if data1:
            session["email"] = data1['email']
            llkey = data1['LoginKey']
        else:
            conn.close()
            return 'Incorrect username / password !'

        message = llkey + ',' + prkey
        key = Fernet.generate_key()
        Decryptkey = key.decode()
        fernet = Fernet(key)
        encMessage = fernet.encrypt(message.encode())

        print("original string: ", message)
        print("encrypted string: ", encMessage)

        secret = lsb.hide("./static/upload/" + savename, encMessage.decode())
        pathname, extension = os.path.splitext("./static/upload/" + savename)
        filename = pathname.split('/')
        imageName = filename[-1] + ".png"
        secret.save("./static/Encode/" + imageName)

        secp_k = generate_key()
        privhex = secp_k.to_hex()
        pubhex = secp_k.public_key.format(True).hex()

        filepath = "./static/Encode/" + imageName
        head, tail = os.path.split(filepath)
        newfilepath1 = './static/Encrypt/' + str(tail)

        data = 0
        with open(filepath, "rb") as File:
            data = base64.b64encode(File.read())

        print("Private_key:", privhex, "\nPublic_key:", pubhex, "Type: ", type(privhex))
        encrypted_secp = encrypt(pubhex, data)

        with open(newfilepath1, "wb") as EFile:
            EFile.write(base64.b64encode(encrypted_secp))

        imagedkey = privhex

        cur.execute(
            "UPDATE userfiletb SET Status='Approved', ImageName=?, Imagedkey=?, Unhidekey=?, Decryptkey=? WHERE id=?",
            (imageName, imagedkey, Unhidekey, Decryptkey, session["rid"])
        )
        conn.commit()
        conn.close()

        mailmsg = (
            f"Request Id{session['rid']}\n"
            f"image decrypt key:{imagedkey}\n"
            f"Unhidekey:{Unhidekey}\n"
            f"Decryptkey:{Decryptkey}"
        )

        print(f"\n[hide] Sending email to: {session['email']}")
        print(f"[hide] imagedkey={imagedkey}")
        print(f"[hide] Unhidekey={Unhidekey}")
        print(f"[hide] Decryptkey={Decryptkey}")

        # ── Send email with encrypted image attached ──
        email_sent = False
        try:
            sendmail_with_attachment(
                Mailid          = session["email"],
                subject         = "Cloud Security",
                message         = mailmsg,
                attachment_path = "./static/Encrypt/" + imageName,
                attachment_name = imageName
            )
            email_sent = True
            print(f"[hide] Email sent OK to {session['email']}")
        except Exception:
            print(f"[hide] !! EMAIL FAILED — full traceback below !!")
            print(traceback.format_exc())

        if email_sent:
            flash('Key Hide and encrypt to Send to User')
        else:
            flash(
                f"File approved but email could not be sent — give these keys to the user manually:\n"
                f"Image Decrypt Key: {imagedkey} | "
                f"Unhide Key: {Unhidekey} | "
                f"Decrypt Key: {Decryptkey}"
            )

        return OwnerFileApproved()

@app.route("/UDownload")
def UDownload():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM userfiletb WHERE status='waiting' AND username=?", (session['uname'],))
    data = cur.fetchall()
    
    cur.execute("SELECT * FROM userfiletb WHERE status='Approved' AND username=?", (session['uname'],))
    data1 = cur.fetchall()
    conn.close()
    return render_template('UDownload.html', data=data, data1=data1)

@app.route("/userdownload")
def userdownload():
    ufid = request.args.get('ufid')
    session["ufid"] = ufid
    return render_template('UnHide.html')

@app.route("/unhide", methods=['GET', 'POST'])
def unhide():
    if request.method == 'POST':
        idk = request.form['idk']
        uhk = request.form['uhk']
        dfk = request.form['dfk']
        file = request.files['file']
        file.save("static/Uupload/" + file.filename)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM userfiletb WHERE id=? AND Imagedkey=?", (session["ufid"], idk))
        data = cur.fetchone()
        if data:
            privhex = idk
            filepath = "./static/Uupload/" + file.filename
            head, tail = os.path.split(filepath)
            newfilepath1 = './static/Uupload/' + str(tail)
            newfilepath2 = './static/Decode/' + str(tail)

            data = 0
            with open(newfilepath1, "rb") as File:
                data = base64.b64decode(File.read())

            print(data)
            decrypted_secp = decrypt(privhex, data)
            print("\nDecrypted:", decrypted_secp)
            with open(newfilepath2, "wb") as DFile:
                DFile.write(base64.b64decode(decrypted_secp))

            cur.execute("SELECT * FROM userfiletb WHERE id=? AND Unhidekey=?", (session["ufid"], uhk))
            data = cur.fetchone()
            if data:
                clear_message = lsb.reveal(newfilepath2)
                print(clear_message)

                cur.execute("SELECT * FROM userfiletb WHERE id=? AND Decryptkey=?", (session["ufid"], dfk))
                data = cur.fetchone()
                if data:
                    fname = data['FileName']
                    key = dfk.encode()
                    print(key)
                    fernet = Fernet(key)
                    encMessage = clear_message.encode()
                    decMessage = fernet.decrypt(encMessage).decode()
                    print("decrypted string: ", decMessage)

                    splitted_string = decMessage.split(',')
                    print(splitted_string[0])
                    print(splitted_string[1])

                    if splitted_string[0] == session['lkey']:
                        privhex = splitted_string[1]
                        filepath = "./static/Encrypt/" + fname
                        head, tail = os.path.split(filepath)
                        newfilepath1 = './static/Encrypt/' + str(tail)
                        newfilepath2 = './static/Decrypt/' + str(tail)

                        data = 0
                        with open(newfilepath1, "rb") as File:
                            data = base64.b64decode(File.read())

                        print(data)
                        decrypted_secp = decrypt(privhex, data)
                        print("\nDecrypted:", decrypted_secp)
                        with open(newfilepath2, "wb") as DFile:
                            DFile.write(base64.b64decode(decrypted_secp))

                        conn.close()
                        return send_file(newfilepath2, as_attachment=True)
                    else:
                        conn.close()
                        alert = 'User key Incorrect!'
                        return render_template('goback.html', data=alert)
                else:
                    conn.close()
                    alert = 'Decrypt file key Incorrect!'
                    return render_template('goback.html', data=alert)
            else:
                conn.close()
                alert = 'Image unhide key Incorrect!'
                return render_template('goback.html', data=alert)
        else:
            conn.close()
            alert = 'Image decrypt key Incorrect!'
            return render_template('goback.html', data=alert)

@app.route("/userlogin", methods=['GET', 'POST'])
def userlogin():
    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['password']
        loginkey = request.form['loginkey']
        session['uname'] = request.form['uname']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM regtb WHERE username=? AND password=?", (username, password))
        data = cur.fetchone()
        if data is None:
            conn.close()
            flash('Username or Password is wrong')
            return render_template('UserLogin.html')
        else:
            Status = data['status']
            lkey = data['LoginKey']
            session['lkey'] = data['LoginKey']
            if Status == "waiting":
                conn.close()
                flash('Waiting For Server Approved!')
                return render_template('UserLogin.html')
            else:
                if lkey == loginkey:
                    cur.execute("SELECT * FROM regtb WHERE username=?", (session['uname'],))
                    data1 = cur.fetchall()
                    conn.close()
                    flash('Login Successfully')
                    return render_template('UserHome.html', data=data1)
                else:
                    conn.close()
                    flash('Login Key Incorrect')
                    return render_template('UserLogin.html')

def loginvales1():
    uname = session['uname']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM regtb WHERE username=?", (uname,))
    data = cur.fetchone()
    if data:
        Email = data['email']
        Phone = data['mobile']
    else:
        conn.close()
        return 'Incorrect username / password !'
    conn.close()
    return uname, Email, Phone

@app.route("/facelogin")
def facelogin():
    uname = session['uname']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM temptb WHERE username=?", (uname,))
    data = cur.fetchone()
    if data is None:
        conn.close()
        alert = 'Face is wrong'
        return render_template('goback.html', data=alert)
    else:
        cur.execute("SELECT * FROM regtb WHERE username=?", (session['uname'],))
        data1 = cur.fetchall()
        conn.close()
        flash('Login Successfully')
        return render_template('UserHome.html', data=data1)

@app.route('/UserHome')
def UserHome():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM regtb WHERE username=?", (session['uname'],))
    data1 = cur.fetchall()
    conn.close()
    return render_template('UserHome.html', data=data1)

@app.route('/USearch')
def USearch():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM filetb")
    data1 = cur.fetchall()
    conn.close()
    return render_template('USearch.html', data=data1)

@app.route("/search", methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        sear = request.form['sear']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM filetb WHERE ownername LIKE ? OR FileInfo LIKE ? OR FileName LIKE ?",
            (f'%{sear}%', f'%{sear}%', f'%{sear}%')
        )
        data1 = cur.fetchall()
        conn.close()
        return render_template('USearch.html', data=data1)

@app.route("/SendKeyRequest")
def SendKeyRequest():
    fid = request.args.get('fid')
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM filetb WHERE id=?", (fid,))
    data = cur.fetchone()
    if data:
        oname = data['OwnerName']
        fname = data['FileName']
        prkey = data['privkey']
    else:
        conn.close()
        return 'Incorrect username / password !'

    cur.execute(
        "INSERT INTO userfiletb (fid, OwnerName, FileName, prkey, Username, status) VALUES (?, ?, ?, ?, ?, 'waiting')",
        (fid, oname, fname, prkey, session['uname'])
    )
    conn.commit()

    cur.execute("SELECT * FROM userfiletb WHERE status='waiting' AND username=?", (session['uname'],))
    data = cur.fetchall()

    cur.execute("SELECT * FROM userfiletb WHERE status='Approved' AND username=?", (session['uname'],))
    data1 = cur.fetchall()
    conn.close()
    return render_template('UDownload.html', data=data, data1=data1)

def sendmail(Mailid, message):
    msg = MIMEMultipart()
    msg['From']    = MAIL_FROM
    msg['To']      = Mailid
    msg['Subject'] = "Alert"
    msg.attach(MIMEText(message, 'plain'))
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(MAIL_FROM, MAIL_PASSWORD)
    s.sendmail(MAIL_FROM, Mailid, msg.as_string())
    s.quit()

def sendmail_with_attachment(Mailid, subject, message, attachment_path, attachment_name):
    """Send an email with a file attachment. Uses the central MAIL_FROM / MAIL_PASSWORD."""
    msg = MIMEMultipart()
    msg['From']    = MAIL_FROM
    msg['To']      = Mailid
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))

    with open(attachment_path, "rb") as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{attachment_name}"')
    msg.attach(part)

    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(MAIL_FROM, MAIL_PASSWORD)
    s.sendmail(MAIL_FROM, Mailid, msg.as_string())
    s.quit()

if __name__ == '__main__':
    # Create the SQLite database and tables if they don't exist
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ownertb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uname TEXT,
            mobile TEXT,
            email TEXT,
            address TEXT,
            username TEXT,
            password TEXT,
            status TEXT,
            LoginKey TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS regtb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uname TEXT,
            mobile TEXT,
            email TEXT,
            address TEXT,
            username TEXT,
            password TEXT,
            status TEXT,
            LoginKey TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS filetb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            OwnerName TEXT,
            FileInfo TEXT,
            FileName TEXT,
            pubkey TEXT,
            privkey TEXT,
            hash1 TEXT,
            hash2 TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS userfiletb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fid TEXT,
            OwnerName TEXT,
            FileName TEXT,
            prkey TEXT,
            Username TEXT,
            status TEXT,
            ImageName TEXT,
            Imagedkey TEXT,
            Unhidekey TEXT,
            Decryptkey TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS temptb (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT
        )
    ''')
    conn.commit()
    conn.close()
    app.run(debug=True, use_reloader=True)