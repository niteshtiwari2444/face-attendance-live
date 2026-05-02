import cv2
import pickle
import pandas as pd
import os
from datetime import datetime

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("encodings/trainer.yml")

with open("encodings/names.pkl", "rb") as file:
    names = pickle.load(file)

face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

os.makedirs("attendance_records", exist_ok=True)

today = datetime.now().strftime("%d-%m-%Y")
file_name = "attendance_records/Attendance_" + today + ".csv"

if not os.path.exists(file_name):
    df = pd.DataFrame(columns=["Name", "Date", "Time"])
    df.to_csv(file_name, index=False)

marked = []

camera = cv2.VideoCapture(0)

print("Attendance System Started")
print("Press ESC to stop")

while True:
    success, frame = camera.read()

    if not success:
        print("Camera not working")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face = gray[y:y+h, x:x+w]

        label, confidence = recognizer.predict(face)

        if confidence < 80:
            name = names[label]

            if name not in marked:
                now = datetime.now()
                date = now.strftime("%d-%m-%Y")
                time = now.strftime("%H:%M:%S")

                df = pd.DataFrame(
                    [[name, date, time]],
                    columns=["Name", "Date", "Time"]
                )

                df.to_csv(file_name, mode="a", header=False, index=False)

                marked.append(name)
                print("Attendance marked for:", name)
        else:
            name = "Unknown"

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(
            frame,
            name,
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    cv2.imshow("Attendance System", frame)

    if cv2.waitKey(1) == 27:
        break

camera.release()
cv2.destroyAllWindows()

print("System Closed")