import cv2
import numpy as np
import random
import time

# ---------------- BASIC SETTINGS ----------------
WIDTH, HEIGHT = 800, 500

drone_x = 150
drone_radius = 18

gravity = 0.6
jump_power = -8

pipe_speed = 4
pipe_width = 60
gap_height = 160

game_time = 60

# Hand detection box
roi_x1, roi_y1 = 20, 80
roi_x2, roi_y2 = 220, 280


# ---------------- OBSTACLE FUNCTION ----------------
def new_pipe():
    gap_y = random.randint(120, HEIGHT - 120)
    return [WIDTH, gap_y]


# ---------------- RESET GAME FUNCTION ----------------
def reset_game():
    global drone_y, velocity, pipe, start_time, crashed, passed

    drone_y = HEIGHT // 2
    velocity = 0
    pipe = new_pipe()
    start_time = time.time()
    crashed = False
    passed = False


# Start webcam
cap = cv2.VideoCapture(1)

reset_game()

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (WIDTH, HEIGHT))

    # ---------------- HAND DETECTION ----------------
    roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]

    ycrcb = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)

    lower_skin = np.array([0, 133, 77])
    upper_skin = np.array([255, 173, 127])

    mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)

    skin_pixels = cv2.countNonZero(mask)

    gesture = "FIST / NO HAND"

    if skin_pixels > 9000:
        gesture = "OPEN PALM"

    # ---------------- GAME LOGIC ----------------
    if not crashed and not passed:

        if gesture == "OPEN PALM":
            velocity = jump_power
        else:
            velocity += gravity

        drone_y += velocity

        pipe[0] -= pipe_speed

        if pipe[0] + pipe_width < 0:
            pipe = new_pipe()

        pipe_x = pipe[0]
        gap_y = pipe[1]

        # Ground or ceiling collision
        if drone_y - drone_radius <= 0 or drone_y + drone_radius >= HEIGHT:
            crashed = True

        # Pipe collision
        if drone_x + drone_radius > pipe_x and drone_x - drone_radius < pipe_x + pipe_width:
            if drone_y - drone_radius < gap_y - gap_height // 2 or drone_y + drone_radius > gap_y + gap_height // 2:
                crashed = True

        # Stage passed condition
        if time.time() - start_time >= game_time:
            passed = True

    # ---------------- DRAWING ----------------

    # Hand box
    cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), (255, 255, 0), 2)
    cv2.putText(frame, "Put hand here", (roi_x1, roi_y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    # Pipe
    pipe_x = pipe[0]
    gap_y = pipe[1]

    cv2.rectangle(frame, (pipe_x, 0), (pipe_x + pipe_width, gap_y - gap_height // 2), (0, 0, 255), -1)

    cv2.rectangle(frame,(pipe_x, gap_y + gap_height//2), (pipe_x + pipe_width, HEIGHT), (0, 0, 255), -1)

    # Drone
    cv2.circle(frame, (drone_x, int(drone_y)), drone_radius, (0, 255, 255), -1)

    # Gesture text
    cv2.putText(frame, "Gesture: " + gesture, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Timer
    time_left = max(0, game_time - int(time.time() - start_time))
    cv2.putText(frame, "Time: " + str(time_left), (650, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    # Crash message
    if crashed:
        cv2.putText(frame, "CRASHED!", (300, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

        cv2.putText(frame, "Press R to Retry", (280, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    # Pass message
    if passed:
        cv2.putText(frame, "Stage 2 Passed!", (230, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 0), 4)

        cv2.putText(frame, "Press R to Retry", (280, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    cv2.imshow("Drone Game", frame)
    cv2.imshow("Hand Mask", mask)

    key = cv2.waitKey(1) & 0xFF

    # Q = quit
    if key == ord('q'):
        break

    # R = retry
    if key == ord('r'):
        reset_game()

cap.release()
cv2.destroyAllWindows()