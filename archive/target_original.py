#This works BEST when there is plane background

import cv2
import numpy as np
import random

#...........................GAME SETTINGS.............................
TARGET_RADIUS = 35
SCORE = 0
target_center = None

LOWER_SKIN = np.array([0, 133, 77], dtype=np.uint8)
UPPER_SKIN = np.array([255, 173, 127], dtype=np.uint8)

def spawn_target(frame_width, frame_height):
    x = random.randint(TARGET_RADIUS, frame_width - TARGET_RADIUS)
    y = random.randint(80 + TARGET_RADIUS, frame_height - TARGET_RADIUS)
    return (x, y)

cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Webcam not found")
    exit()

while True:
    ret, frame = cap.read()

    if not ret:
        print("Frame not captured")
        break

    frame = cv2.flip(frame, 1)

    height, width, _ = frame.shape

    if target_center is None:
        target_center = spawn_target(width, height)

#HAND DETECTION
    ycrcb = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    mask = cv2.inRange(ycrcb, LOWER_SKIN, UPPER_SKIN)

    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.erode(mask, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (7, 7), 0)

    contours, _ = cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)

    hand_center = None
    hand_radius = 0

    if len(contours) > 0:
        largest_contour = max(contours, key=cv2.contourArea)

        area = cv2.contourArea(largest_contour)

        if area > 3000:
            cv2.drawContours(frame, [largest_contour], -1, (255, 0, 0), 2)

            (x, y), radius = cv2.minEnclosingCircle(largest_contour)

            hand_center = (int(x), int(y))
            hand_radius = int(radius)

            cv2.circle(frame, hand_center, 8, (255, 255, 255), -1)


#TARGET
    cv2.circle(frame, target_center, TARGET_RADIUS, (0, 0, 255), -1)
    cv2.circle(frame, target_center, TARGET_RADIUS, (255, 255, 255), 3)

#COLLISION DETECTION
    if hand_center is not None:
        dx = hand_center[0] - target_center[0]
        dy = hand_center[1] - target_center[1]

        distance = np.sqrt(dx ** 2 + dy ** 2)

    
        if distance <= hand_radius + TARGET_RADIUS:
            SCORE += 1
            target_center = spawn_target(width, height)


# DISPLAY SCORE AND INSTRUCTIONS

    cv2.putText(
        frame,
        f"Score: {SCORE}",
        (20, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.3,
        (0, 255, 0),
        3
    )

    cv2.imshow("Webcam Battlefield - Classical CV Hand Shooter", frame)

    cv2.imshow("Skin Mask", mask)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()