import mss
import numpy as np
import cv2

from src.config import MONITOR_INDEX


class ScreenCapture:
    def __init__(self, monitor_index=MONITOR_INDEX):
        self.monitor_index = monitor_index

    def capture_bgr(self):
        with mss.mss() as sct:
            monitor = sct.monitors[self.monitor_index]
            shot = sct.grab(monitor)

            img = np.array(shot)

            # MSS gives BGRA. Convert to BGR for OpenCV.
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            return img