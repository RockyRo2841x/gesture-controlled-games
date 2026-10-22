"""Original-style color segmentation, without capture or window side effects."""
import cv2
import numpy as np

LOWER_SKIN = np.array([0, 133, 77], dtype=np.uint8)
UPPER_SKIN = np.array([255, 173, 127], dtype=np.uint8)
ROI = (20, 80, 220, 280)


def skin_mask(frame, erode_iterations=2, blur=True):
    if frame is None or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("Expected a three-channel BGR frame")
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
    mask = cv2.inRange(image, LOWER_SKIN, UPPER_SKIN)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=erode_iterations)
    mask = cv2.dilate(mask, kernel, iterations=2)
    return cv2.GaussianBlur(mask, (7, 7), 0) if blur else mask


def hand_circle(mask):
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    if cv2.contourArea(contour) <= 3000:
        return None
    (x, y), radius = cv2.minEnclosingCircle(contour)
    return int(x), int(y), int(radius)


def lift_signal(frame):
    x1, y1, x2, y2 = ROI
    if frame.shape[0] < y2 or frame.shape[1] < x2:
        raise ValueError("Frame is too small for the control region")
    mask = skin_mask(frame[y1:y2, x1:x2], erode_iterations=1, blur=False)
    return cv2.countNonZero(mask) > 9000, mask
