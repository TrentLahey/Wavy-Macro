import time
import numpy as np
import cv2
from mss import mss

# Top-left region (tune this once)
REGION = {"left": 0, "top": 52, "width": 500, "height": 50}

def main():
    with mss() as sct:
        while True:
            frame = np.array(sct.grab(REGION))  # BGRA
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            cv2.imshow("top-left HUD", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

            time.sleep(0.01)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
