import functools
import multiprocessing as mp
import pickle
import threading as th
import time
from socket import *

import numpy as np
import pandas as pd

import mysql.connector
import orderdic as od
from utils import *
from scheduler import *
import copy


def Schedule(existing_order_grp_profit,
             order_grp_new,
             order_grp_new_lock,
             update_order_grp_flag,
             update_order_grp_flag_lock,
             pending_df,
             scheduling_required_flag,
             scheduling_required_flag_lock,
             schedule_changed_flag,
             schedule_changed_flag_lock,
             next_orderset_idx,
             next_orderset_idx_lock,
             operating_order_id,
             direction,
             current_address,
             current_basket,
             operating_dump_id):

    print('@@@@@@@@@@@ Schedule() is on@@@@@@@@@@@ ')
    osID = 0
    dumID = 0

    @timefn
    def get_optimized_order_grp(existing_order_grp_profit, pdf, rs, threshold=0):
        if len(pdf) == 0:
            return None
        pdf['partialid'] = 0
        pdf['profit'] = 1
        pending_orders = [od.makeOrder(row) for idx, row in pdf.iterrows()]

        # Convert to partial orders
        # print("!!"*100)
        print(rs['operating_order']['id'])
        to_loading_zone = rs['operating_order']['id'] in [9999, 99999]
        at_loading_zone = rs['current_address'] == 0
        current_basket = rs['current_basket']

        all_partials = partialize_for_loading(pending_orders, item_limit=PARTIAL_THRESHOLD)
        # Update order profit
        all_partials = [evaluate_order(rs['current_address'], order) for order in all_partials]

        if to_loading_zone or at_loading_zone:
            # Sort orders by profit
            all_partials = filter_empty_orders(all_partials)
            partials_sorted = sort_orders(all_partials, by='profit', ascending=False)
            grouped_partial_orders = group_orders_n(partials_sorted, BASKET_SIZE)
        else:
            in_basket, not_in_basket = partialize_for_basket(all_partials, current_basket)
            in_basket = sort_orders(in_basket, by='profit', ascending=False)  # optional
            this_os, remaining_orders = group_orders_for_basket(in_basket, current_basket)
            remaining_orders += not_in_basket

            this_os = filter_empty_orders(this_os)
            remaining_orders = filter_empty_orders(remaining_orders)

            # Sort remaining orders by profit
            remaining_orders = sort_orders(remaining_orders, by='profit', ascending=False)

            # Group partial orders
            grouped_partial_orders = group_orders_n(remaining_orders, BASKET_SIZE)

        # Make dump orders
        nonlocal dumID
        all_dumps = []
        for po_group in grouped_partial_orders:
            group_by_address = group_same_address(po_group).values()
            for dumped_order in group_by_address:
                all_dumps.append(od.makeDumpedOrder(dumpid=dumID, PartialOrderList=dumped_order))

        grouped_dumped_orders = group_orders_n(all_dumps, BASKET_SIZE)

        if to_loading_zone or at_loading_zone:
            grouped_dumped_orders = filter_empty_orders(grouped_dumped_orders)
        else:
            this_dump = []
            group_by_address = group_same_address(this_os).values()
            for i, dumped_order in enumerate(group_by_address, 1):
                dumID = len(all_dumps) + i
                this_dump.append(od.makeDumpedOrder(dumpid=dumID, PartialOrderList=dumped_order))
            grouped_dumped_orders.insert(0, this_dump)

        # Make order sets
        all_ordersets = []
        nonlocal osID
        for do_group in grouped_dumped_orders:
            # TODO : use robot status information to make path
            # TODO : improve algorithm estimating profit
            os = od.makeOrderSet(robot_status=rs, ordersetid=osID,
                                 DumpedOrderList=do_group)
            all_ordersets.append(os)
            osID += 1

        # Make order group
        new_order_grp = od.makeOrderGroup(OrderSetList=all_ordersets)

        if new_order_grp['profit'] - existing_order_grp_profit > threshold:
            return new_order_grp
        else:
            return None

    while True:
        if scheduling_required_flag.value:
            print('@@@@@@@@@@@ Making new schedule @@@@@@@@@@@')
            schedule_info = {
                'direction': direction.value,
                'current_address': current_address.value,
                'current_basket': {'r': current_basket[0], 'g': current_basket[1], 'b': current_basket[2]},
                'operating_order': {'id':operating_dump_id.value}
            }
            pdf_for_scheduling = pending_df.df.copy()
            pdf_for_scheduling = pdf_for_scheduling.iloc[[x not in operating_order_id.l for x in pdf_for_scheduling['id']]].reset_index()
            print('11111111111111111111111111111111111111111111111111111111111111111')
            new_order_grp = get_optimized_order_grp(existing_order_grp_profit.value, pdf_for_scheduling, schedule_info)

            print('222222222222222222222222222222222222222222222222222222222222222222222', new_order_grp)
            if new_order_grp is not None:
                print('3333333333333333333333333333333333333333', new_order_grp)
                order_grp_new_lock.acquire()
                order_grp_new['dict'] = new_order_grp
                order_grp_new_lock.release()

                update_order_grp_flag_lock.acquire()
                update_order_grp_flag.value = True
                update_order_grp_flag_lock.release()

                schedule_changed_flag_lock.acquire()
                schedule_changed_flag.value = True
                schedule_changed_flag_lock.release()

                next_orderset_idx_lock.acquire()
                next_orderset_idx.value = -1
                next_orderset_idx_lock.release()

            scheduling_required_flag_lock.acquire()
            scheduling_required_flag.value = False
            scheduling_required_flag_lock.release()
        time.sleep(5)


def getdb(cursor, pending_pdf_colname):
    query = f"SELECT {', '.join(pending_pdf_colname)} " + "FROM orders WHERE pending = 1"
    cursor.execute(query)
    pending = cursor.fetchall()
    pending = pd.DataFrame(pending, columns=pending_pdf_colname)
    return pending


def largePrint(text):
    print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
          '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
          f'                       {text}',
          '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
          '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
          sep='\n')

class Logger:
    def __init__(self):
        self.host = 'localhost'
        self.user = 'root'
        self.passwd = 'pass'
        self.dbname = 'orderdb'

        print("START EXPERIMENT")
        self.experiment = {
            'table_name': 'experiment',
            'max_time': input('Please enter max_time        :'),
            'num_order': input('Please enter num_order       :'),
            'order_stop_time': input('Please enter order_stop_time :'),
            'scheduler_id': input('Please enter scheduler_id    :')
        }
        self.scheduling = {
            'table_name': 'scheduling',
            'scheduler_id': self.experiment['scheduler_id'],
            'start_time': None,
            'end_time': None,
            'num_order': None,
            'num_item': None
        }
        self.departure = {
            'table_name': 'departure',
            'depart_time': None,
            'arrive_time': None,
            'num_order': None,
            'num_item': None
        }
        self.timestamp_loading = {
            'table_name': 'timestamp_loading',
            'num_item': None,
            'refresh_alert_time': None,
            'connect_time': None,
            'confirm_time': None
        }
        self.timestamp_unloading = {
            'table_name': 'timestamp_unloading',
            'num_item': None,
            'refresh_alert_time': None,
            'connect_time': None,
            'confirm_time': None
        }

        self.InsertLog(self.experiment)
        self.exp_id = self.get_exp_id()

        input(f"Press Enter to Start Experiment #{self.exp_id}")

    def get_exp_id(self):
        cnx = mysql.connector.connect(host=self.host, user=self.user, password=self.passwd, database=self.dbname,
                                      auth_plugin='mysql_native_password')
        cursor = cnx.cursor()
        query = "SELECT MAX(exp_id) FROM experiment;"
        cursor.execute(query)
        return cursor.fetchall()[0][0]

    def InsertLog(self, table):
        cnx = mysql.connector.connect(host=self.host, user=self.user, password=self.passwd, database=self.dbname,
                                      auth_plugin='mysql_native_password')
        cursor = cnx.cursor()

        tbname = table['table_name']
        col = ''
        val = ''
        for key in list(table_name.keys())[0:]:
            col = col + key + ', '
            val = val + table[key] + ', '
        col = col[:-2]
        val = val[:-2]

        query = f"INSERT INTO {tbname} ({col}) VALUES ({val});"
        cursor.execute(query)
        cnx.commit()

    def EndExperiment(self):
        cnx = mysql.connector.connect(host=self.host, user=self.user, password=self.passwd, database=self.dbname,
                                      auth_plugin='mysql_native_password')
        cursor = cnx.cursor()
        query = f'UPDATE experiment SET end_time = NOW(), num_fulfilled = (SELECT COUNT(*) FROM orders WHERE pending=0) WHERE exp_id = {self.exp_id};'
        cursor.execute(query)
        cnx.commit()


class ControlCenter:
    def __init__(self):
        with open("banana.txt") as f:
            print('\n', f.read(),'\n')
        # self.logger = Logger()

        self.pending_pdf_colname = ['id', 'address', 'red', 'green', 'blue', 'required_red','required_green','required_blue', 'orderdate']
        self.pending_df = mp.Manager().Namespace()
        self.pending_df.df = pd.DataFrame(columns=self.pending_pdf_colname)
        self.pending_df_lock = mp.Lock()
        self.just_get_db_flag = False
        self.just_get_db_flag_lock = th.Lock()

        self.fulfill_order_flag = False
        self.fulfill_order_flag_lock = th.Lock()
        self.update_inventory_flag = False
        self.update_inventory_flag_lock = th.Lock()

        self.order_grp = od.makeOrderGroup()
        self.order_grp_lock = th.Lock()

        self.existing_order_grp_profit = mp.Value('d', 0.0)
        self.existing_order_grp_profit_lock = mp.Lock()

        self.order_grp_new = mp.Manager().dict({'dict': None, 'ordersets': []})
        self.order_grp_new_lock = mp.Lock()

        self.operating_order_id = mp.Manager().Namespace()
        self.operating_order_id.l = []
        self.operating_order_id_lock = mp.Lock()

        self.update_order_grp_flag = mp.Manager().Value('flag', False)
        self.update_order_grp_flag_lock = mp.Lock()

        self.next_orderset = {'init': 'init', 'item':  {'r': 0, 'g': 0, 'b': 0}, 'id':99999999}
        self.next_orderset_lock = mp.Lock()

        self.send_next_orderset_flag = False
        self.send_next_orderset_flag_lock = th.Lock()

        self.next_orderset_idx = mp.Manager().Value('i', -1)
        self.next_orderset_idx_lock = mp.Lock()

        self.l_order = {}
        self.l_partial = {}
        self.l_dumped = {}
        self.l_orderset = {}

        self.scheduling_required_flag = mp.Manager().Value('flag', True)
        self.scheduling_required_flag_lock = mp.Lock()
        self.schedule_changed_flag = mp.Manager().Value('flag', False)
        self.schedule_changed_flag_lock = mp.Lock()

        self.loading_complete_flag = False
        self.loading_complete_flag_lock = th.Lock()
        self.unloading_complete_flag = False
        self.unloading_complete_flag_lock = th.Lock()

        self.inventory = {'r': 25, 'g': 25, 'b': 25}
        self.inventory_lock = th.Lock()

        self.got_init_robot_status = False
        self.got_init_orderset = False
        self.robot_status = mp.Manager().dict(
            {'direction': 1, 'current_address': 0,'operating_order': {'address': 99999, 'id': 99999, 'item': {'r': 0, 'g': 0, 'b': 0}, 'orderid':[99999]},
             'operating_orderset':{'item': {'r': 0, 'g': 0, 'b': 0}, 'id':99999999}, 'current_basket': {'r': 0, 'g': 0, 'b': 0},
             'action': 'loading',
             'next_orderset': None,
             'log_time': None})

        self.robot_status_log = []

        self.schedule_direction = mp.Value('i', 1)
        self.schedule_current_address = mp.Value('i',0)
        self.schedule_current_basket = mp.Array('i', [0,0,0])
        self.schedule_operating_dump_id = mp.Value('i', 99999)

        self.loading_complete_id = 88888
        self.unloading_complete_id = 88888

    def ControlDB(self):
        largePrint('ControlDB is operated')
        host = 'localhost'
        user = 'root'
        passwd = 'pass'
        dbname = 'orderdb'

        cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=dbname, auth_plugin='mysql_native_password')
        cursor = cnx.cursor()
        cursor.execute(f"USE {dbname};")

        self.pending_df_lock.acquire()
        self.pending_df.df = getdb(cursor, self.pending_pdf_colname)
        self.pending_df_lock.release()
        getdb_time = time.time()
        dbup_time = time.time()

        while True:

            # 5초에 한번 db 가져와보고 주문 3개이상 더 들어왔을 경우 pdf갱신 및 스케줄링 하게함.
            # 120초동안 주문 3개이상 안들어오게 되면 더이상 스케줄링을 새로하지 않음.
            if time.time() - getdb_time > 5 or self.just_get_db_flag:
                self.just_get_db_flag_lock.acquire()
                self.just_get_db_flag = False
                self.just_get_db_flag_lock.release()

                cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=dbname, auth_plugin='mysql_native_password')
                cursor = cnx.cursor()
                cursor.execute(f"USE {dbname};")

                if time.time() - dbup_time > 120:

                    self.pending_df_lock.acquire()
                    self.pending_df.df = getdb(cursor, self.pending_pdf_colname)
                    self.pending_df_lock.release()

                    getdb_time = time.time()

                else:
                    pending_df = getdb(cursor, self.pending_pdf_colname)
                    getdb_time = time.time()

                    count = 0
                    for id_ in pending_df['id']:
                        if id_ not in list(self.pending_df.df['id']):
                            count += 1
                            if count >= 3:
                                self.pending_df_lock.acquire()
                                self.pending_df.df = pending_df
                                self.pending_df_lock.release()
                                dbup_time = time.time()

                                self.scheduling_required_flag_lock.acquire()
                                rs = copy.deepcopy(self.robot_status)
                                self.schedule_direction.value = rs['direction']
                                self.schedule_current_address.value = rs['operating_order']['address']
                                cur_basket = rs['current_basket']
                                fut_basket = {
                                    'r': cur_basket['r'] - rs['operating_order']['item']['r'],
                                    'g': cur_basket['g'] - rs['operating_order']['item']['g'],
                                    'b': cur_basket['b'] - rs['operating_order']['item']['b']
                                }
                                self.schedule_current_basket = mp.Array('i', [fut_basket['r'],fut_basket['g'],fut_basket['b']])

                                self.scheduling_required_flag.value = True

                                self.scheduling_required_flag_lock.release()
                                break

            if self.fulfill_order_flag:
                cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=dbname, auth_plugin='mysql_native_password')
                cursor = cnx.cursor()
                cursor.execute(f"USE {dbname};")

                for po in self.robot_status['operating_order']['partial']:
                    orderID = po['id']
                    item = po['item']
                    r = item['r']
                    g = item['g']
                    b = item['b']

                    query = f"UPDATE orders " \
                            f"SET " \
                            f"fulfilled_red=fulfilled_red + {r}, " \
                            f"fulfilled_green=fulfilled_green + {g}," \
                            f"fulfilled_blue=fulfilled_blue + {b} " \
                            f"WHERE id={orderID};"

                    cursor.execute(query)
                    cnx.commit()

                self.fulfill_order_flag_lock.acquire()
                self.fulfill_order_flag = False
                self.fulfill_order_flag_lock.release()

                self.update_inventory_flag_lock.acquire()
                self.update_inventory_flag = True
                self.update_inventory_flag_lock.release()

            time.sleep(0.5)

    def Manager(self):
        largePrint('Manager() is on')
        did_dummy = False
        while True:
            self.operating_order_id_lock.acquire()
            self.operating_order_id.l = self.robot_status['operating_order']['orderid']
            self.operating_order_id_lock.release()

            if self.update_order_grp_flag.value:
                largePrint('Schedule is updated!!')
                self.order_grp_lock.acquire()
                self.order_grp = self.order_grp_new['dict']
                self.order_grp_lock.release()

                self.existing_order_grp_profit_lock.acquire()
                self.existing_order_grp_profit.value = self.order_grp['profit']
                self.existing_order_grp_profit_lock.release()

                self.order_grp_len = len(self.order_grp['ordersets'])

                self.update_order_grp_flag_lock.acquire()
                self.update_order_grp_flag.value = False
                self.update_order_grp_flag_lock.release()
# causal learning?
            # Get next orderset from order group
            if self.got_init_robot_status:
                if not self.got_init_orderset:
                    # 제일 처음 오더셋 받기 위함
                    if self.robot_status['operating_order']['address'] == 0 and self.existing_order_grp_profit.value > 0:
                        self.next_orderset_idx_lock.acquire()
                        self.next_orderset_idx.value += 1
                        self.next_orderset_idx_lock.release()

                        if self.next_orderset_idx.value <= self.order_grp_len - 1:

                            self.next_orderset = self.order_grp['ordersets'][self.next_orderset_idx.value]

                            self.send_next_orderset_flag_lock.acquire()
                            self.send_next_orderset_flag = True
                            self.send_next_orderset_flag_lock.release()

                            self.got_init_orderset = True

                            self.schedule_changed_flag_lock.acquire()
                            self.schedule_changed_flag.value = False
                            self.schedule_changed_flag_lock.release()

                if self.robot_status['operating_order']['id'] == 9999 and self.got_init_orderset:
                    if not did_dummy:
                        did_dummy = True

                        self.next_orderset_idx_lock.acquire()
                        self.next_orderset_idx.value += 1
                        self.next_orderset_idx_lock.release()

                        if self.next_orderset_idx.value <= self.order_grp_len-1:
                            self.next_orderset = self.order_grp['ordersets'][self.next_orderset_idx.value]
                            self.send_next_orderset_flag_lock.acquire()
                            self.send_next_orderset_flag = True
                            self.send_next_orderset_flag_lock.release()
                        else:
                            # 오더그룹 다 비웠을 때 초기상태로 돌아오기
                            self.next_orderset_idx_lock.acquire()
                            self.next_orderset_idx.value = -1
                            self.next_orderset_idx_lock.release()

                            self.order_grp_lock.acquire()
                            self.order_grp = {'dict': None, 'orderset': []}
                            self.order_grp_lock.release()

                            self.got_init_orderset = False
                            self.existing_order_grp_profit.value = 0
                            self.robot_status = mp.Manager().dict(
                                {'direction': 1, 'current_address': 0,
                                 'operating_order': {'address': 99999, 'id': 99999, 'item': {'r': 0, 'g': 0, 'b': 0},
                                                     'orderid': [99999]},
                                 'operating_orderset': {'item': {'r': 0, 'g': 0, 'b': 0}, 'id': 99999999},
                                 'current_basket': {'r': 0, 'g': 0, 'b': 0},
                                 'action': 'loading',
                                 'next_orderset': None,
                                 'log_time': None})

                            self.just_get_db_flag_lock.acquire()
                            self.just_get_db_flag = True
                            self.just_get_db_flag_lock.release()

                if self.robot_status['action'] == 'unloading':
                    did_dummy = False

                # 중간에 스케줄 바뀔때 오더셋 갱신하기 위함
                if self.got_init_orderset and self.schedule_changed_flag.value and not self.update_order_grp_flag.value:
                    self.next_orderset_idx_lock.acquire()
                    self.next_orderset_idx.value += 1
                    self.next_orderset_idx_lock.release()

                    self.next_orderset = self.order_grp['ordersets'][self.next_orderset_idx.value]

                    self.send_next_orderset_flag_lock.acquire()
                    self.send_next_orderset_flag = True
                    self.send_next_orderset_flag_lock.release()

                    self.schedule_changed_flag_lock.acquire()
                    self.schedule_changed_flag.value = False
                    self.schedule_changed_flag_lock.release()

                if self.robot_status['next_orderset'] is None and self.next_orderset['id'] != self.robot_status['operating_orderset']['id']: # HQ가 넥스트오더셋 안받고 버리는 경우 다시보내주기
                    self.send_next_orderset_flag_lock.acquire()
                    self.send_next_orderset_flag = True
                    self.send_next_orderset_flag_lock.release()

            # if self.next_orderset['id'] == self.robot_status['operating_orderset']['id']:


            # Update inventory
            if self.update_inventory_flag:
                if self.loading_complete_flag:
                    item = self.robot_status['operating_orderset']['item']
                    self.inventory_lock.acquire()
                    self.inventory['r'] -= item['r']
                    self.inventory['g'] -= item['g']
                    self.inventory['b'] -= item['b']
                    self.inventory_lock.release()

                if self.unloading_complete_flag:
                    item = self.robot_status['operating_order']['item']
                    self.inventory_lock.acquire()
                    self.inventory['r'] += item['r']
                    self.inventory['g'] += item['g']
                    self.inventory['b'] += item['b']
                    self.inventory_lock.release()

                self.update_inventory_flag_lock.acquire()
                self.update_inventory_flag = False
                self.update_inventory_flag_lock.release()



            time.sleep(0.1)

    def RobotSocket(self):
        largePrint('RobotSocket() is on')

        def send(sock):
            while True:
                if self.got_init_robot_status:
                    massage = {
                              'massage': None,  # loading_complete / unloading_complete / None
                              'orderset': None  # 오더셋 넣기 / None
                    }

                    # Send next order set to HQ as HQ.operating_orderset
                    if self.send_next_orderset_flag: # 실시간 o
                    # if self.send_next_orderset_flag and (self.robot_status['operating_order']['id'] == 9999 or
                    #     self.robot_status['operating_order']['id'] == 99999): # 실시간 x

                        massage['orderset'] = self.next_orderset

                        self.send_next_orderset_flag_lock.acquire()
                        self.send_next_orderset_flag = False
                        self.send_next_orderset_flag_lock.release()

                    # After loading and updating inventory
                    if self.loading_complete_flag and not self.update_inventory_flag:
                        massage['massage'] = 'loading_complete'

                        self.loading_complete_flag_lock.acquire()
                        self.loading_complete_flag = False
                        self.loading_complete_flag_lock.release()

                    # After unloading and fulfilling order db and updating inventory
                    if self.unloading_complete_flag and not self.fulfill_order_flag and not self.update_inventory_flag:
                        massage['massage'] = 'unloading_complete'

                        self.unloading_complete_flag_lock.acquire()
                        self.unloading_complete_flag = False
                        self.unloading_complete_flag_lock.release()

                    sock.sendall(pickle.dumps(massage, protocol=pickle.HIGHEST_PROTOCOL))
                time.sleep(0.2)

        def get_robot_status(sock):
            while True:
                data = sock.recv(32768) #2^13 bit
                data = pickle.loads(data)

                # self.robot_status_log.append(self.robot_status)
                self.robot_status = mp.Manager().dict(data)

                self.got_init_robot_status = True
                self.schedule_operating_dump_id = data['operating_order']['id']

        port = 8081

        serverSock = socket(AF_INET, SOCK_STREAM)
        serverSock.bind(('', port))
        serverSock.listen(1)
        print('@@@@@@@@@@@ %d번 포트로 접속 대기중... @@@@@@@@@@@' % port)

        connectionSock, addr = serverSock.accept()

        print('@@@@@@@@@@@ '+str(addr), '에서 접속되었습니다. @@@@@@@@@@@')

        t_get_robot_status = th.Thread(target=get_robot_status, args=(connectionSock,))
        t_send = th.Thread(target=send, args=(connectionSock, ))

        t_get_robot_status.start()
        t_send.start()

        while True:
            time.sleep(1)

    def UIServer(self):
        largePrint('UIServer() is on')
        from flask import Flask, render_template
        from flask_bootstrap import Bootstrap
        app = Flask(__name__)
        Bootstrap(app)
        app.config['ENV'] = 'development'

        @app.route('/loading')
        def loadingworker():
            ########################로딩워커 UI에는 실제로 로딩해야 할 아이템이 보여져야한다. 중간에 스케줄이 체인지 돼서
            # 지금은 next_orderset이 변경된 경우 로딩UI에는 실제로 로딩을 할것도 아닌데 새 next_orderset의 아이템이 보여진다.
            # 실제로 로딩해야할 넥스트오더셋의 아이템이 매니저에서 갱신된 경우 소리등의 방식으로 알림을 줘서 워커가 제대로 된
            # 로딩 아이템을 볼 수 있게 해줘야 함.
            items = self.robot_status['operating_orderset']['item']

            return render_template('loading.html', items=items)

        @app.route('/loading-success')
        def change_flags_loading():
            # 이거 접속되는 시점 기록되야됨.

            if self.robot_status['operating_orderset']['id'] == self.loading_complete_id:
                pass
            else:
                self.loading_complete_id = self.robot_status['operating_orderset']['id']

                self.loading_complete_flag_lock.acquire()
                self.loading_complete_flag = True
                self.loading_complete_flag_lock.release()

                self.update_inventory_flag_lock.acquire()
                self.update_inventory_flag = True
                self.update_inventory_flag_lock.release()
            return render_template('loading_success.html')

        @app.route('/unloading')
        def unloadingworker():
            # 접속시간 기록해야됨
            items = self.robot_status['operating_order']['item']
            order_id = self.robot_status['operating_order']['orderid']
            address = self.robot_status['operating_order']['address']
            return render_template('unloading.html', items=items, order_id=order_id, address=address)

        @app.route('/unloading-success')
        def change_flags_unloading():

            order_id = self.robot_status['operating_order']['orderid']
            address = self.robot_status['operating_order']['address']


            if self.robot_status['operating_order']['id'] == self.unloading_complete_id:
                pass
            else:
                self.unloading_complete_id = self.robot_status['operating_order']['id']

                self.unloading_complete_flag_lock.acquire()
                self.unloading_complete_flag = True
                self.unloading_complete_flag_lock.release()

                self.fulfill_order_flag_lock.acquire()
                self.fulfill_order_flag = True
                self.fulfill_order_flag_lock.release()

            return render_template('unloading_success.html', order_id=order_id, address=address)

        @app.route('/monitor')
        def monitoring():

            return 'This is monitor.'

        app.run(host='0.0.0.0', port=8080)

    def Print_info(self):
        while True:
            robot_status_print = {}
            if not self.got_init_robot_status:
                robot_status_print = {
                    'direction': None,
                    'current_address': None,
                    # 'next_address': None,
                    'action': None,
                    'current_basket': None,
                    'operating_orderset': None,
                    'operating_order': None,
                    'next_orderset': None,
                    'log_time': None
                }
            else:
                robot_status_print = self.robot_status
            with pd.option_context('display.max_rows', None, 'display.max_columns',
                                   None):  # more options can be specified also
                print(f"##------------------------------------{time.strftime('%c', time.localtime(time.time()))}------------------------------------##",
                      f'pending_df.df: \n{self.pending_df.df}',
                      f'got_init_robot_status:++++++++++{self.got_init_robot_status}',
                      f'got_init_orderset:--------------{self.got_init_orderset}',
                      f'scheduling_required_flag.value:-{self.scheduling_required_flag.value}',
                      f'update_order_grp_flag:----------{self.update_order_grp_flag.value}',
                      f'schedule_changed_flag.value:++++{self.schedule_changed_flag.value}',
                      f'send_next_orderset_flag:--------{self.send_next_orderset_flag}',
                      f'loading_complete_flag:----------{self.loading_complete_flag}',
                      f'unloading_complete_flag:++++++++{self.unloading_complete_flag}',
                      f'fulfill_order_flag:-------------{self.fulfill_order_flag}',
                      f'update_inventory_flag:++++++++++{self.update_inventory_flag}',
                      '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -',
                      f'order_grp:----------------------{self.order_grp}',
                      f'next_orderset_idx.value:++++++++{self.next_orderset_idx.value}',
                      f'next_orderset:++++++++++++++++++{self.next_orderset}',
                      f'inventory:----------------------{self.inventory}',
                      '- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -',
                      f'=============== robot_status ===============',
                      f"| log_time: {robot_status_print['log_time']}",
                      f"| diredction: {robot_status_print['direction']}",
                      f"| current_address: {robot_status_print['current_address']}",
                      # f"| next_address: {robot_status_print['next_address']}",
                      f"| action: {robot_status_print['action']}",
                      f"| current_basket: {robot_status_print['current_basket']}",
                      f"| operating_orderset: {robot_status_print['operating_orderset']}",
                      f"| operating_order: {robot_status_print['operating_order']}",
                      f"| operating_order_id: {self.operating_order_id.l}",
                      f"| next_orderset: {robot_status_print['next_orderset']}",
                      f'===========================================',

                      '\n',
                      sep='\n')

            time.sleep(0.5)

    def Operate(self):
        largePrint('Command Center is operated')
        t_ControlDB = th.Thread(target=self.ControlDB, args=())
        t_UIServer = th.Thread(target=self.UIServer, args=())
        t_Manager = th.Thread(target=self.Manager, args=())
        t_RobotSocket = th.Thread(target=self.RobotSocket, args=())
        t_PrintLog = th.Thread(target=self.Print_info, args=())
        p_Schedule = mp.Process(target=Schedule,
                                args=(
                                 self.existing_order_grp_profit,
                                 self.order_grp_new,
                                 self.order_grp_new_lock,
                                 self.update_order_grp_flag,
                                 self.update_order_grp_flag_lock,
                                 self.pending_df,
                                 self.scheduling_required_flag,
                                 self.scheduling_required_flag_lock,
                                 self.schedule_changed_flag,
                                 self.schedule_changed_flag_lock,
                                 self.next_orderset_idx,
                                 self.next_orderset_idx_lock,
                                 self.operating_order_id,
                                 self.schedule_direction,
                                 self.schedule_current_address,
                                 self.schedule_current_basket,
                                 self.schedule_operating_dump_id,
                                ))

        t_ControlDB.daemon = True
        t_UIServer.daemon = True
        t_Manager.daemon = True
        t_RobotSocket.daemon = True
        t_PrintLog.daemon = True
        # p_Schedule.daemon = True

        t_ControlDB.start()
        t_UIServer.start()
        t_Manager.start()
        t_RobotSocket.start()
        t_PrintLog.start()
        p_Schedule.start()


        while True:
            time.sleep(1)
        input()
        p_Schedule.terminate()




if __name__ == "__main__":
    cc = ControlCenter()
    cc.Operate()
