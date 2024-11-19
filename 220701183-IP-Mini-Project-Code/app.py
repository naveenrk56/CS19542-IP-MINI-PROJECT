from flask import Flask, request, render_template, redirect, url_for, session, send_file, make_response
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Used for session management
bcrypt = Bcrypt(app)

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']  # Your database name
users_collection = db['users']  # Collection for user data
audio_collection = db['audio']  # Collection for audio files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_page')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audioFile' not in request.files:
        return "No file part", 400
    
    file = request.files['audioFile']
    
    if file.filename == '':
        return "No selected file", 400

    if file:
        # Store the audio file as binary data in MongoDB
        audio_data = file.read()
        audio_collection.insert_one({
            'filename': file.filename,
            'data': audio_data
        })
        return redirect(url_for('ack'))  # Redirect after a successful upload

    return "File not uploaded", 400

@app.route('/guide')
def guide():
    return render_template('guide.html') 

@app.route('/ack')
def ack():
    return render_template('acknowledgement.html') 

@app.route('/log')
def log():
    return render_template('login.html') 

@app.route('/reg')
def reg():
    return render_template('register.html') 

@app.route('/file/<filename>')
def get_file(filename):
    audio_record = audio_collection.find_one({'filename': filename})
    if audio_record:
        # Create a response and set the appropriate headers
        response = make_response(audio_record['data'])
        response.headers.set('Content-Type', 'audio/mpeg')  # Change based on your audio type
        response.headers.set('Content-Disposition', f'attachment; filename={audio_record["filename"]}')
        return response
    return "File not found", 404

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user already exists
        if users_collection.find_one({'username': username}):
            return "Username already exists. Please <a href='/log'>login</a>."

        # Hash the password and insert into MongoDB
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        users_collection.insert_one({
            'username': username,
            'password': hashed_password
        })
        return "Registration successful. Please <a href='/log'>login</a>."
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if user exists
        user = users_collection.find_one({'username': username})
        if user and bcrypt.check_password_hash(user['password'], password):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return "Invalid username or password. Please try again."

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
