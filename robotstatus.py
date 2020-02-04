import time


def makeRobotStatus(direction, current_address, action, current_basket, operating_orderset, operating_order,next_orderset, ping):
    l = [6, 0, 1, 2, 3, 4, 5, 6, 0]
    dic ={
        'direction' : direction,
        'current_address' : current_address,
        #'next_address' : l[current_address+1+direction],
        'action' : action,
        'current_basket' : current_basket,
        'operating_orderset' : operating_orderset,
        'operating_order' : operating_order,
        'next_orderset': next_orderset,
        'log_time' : time.strftime('%c', time.localtime(time.time())),
        'ping' : ping
    }
    return dic

