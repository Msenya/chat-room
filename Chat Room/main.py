from flask import Flask, config, render_template, request,  redirect, url_for, session, flash   # Flask web framework
from flask_socketio import SocketIO, send, emit, join_room, leave_room   # Flask SocketIO for real time communication
from flask_mysqldb import MySQL   # MySQL integration for Flask
from flask_wtf.csrf import CSRFProtect  # Import CSRF protection for form security
from log import setupLogger
import signal   # Signal module to handle termination signals
import sys   
import mysql.connector
from mysql.connector import errorcode   # Error codes for MySQL
import traceback   # Traceback module for printing stack traces
import socket
import re
from cryptography.fernet import Fernet
import json
import os

# Logger initialization
logger = setupLogger()

# Function to load the encryption key
def loadKey(filePath="config/encryptionKey.key") -> bytes:
    if os.path.exists(filePath):
        with open(filePath, "rb") as keyFile:
            return keyFile.read()
    
    else:
        logger.error("Encryption key not found")
        raise Exception("Encryption key not found")


# Function that decrypts the JSON configuration file
def decryptConfig() -> dict:
    key = loadKey()
    cipher = Fernet(key)

    with open("config/encryptedConfig.json.enc", "rb") as encryptedFile:
        encryptedData = encryptedFile.read()

    decryptedData = cipher.decrypt(encryptedData)
    return json.loads(decryptedData)


# load the configuration
config = decryptConfig()

# Flask initialization
app = Flask(__name__)
app.config["SECRET_KEY"] = config["secretKey"]   # Secret key for session management
csrf =  CSRFProtect(app)
csrf.init_app(app)
socketio = SocketIO(app, async_mode="threading")   # Flask-SocketIO with threading
mysql = MySQL(app)

# Database configurations
app.config["MYSQL_HOST"] = config["dbConfig"]["host"]
app.config["MYSQL_USER"] = config["dbConfig"]["user"]
app.config["MYSQL_PASSWORD"] = config["dbConfig"]["password"]
app.config["MYSQL_DB"] = config["dbConfig"]["database"]

# Function to get the local IP
def getLocalIP():
    # Use dummy connection to get local IP address
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.254.254.254', 1))
        localIP = s.getsockname()[0]

    except Exception:
        localIP = "localhost"
    
    finally:
        s.close()
    
    return localIP


# Function to database connection
def createConnection() -> None:
    try:
        connection = mysql.connector.connect(
            host = config["dbConfig"]["host"],
            user = config["dbConfig"]["user"],
            password = config["dbConfig"]["password"],
            database = config["dbConfig"]["database"]
        )
        return connection
    
    except mysql.connector.Error as e:
        if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your username or password")
            logger.error("Something wrong with username or password")
        
        elif e.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
            logger.error("Database does not exist")
        
        else:
            print(str(e))
            logger.error(str(e))

        traceback.print_exc()
        return None
    

# Function to insert user into the database
def insertUser(firstName, lastName, gender, dateOfBirth, email, phoneNumber, username, password):
    connection = createConnection()
    if connection:
        try:
            cursor = connection.cursor(prepared=True)
            sqlInsertQuery = """
            INSERT INTO users(first_name, last_name, gender, date_of_birth, email, phone_number, username, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sqlInsertQuery, (firstName, lastName, gender, dateOfBirth, email, phoneNumber, username, password))
            cursor.commit()
            print("User inserted successfully")
            logger.info("User successfully entered into database")

        except mysql.connector.Error as e:
            print(str(f"Error: {e}"))
            logger.error(str(e))

        finally:
            cursor.close()
            connection.close()


# This function checks if the password meets the strength requirements
def isStrongPassword(password) -> str | None:
    if len(password) < 8:
        return "Password must be at least 8 characters long"
    
    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter"

    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter"

    if not re.search(r"[0-9]", password):
        return "Password must contain at least one digit"

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return "Password must contain at least one special character"
    
    return None
        

clients = {}   # Dictionary to keep track of connected users

# Signal handler for termination signals
def handleExit(signum, frame) -> None:
    logger.info("Server is closed")
    sys.exit(0)


signal.signal(signal.SIGINT, handleExit)
signal.signal(signal.SIGTERM, handleExit)

@app.route('/')
# Function renders the home page
def home() -> str:
    logger.info("Home page requested")
    return render_template("home.html")


@app.route('/login', methods=['GET', 'POST'])
#  Function that handles login requests
def login() -> str:
    if request.method == 'POST':
        # csrfToken = request.form.get('csrf_token')   # Check CSRF token value
        # logger.info(f"CSRF Token: {csrfToken}")

        # Get username and password from form
        emailOrUsername = request.form["username"]
        password = request.form["password"]
        connection = createConnection()

        if connection:
            try:
                # Check if credentials match a user account
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM users WHERE (email = %s OR username = %s )AND password = %s', (emailOrUsername, emailOrUsername, password))   # Execute query to find user
                user = cursor.fetchone()

                if user:
                    session["username"] = user[0]
                    logger.info(f"User {emailOrUsername} logged in successfully")
                    return redirect(url_for("chat"))   # Redirect to chat page on successful login
                
                # Check if credentials match admin account
                cursor.execute("SELECT username, password FROM admin WHERE username = %s AND password = %s", ("admin", password))
                admin = cursor.fetchone()

                if admin:
                    session["username"] = admin[0]
                    logger.info("Admin logged in successfully")
                    return redirect(url_for("chat"))
        
                logger.warning(f"Failed login attempt for username: {emailOrUsername}")
                flash("Invalid email/username or password.")
            
            except mysql.connector.Error as e:
                logger.error(f"Error during logging: {str(e)}")
                traceback.print_exc()

            finally:
                cursor.close()
                connection.close()

        else:
            flash("Failed to connect to the database. Please try again later.")
            logger.error("Failed to connect to the database")
    
    logger.info("Login page requested")
    return render_template("login.html")    # Render and return the login page template


@app.route('/register', methods=['GET', 'POST'])
# Function that handles registration requests
def register() -> str:
    if request.method == 'POST':
        form = request.form

        firstName = request.form["first_name"]
        lastName = request.form["last_name"]
        gender = request.form["gender"]
        dateOfBirth = request.form["date_of_birth"]
        email = request.form["email"]
        phoneNumber = request.form["phone_number"]
        username = request.form["username"]
        password = request.form["password"]
        confirmPassword = request.form["confirmPassword"]
        cursor = mysql.connection.cursor()

        # Validate email format
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            flash("Invalid email format")
            return render_template("register.html")

        # Validate password strength
        passwordError = isStrongPassword(password)
        if passwordError:
            flash(passwordError)
            return render_template('register.html')

        # Check if passwords match
        if password != confirmPassword:
            flash("Passwords do not match")
            return render_template('register.html')
        
        # Insert user into database
        try:
            cursor.execute("INSERT INTO users(first_name, last_name, gender, date_of_birth, email, phone_number, username, password) VALUES (%s, %s, %s, %s, %s, %s, %s, %s", (firstName, lastName, gender, dateOfBirth, email, phoneNumber, username, password))
            mysql.connection.commit()
            cursor.close()
            logger.info(f"New user registered with username: {username}")
            return redirect(url_for('login'))   # Redirect login page upon successful registration
        
        except Exception as e: 
            logger.error(f"Error during registration: {e}")
            return "An error occurred during registration."
    
    logger.info("Registration page requested")
    return render_template('register.html')   # Render and return the registration page template


@app.route('/chat')
# Function that renders the chat room if the user is logged in
def chat() -> str:
    if 'username' in session:
        logger.info(f"User {session['username']} accessed the chat room")
        serverIP = getLocalIP()
        return render_template('chat.html', username=session['username'], server_ip=serverIP)
    
    logger.warning("Unauthenticated access to chat room attempted")
    return redirect(url_for('login'))


@socketio.on('message')
# Function that handles incoming messages from clients
def handleMessage(msg: str) -> None:
    username = session.get("username")

    if msg.startswith("KICK"):
        if username == "admin":
            nameToKick = msg.split(' ')[1]

            if nameToKick in clients:
                socketio.emit("kick", {"msg": f"You were kicked by an admin!", "name": nameToKick}, room=clients[nameToKick])
                leave_room(clients[nameToKick])   # Remove user from chat
                del clients[nameToKick]   # Remove user from clients dictionary
                logger.info(f"Admin kicked user: {nameToKick}")
        else:
            # Refuse command if not admin
            send("Command was refused!", room=request.sid)
    
    elif msg.startswith("BAN"):
        if username == "admin":
            nameToBan = msg.split(' ')[1]

            if nameToBan in clients:
                socketio.emit('ban', {'msg': f'You were banned by an admin!', 'name': nameToBan}, room=clients[nameToBan])
                leave_room(clients[nameToBan])

                with open("bans.txt", "a") as f:
                    f.write(f"{nameToBan}\n")
                
                del clients[nameToBan]
                logger.info(f"Admin banned user: {nameToBan}")
        else:
            send("Command was refused!", room=request.sid)
        
    else:
        if username:
            send({"msg" : msg, "username": username}, broadcast=True)
            logger.info(f"Message from {username}: {msg}")


@socketio.on('join')
# Function that handles clients joining the chat
def onJoin(data: dict) -> None: 
    username = session.get('username')

    if username:
        with open("bans.txt", "r") as f:
            bans = f.readlines()
        if username + "\n" in bans:
            send("You are banned from the chat!", room=request.sid)
            return
        
        # check if the number of connected clients exceeds the maximum 
        if len(clients) >= config["maxClients"]:
            send("The chat room is full. Please try again later.", room=request.sid)
            logger.warning(f"User {username} was denied due to full capacity")
            return
        
        clients[username] = request.sid   # Add user to clients
        join_room(request.sid)   # Join users session ID to room
        send(f"{username} has joined the chat!", broadcast=True)
        logger.info(f"User {username} joined the chat room")
        emit("updateUserList", list(clients.keys()), broadcast=True)   # Update user list


@socketio.on('disconnect')
# This function handles users disconnecting from the chat
def onLeave() -> None:
    username = session.get("username")

    if username and username in clients:
        del clients[username]
        send(f"{username} has left the chat!", broadcast=True)
        logger.info(f"User {username} left the chat room")
        emit("updateUserList", list(clients.keys()), broadcast=True)


if __name__ == "__main__":
    localIP = getLocalIP()
    print(f"Server is listening on {localIP}:45454")
    logger.info(f"Server is listening on {localIP}:45454")
    app.debug = True
    socketio.run(app, host=localIP, port=config["portNumber"])

