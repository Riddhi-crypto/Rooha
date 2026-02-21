import cv2
import os
import shutil
import random

# Load Haar cascades
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
smile_cascade = cv2.CascadeClassifier('haarcascade_smile.xml')

# Paths
music_folder = 'music'
favorites_folder = 'favorites'

# Create favorites folder if it doesn't exist
if not os.path.exists(favorites_folder):
    os.makedirs(favorites_folder)

# Start video capture
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y+h, x:x+w]
        roi_color = frame[y:y+h, x:x+w]

        # Draw rectangle around face
        cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)

        smiles = smile_cascade.detectMultiScale(roi_gray, 1.8, 20)

        for (sx, sy, sw, sh) in smiles:
            cv2.rectangle(roi_color, (sx, sy), (sx+sw, sy+sh), (0, 255, 0), 2)
            cv2.putText(frame, "Smile Detected!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

            # Pick a random song
            songs = [f for f in os.listdir(music_folder) if f.endswith('.mp3')]
            if songs:
                song = random.choice(songs)
                src = os.path.join(music_folder, song)
                dest = os.path.join(favorites_folder, song)
                shutil.copy(src, dest)
                print(f"😊 Copied '{song}' to Favorites")
            break  # Only once per smile

    cv2.imshow('Rooha - Smile Detection', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
