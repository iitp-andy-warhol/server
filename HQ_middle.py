from socket import *
import pickle
import threading as th
import time
import numpy as np
import robotstatus as rs
from datetime import datetime


mid_ip = '172.20.10.2'


def send_robot_status(server, client):
    global direction, current_address, action, current_basket, operating_orderset, operating_order, id_list
    current_raw_status = None
    mmode_block = False
    mmode_start = None
    error_type = None
    dash_file_name = None
    robot_ping = 0
    while True:
        recvData = client.recv(8192)
        raw_status = pickle.loads(recvData)

        if raw_status['action'] == 'dash_file_name':
            dash_file_name = raw_status['dash_file_name']
            error_type = raw_status['error_type']
            print('!!!!!!!!!!!!!!!!!')
            continue
        elif raw_status['action'] != 'm_mode':
            try:
                robot_ping = time.time() - raw_status['ping']
            except:
                robot_ping = time.time()


        if raw_status != current_raw_status:
            print("Raw status: ", raw_status, time.strftime('%c', time.localtime(time.time())))
            current_raw_status = np.copy(raw_status)

        direction = raw_status['direction']
        current_address = raw_status['current_address']
        action = raw_status['action']

        robot_status = rs.makeRobotStatus(direction, current_address, action, current_basket, operating_orderset,
                                          operating_order, id_list, robot_ping)

        if action == "M-mode" and not mmode_block:
            now = datetime.now()
            mmode_start = now.strftime("%Y-%m-%d %H:%M:%S")
            mmode_block = True
            print('!!!!!!!!!!!Mmodeblock')
        if action != "M-mode" and mmode_block:
            now = datetime.now()
            m_mode = {
                'table_name': 'm_mode',
                'start_time': f"'{mmode_start}'",
                'end_time': f"'{now.strftime('%Y-%m-%d %H:%M:%S')}'",
                'error_type': f"'{error_type}'",
                'dash_file_name': f"'{dash_file_name}'"
            }
            mmode_block = False
            sendData = pickle.dumps(m_mode, protocol=pickle.HIGHEST_PROTOCOL)
            server.sendall(sendData)
            print("dash file send time: ", time.strftime('%c', time.localtime(time.time())))
            print(m_mode)
            continue

        sendData = pickle.dumps(robot_status, protocol=pickle.HIGHEST_PROTOCOL)
        server.sendall(sendData)
        print("status send time: ", time.strftime('%c', time.localtime(time.time())))


def receive_robot_command(server, client):
    global command, massage, operating_orderset, operating_order, operating_order_idx, operating_order_idx_lock
    global need_after_loading_job_flag, need_after_loading_job_flag_lock, need_after_unloading_job_flag, need_after_unloading_job_flag_lock
    global current_basket, action, id_list
    wait_flag = False
    current_massage = None
    current_id = None
    orderset_block = False
    keep_msg = None
    keep_id = None
    orders_list = []
    id_list = []
    counter = 0
    while True:
        recvData = server.recv(8192)
        massage = pickle.loads(recvData)
        print("Message: ", massage, time.strftime('%c', time.localtime(time.time())))
        if massage != current_massage:
            # print("Message: ", massage, time.strftime('%c', time.localtime(time.time())))
            current_massage = np.copy(massage)

        if massage['orderset'] is not None and not orderset_block:
            if massage['orderset']['id'] not in id_list:
                if len(orders_list) < 3:
                    orders_list += [massage['orderset']]
                    id_list += [massage['orderset']['id']]

        if action == 'loading' and (operating_order['id'] == 99999 or operating_order['id'] == 9999):
            if len(id_list) > 0:
                operating_orderset = orders_list.pop(0)
                operating_id = id_list.pop(0)
                if operating_orderset['id'] != operating_id:
                    print('!!!!!!!! ID != ORDERSET !!!!!!!!!!!')
                    print('!!!!!!!! ID != ORDERSET !!!!!!!!!!!')
                    print('!!!!!!!! ID != ORDERSET !!!!!!!!!!!')

                operating_order_idx_lock.acquire()
                operating_order_idx = 0  # reset idx
                operating_order_idx_lock.release()

                operating_order = operating_orderset['dumporders'][operating_order_idx]  # get next order from orderset

                operating_order_idx_lock.acquire()
                operating_order_idx += 1
                operating_order_idx_lock.release()

                # next_orderset = {'id': None, 'path': None, 'item': None}
                # print(3333, next_orderset)
                # if operating_order['address'] != 0:
                #     orderset_block = True
            else:
                operating_orderset = {'init': 'init', 'id': 99999999,
                                      'dumporders': [{'id': 99999, 'partial': [], 'orderid': [999999], 'item': {'r': 0, 'g': 0, 'b': 0}, 'address': 0}],
                                      'path': None, 'profit': None, 'item': {'r': 0, 'g': 0, 'b': 0}}

                operating_order_idx_lock.acquire()
                operating_order_idx = 0  # reset idx
                operating_order_idx_lock.release()

                current_basket = operating_orderset['item']  # update basket
                operating_order = operating_orderset['dumporders'][operating_order_idx]  # get next order from orderset
        elif action != 'loading':
            orderset_block = False
            # print(4444, next_orderset)

        if action == 'unloading' and massage['massage'] == 'unloading_complete':
            # if next_orderset['id'] is None:
                # update basket
            item = operating_order['item']
            current_basket['r'] -= item['r']
            current_basket['g'] -= item['g']
            current_basket['b'] -= item['b']

            operating_order = operating_orderset['dumporders'][operating_order_idx]  # get next order from orderset

            operating_order_idx_lock.acquire()
            operating_order_idx += 1
            operating_order_idx_lock.release()
            # else:
            #     # print("?????????????????????????????????????????????????????")
            #     # update basket
            #     item = operating_order['item']
            #     current_basket['r'] -= item['r']
            #     current_basket['g'] -= item['g']
            #     current_basket['b'] -= item['b']
            #
            #     operating_orderset = next_orderset
            #
            #     operating_order_idx_lock.acquire()
            #     operating_order_idx = 0  # reset idx
            #     operating_order_idx_lock.release()
            #
            #     operating_order = operating_orderset['dumporders'][operating_order_idx]  # get next order from orderset
            #
            #     operating_order_idx_lock.acquire()
            #     operating_order_idx += 1
            #     operating_order_idx_lock.release()
            #
            #     next_orderset = {'id': None, 'path': None, 'item': None}
            #     # print(2222, next_orderset)

        if massage['massage'] == 'loading_complete':
            current_basket = operating_orderset['item']  # update basket

        if operating_orderset['id'] is not None:
            if operating_orderset['path'] == None:
                command['path'] = (0, )
            else:
                command['path'] = tuple(map(int, operating_orderset['path']))
            command['path_id'] = operating_orderset['id']
            command['message'] = massage['massage']
            command['message_id'] = counter
            if command['message'] == 'loading_complete' or command['message'] == 'unloading_complete':
                if action == "loading" or action == "unloading":
                    wait_flag = True
                    keep_msg = command['message']
                    keep_id = command['message_id']
        if action != "loading" and action != "unloading":
            wait_flag = False
        if wait_flag and command['message'] == None:
            command['message'] = keep_msg
            command['message_id'] = keep_id
        command['ping'] = time.time()
        print("Command: ", command)
        sendData = pickle.dumps(command, protocol=3)
        client.sendall(sendData)
        counter += 1


direction = 1
current_address = 0
action = 'loading'
current_basket = {'r': 0, 'g': 0, 'b': 0}
operating_orderset = {'init': 'init', 'id': 99999999,
                     'dumporders': [{'id': 99999, 'partial': [], 'orderid': [999999], 'item': {'r': 0, 'g': 0, 'b': 0}, 'address': 0}],
                     'path': None, 'profit': None, 'item': {'r': 0, 'g': 0, 'b': 0}}

operating_order = {'address': 0, 'id': 99999, 'item': {'r':0,'g':0,'b':0}, 'orderid':[999999]}
id_list = []
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
    'path_id': None,  # to ignore same path
    'message_id': -1,
    'ping': 0
}

# connect to server
server_ip = 'localhost'
server_port = 8081

clientSock = socket(AF_INET, SOCK_STREAM)
clientSock.connect((server_ip, server_port))

print('접속 완료')

# listen to client
middle_ip = mid_ip
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
