# Verification record

Completed on 22 October 2026.

## Original sources

Three scripts were copied unchanged and checked with SHA-256: the target game, the 60-second drone version and the 10-second draft. `source-inventory.json` records names, sizes and hashes.

The RMI drone submission and 10-second draft have equivalent Python syntax trees, so the submission is not duplicated in the main source. The target submission differs mainly in comments and an additional instruction-text drawing call. The prepared game logic derives from the two desktop games, with the older drone draft retained for history.

## Twelve passing checks

Executed `python -m unittest discover -s tests -v` using Python 3.12.14, NumPy 2.5.4 and OpenCV headless 5.0.0.93. Temporary files were directed to the writable workspace.

1. Reloading all prepared modules does not open a camera.
2. Synthetic color matching produces a target region and drone lift signal; blank input does not. A matching blob outside the drone ROI does not produce lift.
3. Target contact at the circle-overlap boundary scores; a separated region and absent detection do not. Reset clears the score.
4. Five hundred seeded target spawns remain within the frame/UI bounds.
5. Drone gravity, lift direction and obstacle movement follow the configured per-frame rules.
6. A drone inside a pipe's gap passes; moving outside the gap collides.
7. A boundary crash on the round deadline does not also count as a win.
8. Winning freezes game state, and retry resets position, flags and obstacles.
9. Rendering creates an annotated frame without modifying the input image.
10. Both complete headless demo paths process 12 frames and save decodable images while patched camera/window methods prohibit hardware or GUI access.
11. Mocked camera-open and frame-read failures produce a failure exit and release the capture object. The configured camera index is passed to the capture factory.
12. Invalid duration and an unbounded headless invocation are rejected.

## Generated preview checks

Ran the target demo for 24 synthetic frames and the drone demo for 12 synthetic frames, using seed 2841. Both completed successfully and wrote 800×500 PNGs. The target run reported score 0; the short drone run was neither crashed nor passed.

Both images were visually inspected. Each prominently states `SYNTHETIC DEMO - NO CAMERA`. They are renderer/processing smoke-test artifacts, not historical recordings, webcam screenshots or evidence of gesture-recognition accuracy.

## What was not tested

No webcam was opened, no GUI window was launched, and no real hand/video footage was processed. The tests ran with OpenCV's headless distribution. GUI-enabled OpenCV 5.0.0.93 was confirmed available in package metadata, but interactive capture and display behavior were not verified here.

The fixed color band is not a trained gesture detector. No recognition accuracy, lighting robustness, frame-rate stability or user-playability measurements are claimed. Live control tuning and frame-rate-independent drone movement remain future work.

## Preparation changes

The original algorithms were organized into import-safe modules and a shared CLI, with frame sizing, camera selection, deterministic demo input, resource cleanup and tests. Target retry support and mutually exclusive crash/win handling were added. The originals remain untouched in the archive, including their immediate camera-open behavior and original global-variable structure.
