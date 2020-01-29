import numpy as np

ADDRESS = [0, 1, 2, 3, 4, 5, 6]
BASKET_SIZE = 20

PARTIAL_THRESHOLD = 20

DISCOUNT_ORDER = 0.9
DISCOUNT_ORDER_SET = 0.9

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

