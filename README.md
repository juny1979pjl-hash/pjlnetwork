import cv2
from deepface import DeepFace

cap = cv2.VideoCapture(0)

frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera not found or failed to open.")
        break

    frame_count += 1

    # Process only every 3rd frame to keep it smoother
    if frame_count % 3 == 0:
        try:
            faces = DeepFace.analyze(
                frame,
                actions=["emotion", "age", "gender"],
                enforce_detection=False
            )

            if isinstance(faces, list):
                for face in faces:
                    region = face.get("region", {})
                    x = region.get("x", 0)
                    y = region.get("y", 0)
                    w = region.get("w", 0)
                    h = region.get("h", 0)

                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    emotion = face.get("dominant_emotion", "unknown")
                    gender = face.get("gender", "unknown")
                    age = face.get("age", "unknown")

                    text = f"{emotion} | {gender} | {age}"
                    cv2.putText(frame, text, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        except ValueError:
            pass

    cv2.imshow("DeepFace Live Camera", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
