import multiprocessing as mp
import threading as th
import mysql.connector
import pandas as pd
import time
import orderdic as od
from socket import *
import pickle
import os


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
             next_orderset_idx_lock):
    print('@@@@@@@@@@@ Schedule() is on@@@@@@@@@@@ ')

    def get_optimized_order_grp(existing_order_grp_profit, pdf, threshold=0):
        def split_partial(order, n=1):
            """일단 속성으로 아웃풋 형식만 맞춰서 만듬. rgb 쪼개는거 해야됨."""
            partialIDs = list(range(n))
            partial_list_per_order = []
            for parID in partialIDs:
                r = order['item']['r']
                g = order['item']['g']
                b = order['item']['b']
                partial_list_per_order.append(od.makePartialOrder(order, str(order['id'])+'-'+str(parID), r,g,b))
            return partial_list_per_order

        # 일단은 각 출발에 주문 1개씩 선입선출로 해놨음.
        sorted_df = pdf.sort_values(by='orderdate')
        """
        OrderSet.path 에는 해당 오더셋을 수행하는 최적 경로를 넣어놓아야함
        """
        all_partials = []
        for i in range(len(sorted_df)):
            order = od.makeOrder(sorted_df.iloc[i:i + 1])
            partials = split_partial(order, n=1)
            for po in partials:
                all_partials.append(po)

        all_dumps = []
        for dumID, po in enumerate(all_partials):
            do = od.makeDumpedOrder(dumID, [po])
            all_dumps.append(do)

        all_ordersets = []
        for osID, do in enumerate(all_dumps):
            path = (f"{do['address']}")
            os = od.makeOrderSet(osID, [do], path=path, profit = 1)
            all_ordersets.append(os)

        new_order_grp = od.makeOrderGroup(OrderSetList=all_ordersets)

        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', new_order_grp['profit'])
        print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!', existing_order_grp_profit)
        if new_order_grp['profit'] - existing_order_grp_profit > threshold:
            return new_order_grp
        else:
            return None

    while True:
        if scheduling_required_flag.value:
            print('@@@@@@@@@@@ Making new schedule @@@@@@@@@@@')
            print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!스케줄함수내부',existing_order_grp_profit.value)

            new_order_grp = get_optimized_order_grp(existing_order_grp_profit.value, pending_df.df)
            if new_order_grp is not None:
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

class ControlCenter:
    def __init__(self):
        largePrint('ControlCenter is initialized')
        self.pending_pdf_colname = ['id', 'address', 'red', 'green', 'blue', 'required_red','required_green','required_blue', 'orderdate']
        self.pending_df = mp.Manager().Namespace()
        self.pending_df.df = pd.DataFrame(columns=self.pending_pdf_colname)
        self.pending_df_lock = mp.Lock()

        self.fulfill_order_flag = False
        self.fulfill_order_flag_lock = th.Lock()
        self.update_inventory_flag = False
        self.update_inventory_flag_lock = th.Lock()

        self.order_grp = od.makeOrderGroup()
        self.order_grp_lock = th.Lock()

        self.existing_order_grp_profit = mp.Value('i',-1)
        self.existing_order_grp_profit_lock = mp.Lock()

        self.order_grp_new = mp.Manager().dict({'dict': None})

        self.order_grp_new_lock = mp.Lock()
        self.update_order_grp_flag = mp.Manager().Value('flag', False)
        self.update_order_grp_flag_lock = mp.Lock()

        self.next_orderset = {'init': 'init', 'item': {'r':99,'g':99,'b':99}}
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
            {'operating_order': {'address': 99999, 'id': 99999, 'item': {'r':99,'g':99,'b':99}}, 'orderid':999999})
        self.robot_status_log = []

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
            if time.time() - getdb_time > 5:
                cnx = mysql.connector.connect(host=host, user=user, password=passwd)
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
                                self.scheduling_required_flag.value = True
                                self.scheduling_required_flag_lock.release()
                                break

            if self.fulfill_order_flag:
                cnx = mysql.connector.connect(host=host, user=user, password=passwd)
                cursor = cnx.cursor()
                cursor.execute(f"USE {dbname};")

                for po in self.robot_status['operating_order']['partial']:
                    orderID = po['orderid']
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

                    print(query,'*************************************************************')
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
            if self.update_order_grp_flag.value:
                largePrint('Schedule is updated!!')
                self.order_grp_lock.acquire()
                self.order_grp = self.order_grp_new['dict']
                self.order_grp_lock.release()

                self.existing_order_grp_profit_lock.acquire()
                self.existing_order_grp_profit.value = self.order_grp['profit']
                self.existing_order_grp_profit_lock.release()

                self.update_order_grp_flag_lock.acquire()
                self.update_order_grp_flag.value = False
                self.update_order_grp_flag_lock.release()
# causal learning
            # Get next orderset from order group
            if self.got_init_robot_status:
                if not self.got_init_orderset:
                    # 제일 처음 오더셋 받기 위함
                    if self.robot_status['operating_order']['address'] == 0 and self.existing_order_grp_profit.value > 2:
                        self.next_orderset_idx_lock.acquire()
                        self.next_orderset_idx.value += 1
                        self.next_orderset_idx_lock.release()

                        self.next_orderset = self.order_grp['ordersets'][self.next_orderset_idx.value]

                        self.send_next_orderset_flag_lock.acquire()
                        self.send_next_orderset_flag = True
                        self.send_next_orderset_flag_lock.release()

                        self.got_init_orderset = True

                        self.schedule_changed_flag_lock.acquire()
                        self.schedule_changed_flag.value = False
                        self.schedule_changed_flag_lock.release()

                if self.robot_status['operating_order']['id'] == 9999 and self.robot_status['current_address'] == 0\
                        and self.got_init_orderset:
                    if not did_dummy:
                        did_dummy = True

                        self.next_orderset_idx_lock.acquire()
                        self.next_orderset_idx.value += 1
                        self.next_orderset_idx_lock.release()

                        print(self.next_orderset_idx.value)
                        try:
                            self.next_orderset = self.order_grp['ordersets'][self.next_orderset_idx.value]
                            self.send_next_orderset_flag_lock.acquire()
                            self.send_next_orderset_flag = True
                            self.send_next_orderset_flag_lock.release()
                        except:
                            self.next_orderset_idx_lock.acquire()
                            self.next_orderset_idx.value = -1
                            self.next_orderset_idx_lock.release()

                            self.got_init_orderset = False


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

            # Update inventory
            if self.update_inventory_flag:
                if self.loading_complete_flag:
                    item = self.next_orderset['item']
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
                    if self.send_next_orderset_flag \
                            and self.robot_status['current_address'] == self.robot_status['operating_order']['address']:
                        massage['orderset'] = self.next_orderset

                        # 로봇이 잘 받았다는 응답을 확인하고 보내는걸 멈추게 하면 좋을 수도 있음.
                        # self.robot_status['operating_orderset'] 이 self.next_orderset이랑 같으면 send_next_orderset_flag를 False로.
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

                    sock.send(pickle.dumps(massage, protocol=pickle.HIGHEST_PROTOCOL))
                time.sleep(0.5)

        def get_robot_status(sock):
            while True:
                data = sock.recv(32768) #2^13 bit
                data = pickle.loads(data)

                # self.robot_status_log.append(self.robot_status)
                self.robot_status = mp.Manager().dict(data)

                self.got_init_robot_status = True

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
            items = self.next_orderset['item']

            return render_template('loading.html', items=items)

        @app.route('/loading-success')
        def change_flags_loading():
            # 이거 접속되는 시점 기록되야됨.
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

            self.unloading_complete_flag_lock.acquire()
            self.unloading_complete_flag = True
            self.unloading_complete_flag_lock.release()

            self.fulfill_order_flag_lock.acquire()
            self.fulfill_order_flag = True
            self.fulfill_order_flag_lock.release()

            return render_template('unloading_success.html', order_id=order_id, address=address)

        @app.route('/monitor')
        def monitoring():
            order_grp = self.order_grp
            return 'This is monitor.'

        app.run(host='0.0.0.0', port=8080)

    def Print_info(self):
        while True:
            robot_status_print = {}
            if self.robot_status['operating_order']['address'] == 99999:
                robot_status_print = {
                    'direction': None,
                    'current_address': None,
                    # 'next_address': None,
                    'action': None,
                    'current_basket': None,
                    'operating_orderset': None,
                    'operating_order': None,
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
                                ))

        t_ControlDB.daemon = True
        t_UIServer.daemon = True
        t_Manager.daemon = True
        t_RobotSocket.daemon = True
        t_PrintLog.daemon = True

        t_ControlDB.start()
        t_UIServer.start()
        t_Manager.start()
        t_RobotSocket.start()
        t_PrintLog.start()
        p_Schedule.start()


        input()
        p_Schedule.terminate()
        os._exit(0)


if __name__ == "__main__":
    cc = ControlCenter()
    cc.Operate()
