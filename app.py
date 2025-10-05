
from flask import Flask, render_template, redirect, url_for, request, session, send_file, flash
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'spero_secret_key'

ADMIN_USER = 'admin'
ADMIN_PASS = 'spero123'
ADMIN_EMAIL = 'sperorestor@outlook.com'

@app.route('/')
def home():
    if 'user' in session:
        return render_template('dashboard.html', user=session['user'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['user'] = username
            flash('Welcome back!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
