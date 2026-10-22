"""Launch a webcam game or a clearly labeled camera-free synthetic demo."""
import argparse
import json
from pathlib import Path
import time
import cv2
import numpy as np

from games import DroneGame, TargetGame, WIDTH, HEIGHT
from vision import skin_mask, hand_circle, lift_signal


def synthetic_frame(index, game):
    frame = np.full((HEIGHT, WIDTH, 3), (70, 35, 15), dtype=np.uint8)
    sample = np.array([[[150, 150, 100]]], dtype=np.uint8)
    color = tuple(int(v) for v in cv2.cvtColor(sample, cv2.COLOR_YCrCb2BGR)[0, 0])
    center = (120, 180) if game == "drone" else (int(400 + 180 * np.sin(index / 12)), 280)
    cv2.circle(frame, center, 65, color, -1)
    return frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", choices=("target", "drone"))
    parser.add_argument("--camera", type=int, default=1)
    parser.add_argument("--demo", action="store_true", help="Use synthetic frames; never opens a camera")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--frames", type=int, default=0, help="Stop after N frames; 0 means unlimited")
    parser.add_argument("--output", type=Path, help="Save the last rendered frame as PNG")
    parser.add_argument("--seed", type=int, default=2841)
    parser.add_argument("--duration", type=int, default=60, help="Drone survival duration in seconds")
    args = parser.parse_args()
    if args.frames < 0 or args.duration <= 0:
        parser.error("Frame limit must be nonnegative and duration positive")
    if args.headless and args.frames == 0:
        parser.error("Headless mode requires a positive --frames limit")
    game = DroneGame(args.seed, args.duration) if args.game == "drone" else TargetGame(args.seed)
    cap = None
    last_frame = None
    count = 0
    round_started_frame = 0
    windows_open = False
    started = time.monotonic()
    try:
        if not args.demo:
            cap = cv2.VideoCapture(args.camera)
            if not cap.isOpened():
                raise RuntimeError(f"Cannot open camera {args.camera}; choose another --camera index")
        started = time.monotonic()
        while args.frames == 0 or count < args.frames:
            if args.demo:
                frame = synthetic_frame(count, args.game)
            else:
                ok, frame = cap.read()
                if not ok:
                    raise RuntimeError("Camera frame read failed")
                frame = cv2.resize(cv2.flip(frame, 1), (WIDTH, HEIGHT))
            elapsed = (count - round_started_frame) / 30 if args.demo else time.monotonic() - started
            if args.game == "target":
                mask = skin_mask(frame)
                hand = hand_circle(mask)
                game.update(hand)
                output = game.draw(frame, hand)
            else:
                lift, mask = lift_signal(frame)
                game.update(lift, elapsed)
                output = game.draw(frame, lift, elapsed)
            if args.demo:
                cv2.putText(output, "SYNTHETIC DEMO - NO CAMERA", (260, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            last_frame = output
            count += 1
            if not args.headless:
                cv2.imshow("Gesture Games", output)
                windows_open = True
                cv2.imshow("Segmentation Mask", mask)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("r"):
                    game.reset()
                    started = time.monotonic()
                    round_started_frame = count
        if args.output is not None and last_frame is not None:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if not cv2.imwrite(str(args.output), last_frame):
                raise RuntimeError("Could not write the output frame")
        report = {"game": args.game, "synthetic": args.demo, "frames": count}
        if args.game == "target":
            report["score"] = game.score
        else:
            report.update(crashed=game.crashed, passed=game.passed)
        print(json.dumps(report))
    except (RuntimeError, cv2.error) as error:
        parser.exit(1, f"Error: {error}\n")
    finally:
        if cap is not None:
            cap.release()
        if windows_open:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
