import random
import cv2
import numpy as np
import time

#............Basic settings............
WIDTH , HEIGHT = 800 , 500

#palm box
x1,y1 = 20 ,80
x2,y2 = 220, 280

drone_x = 150
drone_r = 15

gravity = 0.6
jump_power = -8

pipe_speed = 4
gap_h = 160
pipe_w = 60

win_time = 10

def pipe():
    gap_y = random.randint(120 , HEIGHT-120)
    return [WIDTH,gap_y]


def reset_game():
    global drone_y, velocity, new_pipe, start_time, crash, passed

    drone_y = HEIGHT//2
    velocity = 0
    new_pipe = pipe()
    start_time = time.time()
    crash = False
    passed = False

#Web Cam Setup
cam = cv2.VideoCapture(1)

reset_game()

while 1:
    state,frame = cam.read()

    if not state:
        print("Capture Failed!")
        break

    frame = cv2.flip(frame,1)
    frame = cv2.resize(frame,(WIDTH,HEIGHT))

#Hand detection

    hand_box = frame[y1:y2 , x1:x2]
    ycrcb = cv2.cvtColor(hand_box, cv2.COLOR_BGR2YCrCb)

    lower_skin = np.array([0, 133, 77])
    upper_skin = np.array([255, 173, 127])

    mask = cv2.inRange(ycrcb, lower_skin, upper_skin)

    kernel = np.ones((5,5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (7, 7), 0)
    
    hand_area = cv2.countNonZero(mask)
    gesture = "FIST / NO HAND"
    if hand_area>10000:
        gesture = "OPEN PALM"

#.................game logic...................
    if not crash and not passed:

        if gesture == "OPEN PALM":
            velocity = jump_power
        else:
            velocity += gravity

        drone_y += velocity

        new_pipe[0] -= pipe_speed

        if new_pipe[0] < 0:
            new_pipe = pipe()
        
        pipe_x = new_pipe[0]
        gap_y = new_pipe[1] 

        #ground or cieling collision
        if drone_y - drone_r <= 0 or drone_y + drone_r >= HEIGHT:
            crash = True 

        #pipe collision
        if pipe_x <= drone_x + drone_r and drone_x - drone_r <= pipe_x+pipe_w:
            if drone_y - drone_r < gap_y - gap_h//2 or drone_y + drone_r > gap_y + gap_h//2:
                crash = True

        if time.time() - start_time >= win_time:
            passed = True


#UI UX of Game
    #pipe
    cv2.rectangle(frame, (x1,y1) , (x2,y2) , [0, 0, 0], 2)


    pipe_x = new_pipe[0]
    gap_y = new_pipe[1]

    cv2.rectangle(frame, (pipe_x,0), (pipe_x + pipe_w, gap_y - gap_h//2), [0, 0, 255], -1)
    cv2.rectangle(frame, (pipe_x, gap_y + gap_h//2), (pipe_x + pipe_w, HEIGHT), [0, 0, 255], -1)
    
    #Drone
    cv2.circle(frame, (drone_x, int(drone_y)), drone_r, [0, 255, 0], -1)

    #current Gesture
    cv2.putText(frame, "Gesture:"+ gesture, (20,40), cv2.FONT_HERSHEY_COMPLEX, 0.8, [255, 255, 0], 2)
    
    time_left = max(0, win_time - int(time.time() - start_time))
    cv2.putText(frame, "Time:"+ str(time_left), (650, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, [255, 255, 0], 2)

    if crash:
        cv2.putText(frame, "CRASHED!", (300, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 4)

        cv2.putText(frame, "Press R to Retry", (280, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

    if passed:
        cv2.putText(frame, "Passed!", (320, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)

        cv2.putText(frame, "Press R to Retry", (280, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

    cv2.imshow("Drone Game", frame)
    cv2.imshow("Hand Mask", mask)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    if key == ord('r'):
        reset_game()

cam.release()
cv2.destroyAllWindows()