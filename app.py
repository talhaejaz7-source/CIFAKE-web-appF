from __future__ import division, print_function
# coding=utf-8

import os
import io
import base64
import random
import sqlite3
import smtplib
from email.message import EmailMessage

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for thread-safety in Flask
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, redirect, url_for

from keras.layers import MaxPooling2D, Dense, Dropout, Flatten, Convolution2D
from keras.models import Sequential, Model

app = Flask(__name__)

# Global variables for simple session/OTP handling
otp = None
username = ""
name = ""
email = ""
number = ""
password = ""

# Initialize SQLite database and table if they do not exist (crucial for clean deployments)
try:
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS info(user varchar(250), email varchar(250), password varchar(250), mobile int, name varchar(250))")
    
    # Insert a default tester/admin account so login is guaranteed to work even after Render container restarts
    cur.execute("SELECT * FROM info WHERE user='admin'")
    if cur.fetchone() is None:
        cur.execute("INSERT INTO `info` (`user`, `email`, `password`, `mobile`, `name`) VALUES (?, ?, ?, ?, ?)",
                    ('admin', 'admin@test.com', 'Admin#123', 9999999999, 'Admin Tester'))
        print("Default tester/admin account created (Username: admin, Password: Admin#123).")
        
    con.commit()
    con.close()
    print("Database initialized successfully.")
except Exception as e:
    print("Error initializing database:", e)

path = "Dataset"
if os.path.exists(path):
    labels = sorted([d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))])
else:
    labels = ['FAKE', 'REAL']
print("Dataset Class Labels : " + str(labels))


def getLabel(name):
    index = -1
    for i in range(len(labels)):
        if labels[i] == name:
            index = i
            break
    return index


def getModel():
    extension_model = Sequential()
    extension_model.add(Convolution2D(32, (3, 3), input_shape=(32, 32, 3), activation='relu'))
    extension_model.add(MaxPooling2D(pool_size=(2, 2)))
    extension_model.add(Dropout(0.3))
    extension_model.add(Convolution2D(32, (3, 3), activation='relu'))
    extension_model.add(MaxPooling2D(pool_size=(2, 2)))
    extension_model.add(Dropout(0.3))
    extension_model.add(Flatten())
    extension_model.add(Dense(units=256, activation='relu'))
    extension_model.add(Dense(units=2, activation='softmax'))
    
    extension_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    extension_model.load_weights("model/extension_weights.hdf5")
    return extension_model


# Initialize model and Grad-CAM globally once at startup to prevent OOM memory leak
extension_model = getModel()
grad_cam_model = Model(inputs=extension_model.inputs, outputs=extension_model.layers[0].output)

# Warm up TensorFlow execution graph at startup to avoid delay on first user request
try:
    dummy_input = np.zeros((1, 32, 32, 3), dtype='float32')
    extension_model(dummy_input, training=False)
    grad_cam_model(dummy_input, training=False)
    print("TensorFlow graph warmed up successfully.")
except Exception as e:
    print("Warning: TensorFlow warm-up failed:", e)


def GradCamImage(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    if image is None:
        return np.zeros((30, 30, 32))
    img = cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA)
    im2arr = np.array(img).reshape(1, 32, 32, 3).astype('float32') / 255.0
    preds = grad_cam_model(im2arr, training=False).numpy()[0]
    return preds


@app.route("/about")
def about():
    return render_template("graph.html")


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/logon')
def logon():
    return render_template('signup.html')


@app.route('/login')
def login():
    return render_template('signin.html')


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'POST':
        print("\n>>> [predict] Received POST request from client", flush=True)
        try:
            if 'files' not in request.files:
                print(">>> [predict] 'files' not in request.files", flush=True)
                return redirect(url_for('home'))
            
            file = request.files['files']
            if file.filename == '':
                print(">>> [predict] Empty filename, redirecting to home", flush=True)
                return redirect(url_for('home'))

            print(f">>> [predict] Uploaded file name: {file.filename}", flush=True)
            os.makedirs("static", exist_ok=True)
            test_path = os.path.join("static", "test.jpg")
            
            file.save(test_path)
            print(">>> [predict] File saved locally to static/test.jpg", flush=True)

            image = cv2.imread(test_path, cv2.IMREAD_COLOR)
            if image is None:
                print(">>> [predict] cv2 could not read the image file!", flush=True)
                return redirect(url_for('home'))

            print(">>> [predict] Image read successfully. Resizing...", flush=True)
            # Use INTER_AREA interpolation to avoid pixel aliasing when downscaling high-res photos to 32x32
            img = cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA)
            im2arr = np.array(img).reshape(1, 32, 32, 3).astype('float32') / 255.0

            print(">>> [predict] Running model prediction...", flush=True)
            prediction = extension_model(im2arr, training=False).numpy()
            predict_idx = np.argmax(prediction)
            print(f">>> [predict] Prediction complete: {labels[predict_idx]}", flush=True)

            print(">>> [predict] Generating Grad-CAM...", flush=True)
            grad_cam = GradCamImage(test_path)
            print(">>> [predict] Grad-CAM complete", flush=True)

            display_img = cv2.imread(test_path)
            display_img = cv2.resize(display_img, (500, 300))
            
            predicted_label = labels[predict_idx] if predict_idx < len(labels) else "Unknown"
            cv2.putText(display_img, 'Predicted As : ' + predicted_label, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            output = 'Predicted As : ' + predicted_label

            # OpenCV side-by-side image generation (uses virtually 0MB memory compared to Matplotlib)
            heatmap = grad_cam[:, :, 31]
            heatmap = np.maximum(heatmap, 0)
            max_val = np.max(heatmap)
            if max_val > 0:
                heatmap = heatmap / max_val
            heatmap = np.uint8(255 * heatmap)
            
            # Apply color map and resize
            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            heatmap_color = cv2.resize(heatmap_color, (500, 300))
            
            # Concatenate original image and heatmap side-by-side
            combined = np.hstack((display_img, heatmap_color))

            # Encode image to base64 directly using cv2
            _, encoded_img = cv2.imencode('.png', combined)
            img_b64 = base64.b64encode(encoded_img).decode()
            print(">>> [predict] Base64 encoding complete. Rendering after.html...", flush=True)

            return render_template('after.html', msg=output, img=img_b64)
        except Exception as e:
            import traceback
            print("\n" + "!"*50, flush=True)
            print(" [PREDICT ERROR TRACEBACK]:", flush=True)
            traceback.print_exc()
            print("!"*50 + "\n", flush=True)
            return f"Error during prediction: {str(e)}. Please check Render dashboard Logs for detail."
    
    return redirect(url_for('home'))


@app.route("/signup")
def signup():
    global otp, username, name, email, number, password
    username = request.args.get('user', '')
    name = request.args.get('name', '')
    email = request.args.get('email', '')
    number = request.args.get('mobile', '')
    password = request.args.get('password', '')
    otp = random.randint(1000, 9999)
    print("\n" + "="*40)
    print(f" [OTP GENERATED] for {email}: {otp}")
    print("="*40 + "\n")

    email_sent = False
    try:
        msg = EmailMessage()
        msg.set_content("Your OTP is : " + str(otp))
        msg['Subject'] = 'OTP'
        msg['From'] = "evotingotp4@gmail.com"
        msg['To'] = email

        s = smtplib.SMTP('smtp.gmail.com', 587, timeout=5)
        s.starttls()
        s.login("evotingotp4@gmail.com", "xowpojqyiygprhgr")
        s.send_message(msg)
        s.quit()
        email_sent = True
        print("OTP email sent successfully!")
    except Exception as e:
        print("Error sending OTP email (SMTP block/auth error):", e)

    return render_template("val.html", otp=otp, email=email, email_sent=email_sent)


@app.route('/predict_lo', methods=['POST'])
def predict_lo():
    global otp, username, name, email, number, password
    if request.method == 'POST':
        message = request.form.get('message', '')
        print("Entered OTP:", message)
        if otp is not None and message.isdigit() and int(message) == otp:
            print("OTP Verification Success")
            con = sqlite3.connect('signup.db')
            cur = con.cursor()
            cur.execute("insert into `info` (`user`,`email`, `password`,`mobile`,`name`) VALUES (?, ?, ?, ?, ?)",
                        (username, email, password, number, name))
            con.commit()
            con.close()
            return render_template("signin.html")
    return render_template("signup.html")


@app.route("/signin")
def signin():
    mail1 = request.args.get('user', '')
    password1 = request.args.get('password', '')
    con = sqlite3.connect('signup.db')
    cur = con.cursor()
    cur.execute("select `user`, `password` from info where `user` = ? AND `password` = ?", (mail1, password1,))
    data = cur.fetchone()
    con.close()

    if data is None:
        return render_template("signin.html")
    elif mail1 == str(data[0]) and password1 == str(data[1]):
        return render_template("home.html")
    else:
        return render_template("signin.html")


@app.route("/notebook")
def notebook1():
    return render_template("CIFAKE.html")


if __name__ == '__main__':
    app.run(debug=False)
