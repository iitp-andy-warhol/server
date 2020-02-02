import threading as th
import pickle
import time
import numpy as np

from turtle import Turtle, Screen
from socket import *

def receive_command(sock):
    global command
    current_command = None
    while True:
        recvData = sock.recv(1024)
        command = pickle.loads(recvData)

        if current_command != command:
            print("received", command)
            current_command = command


def send_status(sock):
    global direction, current_address, action
    current_status = None
    while True:
        robot_status = makeRobotStatus(direction, current_address, action)

        sendData = pickle.dumps(robot_status, protocol=pickle.HIGHEST_PROTOCOL)
        sock.send(sendData)

        if current_status != robot_status:
            print("send", robot_status)
            current_status = robot_status

        time.sleep(0.5)


def makeRobotStatus(direction, current_address, action):
    dic = {
        'direction': direction,
        'current_address': current_address,
        'action': action,
    }
    return dic


def change_flag(flag):
    if flag:
        flag = False
    else:
        flag = True
    return flag


def make_TF(amount, tf):
    initialize_flags = []
    for flags in range(amount):
        initialize_flags += [tf]
    return initialize_flags


def Drive(ccw, car, car_speed, rx, ty, lx, by):

    if ccw:
        # Corner checking
        if car.xcor() == rx and car.ycor() == by:
            car.dx = 0
            car.dy = car_speed

        if car.xcor() == rx and car.ycor() == ry:
            car.dx = 0
            car.dy = car_speed

        if car.ycor() == ty and car.xcor() == rx:
            car.dx = -1 * car_speed
            car.dy = 0

        if car.xcor() == lx and car.ycor() == ty:
            car.dx = 0
            car.dy = -1 * car_speed

        if car.xcor() == lx and car.ycor() == ly:
            car.dx = 0
            car.dy = -1 * car_speed

        if car.ycor() == by and car.xcor() == lx:
            car.dx = car_speed
            car.dy = 0

        # Move the Car
        car.setx(car.xcor() + car.dx)
        car.sety(car.ycor() + car.dy)

    else:
        # Corner checking
        if car.xcor() == lx and car.ycor() == by:
            car.dx = 0
            car.dy = car_speed

        if car.xcor() == lx and car.ycor() == ly:
            car.dx = 0
            car.dy = car_speed

        if car.ycor() == ty and car.xcor() == lx:
            car.dx = -1 * car_speed
            car.dy = 0

        if car.xcor() == rx and car.ycor() == ty:
            car.dx = 0
            car.dy = -1 * car_speed

        if car.xcor() == rx and car.ycor() == ry:
            car.dx = 0
            car.dy = -1 * car_speed

        if car.ycor() == by and car.xcor() == rx:
            car.dx = car_speed
            car.dy = 0

        # Move the Car
        car.setx(car.xcor() - car.dx)
        car.sety(car.ycor() + car.dy)


def m_mode_on():
    global mmode_flag
    mmode_flag = True
    print("M-mode On")


def m_mode_off():
    global mmode_flag
    mmode_flag = False
    print("M-mode Off")


def get_obstacle():
    obstacle.goto(loc_st34)


def rm_obstacle():
    obstacle.goto(0, 500)


# GUI
wn = Screen()
wn.title("AndyCar")
wn.bgcolor("black")
wn.setup(width=600, height=800)
wn.tracer(0)


class Gui(Turtle):
    def __init__(self, color, width, length, position, speed=0):
        super().__init__(shape='square')
        self.speed(speed)
        self.color(color)
        self.shapesize(stretch_wid=width, stretch_len=length)
        self.penup()
        self.goto(position)


cx, cy = (0, 0)
lx, ly = (cx-200, cy)
rx, ry = (cx+200, cy)
tx, ty = (cx, cy+300)
bx, by = (cx, cy-300)
brx = int((bx+rx)/2)
bry = int((by+ry)/2)
rty = int((ry+ty)/2)
rlx = int((rx+lx)/2)
tly = int((ty+ly)/2)
lby = int((ly+by)/2)
lbx = int((lx+bx)/2)

loc_st0 = (bx, by)
loc_st01 = (brx, by)
loc_st1 = (rx, by)
loc_st12 = (rx, bry)
loc_st2 = (rx, ry)
loc_st23 = (rx, rty)
loc_st3 = (rx, ty)
loc_st34 = (rlx, ty)
loc_st4 = (lx, ty)
loc_st45 = (lx, tly)
loc_st5 = (lx, ly)
loc_st56 = (lx, lby)
loc_st6 = (lx, by)
loc_st60 = (lbx, by)

track_l = Gui("yellow", 30, 1, (lx, ly))
track_r = Gui("yellow", 30, 1, (rx, ry))
track_t = Gui("yellow", 1, 21, (tx, ty))
track_b = Gui("yellow", 1, 21, (bx, by))

st0 = Gui("red", 3, 1, (bx, by-20))
st1 = Gui("green", 1, 3, (rx+20, by))
st2 = Gui("green", 1, 3, (rx+20, ry))
st3 = Gui("green", 1, 3, (rx+20, ty))
st4 = Gui("green", 1, 3, (lx-20, ty))
st5 = Gui("green", 1, 3, (lx-20, ly))
st6 = Gui("green", 1, 3, (lx-20, by))

obstacle = Gui("orange", 1, 1, (0, 500))
safezone = 20

car = Gui("blue", 3, 3, (bx, by))
car_speed = 10
car.dx = car_speed
car.dy = 0

# UI
pen = Turtle()
pen.speed(0)
pen.color("white")
pen.penup()
pen.hideturtle()
pen.goto(0, 0)
pen.write('flags', align="center", font=("Courier", 11, "normal"))

# Key binding
wn.listen()
wn.onkeypress(m_mode_on, "z")
wn.onkeypress(m_mode_off, "x")
wn.onkeypress(get_obstacle, "a")
wn.onkeypress(rm_obstacle, "s")


# Connect to HQ
HQ_ip = 'localhost'
HQ_port = 8090

clientSock = socket(AF_INET, SOCK_STREAM)
clientSock.connect((HQ_ip, HQ_port))

print('connected')

direction = 1
current_address = 0
action = 'loading'
current_basket = {'r': 0, 'g': 0, 'b': 0}
operating_orderset = None
operating_order = {'address': 0, 'id':99999}

command = {
    'message': None,  # loading_complete / unloading_complete / None
    'path': (0,),  # path / None
    'path_id': 9999  # to ignore same path
}

next_path = command['path']
path_id = command['path_id']
message = command['message']

sender = th.Thread(target=send_status, args=(clientSock,))
receiver = th.Thread(target=receive_command, args=(clientSock,))

sender.start()
receiver.start()


class Address:
    def __init__(self, id, msg):
        self.id = id
        self.msg = msg

    def make_flag(self):
        if self.id == operating_drive:
            self.stop = True

    def get_stop(self):
        global action, stop, get_drive, good_to_go_loading, good_to_go_unloading
        if self.id == operating_drive:
            if self.id == address:
                stop = True
                if self.id == 0:
                    action = "loading"
                    if good_to_go_loading:
                        stop = False
                        get_drive = True
                        good_to_go_loading = False
                else:
                    action = "unloading"
                    if good_to_go_unloading:
                        stop = False
                        get_drive = True
                        good_to_go_unloading = False



    # def stop_flag(self):
    #     self.stop = True


address0 = Address(0, False)
address1 = Address(1, False)
address2 = Address(2, False)
address3 = Address(3, False)
address4 = Address(4, False)
address5 = Address(5, False)
address6 = Address(6, False)


# from datetime import datetime
# now = datetime.now()
# current_time = now.strftime("%Y-%m-%d %H:%M:%S")
#
# print(current_time)

# Initialize flags
address = 0
operating_drive = None
get_drive = True
ccw = True
mmode_flag = False
stop = True
good_to_go_loading = False
good_to_go_unloading = False

current_path_id = None
current_path = None
path = None


# Main game loop
while True:

    # command handler
    if command['path'] == (0,):
        start = False

    else:  # action == 'unloading' or receive_command_flag: and action != "M-mode":
        # receive_command_flag = False
        path_id = command['path_id']
        if command['path'] is not None:  # and path_id != current_path_id:
            next_path = command['path']

        if command['message'] == 'loading_complete':
            good_to_go_loading = True
            command['message'] = None

        if command['message'] == 'unloading_complete':
            good_to_go_unloading = True
            command['message'] = None

    if mmode_flag:
        stop = True
        action = "M-mode"
    elif obstacle.ycor() - safezone < car.ycor() < obstacle.ycor() + safezone and obstacle.xcor() - safezone < car.xcor() < obstacle.xcor() + safezone:
        stop = True
        print('obstacle')
        action = "obstacle"
    else:
        stop = False

    # stop handler
    address0.get_stop()
    address1.get_stop()
    address2.get_stop()
    address3.get_stop()
    address4.get_stop()
    address5.get_stop()
    address6.get_stop()

    # path to flag
    if get_drive:
        if path_id != current_path_id:
            current_path = list(next_path)
            current_path_id = np.copy(path_id)
        if len(current_path) > 0:
            operating_drive = current_path.pop(0)
            print("Next drive: ", operating_drive)
            get_drive = False
        else:
            operating_drive = 0
            get_drive = False

    # get address (cw and ccw both)
    if car.pos() == loc_st0:
        address = 0
    elif car.pos() == loc_st1:
        address = 1
        start = False
    elif car.pos() == loc_st2:
        address = 2
    elif car.pos() == loc_st3:
        address = 3
    elif car.pos() == loc_st4:
        address = 4
    elif car.pos() == loc_st5:
        address = 5
    elif car.pos() == loc_st6:
        address = 6
        start = False
    else:
        address = 999

    # stop handler
    if operating_drive == 9:
        ccw = change_flag(ccw)
        get_drive = True
    else:
        address0.get_stop()
        address1.get_stop()
        address2.get_stop()
        address3.get_stop()
        address4.get_stop()
        address5.get_stop()
        address6.get_stop()

    if not stop:
        action = "moving"
        print("moving")
        Drive(ccw, car, car_speed, rx, ty, lx, by)

    if ccw:
        direction = 1
    else:
        direction = -1
    # if action != "loading" and action != "unloading":
    #     current_address = 999
    if current_address != address:
        current_address = address

    pen.clear()
    # pen.write(
    #     "path: {}\ndirection: {}\naddress: {}\naction: {}\nstart: {}\nstop: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\ngood to go loading/unloading: {}/{}".format(
    #         path, direction, current_address, action, start, stop, 0, stop0, 1, stop1, 2, stop2, 3, stop3, 4, stop4, 5,
    #         stop5, 6, stop6, good_to_go_loading, good_to_go_unloading), align="center", font=("Courier", 11, "normal"))

    wn.update()
    # time.sleep(0.2)