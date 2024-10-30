import can
import serial
import serial.tools.list_ports  
import struct
import time


BITRATE = 1000000

CAN_ID = {
    "position": 0x048021B4,
    "speed": 0x048021b0,
    "motion": 0x03802083,
    "limit_left": 0x040021BB,
    "limit_right": 0x040021BC,
    "set_limits": 0x03802086,
    "get_position": 0x16002005,
    "receive_position": 0x16814005
}

CAN_ID.update({v: k for k, v in CAN_ID.items()})


def main():
    ports = serial.tools.list_ports.comports()
    for i, port in enumerate(ports):
        print(f"{i}. " + port.device)
    port = ports[int(input("Select a port: "))]
    bus = CanInterface(port.device)
    option = input("Enter g to s position or q to quit: ")
    if option == "g":
        print(bus.set_postion(100))
        bus.close()
    elif option == "q":
        bus.close()
        return
    else:
        print("Invalid input")





class CanInterface:
    def __init__(self, port, bitrate = BITRATE):
        self.bus = can.interface.Bus(channel = port, interface = 'slcan', bitrate = bitrate)
        self.buff = bytearray(8)
        self.position = 0 
        self.right_limit = 200
        self.left_limit = -200
    
    def _send(self, id, data, extended_id = True):
        msg_send = can.Message(arbitration_id = id, data = data, is_extended_id = extended_id)
        self.bus.send(msg_send, timeout = 0.2)

    def set_limits(self, left, right):
        self._send(CAN_ID["limit_left"], self._convert_steering_limit(left))
        self.left_limit = left
        self._send(CAN_ID["limit_right"], self._convert_steering_limit(right))
        self.right_limit = right
        self._send(CAN_ID["set_limits"], [0,0,0,0,0,0,0])

    
    def set_postion(self, angle_setpoint: int):
        angle_setpoint = -angle_setpoint
        if angle_setpoint == 0:
            return
        elif angle_setpoint < self.left_limit:
            angle_setpoint = self.left_limit
        elif angle_setpoint > self.right_limit:
            angle_setpoint = self.right_limit
        # self.position = self.get_position()
        delta = angle_setpoint - self.position

        SCALING_FACTOR = 200704/360
        position_setpoint = int(delta * SCALING_FACTOR)
        buff = struct.pack("<ii", position_setpoint, 0)
        self._send(CAN_ID["position"], buff)
        print(f"Position setpoint: {position_setpoint}")

    def get_position(self):
        self._send(CAN_ID["get_position"], [160,00,40,2,0,0,0,0])
        message = self.bus.recv()
        print(message)
        if message is not None:
            if message.arbitration_id == CAN_ID["receive_position"]:
                data = message.data
                self.position = -int((360/200704) * struct.unpack("<i", data[-4:])[0])
                return self.position
        else:
            print("No message received")
            time.sleep(0.3)
            self.get_position()
    
    def set_velocity(self, velocity):
        velocity_data = int(velocity * 65536 * 200.704 / 360)
        self._send(CAN_ID["speed"], struct.pack("<ii", 0, velocity_data))  


    def _convert_steering_limit(self, limit):
        return struct.pack("<i", -limit) #check if -limit is correct


             

    def close(self):
        self.bus.shutdown()

if __name__ == "__main__":
    main()