import numpy as np

ADDRESS = [0, 1, 2, 3, 4, 5, 6]
BASKET_SIZE = 20

PARTIAL_THRESHOLD = 20

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

def count_color(orders, color):
    # Counts the number of items of a specific color
    # in a single order or a sequence of orders
    if type(orders) == dict:
        return orders['item'][color]
    else:
        return sum([count_color(order, color) for order in orders])

def make_path(direction, current_address, order_address):
    address = list(set(order_address))
    if direction > 0:
        front = list(filter(lambda x: x >= current_address, address))
        behind = list(filter(lambda x: x < current_address, address))
        front = sorted(front)
        behind = sorted(behind)
    else:
        front = list(filter(lambda x: x <= current_address, address))
        behind = list(filter(lambda x: x > current_address, address))
        front = sorted(front)[::-1]
        behind = sorted(behind)[::-1]
    rotate = []
    if len(front) * len(behind) > 0:
        if SHORT_DIRECTION[front[-1]][behind[0]] != direction:
            rotate = [ROTATION]
    path = front + rotate + behind
    returning_path = make_shorter_path(path[-1], 0, direction)
    path = path[:-1] + returning_path
    return stringify_path(path)

def stringify_path(address_seq):
    path_string = ''.join(list(map(str, address_seq)))
    return path_string

def make_shorter_path(start, end, direction):
    if SHORT_DIRECTION[start][end] == direction:
        return [start, end]
    else:
        return [start, ROTATION, end]