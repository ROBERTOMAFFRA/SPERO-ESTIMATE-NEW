from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
import os, sqlite3, datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

APP_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(APP_DIR, "database.db")
REPORTS_FOLDER = os.path.join(APP_DIR, "reports")
os.makedirs(REPORTS_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","change-me-please")

def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, role TEXT DEFAULT 'user')''')
    cur.execute('''CREATE TABLE IF NOT EXISTS estimates (id INTEGER PRIMARY KEY AUTOINCREMENT, client TEXT, description TEXT, unit TEXT, qty REAL, unit_price REAL, total REAL, created_at TEXT)''')
    cur.execute("INSERT OR IGNORE INTO users (username,password,role) VALUES (?,?,?)", ('admin','admin','admin'))
    conn.commit()
    conn.close()

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u = request.form.get('username','').strip(); p = request.form.get('password','').strip()
        conn = get_db_conn(); row = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone(); conn.close()
        if row:
            session['user'] = u; session['role'] = row['role']; return redirect(url_for('dashboard'))
        flash('Invalid credentials','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear(); return redirect(url_for('login'))

@app.route('/')
def root():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    conn = get_db_conn(); rows = conn.execute("SELECT * FROM estimates ORDER BY id DESC").fetchall(); conn.close()
    return render_template('dashboard.html', estimates=rows, user=session.get('user'))

@app.route('/estimate/new', methods=['GET','POST'])
def new_estimate():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method=='POST':
        client = request.form.get('client',''); description = request.form.get('description',''); unit = request.form.get('unit','')
        try:
            qty = float(request.form.get('qty') or 0); unit_price = float(request.form.get('unit_price') or 0)
        except:
            qty = 0; unit_price = 0
        total = qty * unit_price
        conn = get_db_conn(); conn.execute("INSERT INTO estimates (client,description,unit,qty,unit_price,total,created_at) VALUES (?,?,?,?,?,?,?)",
                                           (client,description,unit,qty,unit_price,total,datetime.datetime.now().isoformat())); conn.commit(); conn.close()
        flash('Estimate saved','success'); return redirect(url_for('dashboard'))
    return render_template('estimate_form.html')

@app.route('/estimate/<int:eid>/pdf')
def estimate_pdf(eid):
    conn = get_db_conn(); row = conn.execute("SELECT * FROM estimates WHERE id=?", (eid,)).fetchone(); conn.close()
    if not row: flash('Not found','danger'); return redirect(url_for('dashboard'))
    filename = f"estimate_{eid}.pdf"; path = os.path.join(REPORTS_FOLDER, filename)
    c = canvas.Canvas(path, pagesize=A4); width, height = A4; margin=20*mm; y=height-margin
    try: c.drawImage(os.path.join('static','images','Logo Spero.png'), margin, y-40, width=120, preserveAspectRatio=True, mask='auto')
    except: pass
    y-=60; c.setFont('Helvetica-Bold',14); c.drawString(margin, y, 'Estimate'); y-=20
    c.setFont('Helvetica',10); c.drawString(margin, y, f"Client: {row['client']}"); y-=14
    c.drawString(margin, y, f"Description: {row['description']}"); y-=14
    c.drawString(margin, y, f"Unit: {row['unit']}   Qty: {row['qty']}   Unit Price: {row['unit_price']}   Total: {row['total']}"); y-=14
    c.save(); return send_from_directory(REPORTS_FOLDER, filename, as_attachment=True)

@app.route('/estimate/<int:eid>/delete', methods=['POST'])
def delete_estimate(eid):
    conn = get_db_conn(); conn.execute("DELETE FROM estimates WHERE id=?", (eid,)); conn.commit(); conn.close(); flash('Deleted','success'); return redirect(url_for('dashboard'))

@app.route('/test-db')
def test_db():
    try:
        conn = get_db_conn(); cur = conn.cursor(); cur.execute("SELECT COUNT(*) FROM users"); total = cur.fetchone()[0]; conn.close()
        return f"Conexão bem-sucedida! Total de usuários: {total}"
    except Exception as e:
        return f"Erro ao conectar ao banco: {e}"

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
