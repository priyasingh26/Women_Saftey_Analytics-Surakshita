import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename
import cv2
from qreader import QReader
from aadhaar.secure_qr import extract_data
from geopy.distance import geodesic
from flask_mail import Mail, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bkt123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit for file uploads
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Replace with your email server (e.g., Gmail, Outlook)
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'noreply.surakshitha@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'ccgc mimz wvby onkq'  # Replace with your email password or app password
app.config['MAIL_DEFAULT_SENDER'] = 'noreply.surakshitha@gmail.com'

mail = Mail(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Create a QReader instance for QR code reading
qreader = QReader()

# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)  # Add this line
    phone_number = db.Column(db.String(15), nullable=True)
    latitude = db.Column(db.Float)  # Add this if it's not there
    longitude = db.Column(db.Float)  # Add this if it's not there
    profile_image_url = db.Column(db.String(255), nullable=True)
    aadhar_reference_id = db.Column(db.String(12), unique=True, nullable=True)
    aadhar_timestamp = db.Column(db.DateTime, nullable=True)
    aadhar_name = db.Column(db.String(100), nullable=True)
    aadhar_date_of_birth = db.Column(db.String(10), nullable=True)
    aadhar_gender = db.Column(db.String(10), nullable=True)
    aadhar_address_care_of = db.Column(db.String(100), nullable=True)
    aadhar_address_district = db.Column(db.String(100), nullable=True)
    aadhar_address_landmark = db.Column(db.String(100), nullable=True)
    aadhar_address_house = db.Column(db.String(100), nullable=True)
    aadhar_address_location = db.Column(db.String(100), nullable=True)
    aadhar_address_pin_code = db.Column(db.String(10), nullable=True)
    aadhar_address_post_office = db.Column(db.String(100), nullable=True)
    aadhar_address_state = db.Column(db.String(100), nullable=True)
    aadhar_address_street = db.Column(db.String(100), nullable=True)
    aadhar_address_sub_district = db.Column(db.String(100), nullable=True)
    aadhar_address_vtc = db.Column(db.String(100), nullable=True)
    __table_args__ = (
        db.UniqueConstraint('aadhar_reference_id', 'aadhar_name', name='uix_aadhar_reference_id_name'),
    )

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def verify_aadhar(image):
    # image = cv2.cvtColor(cv2.imread(file_path), cv2.COLOR_BGR2RGB)
    decoded_text = qreader.detect_and_decode(image=image)

    if decoded_text:
        received_qr_code_data = int(decoded_text[0])
        extracted_data = extract_data(received_qr_code_data)
        # Convert extracted_data to a dictionary or tuple
        return {
            "reference_id": extracted_data.text_data.reference_id.last_four_aadhaar_digits,
            "timestamp": extracted_data.text_data.reference_id.timestamp,
            "name": extracted_data.text_data.name,
            "date_of_birth": extracted_data.text_data.date_of_birth,
            "gender": extracted_data.text_data.gender.value,  # Use .value to get string representation
            "address": {
                "care_of": extracted_data.text_data.address.care_of,
                "district": extracted_data.text_data.address.district,
                "landmark": extracted_data.text_data.address.landmark,
                "house": extracted_data.text_data.address.house,
                "location": extracted_data.text_data.address.location,
                "pin_code": extracted_data.text_data.address.pin_code,
                "post_office": extracted_data.text_data.address.post_office,
                "state": extracted_data.text_data.address.state,
                "street": extracted_data.text_data.address.street,
                "sub_district": extracted_data.text_data.address.sub_district,
                "vtc": extracted_data.text_data.address.vtc,
            }
        }
    return None
# Add this to your existing imports
from datetime import datetime, timezone

# Database Model for Complaints
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False)
    complaint_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None))

# Create the table
with app.app_context():
    db.create_all()

with app.app_context():
    db.create_all()

from twilio.rest import Client
import requests

user_locations = {}

@app.route('/send-location', methods=['POST'])
def send_location():
    data = request.json
    user_id = "user123"  # Example user ID
    user_locations[user_id] = data['location']
    send_alerts(data['location'])
    return jsonify({"status": "Location updated"}), 200

# Generate tracking link
@app.route('/track-location/<user_id>', methods=['GET'])
def track_location(user_id):
    location = user_locations.get(user_id)
    if location:
        return jsonify({"location": location}), 200
    return jsonify({"error": "No location data available"}), 404

account_sid = 'AC122e95236860d5d538c4a0a8e5e75edf'
auth_token = 'e8a883a9212dc40ebb0688fdea22e19a'
client = Client(account_sid, auth_token)

contacts = ['+919601264186']

def make_call(to_phone_number, from_phone_number, twiml_url):
    """Make a phone call using Twilio."""
    call = client.calls.create(
        to=to_phone_number,
        from_=from_phone_number,
        url=twiml_url  # URL pointing to TwiML instructions
    )
    return call.sid

def send_alerts(user_location):
    # Twilio setup

    message_body = f"Emergency! {session['username']} current location: {user_location}"

    for contact in contacts:
        client.messages.create(
            body=message_body,
            from_='+17277776274',
            to=contact
        )

    # Notify police
    police_contact = '+919601264186'
    client.messages.create(
        body=message_body,
        from_='+17277776274',
        to=police_contact
    )

@app.route('/emergency-alert', methods=['POST'])
def emergency_alert():
    # user_location = request.json['location']  # Get user location (from frontend)
    # send_alerts(user_location)  # Send alerts to contacts and police
    to_phone_number = '+919601264186'  # Replace with the recipient's phone number
    from_phone_number = '+17277776274'  # Replace with your Twilio phone number
    twiml_url = 'http://example.com/twiml'  # URL pointing to TwiML instructions

    call_sid = make_call(to_phone_number, from_phone_number, twiml_url)
    return jsonify({"status": "alert triggered"}), 200

@app.route("/")
def home():
    if 'username' in session:
        # If the user is already logged in, redirect them to the dashboard
        return redirect(url_for('dashboard'))
    return render_template("index.html")

@app.route('/user_counts', methods=['GET'])
def get_user_counts():
    user_lat = float(request.args.get('latitude'))
    user_lon = float(request.args.get('longitude'))

    male_count = 0
    female_count = 0

    users = User.query.all()

    for user in users:
        if user.latitude and user.longitude:
            user_location = (user.latitude, user.longitude)
            current_location = (user_lat, user_lon)
            distance = geodesic(user_location, current_location).km

            if distance <= 1:  # within 1km
                if user.gender == 'Male':
                    male_count += 1
                elif user.gender == 'Female':
                    female_count += 1

    return jsonify({
        'male_count': male_count,
        'female_count': female_count
    })

from werkzeug.utils import secure_filename

# Ensure the upload folder exists in your project
app.config['PROFILE_UPLOAD_FOLDER'] = os.path.join('static', 'profile_images')

# Function to check allowed extensions
def allowed_profile_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

import os
import time  # for using timestamp # for generating a unique filename

@app.route('/upload_profile_image', methods=['POST'])
def upload_profile_image():
    if 'username' not in session:
        flash('You need to log in to upload an image.', 'danger')
        return redirect(url_for('login'))

    if 'profile_image' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('profile'))

    file = request.files['profile_image']

    if file and allowed_profile_file(file.filename):
        # Generate a unique filename using username and timestamp
        ext = file.filename.rsplit('.', 1)[1].lower()  # Get file extension
        unique_filename = f"{session['username']}_{int(time.time())}.{ext}"

        filepath = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)

        # Use forward slashes for URLs
        relative_file_path = os.path.join('profile_images', unique_filename).replace('\\', '/')

        # Update the user's profile_image_url in the database
        user = User.query.filter_by(username=session['username']).first()
        if user:
            user.profile_image_url = relative_file_path  # Save relative path with forward slashes
            db.session.commit()
            flash('Profile image uploaded successfully!', 'success')
        else:
            flash('User not found.', 'danger')

        return redirect(url_for('profile'))
    else:
        flash('Invalid file format. Only images are allowed.', 'danger')
        return redirect(url_for('profile'))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        email = request.form["email"]
        phone_number = request.form["phone_number"]

        if User.query.filter_by(username=username).first():
            flash("Username already taken. Please choose another.", "error")
            return redirect(request.url)
        elif User.query.filter_by(email=email).first():
            flash("Email already registered. Please choose another.", "error")
            return redirect(request.url)
            # return redirect(request.url)
        else:
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
            new_user = User(username=username, password=hashed_password, email=email, phone_number=phone_number)
            db.session.add(new_user)
            db.session.commit()

            # Send welcome email
            send_welcome_email(email, username)
            flash("Registration successful. You can now log in.", "success")
            session['username'] = username
            return redirect(url_for("upload_aadhar"))
    return render_template("register.html")

# Function to send email
def send_welcome_email(to_email, username):
    print(to_email,type(to_email))
    msg = Message('Welcome to Our App!',
                  recipients=[to_email],
                  body=f"Hello {username},\n\nThank you for registering at our app! We are excited to have you with us.\n\nBest regards,\nThe Team")

    mail.send(msg)

@app.route("/login", methods=["GET", "POST"])
def login():
    if 'username' in session:
        # If user is already logged in, redirect them to the dashboard
        flash("You are already logged in!", "info")
        return redirect(url_for('dashboard'))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["username"] = username
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password. Please try again.", "error")

    return render_template("index2.html")


# Aadhaar Upload Route after Login
@app.route('/upload_aadhar', methods=['GET', 'POST'])
def upload_aadhar():
    if 'username' not in session:
        flash('You need to register first!', 'danger')
        return redirect(url_for('register'))

    if request.method == 'POST':
        file = request.files['aadhar_card_image']

        if file and allowed_file(file.filename):
            file_bytes = file.read()

            # Convert the file bytes to a numpy array for OpenCV
            npimg = np.frombuffer(file_bytes, np.uint8)
            image = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

            # Verify the Aadhaar QR code
            aadhar_data = verify_aadhar(image)
            if not aadhar_data:
                flash('Invalid Aadhaar QR code. Please try again.', 'danger')
                return redirect(request.url)

            # Check if Aadhaar data already exists
            existing_user = User.query.filter_by(
                aadhar_reference_id=aadhar_data['reference_id'],
                aadhar_name=aadhar_data['name']
            ).first()

            if existing_user:
                flash('Aadhaar already registered with this reference_id and name. Cannot create duplicate account.', 'danger')
                return redirect(request.url)

            # Update user's Aadhaar data
            user = User.query.filter_by(username=session['username']).first()
            # print(user,"nope")
            if user:
                user.aadhar_reference_id = aadhar_data['reference_id']
                user.aadhar_timestamp = aadhar_data['timestamp']
                user.aadhar_name = aadhar_data['name']
                user.aadhar_date_of_birth = aadhar_data['date_of_birth']
                user.aadhar_gender = aadhar_data['gender']
                user.aadhar_address_care_of = aadhar_data['address']['care_of']
                user.aadhar_address_district = aadhar_data['address']['district']
                user.aadhar_address_landmark = aadhar_data['address']['landmark']
                user.aadhar_address_house = aadhar_data['address']['house']
                user.aadhar_address_location = aadhar_data['address']['location']
                user.aadhar_address_pin_code = aadhar_data['address']['pin_code']
                user.aadhar_address_post_office = aadhar_data['address']['post_office']
                user.aadhar_address_state = aadhar_data['address']['state']
                user.aadhar_address_street = aadhar_data['address']['street']
                user.aadhar_address_sub_district = aadhar_data['address']['sub_district']
                user.aadhar_address_vtc = aadhar_data['address']['vtc']
                db.session.commit()
                flash('Aadhaar card uploaded and verified successfully!', 'success')
                return redirect(url_for('login'))
            else:
                flash('User not found. Please try again.', 'danger')
    return render_template('upload_aadhar.html')
# Serve Uploaded Files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        flash('You need to log in first.', 'danger')
        return redirect(url_for('login'))

    # Check if there are any users in the database
    user_count = User.query.count()

    if user_count == 0:
        flash('No users registered. Please register first.', 'warning')
        return redirect(url_for('register'))

    return render_template('dashboard.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/safety_tips')
def safety_tips():
    return render_template('safety_tips.html')

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()
    print(user)
    if user is None:
        return redirect(url_for('login'))

    return render_template('profile.html', user=user)

@app.route('/recent_incidents')
def recent_incidents():
    return render_template('recent_incidents.html')

@app.route("/complaints", methods=["GET", "POST"])
def complaints():
    # Handle POST request
    if request.method == "POST":
        if 'username' not in session:
            flash("You need to log in to submit a complaint.", "warning")
            return redirect(url_for("login"))

        complaint_text = request.form.get("complaint_text")
        if complaint_text:
            new_complaint = Complaint(username=session['username'], complaint_text=complaint_text)
            db.session.add(new_complaint)
            db.session.commit()
            flash("Your complaint has been submitted.", "success")
        else:
            flash("Complaint cannot be empty.", "danger")

        # Redirect to the complaints page after submitting
        return redirect(url_for("complaints"))

    # Handle GET request and pagination
    page = request.args.get('page', 1, type=int)
    per_page = 10
    complaints = Complaint.query.order_by(Complaint.timestamp.desc()).paginate(page, per_page, False)

    return render_template('complaints.html', complaints=complaints.items, pagination=complaints)



if __name__ == "__main__":
    app.run(debug=True)