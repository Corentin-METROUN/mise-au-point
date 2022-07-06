from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_rs232_v2 import BrickletRS232V2
from tinkerforge.brick_master import BrickMaster
import threading
import time

HOST = "localhost"
PORT = 4223
UID = "6eSrKP" # Change XXYYZZ to the UID of your Master Brick
UID_RS = "W9P"

ipcon = IPConnection() # Create IP connection
rs232 = BrickletRS232V2(UID_RS, ipcon) # Create device object
ipcon.connect(HOST,PORT)
rs232.set_configuration(4800,0,1,8,2)

my_lock = threading.RLock()

# 0 vers l'avant du véhicule, 1 vers l'arrière

x = 0
rst = 0
next = 'no'
mode = 'Receive'
confirm = False

message = [chr(0) for _ in range(8)]
message.append(chr(2))

def cb_error():
    print(rs232.get_error_count())

def cb_read(mess):
    global x
    global rst
    global next
    global mode
    global confirm

    with my_lock:
        print(mess)
        if next == 'position' and mode =='Receive':
            x = int(ord(mess[0]))
            next = 'no'
            #print(x)
        if next == 'reset' and mode =='Receive':
            rst = int(ord(mess[0]))
            next = 'no'
            #print(rst)
        if mode == 'Send':
            if mess == message:
                confirm = True
            else :
                confirm = False
        if mess[0] == 'a':
            next = 'position'
            #print('Position :')
        if mess[0] == 'b':
            next = 'reset'
            #print('Reset :')
        if mess[0] == 'R':
            mode = 'Receive'
        if mess[0] == 'S':
            mode = 'Send'
        
def send(message):
    global confirm
    while not confirm :
        rs232.set_buffer_config(5120,5120)
        rs232.write(message)
        time.sleep(1)
    print('message confirmed!')

rs232.register_callback(rs232.CALLBACK_READ, cb_read)
#rs232.register_callback(rs232.CALLBACK_ERROR_COUNT, cb_error)
rs232.enable_read_callback()

speed = 15
i = 0

while True:
    confirm = False
    send(message)
    time.sleep(5)
message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(2)]
send(message)

message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(0)]
send(message)
print("go vers reset")

while(rst != 1):
    time.sleep(0.1)

print("reset fait")
message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(2)]
send(message)
time.sleep(5)
message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(1)]
send(message)
print("go vers x = 100")
while(x<100):
    time.sleep(0.1)
print('x = 100 atteint')
message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(2)]
send(message)

"""
message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(2)]
rs232.write(message)
time.sleep(5)

message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(1)]
rs232.write(message)

#while True:
    #time.sleep(0.5)
    #print(rs232.get_buffer_status())
    #print('position :')
    #print(x)
    #print('reset :')
    #print(rst)
"""
"""
message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(2)]
rs232.write(message)
time.sleep(2)

message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(1)]
rs232.write(message)

while(rst != 1):
    time.sleep(0.1)

message = [chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(i),chr(speed),chr(2)]
rs232.write(message)
"""