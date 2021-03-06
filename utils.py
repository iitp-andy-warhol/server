import numpy as np
import time
from datetime import datetime
import beepy
import simpleaudio as sa



ADDRESS = [0, 1, 2, 3, 4, 5, 6]
BASKET_SIZE = 25
OS_MIN = 20

PARTIAL_THRESHOLD = 5

DISCOUNT_ORDER = 0.9
DISCOUNT_ORDER_SET = 0.9

ROTATION = 9
SHORT_DIRECTION = np.array([[-1,  1,  1,  1, -1, -1, -1],
                           [-1, -1,  1,  1,  1, -1, -1],
                           [-1, -1, -1,  1,  1,  1, -1],
                           [-1, -1, -1, -1,  1,  1,  1],
                           [ 1, -1, -1, -1, -1,  1,  1],
                           [ 1,  1, -1, -1, -1, -1,  1],
                           [ 1,  1,  1, -1, -1, -1, -1]])

def driving_time_generator(start_address, end_address):
    # Randomly generates driving time between locations.
    diff = np.abs(end_address - start_address)
    dist = min(diff, 7 - diff)
    dist = dist % 4
    return np.abs(np.random.randn()) * 0.1 + dist

def build_driving_time_mat():
    mat = np.zeros((len(ADDRESS), len(ADDRESS)))
    for start_add in ADDRESS:
        mat[start_add] = np.array([driving_time_generator(start_add, end_add) for end_add in ADDRESS])
    return mat

def count_items(orders):
    # Counts the number of items in a single order
    # or the total number of items in a sequence of orders
    if type(orders) == dict:
        return sum(orders['item'].values())
    else:
        return sum([count_items(order) for order in orders])

def get_profit(orders):
    # Counts the number of items in a single order
    # or the total number of items in a sequence of orders
    if type(orders) == dict:
        return orders['profit']
    else:
        # # addresses
        n_address = len(set([order['address'] for order in orders]))
        return sum([get_profit(order) for order in orders]) / max(n_address, 1)

def evaluate_order_set(order_set):
    # TODO: Consider unique number of addresses.
    # Temporary method of evaluation w/ discount factor
    profits = np.array([order['profit'] for order in order_set])
    discount = np.power(DISCOUNT_ORDER, np.arange(len(order_set)))
    return np.dot(profits, discount)

def count_color(orders, color):
    # Counts the number of items of a specific color
    # in a single order or a sequence of orders
    if type(orders) == dict:
        return orders['item'][color]
    else:
        return sum([count_color(order, color) for order in orders])


def make_path(direction, current_address, order_address):
    address = list(set(order_address))
    if direction == 1:
        front = list(filter(lambda x: x >= current_address, address))
        behind = list(filter(lambda x: x < current_address, address))
        front = sorted(front)
        behind = sorted(behind)
    else:
        front = list(filter(lambda x: x <= current_address, address))
        behind = list(filter(lambda x: x > current_address, address))
        front = sorted(front)[::-1]
        behind = sorted(behind)
    addresses = [current_address] + front + behind + [0]
    final_path = []
    for i in range(len(front+behind)+1):
        start = addresses[i]
        end = addresses[i+1]
        path, direction = make_short_path(start, end, direction)
        final_path.extend(path[1:])
    return final_path, direction

def stringify_path(address_seq):
    path_string = ''.join(list(map(str, address_seq)))
    return path_string

def make_short_path(start, end, direction):
    if start == end:
        return [start, end], direction
    try:
        if SHORT_DIRECTION[start][end] == direction:
            return [start, end], direction
        else:
            return [start, ROTATION, end], -direction
    except IndexError:
        return make_short_path(0, end, direction)

def timefn(fn):
    # Prints the time taken to run the inner function.
    def wrap(*args, **kwargs):
        t1 = time.time()
        result = fn(*args, **kwargs)
        t2 = time.time()
        print(f"@timefn: {fn.__name__} took {t2-t1} seconds")
        return result
    return wrap

def now():
    """
    Get datetime as string like '0000-00-00 00:00:00'
    :return: string
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"'{now}'"

def sum_item(items):
    """
    Get the sum of the total items
    :param dict items: item dict
    :return: int
    """

    return items['r']+items['g']+items['b']

def beepsound(type):
    """
    워커 알림음 함수
    :param string type: 'loading' or 'unloading'
    :return:
    """
    if type == 'loading':
        print(beepy.beep(sound=5))

    elif type == 'unloading':
        wave_obj = sa.WaveObject.from_wave_file('alarm.wav')
        play_obj = wave_obj.play()
        play_obj.wait_done()  # Wait until sound has finished playing

if __name__ == "__main__":
    p = make_path(current_address=5, order_address=[], direction=-1)
    print(p)