import cv2
import os
import numpy as np
import pickle

dataset = "dataset"

recognizer = cv2.face.LBPHFaceRecognizer_create()
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

faces = []
labels = []
names = {}
label_id = 0

for person_name in os.listdir(dataset):
    person_folder = os.path.join(dataset, person_name)

    if not os.path.isdir(person_folder):
        continue

    names[label_id] = person_name

    for photo in os.listdir(person_folder):
        photo_path = os.path.join(person_folder, photo)

        if not photo.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        image = cv2.imread(photo_path)

        if image is None:
            print("Cannot read image:", photo_path)
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        detected_faces = face_detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in detected_faces:
            face = gray[y:y+h, x:x+w]
            faces.append(face)
            labels.append(label_id)
            print("Face trained:", person_name)

    label_id += 1

if len(faces) == 0:
    print("No faces found. Please capture photos again.")
    exit()

os.makedirs("encodings", exist_ok=True)

recognizer.train(faces, np.array(labels))
recognizer.save("encodings/trainer.yml")

with open("encodings/names.pkl", "wb") as file:
    pickle.dump(names, file)

print("Training completed")