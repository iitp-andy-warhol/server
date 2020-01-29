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

    pending_df_colname = ['id', 'red', 'blue', 'green', 'orderdate', 'address']
    query = f"SELECT {', '.join(pending_df_colname)} " + "FROM orders WHERE pending = 1"
    cursor.execute(query)
    pending = cursor.fetchall()
    pdf = pd.DataFrame(pending, columns=pending_df_colname)
    pdf['item'] = pdf['red'] + pdf['green'] + pdf['blue']
    # pdf = filter_orders(pdf)
    return pdf

def filter_orders(pdf, max=20):
    if max == None:
        return pdf
    pdf = pdf[pdf['item'] <= max]
    return pdf

def evaluate_order(curr_location, order):
    driving_cost = compute_driving_cost(curr_location, order)
    unloading_cost = compute_unloading_cost(order)
    order['value'] = order['value'] / (unloading_cost + driving_cost)
    return order

def compute_driving_cost(curr_location, order):
    destination = order['address']
    driving_cost = driving_time[curr_location][destination]
    return driving_cost

def compute_unloading_cost(order):
    num_items = order['item']
    if num_items == 0:
        unloading_cost = np.inf
    else:
        unloading_cost = num_items
    return unloading_cost

def sort_orders(orders):
    # 일단은 greedy 하게 value 가 큰 순서대로 정렬
    orders = sorted(orders, key=lambda x: -x['value'])
    return orders

def count_items(orders):
    # Counts the number of items in a single order 
    # or the total number of items in a list of orders
    if type(orders) == dict:
        return orders['item']        
    else:
        return sum([order['item'] for order in orders])

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
    values = np.array([order['value'] for order in order_set])
    discount = np.power(DISCOUNT_ORDER, np.arange(len(order_set)))
    return np.dot(values, discount)

def diff(order, new_order):
    order['red'] -= new_order['red']
    order['green'] -= new_order['green']
    order['blue'] -= new_order['blue']
    order['item'] -= new_order['item']
    return order

def split_order_once(order, item_limit):
    num_partial = np.ceil(order['item'] / item_limit)
    new_order = order.copy()
    new_order['red'] = int(order['red'] // num_partial)
    new_order['green'] = int(order['green'] // num_partial)
    new_order['blue'] = int(order['blue'] // num_partial)
    new_order['item'] = new_order['red'] + new_order['blue'] + new_order['green']
    remaining_order = diff(order.copy(), new_order)
    return (new_order, remaining_order)

def split_order_n(order, item_limit):
    partial_orders = [order]
    while count_items(partial_orders[-1]) > item_limit:
        split_order = split_order_once(partial_orders[-1], item_limit)
        partial_orders.pop()
        partial_orders += split_order
    assert order['item'] == count_items(partial_orders)
    partial_orders = add_partial_info(partial_orders)
    return partial_orders

def add_partial_info(partial_orders):
    for i, partial_order in enumerate(partial_orders, 1):
        partial_order['partialid'] = i
        partial_order['value'] /= len(partial_orders)
    return partial_orders

if __name__ == "__main__":
    pending_df = get_pending()
    pending_df['partialid'] = 0
    pending_df['value'] = 1
    pending_orders = [dict(row) for idx, row in pending_df.iterrows()]   

    # Convert to partial orders
    no_split = list(filter(lambda x: x['item'] <= PARTIAL_THRESHOLD, pending_orders))

    need_split = list(filter(lambda x: x['item'] > PARTIAL_THRESHOLD, pending_orders))
    splitted_orders = [split_order_n(order, PARTIAL_THRESHOLD) for order in need_split]
    splitted_orders = functools.reduce(lambda x, y: x+y, splitted_orders)

    # Update order values
    curr_location = 0
    pending_orders = no_split + splitted_orders
    pending_orders = [evaluate_order(curr_location, order) for order in pending_orders]

    # Sort by value
    orders_sorted = sort_orders(pending_orders)

    # Group orders to order sets
    order_group = group_orders_n(orders_sorted, BASKET_SIZE)

    for order_set in order_group:
        print(f"Number of orders in order set: {len(order_set)} | Number of items: {count_items(order_set)} | Value: {evaluate_order_set(order_set):.3f}")
