import threading as th
import pickle
import time
import numpy as np

import turtle
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

import turtle


def Drive(ccw, car, car_speed, rx, ty, lx, by):

    if ccw:
        # Corner checking
        if car.xcor() == rx and car.ycor() == by:
            car.dx = 0
            car.dy = car_speed

        if car.ycor() == ty and car.xcor() == rx:
            car.dx = -1 * car_speed
            car.dy = 0

        if car.xcor() == lx and car.ycor() == ty:
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

        if car.ycor() == ty and car.xcor() == lx:
            car.dx = -1 * car_speed
            car.dy = 0

        if car.xcor() == rx and car.ycor() == ty:
            car.dx = 0
            car.dy = -1 * car_speed

        if car.ycor() == by and car.xcor() == rx:
            car.dx = car_speed
            car.dy = 0

        # Move the Car
        car.setx(car.xcor() - car.dx)
        car.sety(car.ycor() + car.dy)


def Go():
    global stop, msgstop
    if stop:
        if msgstop:
            print("stop mode, you have to send go message or whatever")
    elif ccw:
        if car.pos() == loc_st0:
            car.goto(loc_st01)
        elif car.pos() == loc_st01:
            car.goto(loc_st1)
        elif car.pos() == loc_st1:
            car.goto(loc_st12)
        elif car.pos() == loc_st12:
            car.goto(loc_st2)
        elif car.pos() == loc_st2:
            car.goto(loc_st23)
        elif car.pos() == loc_st23:
            car.goto(loc_st3)
        elif car.pos() == loc_st3:
            car.goto(loc_st34)
        elif car.pos() == loc_st34:
            car.goto(loc_st4)
        elif car.pos() == loc_st4:
            car.goto(loc_st45)
        elif car.pos() == loc_st45:
            car.goto(loc_st5)
        elif car.pos() == loc_st5:
            car.goto(loc_st56)
        elif car.pos() == loc_st56:
            car.goto(loc_st6)
        elif car.pos() == loc_st6:
            car.goto(loc_st60)
        elif car.pos() == loc_st60:
            car.goto(loc_st0)
    elif not ccw:
        if car.pos() == loc_st0:
            car.goto(loc_st60)
        elif car.pos() == loc_st60:
            car.goto(loc_st6)
        elif car.pos() == loc_st6:
            car.goto(loc_st56)
        elif car.pos() == loc_st56:
            car.goto(loc_st5)
        elif car.pos() == loc_st5:
            car.goto(loc_st45)
        elif car.pos() == loc_st45:
            car.goto(loc_st4)
        elif car.pos() == loc_st4:
            car.goto(loc_st34)
        elif car.pos() == loc_st34:
            car.goto(loc_st3)
        elif car.pos() == loc_st3:
            car.goto(loc_st23)
        elif car.pos() == loc_st23:
            car.goto(loc_st2)
        elif car.pos() == loc_st2:
            car.goto(loc_st12)
        elif car.pos() == loc_st12:
            car.goto(loc_st1)
        elif car.pos() == loc_st1:
            car.goto(loc_st01)
        elif car.pos() == loc_st01:
            car.goto(loc_st0)


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


# Simulator
wn = turtle.Screen()
wn.title("AndyCar")
wn.bgcolor("black")
wn.setup(width=600, height=800)
wn.tracer(0)


# Position
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


# Tracks
track_l = turtle.Turtle()
track_l.speed(0)
track_l.shape("square")  # original size is 20*20
track_l.color("yellow")
track_l.shapesize(stretch_wid=30, stretch_len=1)
track_l.penup()
track_l.goto(lx, ly)

track_r = turtle.Turtle()
track_r.speed(0)
track_r.shape("square")  # original size is 20*20
track_r.color("yellow")
track_r.shapesize(stretch_wid=30, stretch_len=1)
track_r.penup()
track_r.goto(rx, ry)

track_u = turtle.Turtle()
track_u.speed(0)
track_u.shape("square")  # original size is 20*20
track_u.color("yellow")
track_u.shapesize(stretch_wid=1, stretch_len=21)
track_u.penup()
track_u.goto(tx, ty)

track_d = turtle.Turtle()
track_d.speed(0)
track_d.shape("square")  # original size is 20*20
track_d.color("yellow")
track_d.shapesize(stretch_wid=1, stretch_len=21)
track_d.penup()
track_d.goto(bx, by)


# Stations
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

st0 = turtle.Turtle()
st0.speed(0)
st0.shape("square")  # original size is 20*20
st0.color("red")
st0.shapesize(stretch_wid=3, stretch_len=1)
st0.penup()
st0.goto(bx, by-20)

st1 = turtle.Turtle()
st1.speed(0)
st1.shape("square")  # original size is 20*20
st1.color("green")
st1.shapesize(stretch_wid=1, stretch_len=3)
st1.penup()
st1.goto(rx+20, by)

st2 = turtle.Turtle()
st2.speed(0)
st2.shape("square")  # original size is 20*20
st2.color("green")
st2.shapesize(stretch_wid=1, stretch_len=3)
st2.penup()
st2.goto(rx+20, ry)

st3 = turtle.Turtle()
st3.speed(0)
st3.shape("square")  # original size is 20*20
st3.color("green")
st3.shapesize(stretch_wid=1, stretch_len=3)
st3.penup()
st3.goto(rx+20, ty)

st4 = turtle.Turtle()
st4.speed(0)
st4.shape("square")  # original size is 20*20
st4.color("green")
st4.shapesize(stretch_wid=1, stretch_len=3)
st4.penup()
st4.goto(lx-20, ty)

st5 = turtle.Turtle()
st5.speed(0)
st5.shape("square")  # original size is 20*20
st5.color("green")
st5.shapesize(stretch_wid=1, stretch_len=3)
st5.penup()
st5.goto(lx-20, ly)

st6 = turtle.Turtle()
st6.speed(0)
st6.shape("square")  # original size is 20*20
st6.color("green")
st6.shapesize(stretch_wid=1, stretch_len=3)
st6.penup()
st6.goto(lx-20, by)


# Obstacle
obstacle = turtle.Turtle()
obstacle.speed(0)
obstacle.shape("square")  # original size is 20*20
obstacle.color("orange")
obstacle.shapesize(stretch_wid=1, stretch_len=1)
obstacle.penup()
obstacle.goto(0, 500)
safezone = 20



# Car
car_speed = 10
car = turtle.Turtle()
car.shape("square")  # original size is 20*20
car.color("blue")
car.shapesize(stretch_wid=3, stretch_len=3)
car.penup()
car.goto(bx, by)
car.dx = car_speed
car.dy = 0


# loc_st0 = (bx, by)
# loc_st01 = (brx, by)
# loc_st1 = (rx, by)
# loc_st12 = (rx, bry)
# loc_st2 = (rx, ry)
# loc_st23 = (rx, rty)
# loc_st3 = (rx, ty)
# loc_st34 = (rlx, ty)
# loc_st4 = (lx, ty)
# loc_st45 = (lx, tly)
# loc_st5 = (lx, ly)
# loc_st56 = (lx, lby)
# loc_st6 = (lx, by)
# loc_st60 = (lbx, by)


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

path = command['path']
path_id = command['path_id']
message = command['message']

sender = th.Thread(target=send_status, args=(clientSock,))
receiver = th.Thread(target=receive_command, args=(clientSock,))

sender.start()
receiver.start()


# path = command['path']
# UI
pen = turtle.Turtle()
pen.speed(0)
pen.color("white")
pen.penup()
pen.hideturtle()
pen.goto(0, 0)
pen.write('flags', align="center", font=("Courier", 11, "normal"))

# red = turtle.Turtle()
# red.speed(0)
# red.color("white")
# red.penup()
# red.hideturtle()
# red.goto(300, 150)
# red.write(current_address, align="left", font=("Courier", 20, "normal"))
#
# head = turtle.Turtle()
# head.speed(0)
# head.color("white")
# head.penup()
# head.hideturtle()
# head.goto(300, 100)
# head.write(direction, align="left", font=("Courier", 20, "normal"))


wn.listen()
wn.onkeypress(m_mode_on, "z")
wn.onkeypress(m_mode_off, "x")
wn.onkeypress(get_obstacle, "a")
wn.onkeypress(rm_obstacle, "s")



get_flag, ccw = make_TF(2, True)
good_to_go_loading, good_to_go_unloading, mmode_flag = make_TF(3, False)
# receive_command_flag = True
start, stop0 = False, True
stop1, stop2, stop3, stop4, stop5, stop6, msg0, msg1, msg2, msg3, msg4, msg5, msg6, turn0, turn1, turn2, turn3, turn4, turn5, turn6 = make_TF(20, False)

stop = False
msgstop = False
current_path_id = None

# Main game loop
while True:
    wn.update()

    # command handler
    if command['path'] == (0,):
        start = False

    else:  # action == 'unloading' or receive_command_flag: and action != "M-mode":
        # receive_command_flag = False
        path_id = command['path_id']
        if path_id != current_path_id and command['path'] is not None:
            path = command['path']
            current_path_id = np.copy(path_id)

        if command['message'] == 'loading_complete':
            good_to_go_loading = True
            command['message'] = None

        if command['message'] == 'unloading_complete':
            good_to_go_unloading = True
            command['message'] = None


    # path to flag
    if get_flag:
        stop0 = True
        stop1, stop2, stop3, stop4, stop5, stop6, msg0, msg1, msg2, msg3, msg4, msg5, msg6, turn0, turn1, turn2, turn3, turn4, turn5, turn6 = make_TF(20, False)

        b = 0
        for temp in range(len(path)):
            e = path[temp]
            if e == 9:
                if b == 1:
                    turn1 = True
                elif b == 2:
                    turn2 = True
                elif b == 3:
                    turn3 = True
                elif b == 4:
                    turn4 = True
                elif b == 5:
                    turn5 = True
                elif b == 6:
                    turn6 = True
                elif b == 0:
                    turn0 = True
            else:
                if e == 1:
                    stop1 = True
                    msg1 = True
                elif e == 2:
                    stop2 = True
                    msg2 = True
                elif e == 3:
                    stop3 = True
                    msg3 = True
                elif e == 4:
                    stop4 = True
                    msg4 = True
                elif e == 5:
                    stop5 = True
                    msg5 = True
                elif e == 6:
                    stop6 = True
                    msg6 = True
                elif e == 0:
                    stop0 = True
                    msg0 = True
            b = np.copy(e)
        get_flag = False

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
    if mmode_flag:
        stop = True
        action = "M-mode"
        msgstop = True
    elif obstacle.ycor() - safezone < car.ycor() < obstacle.ycor() + safezone and obstacle.xcor() - safezone < car.xcor() < obstacle.xcor() + safezone:
        stop = True
        print('obstacle')
        action = "obstacle"
    elif address == 0 and start and turn0:
        action = "moving"
        ccw = change_flag(ccw)
        turn0 = False
    elif address == 0 and stop0 and not start:
        # if not stop1 and not stop2 and not stop3 and not stop4 and not stop5 and not stop6:
        action = "loading"
        stop = True
        msgstop = True
        if good_to_go_loading:
            start = True
            stop = False
            good_to_go_loading = False
        if msg0:
            # path, " done"
            msg0 = False
            get_flag = True
    elif address == 1 and stop1:
        action = "unloading"
        stop = True
        msgstop = True
        if msg1:
            print("unloading")
            msg1 = False
        if good_to_go_unloading:
            good_to_go_unloading = False
            stop1 = False
            stop = False
    elif address == 2 and stop2:
        action = "unloading"
        stop = True
        msgstop = True
        if turn1:
            ccw = change_flag(ccw)
            turn1 = False
        if msg2:
            print("unloading")
            msg2 = False
        if good_to_go_unloading:
            good_to_go_unloading = False
            stop2 = False
            stop = False
    elif address == 3 and stop3:
        action = "unloading"
        stop = True
        msgstop = True
        if turn3:
            ccw = change_flag(ccw)
            turn3 = False
        if msg3:
            print("unloading")
            msg3 = False
        if good_to_go_unloading:
            print("b3")
            good_to_go_unloading = False
            print("a3")
            stop3 = False
            stop = False
    elif address == 4 and stop4:
        action = "unloading"
        stop = True
        msgstop = True
        if turn4:
            ccw = change_flag(ccw)
            turn4 = False
        if msg4:
            print("unloading")
            msg4 = False
        if good_to_go_unloading:
            good_to_go_unloading = False
            stop4 = False
            stop = False
    elif address == 5 and stop5:
        action = "unloading"
        stop = True
        msgstop = True
        if turn5:
            ccw = change_flag(ccw)
            turn5 = False
        if msg5:
            print("unloading")
            msg5 = False
        if good_to_go_unloading:
            good_to_go_unloading = False
            stop5 = False
            stop = False
    elif address == 6 and stop6:
        action = "unloading"
        stop = True
        msgstop = True
        if turn6:
            ccw = change_flag(ccw)
            turn6 = False
        if msg6:
            print("unloading")
            msg6 = False
        if good_to_go_unloading:
            good_to_go_unloading = False
            stop6 = False
            stop = False
    else:
        action = "moving"
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
    pen.write("path: {}\ndirection: {}\naddress: {}\naction: {}\nstart: {}\nstop: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\nstop{}: {}\ngood to go loading/unloading: {}/{}".format(path, direction, current_address, action, start, stop, 0, stop0, 1, stop1, 2, stop2, 3, stop3, 4, stop4, 5, stop5, 6, stop6, good_to_go_loading, good_to_go_unloading), align="center", font=("Courier", 11, "normal"))

    # time.sleep(0.2)
