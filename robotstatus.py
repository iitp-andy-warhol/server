import time


def makeRobotStatus(direction, current_address, action, current_basket, operating_orderset, operating_order,orderset_id_list, ping):
    l = [6, 0, 1, 2, 3, 4, 5, 6, 0]
    dic ={
        'direction' : direction,
        'current_address' : current_address,
        'action' : action,
        'current_basket' : current_basket,
        'operating_orderset' : operating_orderset,
        'operating_order' : operating_order,
        'orderset_id_list': orderset_id_list,
        'log_time' : time.strftime('%c', time.localtime(time.time())),
        'ping' : ping
    }
    return dic

