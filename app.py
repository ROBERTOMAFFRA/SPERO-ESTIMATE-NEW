import os
from flask import Flask, render_template, request, redirect, session
from models import SessionLocal, User, Estimate, Base, engine
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'spero_secret_key')

# 🧠 Criar tabelas automaticamente ao iniciar
Base.metadata.create_all(bind=engine)

# 🧩 Rota inicial
@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/login')

# 🔐 Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        db = SessionLocal()
        user = db.query(User).filter_by(username=u, password=p).first()
        db.close()

        if user:
            session['user'] = user.username
            session['role'] = user.role
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Usuário ou senha incorretos.')
    return render_template('login.html')

# 🚪 Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# 🏠 Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    db = SessionLocal()
    estimates = db.query(Estimate).all()
    db.close()
    return render_template('dashboard.html', user=session['user'], estimates=estimates)

# ➕ Criar novo orçamento
@app.route('/add_estimate', methods=['GET', 'POST'])
def add_estimate():
    if 'user' not in session:
        return redirect('/login')

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        price = float(request.form['price'])

        db = SessionLocal()
        new_estimate = Estimate(name=name, description=description, category=category, price=price)
        db.add(new_estimate)
        db.commit()
        db.close()

        return redirect('/dashboard')

    return render_template('add_estimate.html')

# 🔍 Testar conexão com o banco
@app.route('/test-db')
def test_db():
    try:
        db = SessionLocal()
        count = db.query(User).count()
        db.close()
        return f"Conexão bem-sucedida! Total de usuários: {count}"
    except Exception as e:
        return f"Erro ao conectar ao banco: {e}"

# 🚀 Executar localmente
if __name__ == '__main__':
    try:
        db = SessionLocal()

        # cria usuário admin padrão se não existir
        if not db.query(User).filter_by(username='admin').first():
            admin_user = User(username='admin', password='admin', role='admin')
            db.add(admin_user)
            db.commit()
            print("✅ Usuário admin criado (login: admin / senha: admin)")

        db.close()
    except Exception as e:
        print(f"⚠️ Erro ao inicializar banco: {e}")

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)
