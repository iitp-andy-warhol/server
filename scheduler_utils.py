import copy
from collections import defaultdict
import functools

import pandas as pd

import mysql.connector
from utils import *

# mysql connection settings

host = 'localhost'
user = 'root'
passwd = 'pass'
dbname = 'orderdb'
table_name = 'orders'

driving_time = build_driving_time_mat()

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
    no_split = list(filter(lambda x: count_items(x) <= item_limit, orders))
    need_split = list(filter(lambda x: count_items(x) > item_limit, orders))
    splitted_orders = [partialize_n(order, item_limit) for order in need_split]
    splitted_orders = concat_orders(splitted_orders)

    all_partials = no_split + splitted_orders

    all_partials = list(filter(lambda x: count_items(x) > 0, all_partials))
    all_partials = add_partial_id(all_partials)
    return all_partials

@timefn
def partialize_by_rgb(orders, rgb_constraint):
    no_split = list(filter(lambda x: fit_basket(x, rgb_constraint), orders))
    need_split = list(filter(lambda x: not fit_basket(x, rgb_constraint), orders))

    splitted_orders = [split_for_basket(order, rgb_constraint) for order in need_split]
    splitted_orders = concat_orders(splitted_orders)

    all_orders = no_split + splitted_orders
    all_orders = filter_empty_orders(all_orders)
    in_ = list(filter(lambda x: fit_basket(x, rgb_constraint), all_orders))
    not_in_ = list(filter(lambda x: not fit_basket(x, rgb_constraint), all_orders))
    return in_, not_in_


def group_same_address(partial_orders):
    partial_by_address = defaultdict(list)
    for order in partial_orders:
        partial_by_address[order['address']].append(order)
    return dict(partial_by_address)


def concat_orders(orders_list):
    if len(orders_list):
        return functools.reduce(lambda x, y: x + y, orders_list)
    else:
        return []