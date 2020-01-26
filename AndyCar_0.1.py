import threading as th
import pickle
import time
import numpy as np

import turtle
from socket import *

def receive_command(sock):
    global command
    while True:
        recvData = sock.recv(1024)
        command = pickle.loads(recvData)
        print("received", command)
        time.sleep(1)


def send_status(sock):
    global direction, current_address, action
    while True:
        robot_status = makeRobotStatus(direction, current_address, action)

        sendData = pickle.dumps(robot_status, protocol=pickle.HIGHEST_PROTOCOL)
        sock.send(sendData)
        print("send", robot_status)
        time.sleep(0.5)


def makeRobotStatus(direction, current_address, action):
    dic = {
        'direction': direction,
        'current_address': current_address,
        'action': action,
    }
    return dic


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


def change_flag(flag):
    if flag:
        flag = False
    else:
        flag = True
    return flag


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


# Car
car = turtle.Turtle()
car.shape("square")  # original size is 20*20
car.color("blue")
car.shapesize(stretch_wid=4, stretch_len=4)
car.penup()
car.goto(bx, by)


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
# # UI
# pen = turtle.Turtle()
# pen.speed(0)
# pen.color("white")
# pen.penup()
# pen.hideturtle()
# pen.goto(300, 200)
# pen.write(path, align="left", font=("Courier", 20, "normal"))
#
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
wn.onkeypress(Go, "Right")

initialize_flags = []
for flags in range(20):
    initialize_flags += [False]
get_flag, start, ccw = True, True, True
good_to_go_loading, good_to_go_unloading, mmode_flag = False, False, False
receive_command_flag = True
stop0 = True
stop1, stop2, stop3, stop4, stop5, stop6, msg0, msg1, msg2, msg3, msg4, msg5, msg6, turn0, turn1, turn2, turn3, turn4, turn5, turn6 = initialize_flags

stop = False
msgstop = False

# Main game loop
while True:
    wn.update()

    if command['path'] == (0,):
        start = False

    elif action != "moving" and action != "M-mode":
        path_id = command['path_id']
        current_path_id = None
        if path_id != current_path_id:
            if command['path'] is not None:
                path = command['path']
                current_path_id = np.copy(path_id)

        if command['message'] == 'loading_complete':
            good_to_go_loading = True
            # command['message'] = None

        if command['message'] == 'unloading_complete':
            good_to_go_unloading = True
            # command['message'] = None

    if get_flag:
        stop0 = True
        stop1, stop2, stop3, stop4, stop5, stop6, msg0, msg1, msg2, msg3, msg4, msg5, msg6, turn0, turn1, turn2, turn3, turn4, turn5, turn6 = initialize_flags

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


    # address
    if car.pos() == loc_st0:
        address = 0
    elif car.pos() == loc_st1:
        address = 1
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
    else:
        address = 999


    # stop
    if mmode_flag:
        action = "M-mode"
        stop = True
        msgstop = True
    elif address == 0 and start and turn0:
        action = "moving"
        ccw = change_flag(ccw)
        turn0 = False
    elif address == 0 and stop0 and not start:
        action = "loading"
        stop = True
        msgstop = True
        if msg0:
            # path, " done"
            msg0 = False
            get_flag = True
        if good_to_go_loading:
            start = True
            stop = False
            good_to_go_loading = False
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
        if msg3:
            print("unloading")
            msg3 = False
        if good_to_go_unloading:
            good_to_go_unloading = False
            stop3 = False
            stop = False
    elif address == 4 and stop4:
        action = "unloading"
        stop = True
        msgstop = True
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
        if msg6:
            print("unloading")
            msg6 = False
        if good_to_go_unloading:
            good_to_go_unloading = False
            stop6 = False
            stop = False
    else:
        action = "moving"

    if ccw:
        direction = 1
    else:
        direction = -1
    if current_address != address:
        current_address = address
    elif action != "loading" and action != "unloading":
        current_address = 999

    time.sleep(0.2)


