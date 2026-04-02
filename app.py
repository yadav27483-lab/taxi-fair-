from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import mysql.connector
import hashlib
from datetime import datetime
import random

app = Flask(__name__, static_folder='../frontend', template_folder='../frontend')
app.secret_key = "secret123"
CORS(app, supports_credentials=True)

# DB
def db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="taxiapp"
    )

def hash_pw(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ================= AUTH =================

@app.route('/api/register', methods=['POST'])
def register():
    d = request.json
    conn = db()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username,email,password_hash,phone) VALUES (%s,%s,%s,%s)",
            (d['username'], d['email'], hash_pw(d['password']), d.get('phone'))
        )
        conn.commit()
        return jsonify({'message':'Registered'})
    except:
        return jsonify({'error':'User exists'}), 400

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    conn = db()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT * FROM users WHERE (username=%s OR email=%s) AND password_hash=%s",
        (d['username'], d['username'], hash_pw(d['password']))
    )
    user = cur.fetchone()

    if user:
        session['user'] = user['username']
        session['role'] = user['role']
        return jsonify({'username':user['username'], 'role':user['role']})

    return jsonify({'error':'Invalid'}), 401

@app.route('/api/me')
def me():
    if 'user' in session:
        return jsonify({'logged_in':True,'username':session['user'],'role':session['role']})
    return jsonify({'logged_in':False})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message':'logout'})

# ================= FARE =================

@app.route('/api/fare/calculate', methods=['POST'])
def fare():
    d = request.json
    dist = float(d.get('distance_km',0))
    total = 50 + (12 * dist) + float(d.get('waiting_charge',0))
    per_km = 12
    return jsonify({
        'distance_km': dist,
        'per_km_charge': per_km,
        'total_fare': round(total, 2)
    })

# ================= BOOKINGS =================

def gen_id():
    return "BK" + str(random.randint(100000,999999))

@app.route('/api/bookings', methods=['POST'])
def book():
    d = request.json
    conn = db()
    cur = conn.cursor()

    bid = gen_id()
    now = datetime.now()

    cur.execute("""
    INSERT INTO taxi_bookings
    (booking_id,user_name,phone_number,pickup_location,drop_location,distance_km,fare,booking_date,booking_time)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """,(
        bid,
        d.get('user_name'),
d.get('phone_number'),
d.get('pickup_location'),
d.get('drop_location'),
d.get('distance_km'),
d.get('fare'),
        now.date(),
        now.time()
    ))
    conn.commit()

    return jsonify({'booking_id':bid})

def serialize_bookings(rows):
    result = []
    for row in rows:
        r = dict(row)
        if r.get('booking_date') and hasattr(r['booking_date'], 'isoformat'):
            r['booking_date'] = r['booking_date'].isoformat()
        if r.get('booking_time') and hasattr(r['booking_time'], 'total_seconds'):
            total = int(r['booking_time'].total_seconds())
            r['booking_time'] = f"{total//3600:02d}:{(total%3600)//60:02d}:{total%60:02d}"
        result.append(r)
    return result

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM taxi_bookings ORDER BY id DESC")
    return jsonify(serialize_bookings(cur.fetchall()))

@app.route('/api/bookings/recent')
def recent():
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM taxi_bookings ORDER BY id DESC LIMIT 5")
    return jsonify(serialize_bookings(cur.fetchall()))

# ================= VEHICLES =================

@app.route('/api/vehicles', methods=['GET', 'POST'])
def vehicles():
    conn = db()
    if request.method == 'POST':
        d = request.json
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO vehicles_for_sale
        (vehicle_name,vehicle_type,model,price,seller_name,contact_number,description)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,(
            d.get('vehicle_name'),
            d.get('vehicle_type'),
            d.get('model'),
            d.get('price'),
            d.get('seller_name'),
            d.get('contact_number'),
            d.get('description')
        ))
        conn.commit()
        return jsonify({'msg':'added'})
    cur = conn.cursor(dictionary=True)
    vtype = request.args.get('type', '')
    if vtype:
        cur.execute("SELECT * FROM vehicles_for_sale WHERE vehicle_type=%s", (vtype,))
    else:
        cur.execute("SELECT * FROM vehicles_for_sale")
    return jsonify(cur.fetchall())
# ================= RENTALS =================

@app.route('/api/rentals', methods=['GET', 'POST'])
def rentals_route():
    conn = db()
    if request.method == 'POST':
        d = request.json
        cur = conn.cursor()
        days = int(d.get('total_days', 0)) or max(1, (
            (__import__('datetime').datetime.strptime(d.get('end_date',''), '%Y-%m-%d') -
             __import__('datetime').datetime.strptime(d.get('start_date',''), '%Y-%m-%d')).days
        ))
        price = float(d.get('price_per_day', 0))
        total = days * price
        cur.execute("""
        INSERT INTO vehicle_rentals
        (user_name,vehicle_name,start_date,end_date,total_days,price_per_day,total_charge)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,(
            d.get('user_name'),
            d.get('vehicle_name'),
            d.get('start_date'),
            d.get('end_date'),
            days, price, total
        ))
        conn.commit()
        return jsonify({'msg':'rented', 'total_days': days, 'total_charge': total})
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM vehicle_rentals ORDER BY id DESC")
    rows = []
    for row in cur.fetchall():
        r = dict(row)
        if r.get('start_date') and hasattr(r['start_date'], 'isoformat'):
            r['start_date'] = r['start_date'].isoformat()
        if r.get('end_date') and hasattr(r['end_date'], 'isoformat'):
            r['end_date'] = r['end_date'].isoformat()
        rows.append(r)
    return jsonify(rows)
# ================= ADMIN =================

@app.route('/api/admin/stats')
def stats():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM taxi_bookings")
    b = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicle_rentals")
    r = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vehicles_for_sale")
    v = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(fare),0) FROM taxi_bookings")
    fare_rev = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(total_charge),0) FROM vehicle_rentals")
    rental_rev = cur.fetchone()[0]

    return jsonify({
        'bookings': b,
        'rentals': r,
        'vehicles': v,
        'total_bookings': b,
        'total_rentals': r,
        'total_vehicles': v,
        'total_fare_revenue': float(fare_rev),
        'total_rental_revenue': float(rental_rev)
    })

@app.route('/api/vehicles/<int:vid>', methods=['DELETE'])
def delete_vehicle(vid):
    conn = db()
    cur = conn.cursor()
    cur.execute("DELETE FROM vehicles_for_sale WHERE id=%s", (vid,))
    conn.commit()
    return jsonify({'msg':'deleted'})

# ================= FRONTEND =================

@app.route('/')
def home():
    return send_from_directory('../frontend','index.html')

if __name__ == '__main__':
    app.run(debug=True)