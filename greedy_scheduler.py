import copy
from collections import defaultdict
import functools
import time

import numpy as np
import pandas as pd

import mysql.connector
from utils import *

# mysql connection settings
host = 'localhost'
user = 'root'
passwd = 'pass'
dbname = 'orderdb'
table_name = 'orders'

# 나중에는 실험에서 만든 결과를 외부 파일로부터 읽어오면 됨
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
    driving_cost = driving_time[curr_location][destination]
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
    i = 0
    order_group = []
    while count_items(order_group) <= item_limit:
        i += 1
        order_group = orders[:i]
    return orders[:i-1], orders[i-1:]

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
    orders = sorted(orders, key=lambda x: x[by])
    if not ascending:
        return orders[::-1]
    return orders

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
    partial_orders = add_partial_info(partial_orders)
    return partial_orders

def add_partial_info(partial_orders):
    for i, partial_order in enumerate(partial_orders, 1):
        partial_order['partialid'] = i
        partial_order['profit'] /= len(partial_orders)
    return partial_orders

def partialize(orders, item_limit, current_basket=None):
    # Loading zone / unloading zone 여부를 알 수 있어야
    no_split = list(filter(lambda x: count_items(x) <= item_limit, orders))
    need_split = list(filter(lambda x: count_items(x) > item_limit, orders))
    if len(need_split):
        splitted_orders = [partialize_n(order, PARTIAL_THRESHOLD) for order in need_split]
        splitted_orders = functools.reduce(lambda x, y: x + y, splitted_orders)
    else:
        splitted_orders = []
    all_partials = no_split + splitted_orders
    return all_partials

def group_same_address(partial_orders):
    partial_by_address = defaultdict(list)
    for order in partial_orders:
        partial_by_address[order['address']].append(order)
    return dict(partial_by_address)



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
