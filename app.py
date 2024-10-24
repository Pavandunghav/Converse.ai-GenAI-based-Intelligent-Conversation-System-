# for flask web app, template rendering, request handling, json, redirecting, url (this url is used inside re-directing function, to store messages that are displayed to user on next page load, to store logged-in user info (session data))
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
# websocket
from flask_socketio import SocketIO, emit
# ORM 
from flask_sqlalchemy import SQLAlchemy
# manages user sessions and auth, default implementation for the user model, logs in user and starts session, to impose user must login, object representing currently logged-in user
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
# to generate hash for password and for comparing the hash
from werkzeug.security import generate_password_hash, check_password_hash
# gemini API, os (to store API KEYS), handle datetime
import google.generativeai as genai
import os
from datetime import datetime


from flask_mysqldb import MySQL
import MySQLdb.cursors

from flask_cors import CORS

import assemblyai as aai

from dotenv import find_dotenv, load_dotenv


active_users = {}

# create flask app and set the secret keys
app = Flask(__name__)

CORS(app)

# for session management, db location, tracks modifications to objects and emits signals to reduce memory usage and improving perfomance
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
# app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///chat.db')
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Pavan@123'
app.config['MYSQL_DB'] = 'npn'


mysql = MySQL(app)


# setting up real time bi-directional event-based communication between clients and the request are allowed from any origin for our flask app
socketio = SocketIO(app, cors_allowed_origins="*")
# setting up ORM for our APP
# db = SQLAlchemy(app)
# to manage user login and if user is not logged in them redirect him to the login page
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY', 'AIzaSyBYwtFNIN9V6gQDmj3yjNxzYwmj_1KkvsA'))
model = genai.GenerativeModel('gemini-pro')


class User(UserMixin):
    def __init__(self, user_id, username, password, is_representative):
        self.id = user_id
        self.username = username
        self.password = password
        self.is_representative = is_representative

    def is_active(self):
        return True

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id




# to load the user from the database based on their user ID - for flask login and manage sessions
@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM User WHERE id = %s', (user_id,))
    user_data = cursor.fetchone()
    cursor.close()

    if user_data:
        return User(
            user_id=user_data['id'],
            username=user_data['username'],
            password=user_data['password'],
            is_representative=user_data['is_representative']
        )
    return None




# for home
# if authenticated ===> is representative ===> not present on the representative url ==> so redirect there
# if authenticated ==> not representative ==> not present on user url ==> so redirect there
# else ===> user not logged in ===> redirect to the login page
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_representative:
            if request.path != url_for('representative'):
                return redirect(url_for('representative'))
        else:
            if request.path != url_for('customer'):
                return redirect(url_for('customer'))
    return redirect(url_for('login'))



# get the username and password and then check if it exists in the users table - if there then login the user else redirect to login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM User WHERE username = %s', (username,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data and check_password_hash(user_data['password'], password):
            user = User(
                user_id=user_data['id'],
                username=user_data['username'],
                password=user_data['password'],
                is_representative=user_data['is_representative']
            )
            login_user(user)
            # user logged in so store username and id
            active_users[user.username] = {
                'id' : user.id,
                'is_representative' : user.is_representative
            }
            return redirect(url_for('index'))

        flash('Invalid username or password')
    
    return render_template('login.html')



# logout user, and also clear the details about the user from the session storage
@app.route('/logout')
@login_required
def logout():

    # if user logouts - remove his details
    user_id = current_user.get_id()

    if user_id in active_users:
        del active_users[user_id]
    
    print(active_users)

    logout_user()
    session.clear()
    return redirect(url_for('login'))



# take the details, verify them and create new user and re-direct to the login page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        is_representative = 'is_representative' in request.form
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM User WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user:
            flash('Username already exists')
            cursor.close()
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password)
        cursor.execute('INSERT INTO User (username, password, is_representative) VALUES (%s, %s, %s)', 
                       (username, hashed_password, is_representative))
        mysql.connection.commit()
        cursor.close()
        flash('Account created successfully! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')



# we can combine the customer and the representative function - as both of them verify the is_representative flag in the user details
# interface to show the customer
@app.route('/customer')
@login_required
def customer():
    if current_user.is_representative:
        return redirect(url_for('representative'))
    return render_template('customer.html')



# interface to show the representative
@app.route('/representative')
@login_required
def representative():
    if not current_user.is_representative:
        return redirect(url_for('customer'))
    print(active_users)
    return render_template('representative.html')


def get_repId():
    for username, user_data in active_users.items():
        if user_data['is_representative']:
            return user_data['id']
    return None

def get_custId(customer_name):
    for username, user_data in active_users.items():
        if username == customer_name and not user_data['is_representative']:
            return user_data['id']
    return None



@app.route('/get_customers')
@login_required
def customer_list():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM User WHERE is_representative = %s', (0,))
    data = cursor.fetchall()

    logged_in_users = [
        customer for customer in data 
        if customer['username'] in active_users
    ]

    print(logged_in_users)
    return jsonify(logged_in_users)


@app.route('/get_customer/<int:cust_id>')
@login_required
def unique_customer(cust_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    query = '''
        SELECT * FROM Messages
        WHERE (sender_id = %s AND receiver_id = %s) 
           OR (sender_id = %s AND receiver_id = %s)
        ORDER BY timestamp ASC;
    '''
    cursor.execute(query, (current_user.id, cust_id, cust_id, current_user.id))
    data = cursor.fetchall()
    print(data)
    return jsonify(data)







# socket listens for a sockeIO event named customer_message and when client emit this event (message) this function is triggered 
@socketio.on('customer_message')
@login_required
def handle_customer_message(data):
    cursor = mysql.connection.cursor()
    # cursor.execute(
    #     'INSERT INTO Message (content, user_id, is_customer) VALUES (%s, %s, %s)', 
    #     (data['message'], current_user.id, True)
    # )
    cursor.execute(
        'INSERT INTO Messages (sender_id, receiver_id, content, is_customer) VALUES (%s, %s, %s,%s)', 
        (current_user.id, get_repId() ,data['message'], True)
    )
    mysql.connection.commit()
    cursor.close()
    # Emit an event to notify clients
    emit('customer_message', data, broadcast=True)




# socket listens for a sockeIO event named rep_message and when representative emit this event (message) this function is triggered 
@socketio.on('rep_message')
@login_required
def handle_rep_message(data):

    # customerId = get_custId(data['customer_name'])
    customerId = data['customer_id']

    cursor = mysql.connection.cursor()
    # cursor.execute(
    #     'INSERT INTO Message (content, user_id, is_customer) VALUES (%s, %s, %s)', 
    #     (data['message'], current_user.id, False)
    # )
    cursor.execute(
        'INSERT INTO Messages (sender_id, receiver_id, content, is_customer) VALUES (%s, %s, %s, %s)', 
        (current_user.id, customerId , data['message'], False)
    )
    mysql.connection.commit()
    cursor.close()
    # Emit an event to notify clients
    emit('rep_message', data, broadcast=True)




@app.route('/audio_to_text', methods=['POST'])
@login_required
def speech_to_text():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file found in request'}), 400

    audio_file = request.files['audio']
    print("\n", audio_file.filename, "\n")

    file_path = os.path.join('C:/Users/Aniket/Desktop/Abhishek Python/personal/django_tutorials/NPN/chatapp_v2/audio', audio_file.filename)
    audio_file.save(file_path)
    print(file_path)

    aai.settings.api_key = "your_assembly_ai_api"
    transcriber = aai.Transcriber()

    transcript = transcriber.transcribe(file_path)
    message = transcript.text
    print(message)

    return jsonify({"message" : message, "customer_type" : current_user.is_representative})

    # return jsonify({"transcription" : output})


    

# model analysis starts from here 

@app.route('/analyze', methods=['POST'])
@login_required
def analyze_message():
    message = request.json['message']
    analysis = analyze_with_gemini(message)
    return jsonify(analysis)

def analyze_with_gemini(conversation_transcript):
    prompt = f"""
    Analyze the following conversation transcript and provide the following details:
    1. Summary: Provide a concise summary.
    2. Sentiment: Assess the sentiment as 'positive', 'negative', or 'neutral'.
    3. Loan Type: Identify the type of loan discussed ('home_loan', 'car_loan', 'personal_loan', or 'other').
    4. Lead Type: Classify the lead type ('hot_lead', 'cold_lead').
    5. Rationale: Provide a brief rationale for the lead classification.

    Respond with each point on a new line. Input: {conversation_transcript}
    """
    
    try:
        response = model.generate_content(prompt)
        print("Gemini API Response:", response.text)  # Print the response for debugging
        
        # Split response into lines and check if lines are present
        analysis = response.text.strip().split('\n')
        if len(analysis) < 5:
            raise ValueError("Insufficient data in API response.")
        
        def extract_field(index):
            try:
                return analysis[index].split(': ', 1)[1]
            except IndexError:
                return 'Data not available'
            except ValueError:
                return 'Malformed data'
        
        return {
            'summary': extract_field(0),
            'sentiment': extract_field(1),
            'loan_type': extract_field(2),
            'lead_type': extract_field(3),
            'rationale': extract_field(4),
        }
    
    except Exception as e:
        print("Error analyzing message:", str(e))
        return {
            'summary': 'Error',
            'sentiment': 'Error',
            'loan_type': 'Error',
            'lead_type': 'Error',
            'rationale': 'Error',
        }

    prompt = f"""Analyze the following customer message:

{message}

Provide a concise analysis with the following structure:
1. Summary: A brief summary of the message.
2. Lead Type: Determine if it's a hot or cold lead.
3. Sentiment: Assess the overall sentiment (positive, negative, or neutral).
4. Rationality: Evaluate the rationality of the message.

Respond with only these four points, each on a new line."""

    response = model.generate_content(prompt)
    analysis = response.text.strip().split('\n')
    
    return {
        'summary': analysis[0].split(': ', 1)[1] if len(analysis) > 0 else '',
        'lead_type': analysis[1].split(': ', 1)[1] if len(analysis) > 1 else '',
        'sentiment': analysis[2].split(': ', 1)[1] if len(analysis) > 2 else '',
        'rationality': analysis[3].split(': ', 1)[1] if len(analysis) > 3 else ''
    }



# render all of the chats for the user
@app.route('/chat_history')
@login_required
def chat_history():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM Message ORDER BY timestamp')
    messages = cursor.fetchall()
    cursor.close()
    return render_template('chat_history.html', messages=messages)



# return wether the user is authenticated and it's type
@app.route('/check_session')
@login_required
def check_session():
    response_data = {
        'is_authenticated': bool(current_user.is_authenticated),
        'role': 'representative' if current_user.is_representative else 'customer'
    }
    return jsonify(response_data)


if __name__ == '__main__':
    # application context is required to perform certain actions like interacting with DB and ensure DB operations work properly
    with app.app_context():
        # creates all the tables defined in the SQLAlchemy models (users and messages)
        # db.create_all()
        pass
    # start the app with the support of socket.IOError
    socketio.run(app, debug=True)
    
