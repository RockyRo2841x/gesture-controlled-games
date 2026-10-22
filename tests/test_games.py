import contextlib
import importlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np
import games
import play
import vision


class GameTests(unittest.TestCase):
    def test_imports_do_not_open_camera(self):
        with patch.object(cv2, "VideoCapture", side_effect=AssertionError("Camera access")):
            for module in (vision, games, play):
                importlib.reload(module)

    def test_segmentation_and_lift_region(self):
        frame = play.synthetic_frame(0, "drone")
        lift, mask = vision.lift_signal(frame)
        self.assertTrue(lift)
        self.assertGreater(cv2.countNonZero(mask), 9000)
        self.assertIsNotNone(vision.hand_circle(vision.skin_mask(frame)))
        blank = np.zeros_like(frame)
        self.assertFalse(vision.lift_signal(blank)[0])
        self.assertIsNone(vision.hand_circle(vision.skin_mask(blank)))
        # A color-matched blob outside the control box must not produce lift.
        shifted = np.zeros_like(frame)
        shifted[250:450, 400:600] = frame[80:280, 20:220]
        self.assertFalse(vision.lift_signal(shifted)[0])

    def test_target_contact_and_no_contact(self):
        game = games.TargetGame(seed=1)
        game.target = (400, 300)
        game.update(None)
        game.update((446, 300, 10))
        self.assertEqual(game.score, 0)
        game.update((445, 300, 10))
        self.assertEqual(game.score, 1)
        self.assertNotEqual(game.target, (400, 300))
        game.reset()
        self.assertEqual(game.score, 0)

    def test_target_spawns_stay_inside_frame(self):
        game = games.TargetGame(seed=2841)
        for _ in range(500):
            x, y = game.spawn()
            self.assertTrue(35 <= x <= 765)
            self.assertTrue(115 <= y <= 465)

    def test_drone_lift_and_gravity(self):
        game = games.DroneGame(seed=1)
        game.update(False, 0)
        self.assertAlmostEqual(game.y, 250.6)
        self.assertEqual(game.pipe[0], 796)
        game.update(True, 1)
        self.assertAlmostEqual(game.velocity, -8)
        self.assertAlmostEqual(game.y, 242.6)

    def test_pipe_gap_and_collision(self):
        game = games.DroneGame(seed=1)
        game.pipe = [150, 250]
        game.update(False, 0)
        self.assertFalse(game.crashed)
        game.y, game.velocity = 100, 0
        game.update(False, 1)
        self.assertTrue(game.crashed)

    def test_crash_on_deadline_cannot_also_win(self):
        game = games.DroneGame(seed=1, duration=10)
        game.y = games.HEIGHT - game.radius - 0.1
        game.update(False, 10)
        self.assertTrue(game.crashed)
        self.assertFalse(game.passed)

    def test_win_freezes_state_and_retry_resets(self):
        game = games.DroneGame(seed=1, duration=10)
        game.update(False, 9.99)
        self.assertFalse(game.passed)
        game.update(False, 10)
        self.assertTrue(game.passed)
        state = (game.y, game.velocity, tuple(game.pipe))
        game.update(True, 20)
        self.assertEqual((game.y, game.velocity, tuple(game.pipe)), state)
        game.reset()
        self.assertFalse(game.crashed or game.passed)
        self.assertEqual(game.y, 250)
        self.assertEqual(game.pipe[0], 800)

    def test_rendering_does_not_modify_input(self):
        frame = play.synthetic_frame(0, "target")
        original = frame.copy()
        output = games.TargetGame(1).draw(frame, (400, 280, 65))
        self.assertEqual(output.shape, (500, 800, 3))
        self.assertTrue(np.array_equal(frame, original))
        self.assertFalse(np.array_equal(frame, output))

    def test_both_headless_demos_never_open_camera_or_gui(self):
        with tempfile.TemporaryDirectory() as folder:
            for game in ("target", "drone"):
                output = Path(folder) / f"{game}.png"
                argv = ["play.py", game, "--demo", "--headless", "--frames", "12", "--output", str(output)]
                report = io.StringIO()
                with patch("sys.argv", argv), contextlib.redirect_stdout(report), \
                     patch.object(cv2, "VideoCapture", side_effect=AssertionError("Camera access")), \
                     patch.object(cv2, "imshow", side_effect=AssertionError("GUI access")):
                    play.main()
                data = json.loads(report.getvalue())
                self.assertTrue(data["synthetic"])
                self.assertEqual(data["frames"], 12)
                self.assertEqual(cv2.imread(str(output)).shape, (500, 800, 3))

    def test_camera_failures_release_capture(self):
        for opens in (False, True):
            capture = Mock()
            capture.isOpened.return_value = opens
            capture.read.return_value = (False, None)
            argv = ["play.py", "target", "--camera", "7", "--headless", "--frames", "1"]
            with self.subTest(opens=opens), patch("sys.argv", argv), \
                 patch.object(cv2, "VideoCapture", return_value=capture) as factory, \
                 contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    play.main()
                self.assertEqual(error.exception.code, 1)
                factory.assert_called_once_with(7)
                capture.release.assert_called_once()

    def test_invalid_duration_and_headless_limit(self):
        with self.assertRaises(ValueError):
            games.DroneGame(duration=0)
        with patch("sys.argv", ["play.py", "drone", "--demo", "--headless"]), \
             contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                play.main()
            self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
