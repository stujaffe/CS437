import socket
import psutil
import picar_4wd as fc
from time import sleep
from random import random

HOST = "192.168.50.45" # IP address of your Raspberry PI
PORT = 8080          # Port to listen on (non-privileged ports are > 1023)

TURN_POWER = 10 # turn power
CAR_POWER_ACT = 0 # actual power of the car
CAR_POWER_SET = 20 # what we will set the car power to when moving forwar/backward

def move_car_keystroke(k):
    
    global CAR_POWER_ACT

    # key 87 = W
    if k == 87:
        CAR_POWER_ACT = CAR_POWER_SET
        fc.forward(CAR_POWER_ACT)
    # key 83 = S
    elif k == 83:
        CAR_POWER_ACT = CAR_POWER_SET
        fc.backward(CAR_POWER_ACT)
    # key 65 = A
    elif k == 65:
        CAR_POWER_ACT = 0 # speed is 0
        fc.turn_left(TURN_POWER)
        sleep(random())
    # key 68 = D
    elif k == 68:
        CAR_POWER_ACT = 0 # speed is 0
        fc.turn_right(TURN_POWER)
        sleep(random())
    # key 88 = X (stops the car)
    elif k == 88:
        CAR_POWER_ACT = 0
        fc.stop()

# speed function from Lab 1 Part 2
def get_speed(car_power):
    # get additional speed if car is over 10 power
    extra = (car_power - 10)/10*2.5
    # speed at 10 power is about 26.7 cm/s
    speed = extra + 26.7 if car_power > 0 else 0

    return speed
        

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    try:
        while 1:
            client, clientInfo = s.accept()
            print("server recv from: ", clientInfo)
            data = client.recv(1024)      # receive 1024 Bytes of message in binary format
            if data != b"":
                
                # decode the data from the client from bytes into a string and remove
                # extra whitespace
                data_decode = data.decode().strip()
                # try to convert decoded data to an integer if it is a keystroke number
                # if it is not, continue as normal
                try:
                    data_decode_int = int(data_decode)
                    print(f"Data is the keystroke number {data_decode_int}. Engaging PiCar.")
                    move_car_keystroke(data_decode_int)
                except ValueError:
                    print("Data is not a keystroke number.")
                
                # get Pi CPU temp
                temp = psutil.sensors_temperatures()['cpu_thermal'][0].current
                temp = round(float(temp),2)
                # convert to bytes
                temp = bytes(str(f"{temp} C\n"),"utf-8")
                
                # get car's speed
                speed = round(float(get_speed(CAR_POWER_ACT)),2)
                speed = bytes(str(f"{speed}\n"),"utf-8")
                
                # get car's power supply reading
                power_supply = round(float(fc.power_read()),2)
                power_supply = bytes(str(f"{power_supply}V\n"),"utf-8")
                
                # data to echo back to client
                data_ret = temp + speed + power_supply
                client.sendall(data_ret) # Echo back to client
    except: 
        print("Closing socket")
        client.close()
        s.close()    
