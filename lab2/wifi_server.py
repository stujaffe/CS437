import socket
import psutil
import picar_4wd as fc
from time import sleep
from random import random

HOST = "192.168.50.45" # IP address of your Raspberry PI
PORT = 8080          # Port to listen on (non-privileged ports are > 1023)

CAR_POWER = 20
TURN_POWER = 10

def move_car_keystroke(k):
    
    # key 87 = W
    if k == 87:
        fc.forward(CAR_POWER)
    # key 83 = S
    elif k == 83:
        fc.backward(CAR_POWER)
    # key 65 = A
    elif k == 65:
        fc.turn_left(TURN_POWER)
        sleep(random())
    # key 68 = D
    elif k == 68:
        fc.turn_right(TURN_POWER)
        sleep(random())
    # key 88 = X (stops the car)
    elif k == 88: 
        fc.stop()
        

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
                speed = round(float(fc.speed_val()),2)
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
