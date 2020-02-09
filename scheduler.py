import copy
from collections import defaultdict
import functools
import time

import pandas as pd

import mysql.connector
from utils import *
from server import *

# mysql connection settings
host = 'localhost'
user = 'root'
passwd = 'pass'
dbname = 'orderdb'
table_name = 'orders'

def get_pending():
    cnx = mysql.connector.connect(host=host, user=user, password=passwd)
    cursor = cnx.cursor()
    cursor.execute(f"USE {dbname};")

    pending_df_colname = ['id', 'red', 'green', 'blue', 'orderdate', 'address']
    query = f"SELECT {', '.join(pending_df_colname)} " + "FROM orders WHERE pending = 1"
    cursor.execute(query)
    pending = cursor.fetchall()
    pdf = pd.DataFrame(pending, columns=pending_df_colname)
    return pdf

def evaluate_order(curr_location, order):
    driving_cost = compute_driving_cost(curr_location, order)
    unloading_cost = compute_unloading_cost(order)
    order['profit'] = order['profit'] / (unloading_cost + driving_cost)
    return order

def compute_driving_cost(curr_location, order):
    destination = order['address']
    try:
        driving_cost = driving_time[curr_location][destination]
    except:
        driving_cost = 1.0
    return driving_cost

def compute_unloading_cost(order):
    num_items = count_items(order)
    if num_items == 0:
        unloading_cost = np.inf
    else:
        unloading_cost = num_items
    return unloading_cost


def group_orders_once(orders, item_limit):
    # Split a sequence of orders to two parts.
    # The first part is a list of orders with num_item < item_limit, 
    # and the second part is rest of the orders.
    for i in range(len(orders)):
        if count_items(orders[:i+1]) > item_limit:
            return orders[:i], orders[i:]
    return orders, []

def group_orders_for_basket(orders, current_basket):
    if min(current_basket.values()) < 0 or max(current_basket.values()) == 0:
        return [], orders
    for i in range(len(orders)):
        if not fit_basket(orders[:i+1], current_basket):
            return orders[:i], orders[i:]
    return orders, []

def filter_empty_orders(orders):
    return list(filter(lambda x: count_items(x) > 0, orders))

def group_orders_n(orders, item_limit):
    # Split a sequence of orders to sub-sequences,
    # so that all sub-sequences meet the item_limit
    scheduled_orders = [orders]
    while count_items(scheduled_orders[-1]) > item_limit:
        split_order = group_orders_once(scheduled_orders[-1], item_limit)
        scheduled_orders.pop()
        scheduled_orders += split_order
    return scheduled_orders

def evaluate_order_set(order_set):
    # TODO: Consider unique number of addresses.
    # Temporary method of evaluation w/ discount factor
    profits = np.array([order['profit'] for order in order_set])
    discount = np.power(DISCOUNT_ORDER, np.arange(len(order_set)))
    return np.dot(profits, discount)

def sort_orders(orders, by, ascending=False):
    # 일단은 greedy 하게 profit 이 큰 순서대로 정렬
    if len(orders):
        orders = sorted(orders, key=lambda x: x[by])
        if not ascending:
            return orders[::-1]
    return orders

def sort_address_by_cnt(address_dict):
    cnt_list = [(add, count_items(orders)) for add, orders in address_dict.items()]
    cnt_list = sorted(cnt_list, key=lambda x: x[-1])[::-1]
    sorted_add, sorted_cnt = tuple(zip(*cnt_list))
    return sorted_add, sorted_cnt

def sort_order_sets(order_group):
    ordersets = sorted(order_group, key=lambda x: -evaluate_order_set(x))
    return ordersets

def diff(order, new_order):
    order['item']['r'] -= new_order['item']['r']
    order['item']['g'] -= new_order['item']['g']
    order['item']['b'] -= new_order['item']['b']
    return order

def partialize_once(order, item_limit):
    num_partial = np.ceil(count_items(order) / item_limit) # number of subsequences to meet item_limit
    new_order = copy.deepcopy(order)
    new_order['item']['r'] = int(order['item']['r'] // num_partial)
    new_order['item']['g'] = int(order['item']['g'] // num_partial)
    new_order['item']['b'] = int(order['item']['b'] // num_partial)
    remaining_order = diff(copy.deepcopy(order), new_order)
    return new_order, remaining_order

def partialize_n(order, item_limit):
    partial_orders = [order]
    while count_items(partial_orders[-1]) > item_limit:
        split_order = partialize_once(partial_orders[-1], item_limit)
        partial_orders.pop()
        partial_orders += split_order
    assert count_items(order) == count_items(partial_orders)
    partial_orders = add_partial_value(partial_orders)
    return partial_orders

def add_partial_value(partial_orders):
    total_item_count = count_items(partial_orders)
    for partial_order in partial_orders:
        partial_order['profit'] *= (count_items(partial_order) / total_item_count)
    return partial_orders

def add_partial_id(orders):
    for i, order in enumerate(orders):
        order['partialid'] = i
    return orders

def split_for_basket(order, current_basket):
    basket_items = np.array([current_basket['r'],
                             current_basket['g'],
                             current_basket['b']])
    order_items = np.array([order['item']['r'],
                            order['item']['g'],
                            order['item']['b']])
    partial_items = np.min([basket_items, order_items], axis=0)
    remaining_items = order_items - partial_items
    partial_order = update_items(order, partial_items)
    remaining_order = update_items(order, remaining_items)
    split_orders = add_partial_value([partial_order, remaining_order])
    return split_orders

def update_items(order, item_array):
    new_order = copy.deepcopy(order)
    new_order['item'] = dict(zip(['r', 'g', 'b'], item_array))
    return new_order

def fit_basket(order, current_basket):
    if min(current_basket.values()) < 0 or max(current_basket.values()) == 0:
        return False
    red = count_color(order, 'r') <= current_basket['r']
    green = count_color(order, 'g') <= current_basket['g']
    blue = count_color(order, 'b') <= current_basket['b']
    return all([red, green, blue])

def partialize_for_loading(orders, item_limit):
    splitted_orders = [[]]
    no_split = list(filter(lambda x: count_items(x) <= item_limit, orders))
    need_split = list(filter(lambda x: count_items(x) > item_limit, orders))
    splitted_orders += [partialize_n(order, item_limit) for order in need_split]
    splitted_orders = functools.reduce(lambda x, y: x + y, splitted_orders)

    all_partials = no_split + splitted_orders

    all_partials = list(filter(lambda x: count_items(x) > 0, all_partials))
    all_partials = add_partial_id(all_partials)
    return all_partials

@timefn
def partialize_for_basket(orders, current_basket):
    no_split = list(filter(lambda x: fit_basket(x, current_basket), orders))
    need_split = list(filter(lambda x: not fit_basket(x, current_basket), orders))

    splitted_orders = [[]]
    splitted_orders += [split_for_basket(order, current_basket) for order in need_split]
    splitted_orders = functools.reduce(lambda x, y: x + y, splitted_orders)

    all_orders = no_split + splitted_orders
    in_basket = list(filter(lambda x: fit_basket(x, current_basket), all_orders))
    not_in_basket = list(filter(lambda x: not fit_basket(x, current_basket), all_orders))
    return in_basket, not_in_basket


def group_same_address(partial_orders):
    partial_by_address = defaultdict(list)
    for order in partial_orders:
        partial_by_address[order['address']].append(order)
    return dict(partial_by_address)


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
             current_basket_r,
             current_basket_g,
             current_basket_b,
             schedule_current_basket_lock,
             operating_dump_id,
             scheduler_id,
             did_scheduling_dumpid):

    print('@@@@@@@@@@@ Schedule() is on@@@@@@@@@@@ ')
    sc_logger = Logger(for_scheduler=True, scheduler_id=scheduler_id.value)
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
        print(rs['operating_order']['id'])
        to_loading_zone = rs['operating_order']['id'] in [9999, 99999]
        at_loading_zone = rs['current_address'] == 0
        current_basket = rs['current_basket']
        print("*" * 60)
        print("BASKET INSIDE SCHEDULER")
        print(current_basket)
        print("*"*60)

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
            # in_basket = sort_orders(in_basket, by='profit', ascending=False)  # optional
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
                dumID += 1

        grouped_dumped_orders = group_orders_n(all_dumps, BASKET_SIZE)

        if to_loading_zone or at_loading_zone:
            grouped_dumped_orders = filter_empty_orders(grouped_dumped_orders)
        else:
            this_dump = []
            group_by_address = group_same_address(this_os).values()
            for i, dumped_order in enumerate(group_by_address, 1):
                this_dump.append(od.makeDumpedOrder(dumpid=dumID, PartialOrderList=dumped_order))
                dumID += 1
            grouped_dumped_orders.insert(0, this_dump)

        nonlocal osID
        # Make order sets
        all_ordersets = [od.makeOrderSet(direction=rs['direction'], current_address=rs['current_address'],
                                         ordersetid=osID, DumpedOrderList=grouped_dumped_orders[0])]
        osID += 1
        for do_group in grouped_dumped_orders[1:]:
            # TODO : improve algorithm estimating profit
            os = od.makeOrderSet(direction=all_ordersets[-1]['last_direction'],
                                 ordersetid=osID, DumpedOrderList=do_group)
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
            schedule_current_basket_lock.acquire()
            schedule_info = {
                'direction': direction.value,
                'current_address': current_address.value,
                'current_basket': {'r': current_basket_r.value, 'g': current_basket_g.value, 'b': current_basket_b.value},
                'operating_order': {'id':operating_dump_id.value}
            }
            schedule_current_basket_lock.release()

            print("schedule_info: ", schedule_info)
            # for i in range(20):
            #     print(f"Current basket in Scheduler : {schedule_info['current_basket']}")
            #     time.sleep(0.1)

            pdf_for_scheduling = pending_df.df.copy()
            pdf_for_scheduling = pdf_for_scheduling.iloc[[x not in operating_order_id.l for x in pdf_for_scheduling['id']]].reset_index()

            sc_logger.scheduling['start_time'] = now()
            if len(pdf_for_scheduling) != 0:
                sc_logger.scheduling['num_order'] = len(pdf_for_scheduling)
            else:
                sc_logger.scheduling['num_order'] = 1

            num_item = 0
            for i in range(len(pdf_for_scheduling)):
                num_item += pdf_for_scheduling[['red', 'green', 'blue']].iloc[i].sum()
            sc_logger.scheduling['num_item'] = num_item

            # print('11111111111111111111111111111111111111111111111111111111111111111')
            new_order_grp = get_optimized_order_grp(existing_order_grp_profit.value, pdf_for_scheduling, schedule_info)
            # print('222222222222222222222222222222222222222222222222222222222222222222222', new_order_grp)
            sc_logger.scheduling['end_time'] = now()
            sc_logger.insert_log(sc_logger.scheduling)

            if new_order_grp is not None:

                did_scheduling_dumpid.value = schedule_info['operating_order']['id']
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

                time.sleep(1)
            else:
                scheduling_required_flag_lock.acquire()
                scheduling_required_flag.value = False
                scheduling_required_flag_lock.release()
        time.sleep(1)


def ScheduleByAddress(existing_order_grp_profit,
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
                     operating_dump_id,
                     scheduler_id):

    print('@@@@@@@@@@@ Schedule() is on@@@@@@@@@@@ ')
    sc_logger = Logger(for_scheduler=True, scheduler_id=scheduler_id.value)
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
        to_loading_zone = rs['operating_order']['id'] in [9999, 99999]
        at_loading_zone = rs['current_address'] == 0
        current_basket = rs['current_basket']

        all_partials = partialize_for_loading(pending_orders, item_limit=PARTIAL_THRESHOLD)
        # Update order profit
        all_partials = [evaluate_order(rs['current_address'], order) for order in all_partials]

        if to_loading_zone or at_loading_zone:
            # Sort orders by profit
            all_partials = filter_empty_orders(all_partials)
            add_dict = group_same_address(all_partials)
            sorted_add = sorted(add_dict.values(), key=lambda x: count_items(x))[::-1]
            os_by_add = [group_orders_n(add, BASKET_SIZE) for add in sorted_add]
            grouped_partial_orders = functools.reduce(lambda x, y: x+y, os_by_add)
        else:
            in_basket, not_in_basket = partialize_for_basket(all_partials, current_basket)
            in_basket = sort_orders(in_basket, by='profit', ascending=False)  # optional
            this_os, remaining_orders = group_orders_for_basket(in_basket, current_basket)
            remaining_orders += not_in_basket

            this_os = filter_empty_orders(this_os)
            remaining_orders = filter_empty_orders(remaining_orders)

            add_dict = group_same_address(remaining_orders)
            sorted_add = sorted(add_dict.values(), key=lambda x: count_items(x))[::-1]
            os_by_add = [group_orders_n(add, BASKET_SIZE) for add in sorted_add]
            grouped_partial_orders = functools.reduce(lambda x, y: x + y, os_by_add)

            # Sort remaining orders by profit
            # remaining_orders = sort_orders(remaining_orders, by='profit', ascending=False)

            # Group partial orders
            # grouped_partial_orders = group_orders_n(remaining_orders, BASKET_SIZE)

        single_add = list(filter(lambda x: count_items(x) > OS_MIN, grouped_partial_orders))
        multiple_add = list(filter(lambda x: count_items(x) <= OS_MIN, grouped_partial_orders))
        
        if len(multiple_add):
            partials = functools.reduce(lambda x, y: x+y, multiple_add)
            multiple_add = group_orders_n(partials, BASKET_SIZE)

        grouped_partial_orders = single_add + multiple_add

        # Make dump orders
        nonlocal dumID
        all_dumps = []
        for po_group in grouped_partial_orders:
            group_by_address = group_same_address(po_group).values()
            for dumped_order in group_by_address:
                all_dumps.append(od.makeDumpedOrder(dumpid=dumID, PartialOrderList=dumped_order))
                dumID += 1

        grouped_dumped_orders = group_orders_n(all_dumps, BASKET_SIZE)

        if to_loading_zone or at_loading_zone:
            grouped_dumped_orders = filter_empty_orders(grouped_dumped_orders)
        else:
            this_dump = []
            group_by_address = group_same_address(this_os).values()
            for i, dumped_order in enumerate(group_by_address, 1):
                this_dump.append(od.makeDumpedOrder(dumpid=dumID, PartialOrderList=dumped_order))
                dumID += 1
            grouped_dumped_orders.insert(0, this_dump)

        nonlocal osID
        # Make order sets
        all_ordersets = [od.makeOrderSet(direction=1,
                                         current_address=rs['current_address'],
                                         ordersetid=osID, DumpedOrderList=grouped_dumped_orders[0])]
        osID += 1
        for do_group in grouped_dumped_orders[1:]:
            # TODO : improve algorithm estimating profit
            os = od.makeOrderSet(direction=all_ordersets[-1]['last_direction'],
                                 ordersetid=osID, DumpedOrderList=do_group)
            all_ordersets.append(os)
            osID += 1

        all_ordersets = all_ordersets[:1] + sort_orders(all_ordersets[1:], by='profit')

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
            print("Operating order ID: ", schedule_info['operating_order']['id'])

            print(f"direction in Scheduler      : {schedule_info['direction']}")
            pdf_for_scheduling = pending_df.df.copy()
            pdf_for_scheduling = pdf_for_scheduling.iloc[[x not in operating_order_id.l for x in pdf_for_scheduling['id']]].reset_index()

            sc_logger.scheduling['start_time'] = now()
            if len(pdf_for_scheduling) != 0:
                sc_logger.scheduling['num_order'] = len(pdf_for_scheduling)
            else:
                sc_logger.scheduling['num_order'] = 1

            num_item = 0
            for i in range(len(pdf_for_scheduling)):
                num_item += pdf_for_scheduling[['red', 'green', 'blue']].iloc[i].sum()
            print('num_item: ', num_item)
            sc_logger.scheduling['num_item'] = num_item

            print('11111111111111111111111111111111111111111111111111111111111111111')
            new_order_grp = get_optimized_order_grp(existing_order_grp_profit.value, pdf_for_scheduling, schedule_info)
            print('222222222222222222222222222222222222222222222222222222222222222222222', new_order_grp)
            sc_logger.scheduling['end_time'] = now()
            sc_logger.insert_log(sc_logger.scheduling)

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

                time.sleep(1)
            else:
                scheduling_required_flag_lock.acquire()
                scheduling_required_flag.value = False
                scheduling_required_flag_lock.release()
        time.sleep(1)


if __name__ == "__main__":
    pending_df = get_pending()
    pending_df['partialid'] = 0
    pending_df['profit'] = 1
    pending_orders = [dict(row) for idx, row in pending_df.iterrows()]

    # Convert to partial orders
    no_split = list(filter(lambda x: x['item'] <= PARTIAL_THRESHOLD, pending_orders))

    need_split = list(filter(lambda x: x['item'] > PARTIAL_THRESHOLD, pending_orders))
    splitted_orders = [partialize_n(order, PARTIAL_THRESHOLD) for order in need_split]
    splitted_orders = functools.reduce(lambda x, y: x+y, splitted_orders)

    # Update order profits
    curr_location = 0
    pending_partial_orders = no_split + splitted_orders
    pending_partial_orders = [evaluate_order(curr_location, order) for order in pending_partial_orders]

    # Sort orders by profit
    orders_sorted = sort_orders(pending_partial_orders)

    # Group orders to order sets
    order_group = group_orders_n(orders_sorted, BASKET_SIZE)

    # Sort order sets by profit
    order_group_sorted = sort_order_sets(order_group)

    # print(len(pending_orders))
    # print(len(pending_partial_orders))

    for order_set in order_group_sorted:
        print(f"Number of orders in order set: {len(order_set)} | Number of items: {count_items(order_set)} | Profit: {evaluate_order_set(order_set):.3f}")
