from flask import Flask, render_template, request, redirect, url_for, Response, jsonify
import cv2
import os
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
import time

app = Flask(__name__)

# Global variables for camera and recognition
recognizer = None
face_detector = None
names = None
marked_persons = set()
is_attendance_running = False

def load_recognizer():
    global recognizer, face_detector, names
    
    face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        if os.path.exists("encodings/trainer.yml"):
            recognizer.read("encodings/trainer.yml")
            print("✅ Recognizer loaded")
        else:
            print("⚠️ No trained model found")
    except:
        print("⚠️ Using detection only")
        recognizer = None
    
    if os.path.exists("encodings/names.pkl"):
        with open("encodings/names.pkl", "rb") as f:
            names = pickle.load(f)
    else:
        names = {}

def initialize_folders():
    os.makedirs("dataset", exist_ok=True)
    os.makedirs("encodings", exist_ok=True)
    os.makedirs("attendance_records", exist_ok=True)
    load_recognizer()

initialize_folders()

@app.route('/')
def index():
    registered = len([d for d in os.listdir("dataset") if os.path.isdir(f"dataset/{d}") and len(os.listdir(f"dataset/{d}")) > 0]) if os.path.exists("dataset") else 0
    
    today = datetime.now().strftime("%d-%m-%Y")
    today_file = f"attendance_records/Attendance_{today}.csv"
    today_count = 0
    if os.path.exists(today_file):
        try:
            df = pd.read_csv(today_file)
            today_count = len(df)
        except:
            today_count = 0
    
    total_files = len([f for f in os.listdir("attendance_records") if f.endswith('.csv')])
    
    return render_template('index.html', 
                         registered_count=registered,
                         today_attendance=today_count,
                         total_records=total_files)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/video_feed_register')
def video_feed_register():
    def gen():
        cap = cv2.VideoCapture(0)
        while True:
            success, frame = cap.read()
            if not success:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        cap.release()
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture_photo', methods=['POST'])
def capture_photo():
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'message': 'Name required'})
    
    folder = f"dataset/{name}"
    os.makedirs(folder, exist_ok=True)
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    time.sleep(0.5)  # Stable camera
    success, frame = cap.read()
    cap.release()
    
    if success:
        # Save raw frame first
        photos = len([f for f in os.listdir(folder) if f.endswith('.jpg')])
        raw_path = f"{folder}/{name}_{photos+1}.jpg"
        cv2.imwrite(raw_path, frame)
        
        # Verify save
        if os.path.exists(raw_path) and os.path.getsize(raw_path) > 1000:
            return jsonify({'success': True, 'message': f'Photo {photos+1} saved!', 'count': photos+1})
        else:
            if os.path.exists(raw_path):
                os.remove(raw_path)
            return jsonify({'success': False, 'message': 'Image too small - retry'})
    return jsonify({'success': False, 'message': 'Camera capture failed'})

@app.route('/get_photo_count/<name>')
def get_photo_count(name):
    folder = f"dataset/{name}"
    count = len([f for f in os.listdir(folder) if f.endswith('.jpg')]) if os.path.exists(folder) else 0
    return jsonify({'count': count})

@app.route('/get_all_users')
def get_all_users():
    users = []
    if os.path.exists("dataset"):
        for user in os.listdir("dataset"):
            folder = f"dataset/{user}"
            if os.path.isdir(folder):
                photos = len([f for f in os.listdir(folder) if f.endswith('.jpg')])
                if photos > 0:
                    users.append({'name': user, 'photo_count': photos})
    return jsonify({'users': sorted(users, key=lambda x: x['name'].lower())})

@app.route('/delete_user', methods=['POST'])
def delete_user():
    data = request.get_json()
    name = data.get('name', '').strip()
    
    folder = f"dataset/{name}"
    if os.path.exists(folder):
        import shutil
        shutil.rmtree(folder, ignore_errors=True)
        load_recognizer()
        return jsonify({'success': True, 'message': f'{name} deleted'})
    return jsonify({'success': False, 'message': 'User not found'})

@app.route('/train')
def train():
    return render_template('train.html')

@app.route('/run_training', methods=['POST'])
def run_training():
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        faces = []
        labels = []
        name_dict = {}
        label_id = 0
        
        if not os.path.exists("dataset"):
            return jsonify({'success': False, 'message': 'No dataset'})
        
        for person in os.listdir("dataset"):
            person_path = f"dataset/{person}"
            if not os.path.isdir(person_path):
                continue
                
            photos = [f for f in os.listdir(person_path) if f.endswith('.jpg')]
            if len(photos) == 0:
                continue
                
            name_dict[label_id] = person
            
            for photo in photos:
                img_path = f"{person_path}/{photo}"
                img = cv2.imread(img_path)
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                face_rects = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in face_rects:
                    face = gray[y:y+h, x:x+w]
                    faces.append(face)
                    labels.append(label_id)
            
            label_id += 1
        
        if len(faces) > 0:
            recognizer.train(faces, np.array(labels))
            recognizer.save("encodings/trainer.yml")
            
            with open("encodings/names.pkl", "wb") as f:
                pickle.dump(name_dict, f)
            
            load_recognizer()
            return jsonify({'success': True, 'message': 'Training complete! ✅'})
        return jsonify({'success': False, 'message': 'No faces to train'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/attendance')
def attendance():
    global is_attendance_running
    is_attendance_running = True
    return render_template('attendance.html', subjects=['Math', 'Science', 'English', 'Physics', 'Chemistry', 'CS', 'History', 'General'])

@app.route('/video_feed_attendance')
def video_feed_attendance():
    global is_attendance_running
    subject = request.args.get('subject', 'General')
    
    def gen():
        global marked_persons
        marked_persons = set()
        
        cap = cv2.VideoCapture(0)
        cap.set(3, 640)
        cap.set(4, 480)
        
        today = datetime.now().strftime("%d-%m-%Y")
        csv_file = f"attendance_records/Attendance_{today}.csv"
        if not os.path.exists(csv_file):
            pd.DataFrame(columns=["Name", "Subject", "Date", "Time"]).to_csv(csv_file, index=False)
        
        while is_attendance_running:
            success, frame = cap.read()
            if not success:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_detector.detectMultiScale(gray, 1.2, 4)
            
            for (x, y, w, h) in faces:
                face_roi = cv2.resize(gray[y:y+h, x:x+w], (100, 100))
                face_roi = cv2.equalizeHist(face_roi)
                
                name = "Unknown"
                confidence = 999
                if recognizer and names:
                    try:
                        label, confidence = recognizer.predict(face_roi)
                        print(f"🎯 PREDICT: label={label}, conf={confidence:.0f}")
                        if confidence < 120:  # VERY LENIENT
                            name = names.get(label, "Unknown")
                        else:
                            name = "Unknown"
                        
                        if name not in marked_persons and name != "Unknown":
                            subject = request.args.get('subject', 'General')
                            now = datetime.now()
                            new_row = pd.DataFrame([[name, subject, now.strftime("%d-%m-%Y"), now.strftime("%H:%M:%S")]],
                                                 columns=["Name", "Subject", "Date", "Time"])
                            new_row.to_csv(csv_file, mode='a', header=False, index=False)
                            marked_persons.add(name)
                            print(f"✅ {name} ATTENDED! Conf: {confidence:.0f}")
                    except Exception as e:
                        print(f"❌ Recognition error: {e}")

                
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                cv2.rectangle(frame, (x, y-40), (x+w, y), (0, 255, 0), cv2.FILLED)
                cv2.putText(frame, name, (x+10, y-15), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                cv2.putText(frame, f"Conf: {confidence if 'confidence' in locals() else 999}", (x+10, y-3), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
        cap.release()
    
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_attendance', methods=['POST'])
def stop_attendance():
    global is_attendance_running
    is_attendance_running = False
    return jsonify({'success': True})

@app.route('/get_marked_today')
def get_marked_today():
    today = datetime.now().strftime("%d-%m-%Y")
    file = f"attendance_records/Attendance_{today}.csv"
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            return jsonify({'marked': df['Name'].unique().tolist()})
        except:
            pass
    return jsonify({'marked': []})

@app.route('/records')
def records():
    records = []
    if os.path.exists("attendance_records"):
        for file in sorted(os.listdir("attendance_records")):
            if file.endswith('.csv'):
                path = f"attendance_records/{file}"
                try:
                    df = pd.read_csv(path)
                    date = file.replace('Attendance_', '').replace('.csv', '')
                    for _, row in df.iterrows():
                        records.append({
                            'name': row['Name'],
                            'subject': row.get('Subject', 'General'),
                            'date': date,
                            'time': row['Time']
                        })
                except:
                    continue
    records.sort(key=lambda x: x['date'], reverse=True)
    return render_template('records.html', records=records)

@app.route('/delete_record/<filename>', methods=['DELETE'])
def delete_record(filename):
    path = f"attendance_records/{filename}"
    try:
        if os.path.exists(path):
            os.remove(path)
            return jsonify({'success': True, 'message': f'{filename} deleted'})
    except:
        pass
    return jsonify({'success': False, 'message': 'Failed'})

@app.route('/clear_all')
def clear_all():
    for file in os.listdir("attendance_records"):
        try:
            os.remove(f"attendance_records/{file}")
        except:
            pass
    return jsonify({'success': True, 'message': 'All records cleared'})

if __name__ == '__main__':
    app.run(debug=False, port=int(os.environ.get('PORT', 5000)), host='0.0.0.0')

