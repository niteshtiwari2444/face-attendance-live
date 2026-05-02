import cv2
import os

name = input("Enter your name: ")

folder = "dataset/" + name
os.makedirs(folder, exist_ok=True)

camera = cv2.VideoCapture(0)
count = 0

print("Camera started")
print("Press SPACE to take photo")
print("Press ESC to stop")

while True:
    success, frame = camera.read()

    if not success:
        print("Camera not working")
        break

    cv2.imshow("Register Face", frame)

    key = cv2.waitKey(1)

    if key == 32:
        count = count + 1
        path = folder + "/" + name + "_" + str(count) + ".jpg"
        cv2.imwrite(path, frame)
        print("Photo saved:", path)

    if key == 27:
        break

camera.release()
cv2.destroyAllWindows()

print("Done")