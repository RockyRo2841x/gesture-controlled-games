"""State and drawing for the two original color-controlled games."""
import math
import random
import cv2

WIDTH, HEIGHT = 800, 500


class TargetGame:
    radius = 35

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.reset()

    def spawn(self):
        return (self.rng.randint(self.radius, WIDTH - self.radius),
                self.rng.randint(80 + self.radius, HEIGHT - self.radius))

    def reset(self):
        self.score = 0
        self.target = self.spawn()

    def update(self, hand):
        if hand is None:
            return
        x, y, radius = hand
        if math.hypot(x - self.target[0], y - self.target[1]) <= radius + self.radius:
            self.score += 1
            self.target = self.spawn()

    def draw(self, frame, hand):
        output = frame.copy()
        cv2.circle(output, self.target, self.radius, (0, 0, 255), -1)
        cv2.circle(output, self.target, self.radius, (255, 255, 255), 3)
        if hand is not None:
            x, y, radius = hand
            cv2.circle(output, (x, y), radius, (255, 0, 0), 2)
            cv2.circle(output, (x, y), 8, (255, 255, 255), -1)
        cv2.putText(output, f"Score: {self.score}", (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
        cv2.putText(output, "Touch the target | R: reset | Q: quit", (20, HEIGHT - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return output


class DroneGame:
    x, radius = 150, 18
    gravity, jump_power = 0.6, -8
    pipe_speed, pipe_width, gap_height = 4, 60, 160

    def __init__(self, seed=None, duration=60):
        if duration <= 0:
            raise ValueError("Duration must be positive")
        self.rng = random.Random(seed)
        self.duration = duration
        self.reset()

    def new_pipe(self):
        return [WIDTH, self.rng.randint(120, HEIGHT - 120)]

    def reset(self):
        self.y, self.velocity = HEIGHT // 2, 0
        self.pipe = self.new_pipe()
        self.crashed = self.passed = False

    def update(self, lift, elapsed):
        if self.crashed or self.passed:
            return
        self.velocity = self.jump_power if lift else self.velocity + self.gravity
        self.y += self.velocity
        self.pipe[0] -= self.pipe_speed
        if self.pipe[0] + self.pipe_width < 0:
            self.pipe = self.new_pipe()
        left, center = self.pipe
        bounds = self.y - self.radius <= 0 or self.y + self.radius >= HEIGHT
        overlaps = self.x + self.radius > left and self.x - self.radius < left + self.pipe_width
        outside_gap = self.y - self.radius < center - self.gap_height // 2 or self.y + self.radius > center + self.gap_height // 2
        self.crashed = bounds or (overlaps and outside_gap)
        # A crash on the deadline frame must not also count as a win.
        self.passed = not self.crashed and elapsed >= self.duration

    def draw(self, frame, lift, elapsed):
        output = frame.copy()
        left, center = self.pipe
        cv2.rectangle(output, (left, 0), (left + self.pipe_width, center - self.gap_height // 2), (0, 0, 255), -1)
        cv2.rectangle(output, (left, center + self.gap_height // 2), (left + self.pipe_width, HEIGHT), (0, 0, 255), -1)
        cv2.rectangle(output, (20, 80), (220, 280), (255, 255, 0), 2)
        cv2.circle(output, (self.x, int(self.y)), self.radius, (0, 255, 255), -1)
        cv2.putText(output, f"Lift: {'ON' if lift else 'OFF'}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(output, f"Time: {max(0, self.duration - int(elapsed))}", (620, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        if self.crashed or self.passed:
            message = "CRASHED!" if self.crashed else "STAGE PASSED!"
            cv2.putText(output, message, (260, 235), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
        cv2.putText(output, "Hand in box to climb | R: retry | Q: quit", (20, HEIGHT - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        return output
