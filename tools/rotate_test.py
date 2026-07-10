import pydirectinput
import time

pydirectinput.MINIMUM_DURATION = 0.0

time.sleep(5)

for _ in range(60):
    pydirectinput.moveRel(50, 0, duration=0, relative=True)