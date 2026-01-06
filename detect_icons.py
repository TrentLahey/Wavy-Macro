import time
import os
import glob

import numpy as np
import cv2
from mss import mss

HUD = {"left": 0, "top": 52, "width": 500, "height": 50}

TEMPLATE_DIR = "templates"
THRESHOLD = 0.82          # non-haste templates
HASTE_THRESHOLD = 0.90    # haste templates (pickup moments)
HASTE_DURATION = 20.0     # seconds
PICKUP_DEBOUNCE = 0.6     # seconds (prevents double-counting the same pickup)

def load_templates(template_dir: str):
    paths = sorted(glob.glob(os.path.join(template_dir, "*.png")))
    if not paths:
        raise RuntimeError(f"No templates found in: {template_dir}")

    templates = []
    for p in paths:
        img = cv2.imread(p, cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError(f"Failed to read template: {p}")
        name = os.path.splitext(os.path.basename(p))[0]
        templates.append((name, img))
    return templates

def match_template(frame_bgr: np.ndarray, templ_bgr: np.ndarray):
    res = cv2.matchTemplate(frame_bgr, templ_bgr, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)
    return float(max_val), max_loc  # score, (x,y)

def main():
    templates = load_templates(TEMPLATE_DIR)

    # Split templates into haste stack templates and "other" templates
    haste_templates = {}   # e.g. {"hastex1": img, ..., "hastex10": img}
    other_templates = []   # list of (name, img)

    for name, img in templates:
        if name.startswith("hastex"):
            haste_templates[name] = img
        else:
            other_templates.append((name, img))

    print(f"Loaded templates: {[name for name, _ in templates]}")
    print("Press Ctrl+C to stop.")

    haste_stack = 0
    haste_expires_at = 0.0
    last_haste_pickup_at = 0.0

    with mss() as sct:
        while True:
            now = time.time()

            frame = np.array(sct.grab(HUD))  # BGRA
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            cv2.imshow("HUD", frame_bgr)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            # Expire haste by timer (vision no longer responsible for persistence)
            if haste_stack > 0 and now >= haste_expires_at:
                haste_stack = 0
                haste_expires_at = 0.0

            detected_this_frame = []

            # ---- Detect non-haste templates (same as before) ----
            for name, templ in other_templates:
                score, _ = match_template(frame_bgr, templ)
                if score >= THRESHOLD:
                    detected_this_frame.append(name)

            # ---- Haste state machine (robust to fast double pickups) ----
            # Check a small forward window and accept the highest detected stack.
            WINDOW_AHEAD = 4  # how many stacks ahead to consider (2–4 is typical)

            start_level = 1 if haste_stack == 0 else haste_stack + 1
            end_level = min(10, start_level + WINDOW_AHEAD - 1)

            best_level = None
            best_score = -1.0

            for lvl in range(start_level, end_level + 1):
                name = f"hastex{lvl}"
                templ = haste_templates.get(name)
                if templ is None:
                    continue
                score, _ = match_template(frame_bgr, templ)
                if score >= HASTE_THRESHOLD and score > best_score:
                    best_score = score
                    best_level = lvl

            if best_level is not None:
                # Smart debounce:
                # - allow normal +1 pickup only if we're outside debounce
                # - allow "multi-step jump" even inside debounce (covers back-to-back pickups)
                jump = best_level - haste_stack

                if jump >= 2 or (now - last_haste_pickup_at) >= PICKUP_DEBOUNCE:
                    last_haste_pickup_at = now
                    haste_stack = best_level
                    haste_expires_at = now + HASTE_DURATION
                    detected_this_frame.append(f"hastex{best_level}")


            # ---- Output ----
            if haste_stack > 0:
                time_left = max(0.0, haste_expires_at - now)
                print(f"Haste: x{haste_stack} ({time_left:.1f}s left)")
            else:
                print("Haste: (none)")

            print("Detected tokens:")
            if detected_this_frame:
                print(", ".join(detected_this_frame))
            else:
                print("(none)")

            time.sleep(.25)

if __name__ == "__main__":
    main()
