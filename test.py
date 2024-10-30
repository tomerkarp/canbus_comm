import can 
import time

bus = can.interface.Bus(channel='/dev/cu.usbmodem11201', bustype='slcan', bitrate=1000000)

while True:
    print("ok")
    time.sleep(1)