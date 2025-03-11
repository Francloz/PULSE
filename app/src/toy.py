from flask import Flask
from flask import Flask, render_template, request, redirect, url_for, session, flash

from config import TEMPLATE_FOLDER, STATIC_FOLDER
app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
app.secret_key = 'your_secret_key'  # Replace with a secure random secret key in production

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit_form():
    username = request.form['username']
    password = request.form['password']
    if password == "1234":
        session['logged_in'] = True
        session['username'] = username
        return redirect(url_for('chat'))
    else:
        flash('Invalid username or password. Please try again.', 'error')
        return redirect(url_for('home'))


@app.route('/chat')
def chat():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    return render_template('chat.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)