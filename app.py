from flask import Flask, request, render_template, jsonify, send_file, redirect, session, url_for
from datetime import datetime
from flask_cors import CORS
import pandas as pd
from io import BytesIO
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from functools import partial
import subprocess, time, requests, json, os, pytz, sys, bcrypt, psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import errors as pg_errors # Import PostgreSQL specific errors
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback-secret")
CORS(app)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False  # True ถ้า deploy บน HTTPS จริง
)

if getattr(sys, 'frozen', False):
    # ถูกรันจาก .exe ที่ถูก bundle โดย PyInstaller
    BASE_DIR = sys._MEIPASS
else:
    # ถูกรันจาก .py ปกติ
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# NGROK_PATH = "ngrok.exe"
# PORT = 5000
PORT = int(os.environ.get('PORT', 5000))
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
if not LINE_CHANNEL_ACCESS_TOKEN:
    raise Exception("LINE_CHANNEL_ACCESS_TOKEN environment variable is not set.")

DATABASE_URL = os.environ.get('DATABASE_URL')
if not DATABASE_URL:
    raise Exception("DATABASE_URL environment variable is not set.")

# ✅ พิมพ์เช็คว่าค่าโหลดจาก .env สำเร็จไหม
# print("✅ Loaded DATABASE_URL:", DATABASE_URL[:30] + "...")
# print("✅ Loaded LINE_CHANNEL_ACCESS_TOKEN:", LINE_CHANNEL_ACCESS_TOKEN[:10] + "...")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)
    
@app.route('/api/users')
def get_users():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)  # ใช้ RealDictCursor เพื่อให้ได้ dict แทน tuple
        cur.execute('SELECT id, username, role FROM users_login;')
        users = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- Login Guard ----------
@app.before_request
def require_login():
    allowed_routes = ['login', 'static', 'webhook', 'callback']  # เพิ่ม 'webhook', 'callback' เพื่อให้ LINE เข้าถึงได้
    if 'username' not in session and request.endpoint not in allowed_routes:
        return redirect(url_for('login'))

# ---------- หน้า Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_input = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        # เปลี่ยน ? เป็น %s สำหรับ PostgreSQL
        cursor.execute("SELECT password, role FROM Users_Login WHERE username = %s", (username,))
        row = cursor.fetchone()
        conn.close()

        if row:
            hashed_password, role = row
            # bcrypt.checkpw ต้องการ bytes สำหรับทั้งสอง arguments
            if bcrypt.checkpw(password_input.encode('utf-8'), hashed_password.encode('utf-8')):
                session['username'] = username
                session['role'] = role
                return redirect(url_for('form'))  # 🔁 เปลี่ยนไปหน้า form ทันที
        return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

font_path = resource_path("fonts/THSarabunNew.ttf")
pdfmetrics.registerFont(TTFont('THSarabunNew', font_path))

font_bold_path = resource_path("fonts/THSarabunNew-Bold.ttf")
pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', font_bold_path))
# NGROK_PATH = resource_path("ngrok.exe")

def save_or_update_user(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # ตรวจสอบว่ามี user_id ใน DB หรือยัง
        cur.execute("SELECT * FROM Users WHERE userId = %s", (user_id,))
        existing = cur.fetchone()

        if existing:
            print(f"ℹ️ userId {user_id} มีอยู่แล้วในฐานข้อมูล")
        else:
            # ดึงข้อมูลโปรไฟล์จาก LINE
            profile = get_user_profile(user_id)
            if profile:
                display_name = profile.get("displayName", "")
                picture_url = profile.get("pictureUrl", "")

                cur.execute("""
                    INSERT INTO Users (userId, displayName, pictureUrl)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (userId) DO NOTHING
                """, (user_id, display_name, picture_url))
                conn.commit()
                print(f"✅ บันทึก userId ใหม่: {user_id}")
            else:
                print("❌ ไม่สามารถดึง profile จาก LINE ได้")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ save_or_update_user error: {e}")
 
def get_group_profile(group_id):
    url = f'https://api.line.me/v2/bot/group/{group_id}/summary'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}'
    }
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        return res.json()  # จะได้ dict ที่มี groupName, pictureUrl
    else:
        print("❌ Error fetching group profile:", res.status_code, res.text)
        return None

def store_group_id(group_id, group_name=None, group_picture=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # ใช้ %s สำหรับ PostgreSQL และเปลี่ยน COUNT(*) เป็น EXISTS
        cursor.execute("SELECT EXISTS(SELECT 1 FROM Groups WHERE group_id = %s)", (group_id,))
        exists = cursor.fetchone()[0] # [0] เพื่อดึงค่า boolean ออกมา

        group_name = group_name or ''
        group_picture = group_picture or ''
        if not exists: # ถ้าไม่มีอยู่แล้ว
            cursor.execute(
                "INSERT INTO Groups (group_id, group_name, group_picture) VALUES (%s, %s, %s)",
                (group_id, group_name, group_picture)
            )
        else:
            cursor.execute(
                "UPDATE Groups SET group_name = %s, group_picture = %s WHERE group_id = %s",
                (group_name, group_picture, group_id)
            )
        conn.commit()
    except Exception as e:
        print("❌ บันทึก group_id ผิดพลาด:", e)
    finally:
        cursor.close()
        conn.close()

def get_user_profile(user_id):
    url = f"https://api.line.me/v2/bot/profile/{user_id}"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ ดึง profile ไม่ได้: {response.status_code} - {response.text}")
        return None

def send_line_message(user_id, message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    resp = requests.post(url, headers=headers, json=data)
    print("📤 ส่ง LINE:", resp.status_code, resp.text)
    return resp.status_code == 200

def send_line_message_to_group(group_id, message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "to": group_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    resp = requests.post(url, headers=headers, json=data)
    print("📤 ส่ง LINE group:", resp.status_code, resp.text)
    return resp.status_code == 200

# --- แก้ฟังก์ชัน send_line_message_to_all ให้ดึง userId จาก DB แทนไฟล์ ---
def send_line_message_to_all(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT userId FROM Users")
        user_ids = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        print("❌ send_line_message_to_all error:", e)
        user_ids = []
    finally:
        cursor.close()
        conn.close()

    for uid in user_ids:
        send_line_message(uid, message)

@app.route('/get_user_ids', methods=['GET'])
def get_user_ids():
    conn = get_db_connection()
    # ใช้ RealDictCursor เพื่อให้ได้ dict ที่มีชื่อคอลัมน์เป็น key
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT userId, displayName, pictureUrl FROM Users")
    rows = cursor.fetchall()
    conn.close()
    # เนื่องจากใช้ RealDictCursor แล้ว ไม่ต้องแปลงเป็น dict อีก
    users = [{'userId': row['userid'], 'displayName': row['displayname'], 'pictureUrl': row['pictureurl']} for row in rows] # PostgreSQL จะแปลงชื่อคอลัมน์เป็น lowercase
    return jsonify({'users': users})

@app.route('/send_line_to_selected', methods=['POST'])
def send_line_notify():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'success': False, 'error': 'No JSON received'}), 400

        user_ids = data.get('user_ids', [])
        group_ids = data.get('group_ids', [])
        row_ids = data.get('ids', [])
        form_type = data.get('formType')

        print('user_ids:', user_ids)
        print('group_ids:', group_ids)
        print('row_ids:', row_ids)
        print('formType:', form_type)

        if not row_ids:
            return jsonify({'success': False, 'error': 'No row_ids provided to send LINE message.'}), 400

        # ดึงข้อมูลจาก Transports เฉพาะรายการที่เลือก
        # ใช้ %s สำหรับ PostgreSQL parameters และปรับเปลี่ยน IN clause
        placeholders = ','.join(['%s'] * len(row_ids))
        conn = get_db_connection()
        # ใช้ RealDictCursor เพื่อให้เข้าถึงข้อมูลด้วยชื่อคอลัมน์ได้ง่ายขึ้น
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = f"SELECT * FROM Transports WHERE ID IN ({placeholders}) AND FormType = %s"
        cursor.execute(query, (*row_ids, form_type))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in rows:
            # PostgreSQL มักจะคืนชื่อคอลัมน์เป็น lowercase
            if form_type.lower() == "domestic": # ใช้ .lower() เพื่อความชัวร์
                msg = (
                    f"ทะเบียน: {row.get('plate', '-')}\n"
                    f"ชื่อ: {row.get('name', '-')}\n"
                    f"ผู้ขนส่ง: {row.get('sender', '-')}\n"
                    f"ลูกค้า: {row.get('customer', '-')}\n"
                    f"Delivery Date: {row.get('deliverydate', '-')}\n"
                    f"เริ่มโหลดสินค้า: {row.get('startload', '-')}\n"
                    f"โหลดสินค้าเสร็จ: {row.get('doneload', '-')}\n"
                    f"เวลาส่งสินค้า: {row.get('deliverytime', '-')}\n"
                    f"Status: {row.get('status', '-')}\n"
                    f"เวลาส่งถึงลูกค้า: {row.get('deliverytimetocustomer', '-')}\n"
                    f"หมายเหตุ: {row.get('remark', '-')}\n"
                    f"---------------------------"
                )
            elif form_type.lower() == "export": # ใช้ .lower() เพื่อความชัวร์
                msg = (
                    f"PI: {row.get('pi', '-')}\n"
                    f"ทะเบียน: {row.get('plate', '-')}\n"
                    f"ชื่อ: {row.get('name', '-')}\n"
                    f"ผู้ขนส่ง: {row.get('sender', '-')}\n"
                    f"ประเทศ: {row.get('customer', '-')}\n"
                    f"ถึงโรงงาน: {row.get('queuetime', '-')}\n"
                    f"เริ่มตั้ง: {row.get('startdeliver', '-')}\n"
                    f"ตั้งเสร็จ: {row.get('donedeliver', '-')}\n"
                    f"เข้าช่องโหลด: {row.get('truckloadin', '-')}\n"
                    f"เริ่มโหลด: {row.get('startload', '-')}\n"
                    f"โหลดเสร็จ: {row.get('doneload', '-')}\n"
                    f"หมายเหตุ: {row.get('remark', '-')}\n"
                    f"---------------------------"
                )
            else:
                continue

            # เตรียมข้อความพร้อม prefix
            short_message = f"[WICE TRANSPORT - {form_type.upper()}]\n\n" + msg[:950]  # Limit for LINE push

            # ส่งไปยัง user แต่ละคน
            for uid in user_ids:
                success = send_line_message(uid, short_message)
                print(f"ส่งหา {uid}: {'✅ สำเร็จ' if success else '❌ ล้มเหลว'}")

            # ส่งไปยัง group แต่ละกลุ่ม
            for gid in group_ids:
                success = send_line_message_to_group(gid, short_message)
                print(f"ส่งหา {gid}: {'✅ สำเร็จ' if success else '❌ ล้มเหลว'}")

        return jsonify({'success': True})

    except Exception as e:
        print("❌ Error sending LINE message:", e)
        return jsonify({'success': False, 'error': str(e)}), 400

def send_welcome_message(reply_token):
    url = 'https://api.line.me/v2/bot/message/reply'
    headers = {
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "replyToken": reply_token,
        "messages": [
            {
                "type": "text",
                "text": "สวัสดีครับ! ขอบคุณที่เชิญบอทเข้ากลุ่มครับ"
            }
        ]
    }
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 200:
        print("✅ ส่งข้อความทักทายสำเร็จ")
    else:
        print(f"❌ ส่งข้อความทักทายไม่สำเร็จ: {resp.status_code} {resp.text}")

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    events = json.loads(body).get('events', [])

    for event in events:
        event_type = event.get('type')
        source = event.get('source', {})

        if event_type == 'message':
            user_id = source.get('userId')
            print("👤 USER ID:", user_id)
            save_or_update_user(user_id)

        elif event_type == 'join' and source.get('type') == 'group':
            group_id = source.get('groupId')
            print("✅ บอทถูกเชิญเข้ากลุ่ม groupId:", group_id)

            group_profile = get_group_profile(group_id)
            group_name = group_profile.get('groupName') if group_profile else None
            group_picture = group_profile.get('pictureUrl') if group_profile else None

            store_group_id(group_id, group_name, group_picture)

        elif event_type == 'leave' and source.get('type') == 'group':
            group_id = source.get('groupId')
            print(f"❌ บอทถูกลบออกจากกลุ่ม groupId: {group_id}")

    return 'OK'

# def start_ngrok(port=PORT):
#     """Start ngrok tunnel"""
#     print("🚀 Starting ngrok...")
#     try:
#         # ใช้ command line arguments ที่ถูกต้องสำหรับ ngrok v3+
#         # 'ngrok http 5000'
#         subprocess.Popen([NGROK_PATH, "http", str(PORT)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         time.sleep(5)  # wait for ngrok to start (อาจต้องปรับเวลา)

#         # Get public URL
#         ngrok_api = "http://localhost:4040/api/tunnels"
#         r = requests.get(ngrok_api)
#         r.raise_for_status() # ตรวจสอบสถานะ http error
#         tunnels = r.json()["tunnels"]
#         if tunnels:
#             public_url = tunnels[0]["public_url"]
#             print(f"🌐 ngrok URL: {public_url}")
#             return public_url
#         else:
#             print("❌ No ngrok tunnels found.")
#             return None
#     except requests.exceptions.ConnectionError:
#         print("❌ Could not connect to ngrok API. Is ngrok running?")
#         return None
#     except Exception as e:
#         print("❌ Failed to get ngrok URL:", e)
#         return None

# def set_line_webhook(webhook_url):
#     print("🔗 Setting LINE webhook...")
#     headers = {
#         "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
#         "Content-Type": "application/json"
#     }
#     # ให้ตรงกับ route
#     data = {"endpoint": webhook_url + "/callback"}
#     r = requests.put(
#         "https://api.line.me/v2/bot/channel/webhook/endpoint",
#         headers=headers,
#         data=json.dumps(data)
#     )
#     print("📡 Webhook response:", r.status_code, r.text)

def set_line_webhook(webhook_url):
    print("🔗 Setting LINE webhook...")
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"endpoint": webhook_url + "/callback"}
    r = requests.put(
        "https://api.line.me/v2/bot/channel/webhook/endpoint",
        headers=headers,
        json=data
    )
    print("📡 Webhook response:", r.status_code, r.text)

@app.route('/form')
def form():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        today = datetime.today().date()

        cursor.execute("SELECT * FROM Transports WHERE TRIM(LOWER(FormType)) = %s AND RecordDate = %s", ('domestic', today))
        domestic_data = cursor.fetchall()
        cursor.execute("""SELECT ID, Plate, Name, Sender, Customer, QueueTime, StartDeliver, DoneDeliver, TruckLoadIn, StartLoad, DoneLoad, PI, EO, Containernumber, Producttype, Remark FROM Transports WHERE TRIM(LOWER(FormType)) = %s AND RecordDate = %s""", ('export', today))
        export_data = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('form.html',
                               username=session['username'],
                               role=session['role'],
                               domestic_data=domestic_data,
                               export_data=export_data)
    except Exception as e:
        return f"Error loading form: {e}"

@app.route('/search', methods=['GET'])
def search_data():
    form_type = request.args.get('formType', '').strip()
    keyword = request.args.get('keyword', '').strip()
    date_str = request.args.get('date', '').strip()
    start_date_str = request.args.get('start_date', '').strip()
    end_date_str = request.args.get('end_date', '').strip()

    if form_type not in ['Domestic', 'Export']:
        return jsonify({'success': False, 'error': 'Invalid formType'})

    try:
        conn = get_db_connection()
        # ใช้ RealDictCursor เพื่อคืนค่าเป็น dict
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Base SQL - ใช้ LOWER() สำหรับ FormType เพื่อให้ case-insensitive
        if form_type == 'Domestic':
            sql = "SELECT * FROM Transports WHERE LOWER(FormType) = %s"
        else: # Export
            sql = """SELECT ID, Plate, Name, Sender, Customer, QueueTime, StartDeliver, DoneDeliver,
                            TruckLoadIn, StartLoad, DoneLoad, PI, EO, Containernumber, Producttype, Remark
                     FROM Transports WHERE LOWER(FormType) = %s"""

        params = [form_type.lower()] # แปลงเป็น lowercase สำหรับการเปรียบเทียบ

        # เงื่อนไขวันที่
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            sql += " AND RecordDate BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        elif start_date_str: # ถ้าเลือกวันเดียวจาก start_date
            date_obj = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            sql += " AND RecordDate = %s"
            params.append(date_obj)
        elif date_str: # fallback กรณีใช้ date ธรรมดา
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            sql += " AND RecordDate = %s"
            params.append(date_obj)

        # เงื่อนไข keyword - ใช้ ILIKE สำหรับ case-insensitive search ใน PostgreSQL
        if keyword:
            sql += " AND (Plate ILIKE %s OR Name ILIKE %s)"
            keyword_param = f"%{keyword}%"
            params.extend([keyword_param, keyword_param])

        # Execute
        cursor.execute(sql, params)
        rows = cursor.fetchall() # RealDictCursor คืนค่าเป็น list of dicts แล้ว
        conn.close()
        return jsonify({'success': True, 'data': rows}) # rows เป็น dicts อยู่แล้ว

    except Exception as e:
        print("Search error:", e)
        return jsonify({'success': False, 'error': str(e)})

@app.route('/submit', methods=['POST'])
def submit():
    plate = request.form.get('plate', '')
    name = request.form.get('name', '')
    sender = request.form.get('sender', '')
    customer = request.form.get('customer', '')
    arrival_time = request.form.get('arrivalTime', '')
    start_unload = request.form.get('startUnload', '')
    end_unload = request.form.get('endUnload', '')
    reg_receive = request.form.get('regReceive', '')
    truck_unload = request.form.get('truckUnload', '')
    start_load = request.form.get('startLoad', '')
    end_load = request.form.get('endLoad', '')
    Delivery_time = request.form.get('Deliverytime', '')
    Status = request.form.get('Status', '')
    Deliverytime_tocustomer = request.form.get('Deliverytimetocustomer', '')
    Delivery_Date = request.form.get('DeliveryDate', '')
    Pi = request.form.get('PI', '')
    Eo = request.form.get('EO', '')
    Container_number = request.form.get('Containernumber', '')
    Product_type = request.form.get('Producttype', '')
    form_type = request.form.get('formType', '')
    RecordDate = request.form.get('date', '')

    # แปลง date_str เป็นวันที่ ถ้าไม่มีหรือแปลงไม่สำเร็จใช้วันที่วันนี้แทน
    try:
        date_value = datetime.strptime(RecordDate, '%Y-%m-%d').date()
    except Exception:
        date_value = datetime.now().date()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # เปลี่ยน ? เป็น %s สำหรับ PostgreSQL
        cursor.execute("""
            INSERT INTO Transports
            (Plate, Name, Sender, Customer, QueueTime, StartDeliver, DoneDeliver,
             ConfirmRegis, TruckLoadIn, StartLoad, DoneLoad, Deliverytime, Status, Deliverytimetocustomer, DeliveryDate, PI, EO, Containernumber, Producttype, FormType, RecordDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (plate, name, sender, customer, arrival_time, start_unload, end_unload,
              reg_receive, truck_unload, start_load, end_load, Delivery_time, Status, Deliverytime_tocustomer, Delivery_Date, Pi, Eo, Container_number, Product_type, form_type, date_value))
        conn.commit()
        cursor.close()
        conn.close()

        return '', 200
    except Exception as e:
        print("Error:", e)
        return f'Error: {e}', 500

@app.route('/import_excel', methods=['POST'])
def import_excel():
    file = request.files.get('excelFile')
    form_type = request.form.get('formType')
    if not file:
        return jsonify({'success': False, 'error': 'No file uploaded.'}), 400

    try:
        df = pd.read_excel(file)

        # แปลงวันที่ RecordDate
        if 'RecordDate' in df.columns:
            # ใช้ errors='coerce' เพื่อให้ค่าที่ไม่ถูกต้องกลายเป็น NaT (Not a Time)
            df['RecordDate'] = pd.to_datetime(df['RecordDate'], dayfirst=True, errors='coerce')
            # แปลง NaT เป็น None เพื่อให้ psycopg2 จัดการได้
            df['RecordDate'] = df['RecordDate'].apply(lambda x: x.date() if pd.notna(x) else None)

        conn = get_db_connection() # ใช้ฟังก์ชัน get_db_connection ที่เชื่อมต่อกับ PostgreSQL
        cursor = conn.cursor()

        # สร้างรายการคอลัมน์ทั้งหมดที่ Transports มี
        # ต้องแน่ใจว่าคอลัมน์ใน DB และใน Excel ตรงกัน หรือปรับให้ตรง
        db_columns = [
            "Plate", "Name", "Sender", "Customer", "QueueTime", "StartDeliver", "DoneDeliver",
            "ConfirmRegis", "TruckLoadIn", "StartLoad", "DoneLoad", "Deliverytime", "Status",
            "Deliverytimetocustomer", "DeliveryDate", "PI", "EO", "Containernumber", "Producttype",
            "FormType", "RecordDate"
        ]
        # สร้าง placeholder สำหรับ INSERT
        placeholders = ', '.join(['%s'] * len(db_columns))
        insert_query = f"INSERT INTO Transports ({', '.join(db_columns)}) VALUES ({placeholders})"

        for index, row in df.iterrows():
            # เตรียมข้อมูลตามลำดับคอลัมน์ของ db_columns
            values = []
            for col in db_columns:
                if col == 'FormType':
                    values.append(form_type)
                elif col == 'RecordDate':
                    values.append(row.get(col, None)) # ใช้ None ถ้าไม่มีค่า
                else:
                    values.append(str(row.get(col, '')) if pd.notna(row.get(col)) else '') # แปลงเป็น str และจัดการ NaN

            cursor.execute(insert_query, tuple(values))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        print("Error importing Excel:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/update', methods=['POST'])
def update():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # ตรวจสอบว่า 'confirmregis' (หรือ 'regReceive' ที่เป็นชื่อในฟอร์ม) มีอยู่ในข้อมูลหรือไม่
        # เพื่อแยก Domestic และ Export
        if 'regReceive' in data: # Domestic update
            cursor.execute("""
                UPDATE Transports SET
                    Plate=%s, Name=%s, Sender=%s, Customer=%s, QueueTime=%s,
                    StartDeliver=%s, DoneDeliver=%s, ConfirmRegis=%s, TruckLoadIn=%s,
                    StartLoad=%s, DoneLoad=%s, Deliverytime=%s, Status=%s, Deliverytimetocustomer=%s, DeliveryDate=%s, Remark=%s
                WHERE ID=%s
            """, (
                data['plate'], data['name'], data['sender'], data['customer'], data['arrivalTime'],
                data['startUnload'], data['endUnload'], data['regReceive'], data['truckUnload'],
                data['startLoad'], data['endLoad'], data['Deliverytime'], data['Status'], data['Deliverytimetocustomer'], data['DeliveryDate'], data['remark'],
                data['id']
            ))
        else: # Export update
            cursor.execute("""
                UPDATE Transports SET
                    Plate=%s, Name=%s, Sender=%s, Customer=%s, QueueTime=%s,
                    StartDeliver=%s, DoneDeliver=%s, TruckLoadIn=%s,
                    StartLoad=%s, DoneLoad=%s, PI=%s, EO=%s, Containernumber=%s, Producttype=%s, Remark=%s
                WHERE ID=%s
            """, (
                data['plate'], data['name'], data['sender'], data['customer'], data['arrivalTime'],
                data['startUnload'], data['endUnload'], data['truckUnload'],
                data['startLoad'], data['endLoad'], data['Pi'], data['Eo'], data['Container_number'], data['Product_type'], data['remark'],
                data['id']
            ))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print("Error:", e)
        return jsonify({'error': str(e)}), 500

@app.route('/delete', methods=['POST'])
def delete():
    data = request.get_json()
    record_id = data.get('id')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Transports WHERE ID = %s", (record_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print("Delete error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/get_group_ids', methods=['GET'])
def get_group_ids():
    conn = get_db_connection()
    # ใช้ RealDictCursor เพื่อคืนค่าเป็น dict
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT group_id, group_name, group_picture FROM Groups")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    # ปรับชื่อ key ให้เป็น lowercase ตาม PostgreSQL ถ้าจำเป็น
    groups = [{'group_id': row['group_id'], 'group_name': row['group_name'], 'group_picture': row['group_picture']} for row in rows]
    return jsonify({'groups': groups})

# ✅ เพิ่มลูกค้าใหม่
@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.get_json()
    customer = data.get('customer')
    formtype = data.get('formtype', '')
    createdate = datetime.now()

    if not customer:
        return jsonify({'success': False, 'error': 'Missing customer field'})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Customers (customer, formtype, createdate) VALUES (%s, %s, %s)",
                       (customer, formtype, createdate))
        conn.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Customer added successfully'})
    except Exception as e:
        print(f"Error adding customer: {e}")
        conn.rollback() # Rollback ถ้าเกิด error
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/api/customers', methods=['GET'])
def get_customers():
    formtype = request.args.get('formtype')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor) # ใช้ RealDictCursor
        if formtype:
            cursor.execute("SELECT customer, formtype, createdate FROM Customers WHERE LOWER(formtype) = %s", (formtype.lower(),))
        else:
            cursor.execute("SELECT customer, formtype, createdate FROM Customers")

        rows = cursor.fetchall()
        # rows เป็น list of dicts อยู่แล้ว
        customers = []
        for row in rows:
            customers.append({
                'customer': row['customer'],
                'formtype': row['formtype'],
                # จัดการ datetime object ของ psycopg2
                'createdate': row['createdate'].strftime('%Y-%m-%d %H:%M:%S') if row['createdate'] else None
            })
        cursor.close()
        return jsonify({'success': True, 'data': customers})
    except Exception as e:
        print(f"Error getting customers: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

# ✅ ลบลูกค้า (โดยใช้ชื่อ customer)
@app.route('/api/customers/<customer>', methods=['DELETE'])
def delete_customer(customer):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Customers WHERE customer = %s", (customer,))
        conn.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Customer deleted successfully'})
    except Exception as e:
        print(f"Error deleting customer: {e}")
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

# ✅ เพิ่มผู้ขนส่ง
@app.route('/api/masterTransports', methods=['POST'])
def add_transport():
    data = request.get_json()
    Transport = data.get('transport')
    formtype = data.get('formtype', '')
    createdate = datetime.now()

    if not Transport:
        return jsonify({'success': False, 'error': 'Missing transport field'}) # แก้ข้อความ error

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO MasterTransport (Transport, formtype, createdate) VALUES (%s, %s, %s)",
                       (Transport, formtype, createdate))
        conn.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Transport added successfully'})
    except Exception as e:
        print(f"Error adding transport: {e}")
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route('/api/masterTransports', methods=['GET'])
def get_transport():
    formtype = request.args.get('formtype')
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor) # ใช้ RealDictCursor

        if formtype:
            cursor.execute("SELECT Transport, formtype, createdate FROM MasterTransport WHERE LOWER(formtype) = %s", (formtype.lower(),))
        else:
            cursor.execute("SELECT Transport, formtype, createdate FROM MasterTransport")

        rows = cursor.fetchall()
        transport_list = [] # เปลี่ยนชื่อตัวแปรเพื่อไม่ให้ซ้ำกับ parameter
        for row in rows:
            transport_list.append({
                'Transport': row['transport'],
                'formtype': row['formtype'],
                'createdate': row['createdate'].strftime('%Y-%m-%d %H:%M:%S') if row['createdate'] else None
            })
        cursor.close()
        return jsonify({'success': True, 'data': transport_list})
    except Exception as e:
        print(f"Error getting transports: {e}")
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

# ✅ ลบผู้ขนส่ง
@app.route('/api/masterTransports/<transport>', methods=['DELETE'])
def delete_transport(transport):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM MasterTransport WHERE Transport = %s", (transport,))
        conn.commit()
        cursor.close()
        return jsonify({'success': True, 'message': 'Transport deleted successfully'})
    except Exception as e:
        print(f"Error deleting transport: {e}")
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)})
    finally:
        conn.close()

@app.route("/export_excel")
def export_excel():
    form_type = request.args.get("formtype", "").strip()
    start = request.args.get("start")
    end = request.args.get("end")

    conn = get_db_connection()
    # ใช้ RealDictCursor เพื่อให้ได้ dict และจัดการชื่อคอลัมน์ได้ง่าย
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    form_type_lower = form_type.lower() # แปลงเป็น lowercase

    query = "SELECT * FROM Transports WHERE LOWER(FormType) = %s"
    params = [form_type_lower]

    if start and end:
        query += " AND RecordDate BETWEEN %s AND %s"
        params.extend([start, end])
    elif start and not end:
        query += " AND RecordDate = %s"
        params.append(start)

    cursor.execute(query, params)
    rows = cursor.fetchall() # RealDictCursor คืนค่าเป็น list of dicts
    cursor.close()
    conn.close()

    # สร้าง DataFrame จาก list of dicts โดยตรง
    df = pd.DataFrame(rows)

    if df.empty:
        return "ไม่มีข้อมูลสำหรับการส่งออก", 404

    # เนื่องจาก RealDictCursor จะคืนชื่อคอลัมน์เป็น lowercase (ตามปกติของ PostgreSQL)
    # เราต้องปรับชื่อคอลัมน์ที่คาดหวังให้เป็น lowercase ด้วย
    columns_domestic = [
        "plate", "name", "sender", "customer", "queuetime", "startdeliver", "donedeliver",
        "confirmregis", "truckloadin", "startload", "doneload", "deliverytime", "status",
        "deliverytimetocustomer", "deliverydate", "remark", "formtype", "recorddate"
    ]
    columns_export = [
        "plate", "name", "sender", "customer", "queuetime", "startdeliver",
        "donedeliver", "truckloadin", "startload", "doneload", "pi", "eo",
        "containernumber", "producttype", "remark", "formtype", "recorddate"
    ]

    # กำหนดคอลัมน์ที่จะเลือกและเปลี่ยนชื่อกลับเป็นรูปแบบที่ต้องการใน Excel
    if form_type_lower == "domestic":
        df = df[columns_domestic]
        # map ชื่อคอลัมน์เป็นภาษาที่เข้าใจง่าย (หรือตามเดิมที่ต้องการ)
        df.rename(columns={
            "plate": "Plate", "name": "Name", "sender": "Sender", "customer": "Customer",
            "queuetime": "QueueTime", "startdeliver": "StartDeliver", "donedeliver": "DoneDeliver",
            "confirmregis": "ConfirmRegis", "truckloadin": "TruckLoadIn", "startload": "StartLoad",
            "doneload": "DoneLoad", "deliverytime": "Deliverytime", "status": "Status",
            "deliverytimetocustomer": "Deliverytimetocustomer", "deliverydate": "DeliveryDate",
            "remark": "Remark", "formtype": "FormType", "recorddate": "RecordDate"
        }, inplace=True)
    elif form_type_lower == "export":
        df = df[columns_export]
        df.rename(columns={
            "plate": "Plate", "name": "Name", "sender": "Sender", "customer": "Customer",
            "queuetime": "QueueTime", "startdeliver": "StartDeliver",
            "donedeliver": "DoneDeliver", "truckloadin": "TruckLoadIn", "startload": "StartLoad",
            "doneload": "DoneLoad", "pi": "PI", "eo": "EO",
            "containernumber": "Containernumber", "producttype": "Producttype", "remark": "Remark",
            "formtype": "FormType", "recorddate": "RecordDate"
        }, inplace=True)
    else:
        return "❌ FormType ต้องเป็น 'Domestic' หรือ 'Export'", 400

    # จัดการ RecordDate ให้เป็นรูปแบบวันที่ที่ต้องการ ถ้าเป็น datetime object
    for col in ["RecordDate", "DeliveryDate"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) and isinstance(x, (datetime, pd.Timestamp)) else x)


    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=f"{form_type.capitalize()} Report")

    output.seek(0)
    return send_file(output,
                     download_name=f"{form_type.capitalize()}_Transport_Report.xlsx",
                     as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

def draw_header(canvas, doc, form_type):
    canvas.saveState()

    # โลโก้ซ้ายบน
    logo_path = "static/Img/Wice.jpg"
    if os.path.exists(logo_path):
        canvas.drawImage(logo_path, x=20, y=doc.height + 70, width=100, height=60)

    # ตั้งค่าฟอนต์และคำนวณตำแหน่ง
    canvas.setFont("THSarabunNew-Bold", 18)
    center_x = doc.width / 2.0 + doc.leftMargin
    top_y = doc.height + 90

    # ข้อความแยกสี
    text_form = form_type
    text_report = " Transport Report"

    text_form_width = canvas.stringWidth(text_form, "THSarabunNew-Bold", 20)
    text_report_width = canvas.stringWidth(text_report, "THSarabunNew-Bold", 20)
    total_width = text_form_width + text_report_width
    start_x = center_x - total_width / 2

    # สีของ form_type
    if form_type.lower() == "domestic":
        canvas.setFillColor(colors.red)
    else:  # Export หรืออื่น ๆ
        canvas.setFillColor(colors.HexColor("#0070C0"))

    # วาดชื่อ form_type
    canvas.setFont("THSarabunNew-Bold", 20)
    canvas.drawString(start_x, top_y, text_form)

    # วาด Transport Report เป็นสีดำ
    canvas.setFillColor(colors.black)
    canvas.drawString(start_x + text_form_width, top_y, text_report)

    # วันที่ปัจจุบัน มุมขวาบน
    tz = pytz.timezone('Asia/Bangkok')
    now = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
    canvas.setFont("THSarabunNew", 12)
    canvas.setFillColorRGB(0, 0, 0)
    canvas.drawRightString(doc.width + doc.leftMargin, doc.height + 90, f"Report Date: {now}")

    canvas.restoreState()

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    data = request.get_json()
    form_type = data.get("formtype", "").capitalize()
    table_data = data.get("table_data", [])
    columns = data.get("columns", [])

    if not table_data or not columns:
        return "❌ ต้องส่งข้อมูล table_data และ columns", 400

    font_path = "fonts/THSarabunNew.ttf"
    font_bold_path = "fonts/THSarabunNew-Bold.ttf"
    # ตรวจสอบว่าไฟล์ font มีอยู่จริง
    if os.path.exists(resource_path(font_path)):
        pdfmetrics.registerFont(TTFont("THSarabunNew", resource_path(font_path)))
        pdfmetrics.registerFont(TTFont("THSarabunNew-Bold", resource_path(font_bold_path)))
        default_font = "THSarabunNew"
        bold_font = "THSarabunNew-Bold"
    else:
        default_font = "Helvetica"
        bold_font = "Helvetica-Bold"

    col_width_map = {
        "plate": 12 * mm,
        "name": 25 * mm,
        "sender": 13 * mm,
        "customer": 28 * mm,
        "queuetime": 14 * mm,
        "startdeliver": 13 * mm,
        "donedeliver": 16 * mm,
        "confirmregis": 20 * mm,
        "truckloadin": 16 * mm,
        "startload": 15 * mm,
        "doneload": 16 * mm,
        "deliverytime": 14 * mm,
        "status": 16 * mm,
        "deliverytimetocustomer": 15 * mm,
        "deliverydate": 14 * mm,
        "remark": 20 * mm,
        "pi": 14 * mm,
        "eo": 14 * mm,
        "containernumber": 14 * mm,
        "producttype": 30 * mm,
    }


    # กำหนดชื่อหัวตารางเป็นภาษาไทย (ต้อง match จำนวนคอลัมน์ที่เลือก)
    # ใช้ key เป็น lowercase ตามที่ RealDictCursor คืนค่ามา
    header_thai = {
        "plate": "ทะเบียน",
        "name": "ชื่อพนักงานขับ",
        "sender": "ผู้ขนส่ง",
        "customer": "ลูกค้า",
        "queuetime": "เวลาที่รถลงคิว",
        "startdeliver": "เริ่มตั้งสินค้า",
        "donedeliver": "ตั้งสินค้าสำเร็จ",
        "confirmregis": "ขนส่งตอบรับทะเบียน",
        "truckloadin": "รถเข้าโหลดสินค้า",
        "startload": "เริ่มโหลดสินค้า",
        "doneload": "โหลดสินค้าสำเร็จ",
        "deliverytime": "เวลาส่งสินค้า",
        "status": "สถานะ",
        "deliverytimetocustomer": "เวลาส่งถึงลูกค้า",
        "deliverydate": "วันที่ส่งสินค้า",
        "remark": "หมายเหตุ",
        "pi": "PI", # เพิ่ม PI, EO ถ้ายังไม่มี
        "eo": "EO",
        "containernumber": "เบอร์ตู้",
        "producttype": "ชนิดสินค้า",
    }

    # สร้างแถวหัวตารางภาษาไทย ตาม columns ที่ส่งมา
    # ปรับ columns ที่ส่งมาให้เป็น lowercase ก่อนหาใน header_thai
    headers = [header_thai.get(col.lower(), col) for col in columns]

    # สร้างข้อมูลตาราง: แถวหัว + แถวข้อมูล
    # ตรวจสอบการเข้าถึงข้อมูลใน row ให้เป็น row[col.lower()]
    data_rows = [
        [str(row.get(col.lower(), "")) for col in columns]
        for row in table_data
    ]

    pdf_table_data = [headers] + data_rows

    # ปรับ col_widths ให้ตรงกับ columns ที่ส่งมาและใช้ lowercase
    # col_widths = [col_width_map.get(col.capitalize(), 25 * mm) for col in columns] # .capitalize() เพราะ key ใน map เป็นแบบนั้น
    col_widths = [col_width_map.get(col.lower(), 25 * mm) for col in columns]

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    table = Table(pdf_table_data, repeatRows=1, colWidths=col_widths)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.navy),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), bold_font),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),

        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), default_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),

        ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
    ])
    table.setStyle(style)


    elements = [Spacer(1, 2*mm), table]

    doc.build(elements,onFirstPage=partial(draw_header, form_type=form_type),onLaterPages=partial(draw_header, form_type=form_type))
    buffer.seek(0)

    return send_file(buffer,
                mimetype='application/pdf',
                download_name=f"{form_type}_Report.pdf",
                as_attachment=True)

# if __name__ == '__main__':
#     public_url = start_ngrok(PORT)
#     if public_url:
#         set_line_webhook(public_url)
#     app.run(debug=True, port=PORT)

if os.environ.get("RENDER") == "true":
    webhook_url = "https://wice-transports.onrender.com"
    set_line_webhook(webhook_url)

if __name__ == '__main__':
    webhook_url = "http://localhost:5000"
    set_line_webhook(webhook_url)

    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT)