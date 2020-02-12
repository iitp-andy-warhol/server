import multiprocessing as mp
import pickle
import threading as th
import time
from socket import *

import pandas as pd
import sys
from datetime import datetime

import mysql.connector
import orderdic as od
from utils import *
from scheduler import *
import copy
import operator

from flask import request

def getdb(exp_id, cursor, pending_df_colname, address_dict):
    query = f"SELECT {', '.join(pending_df_colname)} " + f"FROM orders WHERE pending = 1 and exp_id = {exp_id}"
    cursor.execute(query)
    pending = cursor.fetchall()
    pending = pd.DataFrame(pending, columns=pending_df_colname)
    pending['address'] = pending['address'].apply(lambda x: address_dict[x])
    return pending


def largePrint(text):
    print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
          '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
          f'                       {text}',
          '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
          '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',
          sep='\n')

class Logger:
    def __init__(self, for_scheduler=False, scheduler_id=None):
        self.host = 'localhost'
        self.user = 'root'
        self.passwd = 'pass'
        self.dbname = 'orderdb'

        if not for_scheduler:

            contin = input('Do you want to start a new experiment? Y/N ')
            if contin in ['Y', 'y']:
                print("STARTING A NEW EXPERIMENT")

                self.experiment = {
                    'table_name': 'experiment',
                    'max_time': input('Please enter max_time        :'),
                    'num_order': input('Please enter num_order       :'),
                    'order_stop_time': input('Please enter order_stop_time :'),
                    'scheduler_id': input('Please enter scheduler_id    :')
                }

                self.insert_log(self.experiment, reset=False)
                self.exp_id = self.get_exp_id()

            else:
                self.exp_id = self.get_exp_id()
                print(f"START THE LAST EXPERIMENT #{self.exp_id}")
                self.experiment = self.get_last_exp_info()


            self.departure = {
                'table_name': 'departure',
                'depart_time': None,
                'arrive_time': None,
                'num_order': None,
                'num_item': None,
                'total_profit': None
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

            self.m_mode_list = []

            self.num_pending = 0
            self.num_pending_list = []

            # m_mode ={
            #     'table_name': 'm_mode',
            #     'start_time': '0000-00-00 00:00:00'
            #     'end_time': '0000-00-00 00:00:00'
            #     'error_type': 'blahblah'
            #     'dash_file': []
            # }

        elif for_scheduler:
            self.scheduler_id = scheduler_id
            self.scheduling = {
                'table_name': 'scheduling',
                'scheduler_id': self.scheduler_id,
                'start_time': None,
                'end_time': None,
                'num_order': None,
                'num_item': None
            }

    def reset_table(self, table):
        if table == 'scheduling':
            self.scheduling = {
                'table_name': 'scheduling',
                'scheduler_id': self.scheduler_id,
                'start_time': None,
                'end_time': None,
                'num_order': None,
                'num_item': None
            }
        elif table == 'departure':
            self.departure = {
                'table_name': 'departure',
                'depart_time': None,
                'arrive_time': None,
                'num_order': None,
                'num_item': None,
                'total_profit': None
            }
        elif table == 'timestamp_loading':
            self.timestamp_loading = {
                'table_name': 'timestamp_loading',
                'num_item': None,
                'refresh_alert_time': None,
                'connect_time': None,
                'confirm_time': None
            }
        elif table == 'timestamp_unloading':
            self.timestamp_unloading = {
                'table_name': 'timestamp_unloading',
                'num_item': None,
                'refresh_alert_time': None,
                'connect_time': None,
                'confirm_time': None
            }

    def get_exp_id(self):
        cnx = mysql.connector.connect(host=self.host, user=self.user, password=self.passwd, database=self.dbname,
                                      auth_plugin='mysql_native_password')
        cursor = cnx.cursor()
        query = "SELECT MAX(exp_id) FROM experiment;"
        cursor.execute(query)
        return cursor.fetchall()[0][0]

    def insert_log(self, table, reset=True):
        cnx = mysql.connector.connect(host=self.host, user=self.user, password=self.passwd, database=self.dbname,
                                      auth_plugin='mysql_native_password')
        cursor = cnx.cursor()

        tbname = table['table_name']
        col = ''
        val = ''
        for key in list(table.keys())[1:]:
            col = str(col) + str(key) + ', '
            val = str(val) + str(table[key]) + ', '
        col = col[:-2]
        val = val[:-2]

        query = f"INSERT INTO {tbname} ({col}) VALUES ({val});"
        cursor.execute(query)
        cnx.commit()

        if reset:
            self.reset_table(tbname)

    def end_experiment(self, result):
        # list result contains: end_time, total_time, num_peak, auc
        num_item = result[0]
        end_time = result[1]
        total_time = result[2]
        num_peak = result[3]
        auc = result[4]

        cnx = mysql.connector.connect(host=self.host, user=self.user, password=self.passwd, database=self.dbname,
                                      auth_plugin='mysql_native_password')
        cursor = cnx.cursor()

        # # M-mode 기록 추가
        # for record in self.m_mode_list:
        #     imgs = record.popitem()[1]
        #     # imgs 이미지 저장 해야됨!!!!!!!!!!!!!!!!!!!!
        #     self.insert_log(record, reset=False)

        # 마지막으로 experiment 테이블 업데이트
        query = f"UPDATE experiment SET num_item={num_item},end_time='{end_time}', total_time='{total_time}', num_pending_at_peak={num_peak}, AUC={auc}, num_fulfilled = (SELECT COUNT(*) FROM orders WHERE pending=0 and exp_id={self.exp_id}) WHERE exp_id = {self.exp_id};"
        cursor.execute(query)
        cnx.commit()

    def get_last_exp_info(self):
        cnx = mysql.connector.connect(host=self.host, user=self.user, password=self.passwd, database=self.dbname,
                                      auth_plugin='mysql_native_password')
        cursor = cnx.cursor()
        query = f"SELECT max_time, num_order, order_stop_time, scheduler_id FROM experiment WHERE exp_id={self.exp_id};"
        cursor.execute(query)
        info = cursor.fetchall()[0]

        info_dict = {
            'table_name': 'experiment',
            'max_time': info[0],
            'num_order': info[1],
            'order_stop_time': info[2],
            'scheduler_id': info[3]
        }
        return info_dict

    def get_pending_log(self):
        while True:
            cnx = mysql.connector.connect(host=self.host, user=self.user, password=self.passwd, database=self.dbname,
                                          auth_plugin='mysql_native_password')
            cursor = cnx.cursor()
            query = f"SELECT num_pending FROM pending WHERE exp_id={self.exp_id} and time_point=(SELECT MAX(time_point) FROM pending);"
            cursor.execute(query)
            self.num_pending = cursor.fetchall()[0][0]

            time.sleep(5)


class ControlCenter:
    def __init__(self):
        self.logger = Logger()
        with open("banana.txt") as f:
            print('\n', f.read(),'\n')
        input('Please Run The pending_logger.py And Press Enter')
        input(f"Press Enter to Start Experiment #{self.logger.exp_id}")

        self.scheduler_id = mp.Value('i', int(self.logger.experiment['scheduler_id']))

        self.pending_df_colname = ['id', 'address', 'red', 'green', 'blue', 'required_red','required_green','required_blue', 'orderdate']
        self.pending_df = pd.DataFrame(columns=self.pending_df_colname)
        self.pending_df_lock = th.Lock()
        self.schedule_pending_df = mp.Manager().Namespace()
        self.schedule_pending_df.df = pd.DataFrame(columns=self.pending_df_colname)
        self.schedule_pending_df_lock = mp.Lock()

        self.address_dict = {
            101: 1,
            102: 2,
            103: 3,
            203: 4,
            202: 5,
            201: 6
        }

        self.just_get_db_flag = False
        self.just_get_db_flag_lock = th.Lock()

        self.fulfill_order_flag = False
        self.fulfill_order_flag_lock = th.Lock()
        self.update_inventory_flag = False
        self.update_inventory_flag_lock = th.Lock()

        self.new_orderset = {'init': 'init', 'item':  {'r': 0, 'g': 0, 'b': 0}, 'id':99999999, 'path':None, 'dumporders':[]}
        self.new_orderset_lock = th.Lock()
        self.new_orderset_container = mp.Manager().dict({'dict': None})
        self.new_orderset_container_lock = mp.Lock()

        self.new_orderset_ready_flag = False
        self.new_orderset_ready_flag_lock = th.Lock()

        self.update_orderset_flag = mp.Manager().Value('flag', False)
        self.update_orderset_flag_lock = mp.Lock()

        self.operating_orderset = {'item': {'r': 0, 'g': 0, 'b': 0}, 'id':99999999,'path':'0','dumporders': [{'id': 99999, 'partial': [], 'orderid': [999999], 'item': {'r': 0, 'g': 0, 'b': 0}, 'address': 0}]}
        self.orderset_queue = []
        self.QUEUE_SIZE = 2
        self.sended_orders = {} #{112:(3,4,2), ...}
        self.just_sended_orderset = {'item': {'r': 0, 'g': 0, 'b': 0}, 'id':99999999,'path':'0','dumporders': [{'id': 99999, 'partial': [], 'orderid': [999999], 'item': {'r': 0, 'g': 0, 'b': 0}, 'address': 0}]}

        self.send_next_orderset_flag = False
        self.send_next_orderset_flag_lock = th.Lock()

        self.new_orderset_sended_flag = False
        self.new_orderset_sended_flag_lock = th.Lock()

        self.ready_for_scheduling_flag = True
        self.ready_for_scheduling_flag_lock = th.Lock()

        self.scheduling_required_flag = mp.Manager().Value('flag', False)
        self.scheduling_required_flag_lock = mp.Lock()

        self.loading_complete_flag = False
        self.loading_complete_flag_lock = th.Lock()
        self.unloading_complete_flag = False
        self.unloading_complete_flag_lock = th.Lock()

        self.inventory = {'r': 25, 'g': 25, 'b': 25}
        self.inventory_lock = th.Lock()

        self.got_init_robot_status = False
        self.robot_status = mp.Manager().dict(
            {'direction': 1, 'current_address': 0,'operating_order': {'address': 99999, 'id': 99999, 'item': {'r': 0, 'g': 0, 'b': 0}, 'orderid':[99999]},
             'operating_orderset':{'item': {'r': 0, 'g': 0, 'b': 0}, 'id':99999999,'path':'0','dumporders': [{'id': 99999, 'partial': [], 'orderid': [999999], 'item': {'r': 0, 'g': 0, 'b': 0}, 'address': 0}]},
             'current_basket': {'r': 0, 'g': 0, 'b': 0},
             'action': 'loading',
             'orderset_id_list': [],
             'log_time': None,
             'ping': None})

        self.schedule_direction = mp.Value('i', 1)
        self.schedule_inventory_r = mp.Value('i',25)
        self.schedule_inventory_g = mp.Value('i',25)
        self.schedule_inventory_b = mp.Value('i',25)
        self.schedule_inventory_lock = mp.Lock()

        self.loading_complete_id = 88888
        self.unloading_complete_id = 88888

        self.end_sys = False



    def performance_report(self):
        import math
        from numpy import trapz
        import matplotlib.pyplot as plt
        cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=dbname, auth_plugin='mysql_native_password')
        cursor = cnx.cursor()

        query = f"SELECT COUNT(*) FROM orders WHERE exp_id={self.logger.exp_id};"
        cursor.execute(query)
        num_order = cursor.fetchall()[0][0]

        end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = f"SELECT TIMESTAMPDIFF(SECOND, start_time, NOW()) FROM experiment WHERE exp_id = {self.logger.exp_id};"
        cursor.execute(query)
        total_sec = cursor.fetchall()[0][0]
        h = math.trunc(total_sec / 3600)
        m = math.trunc((total_sec % 3600) / 60)
        s = (total_sec % 3600) % 60
        h = ('00' + str(h))[-2:]
        m = ('00' + str(m))[-2:]
        s = ('00' + str(s))[-2:]
        total_time = h+':'+m+':'+s

        query = f"SELECT SUM(total_item) from orders WHERE exp_id={self.logger.exp_id};"
        cursor.execute(query)
        num_item = cursor.fetchall()[0][0]

        query = f"SELECT MAX(num_pending) FROM pending WHERE exp_id={self.logger.exp_id};"
        cursor.execute(query)
        num_peak = cursor.fetchall()[0][0]

        query = f"SELECT num_pending FROM pending WHERE exp_id={self.logger.exp_id};"
        cursor.execute(query)
        num_pending_list = list(pd.DataFrame(cursor.fetchall(), columns=['ls'])['ls'])

        while True:
            try:
                num_pending_list.remove(0)
            except:
                num_pending_list.insert(0, 0)
                num_pending_list.append(0)
                break
        plt.plot(num_pending_list)
        plt.ylabel('# pending orders')

        auc = trapz(num_pending_list, dx=5)

        print(
            f"# of Orders         : {num_order}",
            f"# of Items          : {num_item}",
            f"Total Time          : {total_time}",
            f"# of Orders at Peak : {num_peak}",
            f"AUC                 : {auc}"
            , sep='\n')
        # plt.show()

        return [num_item, end_time, total_time, num_peak, auc], plt

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
        self.pending_df = getdb(self.logger.exp_id, cursor, self.pending_df_colname, self.address_dict)
        self.pending_df_lock.release()
        getdb_time = time.time()

        self.schedule_pending_df.df = self.pending_df
        dbup_time = time.time()

        while not self.end_sys:

            # 4초에 한번 데이터베이스 가져와봄
            if time.time() - getdb_time > 4 or self.just_get_db_flag:
                self.just_get_db_flag_lock.acquire()
                self.just_get_db_flag = False
                self.just_get_db_flag_lock.release()

                cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=dbname, auth_plugin='mysql_native_password')
                cursor = cnx.cursor()

                pending_df = getdb(self.logger.exp_id, cursor, self.pending_df_colname, self.address_dict)
                getdb_time = time.time()

                count = 0
                for id_ in pending_df['id']:
                    if id_ not in list(self.pending_df['id']):
                        count += 1

                if time.time() - dbup_time > 10 or count >= 1:

                    self.pending_df_lock.acquire()
                    self.pending_df = pending_df
                    self.pending_df_lock.release()

                    dbup_time = time.time()

                    self.ready_for_scheduling_flag_lock.acquire()
                    self.ready_for_scheduling_flag = True
                    self.ready_for_scheduling_flag_lock.release()

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

                    self.sended_orders[orderID] = tuple(map(operator.sub, self.sended_orders[orderID], (r, g, b)))

                self.fulfill_order_flag_lock.acquire()
                self.fulfill_order_flag = False
                self.fulfill_order_flag_lock.release()

                self.update_inventory_flag_lock.acquire()
                self.update_inventory_flag = True
                self.update_inventory_flag_lock.release()

            time.sleep(0.1)


    def Manager(self):
        largePrint('Manager() is on')
        did_dummy = False

        while True: #not self.end_sys:

            # orderset_queue에 빠져야할거 뺌
            if len(self.orderset_queue) > 0:
                if self.robot_status['operating_orderset']['id'] == self.orderset_queue[0]['id']:
                    self.operating_orderset = self.orderset_queue.pop(0)

            # 스케줄러에 넘겨줄 정보 준비
            if self.ready_for_scheduling_flag and not self.send_next_orderset_flag:

                self.ready_for_scheduling_flag_lock.acquire()
                self.ready_for_scheduling_flag = False
                self.ready_for_scheduling_flag_lock.release()


                if len(self.orderset_queue) > 0:
                    prev_orderset = self.orderset_queue[-1]
                    self.schedule_direction.value = prev_orderset['last_direction']

                    next_inventory = {'r': 25 - prev_orderset['item']['r'],
                                      'g': 25 - prev_orderset['item']['g'],
                                      'b': 25 - prev_orderset['item']['b']
                                      }

                    self.schedule_inventory_lock.acquire()
                    self.schedule_inventory_r.value = next_inventory['r']
                    self.schedule_inventory_g.value = next_inventory['g']
                    self.schedule_inventory_b.value = next_inventory['b']
                    self.schedule_inventory_lock.release()
                elif self.operating_orderset['id'] != 99999999:
                    prev_orderset = self.operating_orderset
                    self.schedule_direction.value = prev_orderset['last_direction']

                    next_inventory = {'r': 25 - prev_orderset['item']['r'],
                                      'g': 25 - prev_orderset['item']['g'],
                                      'b': 25 - prev_orderset['item']['b']
                                      }

                    self.schedule_inventory_lock.acquire()
                    self.schedule_inventory_r.value = next_inventory['r']
                    self.schedule_inventory_g.value = next_inventory['g']
                    self.schedule_inventory_b.value = next_inventory['b']
                    self.schedule_inventory_lock.release()
                else:
                    self.schedule_direction.value = self.robot_status['direction']
                    next_inventory = {'r': 25,
                                      'g': 25,
                                      'b': 25
                                      }

                    self.schedule_inventory_lock.acquire()
                    self.schedule_inventory_r.value = next_inventory['r']
                    self.schedule_inventory_g.value = next_inventory['g']
                    self.schedule_inventory_b.value = next_inventory['b']
                    self.schedule_inventory_lock.release()


                self.pending_df = self.pending_df.reset_index(drop=True)
                pdf = copy.deepcopy(self.pending_df)
                for id in list(self.sended_orders):
                    if id in list(self.pending_df['id']):
                        idx = self.pending_df[self.pending_df['id'] == id].index.values[0]
                        pdf.loc[idx, 'required_red'] -= self.sended_orders[id][0]
                        pdf.loc[idx, 'required_green'] -= self.sended_orders[id][1]
                        pdf.loc[idx, 'required_blue'] -= self.sended_orders[id][2]

                        if pdf.loc[idx, 'required_red'] < 0 or pdf.loc[idx, 'required_green'] < 0 or\
                                pdf.loc[idx, 'required_blue'] < 0:
                            pdf = pdf.drop(idx)
                    else:
                        self.sended_orders.pop(id)

                self.schedule_pending_df_lock.acquire()
                self.schedule_pending_df.df = copy.deepcopy(pdf)
                self.schedule_pending_df_lock.release()

                self.scheduling_required_flag_lock.acquire()
                self.scheduling_required_flag.value = True
                self.scheduling_required_flag_lock.release()

            # new_orderset 획득
            if self.update_orderset_flag.value:
                largePrint('A New Orderset is Generated!')

                self.new_orderset_ready_flag_lock.acquire()
                self.new_orderset_ready_flag = False
                self.new_orderset_ready_flag_lock.release()

                self.new_orderset_lock.acquire()
                self.new_orderset = self.new_orderset_container['dict']
                self.new_orderset_lock.release()

                self.update_orderset_flag_lock.acquire()
                self.update_orderset_flag.value = False
                self.update_orderset_flag_lock.release()

                self.new_orderset_ready_flag_lock.acquire()
                self.new_orderset_ready_flag = True
                self.new_orderset_ready_flag_lock.release()

            # HQ의 오더셋 큐가 줄어들었을 때 다음 오더셋 전달신호 생성
            if self.got_init_robot_status:
                if len(self.robot_status['orderset_id_list']) < self.QUEUE_SIZE and self.new_orderset_ready_flag and len(self.orderset_queue)<self.QUEUE_SIZE:
                    self.send_next_orderset_flag_lock.acquire()
                    self.send_next_orderset_flag = True
                    self.send_next_orderset_flag_lock.release()

            # send한 오더셋 정보  sended_orders에 추가
            if self.new_orderset_sended_flag:

                item_dict = {}
                for do in self.just_sended_orderset['dumporders']:
                    for po in do['partial']:
                        try:
                            item_dict[po['id']] = tuple(map(operator.add, item_dict[po['id']], (po['item']['r'],po['item']['g'],po['item']['b'])))
                        except:
                            item_dict[po['id']] = (po['item']['r'], po['item']['g'], po['item']['b'])

                for id in list(item_dict):
                    try:
                        self.sended_orders[id] = tuple(map(operator.add, self.sended_orders[id], item_dict[id]))
                    except:
                        self.sended_orders[id] = item_dict[id]

                self.new_orderset_sended_flag_lock.acquire()
                self.new_orderset_sended_flag = False
                self.new_orderset_sended_flag_lock.release()

            # inventory 갱신
            if self.update_inventory_flag:
                if self.loading_complete_flag:
                    item = self.robot_status['operating_orderset']['item']
                    self.inventory_lock.acquire()
                    self.inventory['r'] += self.robot_status['current_basket']['r']
                    self.inventory['g'] += self.robot_status['current_basket']['g']
                    self.inventory['b'] += self.robot_status['current_basket']['b']
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

            time.sleep(0.05)

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
                    if self.send_next_orderset_flag:

                        massage['orderset'] = self.new_orderset

                        self.orderset_queue.append(self.new_orderset)
                        self.just_sended_orderset = self.new_orderset

                        self.send_next_orderset_flag_lock.acquire()
                        self.send_next_orderset_flag = False
                        self.send_next_orderset_flag_lock.release()

                        self.new_orderset_ready_flag_lock.acquire()
                        self.new_orderset_ready_flag = False
                        self.new_orderset_ready_flag_lock.release()

                        self.new_orderset_sended_flag_lock.acquire()
                        self.new_orderset_sended_flag = True
                        self.new_orderset_sended_flag_lock.release()

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
            did_alert_od_id = 8888
            did_alert_os_id = 8888
            while True:
                data = sock.recv(2**15)
                data = pickle.loads(data)

                if 'table_name' in list(data.keys()):
                    self.logger.insert_log(data, reset=False)

                else:
                    self.robot_status = mp.Manager().dict(data)

                    self.got_init_robot_status = True

                    # 로딩워커 UI 갱신 알림 및 로깅
                    if data['operating_orderset']['id'] not in [99999999, did_alert_os_id] and data['current_address'] == 0\
                            and data['operating_order']['id'] != 9999:
                        did_alert_os_id = data['operating_orderset']['id']

                        self.logger.timestamp_loading['refresh_alert_time'] = now()
                        beepsound('loading')

                    # 언로딩워커 UI 갱신 알림 및 로깅
                    if data['operating_order']['id'] not in [9999, did_alert_od_id] and data['current_address'] != 0:
                        did_alert_od_id = data['operating_order']['id']

                        self.logger.timestamp_unloading['refresh_alert_time'] = now()
                        beepsound('unloading')

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

        while True: #not self.end_sys:
            time.sleep(1)

    def UIServer(self):
        largePrint('UIServer() is on')
        from flask import Flask, render_template
        from flask_bootstrap import Bootstrap
        app = Flask(__name__)
        Bootstrap(app)
        app.config['ENV'] = 'development'

        self.loading_check_id = 88888
        self.loading_complete_id = 88888
        self.unloading_complete_id = 88888
        self.unloading_check_id = 88888
        self.departure_info = {
            'order_ids': [],
            'num_item': 0,
            'total_profit': 0
        }



        @app.route('/loading', methods=['GET', 'POST'])
        def loadingworker():
            op_item = self.robot_status['operating_orderset']['item']
            ordersets = [self.operating_orderset] + self.orderset_queue

            if 'confirm' in request.form:
                complete = 1
                if self.robot_status['operating_orderset']['id'] in [self.loading_complete_id, 99999999]:
                    pass
                else:
                    # log 기록
                    self.logger.timestamp_loading['confirm_time'] = now()
                    self.logger.insert_log(self.logger.timestamp_loading)
                    self.logger.departure['depart_time'] = now()

                    self.loading_complete_id = self.robot_status['operating_orderset']['id']

                    self.loading_complete_flag_lock.acquire()
                    self.loading_complete_flag = True
                    self.loading_complete_flag_lock.release()

                    self.update_inventory_flag_lock.acquire()
                    self.update_inventory_flag = True
                    self.update_inventory_flag_lock.release()

            else:
                complete = 0
                self.departure_info['num_item'] += sum_item(op_item)

                if self.robot_status['operating_orderset']['id'] in [self.loading_check_id, 99999999]:
                    pass
                else:
                    self.loading_check_id = self.robot_status['operating_orderset']['id']
                    self.logger.timestamp_loading['connect_time'] = now()
                    self.logger.timestamp_loading['num_item'] = sum_item(op_item)

                    if self.logger.departure['depart_time'] is not None:
                        self.logger.departure['arrive_time'] = now()
                        self.logger.departure['num_order'] = len(set(self.departure_info['order_ids']))
                        self.logger.departure['num_item'] = self.departure_info['num_item']
                        self.logger.departure['total_profit'] = self.departure_info['total_profit']
                        self.logger.insert_log(self.logger.departure)
                        self.departure_info = {
                            'order_ids': [],
                            'num_item': 0,
                            'total_profit': 0
                        }
            n_orders = len(ordersets)
            return render_template('loading.html', orders=ordersets,
                                   n_orders=n_orders, complete=complete)

        @app.route('/unloading', methods=['GET', 'POST'])
        def unloadingworker():
            items = self.robot_status['operating_order']['item']
            order_id = self.robot_status['operating_order']['orderid']

            current_order = self.robot_status['operating_order']
            current_orderset = self.robot_status['operating_orderset']['dumporders']
            upcoming = current_orderset[current_orderset.index(current_order)+1:]
            n_upcoming = len(upcoming)

            if n_upcoming == 0:
                time.sleep(3)
                complete = 1
                if self.robot_status['operating_order']['id'] in [self.unloading_complete_id, 99999]:
                    pass
                else:
                    self.unloading_complete_id = self.robot_status['operating_order']['id']

                    # log 기록
                    self.logger.timestamp_unloading['confirm_time'] = now()
                    self.logger.insert_log(self.logger.timestamp_unloading)
                    self.departure_info['order_ids'] = self.departure_info['order_ids'] + order_id
                    self.departure_info['total_profit'] += self.robot_status['operating_order']['profit']

                    self.unloading_complete_flag_lock.acquire()
                    self.unloading_complete_flag = True
                    self.unloading_complete_flag_lock.release()

                    self.fulfill_order_flag_lock.acquire()
                    self.fulfill_order_flag = True
                    self.fulfill_order_flag_lock.release()
                return render_template('unloading.html',
                                       current_order=current_order,
                                       upcoming=upcoming, n_upcoming=n_upcoming,
                                       complete=complete)

            if 'confirm' in request.form:
                complete = 1
                if self.robot_status['operating_order']['id'] in [self.unloading_complete_id, 99999]:
                    pass
                else:
                    self.unloading_complete_id = self.robot_status['operating_order']['id']

                    # log 기록
                    self.logger.timestamp_unloading['confirm_time'] = now()
                    self.logger.insert_log(self.logger.timestamp_unloading)
                    self.departure_info['order_ids'] = self.departure_info['order_ids'] + order_id
                    self.departure_info['total_profit'] += self.robot_status['operating_order']['profit']

                    self.unloading_complete_flag_lock.acquire()
                    self.unloading_complete_flag = True
                    self.unloading_complete_flag_lock.release()

                    self.fulfill_order_flag_lock.acquire()
                    self.fulfill_order_flag = True
                    self.fulfill_order_flag_lock.release()
            else:
                complete = 0
                if self.robot_status['operating_order']['id'] in [self.unloading_check_id, 99999]:
                    pass
                else:
                    self.unloading_check_id = self.robot_status['operating_order']['id']

                    host = 'localhost'
                    user = 'root'
                    passwd = 'pass'
                    dbname = 'orderdb'
                    cnx = mysql.connector.connect(host=host, user=user, password=passwd,
                                                  database=dbname, auth_plugin='mysql_native_password')
                    cursor = cnx.cursor()

                    r_r = 0
                    r_g = 0
                    r_b = 0
                    for id in order_id:
                        query = f"SELECT required_red, required_green, required_blue FROM orders WHERE id={id} and exp_id={self.logger.exp_id};"
                        cursor.execute(query)
                        r_item = cursor.fetchall()[0]
                        r_r += r_item[0]
                        r_g += r_item[1]
                        r_b += r_item[2]
                    if r_r < items['r'] or r_g < items['g'] or r_b < items['b']:
                        self.unloading_complete_flag = True
                        self.fulfill_order_flag = False
                        self.update_inventory_flag = False
                        return 'Just passing by..'
                    else:
                        self.logger.timestamp_unloading['connect_time'] = now()
                        self.logger.timestamp_unloading['num_item'] = sum_item(items)

            return render_template('unloading.html',
                                   current_order=current_order,
                                   upcoming=upcoming, n_upcoming=n_upcoming,
                                   complete=complete)

        @app.route('/monitor')
        def monitoring():

            return 'This is monitor.'

        app.run(host='0.0.0.0', port=8080)

    def Print_info(self):
        while not self.end_sys:
            robot_status_print = {}
            if not self.got_init_robot_status:
                robot_status_print = {
                    'direction': None,
                    'current_address': None,
                    'action': None,
                    'current_basket': None,
                    'operating_orderset': {'id':None, 'path':None, 'item': None, 'dumporders':[]},
                    'operating_order': {'id':None, 'address':None, 'item': None},
                    'next_orderset': {'id': None, 'path': None, 'item': None},
                    'ping': None,
                    'log_time': None
                }
            else:
                robot_status_print = self.robot_status
            with pd.option_context('display.max_rows', None, 'display.max_columns',
                                   None):
                print(f"## ============================= EXP_ID: {self.logger.exp_id} ============================= ##",
                      f"                          {time.strftime('%c', time.localtime(time.time()))} ",
                      '- - - - - - - - - - - - - - - - System Status - - - - - - - - - - - - - - - -',
                      f'| got_init_robot_status +++++: {self.got_init_robot_status}',
                      f'| ready_for_scheduling_flag -: {self.ready_for_scheduling_flag}',
                      f'| scheduling_required_flag ++: {self.scheduling_required_flag.value}',
                      f'| update_orderset_flag ------: {self.update_orderset_flag.value}',
                      f'| send_next_orderset_flag +++: {self.send_next_orderset_flag}',
                      f'| just_get_db_flag ----------: {self.just_get_db_flag}',
                      f'| new_orderset_ready_flag +++: {self.new_orderset_ready_flag}',
                      f'| send_next_orderset_flag ---: {self.send_next_orderset_flag}',
                      f'| new_orderset_sended_flag ++: {self.new_orderset_sended_flag}',
                      f'| sended_orders -------------: {self.sended_orders}',
                      f'| loading_complete_flag +++++: {self.loading_complete_flag}',
                      f'| unloading_complete_flag ---: {self.unloading_complete_flag}',
                      f'| fulfill_order_flag ++++++++: {self.fulfill_order_flag}',
                      f'| update_inventory_flag -----: {self.update_inventory_flag}',

                      '\n- - - - - - - - - - - - - - - Order Status - - - - - - - - - - - - - - - -',
                      f"| num_pending_order +++++++++: {self.logger.num_pending}",
                      f"| operating_orderset --------: {self.operating_orderset}",
                      f"| orderset_queue ++++++++++++: {[os['id'] for os in self.orderset_queue]}",
                      f'| inventory -----------------: {self.inventory}',

                      f"\n- - - - - - - - - - - - - - - Robot Status - - - - - - - - - - - - - - -",
                      f"                        {robot_status_print['log_time']}",
                      f"| ping ++++++++++++++++++++++: {robot_status_print['ping']}",
                      f"| diredction ----------------: {robot_status_print['direction']}",
                      f"| current_address +++++++++++: {robot_status_print['current_address']}",
                      f"| action --------------------: {robot_status_print['action']}",
                      f"| current_basket ++++++++++++: {robot_status_print['current_basket']}",
                      f"| operating_order",
                      f"|  └ id +++++++++++++++++++++: {robot_status_print['operating_order']['id']}",
                      f"|  └ address ----------------: {robot_status_print['operating_order']['address']}",
                      f"|  └ item +++++++++++++++++++: {robot_status_print['operating_order']['item']}",
                      f"| operating_orderset",
                      f"|  └ id +++++++++++++++++++++: {robot_status_print['operating_orderset']['id']}",
                      f"|  └ path -------------------: {robot_status_print['operating_orderset']['path']}",
                      f"|  └ item +++++++++++++++++++: {robot_status_print['operating_orderset']['item']}",
                      f"|  └ dumporders_id ----------: {[dumporder['id'] for dumporder in robot_status_print['operating_orderset']['dumporders']]}",
                      f"|  └ dumporders_address +++++: {[dumporder['address'] for dumporder in robot_status_print['operating_orderset']['dumporders']]}",
                      f"|  └ dumporders_item --------: {[dumporder['item'] for dumporder in robot_status_print['operating_orderset']['dumporders']]}",
                      f"| orderset_id_list  +++++++++: {robot_status_print['orderset_id_list']}",

                      f'## ====================================================================== ##',

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
        t_PendingLog = th.Thread(target=self.logger.get_pending_log, args=())
        p_Schedule = mp.Process(target=ScheduleByAddress,
                                args=(
                                 self.schedule_pending_df,
                                 self.update_orderset_flag,
                                 self.update_orderset_flag_lock,
                                 self.scheduling_required_flag,
                                 self.scheduling_required_flag_lock,
                                 self.new_orderset_container,
                                 self.new_orderset_container_lock,
                                 self.schedule_direction,
                                 self.schedule_inventory_r,
                                 self.schedule_inventory_g,
                                 self.schedule_inventory_b,
                                 self.scheduler_id,
                                 ))

        t_ControlDB.daemon = True
        t_UIServer.daemon = True
        t_Manager.daemon = True
        t_RobotSocket.daemon = True
        t_PendingLog.daemon = True
        t_PrintLog.daemon = True
        # p_Schedule.daemon = True

        t_ControlDB.start()
        t_UIServer.start()
        t_Manager.start()
        t_RobotSocket.start()
        t_PendingLog.start()
        t_PrintLog.start()
        p_Schedule.start()


        while self.logger.num_pending == 0:
            time.sleep(1)

        time.sleep(60)

        while self.logger.num_pending != 0: # 또는 제한시간 종료조건 추가
            time.sleep(1)

        self.end_sys = True

        # t_ControlDB.join()
        # t_UIServer.join()
        # t_Manager.join()
        # t_RobotSocket.join()
        # t_PendingLog.join()
        # t_PrintLog.join()
        # p_Schedule.terminate()

        with open("finish.txt") as f:
            print('\n', f.read(), '\n')
        largePrint(f'Experiment #{self.logger.exp_id} is finished!!')
        result, plt = self.performance_report()
        self.logger.end_experiment(result)

        plt.show()

if __name__ == "__main__":
    cc = ControlCenter()
    cc.Operate()
