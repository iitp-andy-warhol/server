from socket import *
import pickle
import threading as th
import time
import numpy as np
import robotstatus as rs


def send_robot_status(server, client):
    global direction, current_address, action, current_basket, operating_orderset, operating_order, next_orderset
    current_raw_status = None
    while True:
        recvData = client.recv(8192)
        raw_status = pickle.loads(recvData)
        if raw_status != current_raw_status:
            print("Raw status: ", raw_status, time.strftime('%c', time.localtime(time.time())))
            current_raw_status = np.copy(raw_status)

        direction = raw_status['direction']
        current_address = raw_status['current_address']
        action = raw_status['action']

        robot_status = rs.makeRobotStatus(direction, current_address, action, current_basket, operating_orderset,
                                       operating_order, next_orderset)

        sendData = pickle.dumps(robot_status, protocol=pickle.HIGHEST_PROTOCOL)
        server.send(sendData)
        print("status send time: ", time.strftime('%c', time.localtime(time.time())))


def receive_robot_command(server, client):
    global command, massage, operating_orderset, operating_order, operating_order_idx, operating_order_idx_lock, next_orderset
    global need_after_loading_job_flag, need_after_loading_job_flag_lock, need_after_unloading_job_flag, need_after_unloading_job_flag_lock
    global current_basket, action, next_orderset
    current_massage = None
    while True:
        recvData = server.recv(8192)
        massage = pickle.loads(recvData)
        print("Message: ", massage, time.strftime('%c', time.localtime(time.time())))
        if massage != current_massage:
            # print("Message: ", massage, time.strftime('%c', time.localtime(time.time())))
            current_massage = np.copy(massage)

        if massage['orderset'] is not None:
            next_orderset = massage['orderset']

        if next_orderset is not None and massage['massage'] is not None:
            print("?????????????????????????????????????????????????????")
            operating_orderset = next_orderset

            operating_order_idx_lock.acquire()
            operating_order_idx = 0  # reset idx
            operating_order_idx_lock.release()

            next_orderset = None

        if massage['massage'] == 'loading_complete':
            current_basket = operating_orderset['item']  # update basket
            operating_order = operating_orderset['dumporders'][operating_order_idx]  # get next order from orderset

            operating_order_idx_lock.acquire()
            operating_order_idx += 1
            operating_order_idx_lock.release()

        if massage['massage'] == 'unloading_complete':
            # update basket
            item = operating_order['item']
            current_basket['r'] -= item['r']
            current_basket['g'] -= item['g']
            current_basket['b'] -= item['b']

            operating_order = operating_orderset['dumporders'][operating_order_idx]  # get next order from orderset

            operating_order_idx_lock.acquire()
            operating_order_idx += 1
            operating_order_idx_lock.release()
        if operating_orderset is not None:
            if operating_orderset['path'] == None:
                command['path'] = (0, )
            else:
                command['path'] = tuple(map(int, operating_orderset['path']))
            command['path_id'] = operating_orderset['id']
            command['message'] = massage['massage']

        sendData = pickle.dumps(command, protocol=pickle.HIGHEST_PROTOCOL)
        client.send(sendData)


direction = 1
current_address = 0
action = 'loading'
current_basket = {'r': 0, 'g': 0, 'b': 0}
operating_orderset = {'init': 'init', 'item': {'r':99,'g':99,'b':99}, 'path':None, 'id':99999999}
operating_order = {'address': 0, 'id': 99999, 'item': {'r':99,'g':99,'b':99}, 'orderid':[999999]}
next_orderset = None

operating_order_idx = 0
operating_order_idx_lock = th.Lock()

need_after_loading_job_flag = False
need_after_loading_job_flag_lock = th.Lock()
need_after_unloading_job_flag = False
need_after_unloading_job_flag_lock = th.Lock()

massage = {
    'massage': None,  # loading_complete / unloading_complete / None
    'orderset': None  # 오더셋 넣기 / None
}

command = {
    'message': None,  # loading_complete / unloading_complete / None
    'path': (0, ),  # path / None
    'path_id': None  # to ignore same path
}

# connect to server
server_ip = 'localhost'
server_port = 8081

clientSock = socket(AF_INET, SOCK_STREAM)
clientSock.connect((server_ip, server_port))

print('접속 완료')

# listen to client
middle_ip = 'localhost'
middle_port = 8090

middleSock = socket(AF_INET, SOCK_STREAM)
middleSock.bind((middle_ip, middle_port))  # Middleware IP
middleSock.listen(5)

print('Waiting for client')

connectionSock, addr = middleSock.accept()

print(str(addr), 'connected as a client')

# start threads
t_send_robot_status = th.Thread(target=send_robot_status, args=(clientSock, connectionSock))
t_receive = th.Thread(target=receive_robot_command, args=(clientSock, connectionSock))

t_send_robot_status.start()
t_receive.start()

while True:
    # print(operating_order_idx)
    time.sleep(1)
