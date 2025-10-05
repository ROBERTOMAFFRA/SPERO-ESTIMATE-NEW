from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import os, sqlite3, datetime
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# --- PostgreSQL via SQLAlchemy ---
from models import init_db

# Inicializa o banco de dados no início da aplicação
init_db()
# ---------------------------------


APP_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(APP_DIR, "data", "app.db")
REPORTS_FOLDER = os.path.join(APP_DIR, "reports")
os.makedirs(REPORTS_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","change-me-please")
app.config['UPLOAD_FOLDER'] = os.path.join(APP_DIR, "data")



def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    from functools import wraps
    @wraps(f)
    def inner(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return inner

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def inner(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        conn = get_db_conn(); row = conn.execute("SELECT role FROM users WHERE username=?", (session['user'],)).fetchone(); conn.close()
        if not row or row['role']!='Admin':
            flash('Admin required','danger'); return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return inner

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
@login_required
def dashboard():
    conn = get_db_conn(); rows = conn.execute("SELECT * FROM estimates ORDER BY id DESC").fetchall(); conn.close()
    total = sum([r['total'] for r in rows]) if rows else 0
    return render_template('dashboard.html', estimates=rows, total_sum=total, user=session.get('user'))

@app.route('/estimate/new', methods=['GET','POST'])
@login_required
def new_estimate():
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
@login_required
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
@admin_required
def delete_estimate(eid):
    conn = get_db_conn(); conn.execute("DELETE FROM estimates WHERE id=?", (eid,)); conn.commit(); conn.close(); flash('Deleted','success'); return redirect(url_for('dashboard'))

@app.route('/settings', methods=['GET','POST'])
@admin_required
def settings():
    info = {}
    if request.method=='POST':
        f = request.files.get('file')
        if f and f.filename.lower().endswith('.xlsx'):
            f.save(os.path.join(app.config['UPLOAD_FOLDER'],'estimate.xlsx')); flash('✅ New price list uploaded successfully!','success'); return redirect(url_for('settings'))
        else: flash('Please upload a .xlsx file','danger')
    p = os.path.join(app.config['UPLOAD_FOLDER'],'estimate.xlsx')
    if os.path.exists(p): info['size'] = os.path.getsize(p)
    return render_template('settings.html', info=info)

@app.route('/manage-users', methods=['GET','POST'])
@admin_required
def manage_users():
    conn = get_db_conn()
    if request.method=='POST':
        action = request.form.get('action')
        if action=='add':
            u = request.form.get('username').strip(); p = request.form.get('password').strip(); r = request.form.get('role','Viewer')
            try: conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",(u,p,r)); conn.commit(); flash('User added','success')
            except: flash('Error adding user','danger')
        elif action=='delete':
            u = request.form.get('del_username').strip()
            if u==ADMIN_USER: flash('Cannot delete admin','danger')
            else: conn.execute("DELETE FROM users WHERE username=?", (u,)); conn.commit(); flash('Deleted','success')
    rows = conn.execute("SELECT username,role FROM users").fetchall(); conn.close()
    return render_template('manage_users.html', users=rows)

if __name__=='__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',5000)), debug=True)
migrate from sqlite to postgresql
