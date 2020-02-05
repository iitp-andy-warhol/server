from utils import *
from collections import defaultdict

def makeOrder(order):
    """
    An order.
    :param pd.DataFrame order: A row of pd.DataFrame like df.iloc[0]
    """
    dic = {
        'id': order['id'],
        'partialid': 0,
        'address': order['address'],
        'item': {'r': order['red'], 'g': order['green'], 'b': order['blue']},
        'orderdate': order['orderdate'],
        'profit': order['profit']
    }
    return dic


def makePartialOrder(Order, partialid, r, g, b):
    """
    An order that may have been split or not.
    :param Order Order:
    :param int partialid: just for loop index that used for making partial order
    :param int r: partial r
    :param int g: partial g
    :param int b: partial b
    """
    dic = {
        'id': Order['id'],
        'partialid': partialid,
        'address': Order['address'],
        'item': {'r': r, 'g': g, 'b': b},
        'orderdate': Order['orderdate']
    }
    return dic

def makeDumpedOrder(dumpid=9999, PartialOrderList=[], dummy=False):
    """
    A set of ‘PartialOrder’s processed at one time by the robot delivering to one address.
    :param int dumpid: have to think about how to generate it
    :param list PartialOrderList: a list of PartialOrder dictionary
    :param dummy: True if dummy DumpedOrder
    """
    r = g = b = 0
    orderlist=[]
    if not dummy:
        r = count_color(PartialOrderList, 'r')
        g = count_color(PartialOrderList, 'g')
        b = count_color(PartialOrderList, 'b')
        orderlist = [po['id'] for po in PartialOrderList]
        address = PartialOrderList[0]['address']
        profit = sum([po['profit'] for po in PartialOrderList])
    else:
        address = 0
        profit = 0


    dic = {
        'id': dumpid,
        'partial': PartialOrderList,
        'orderid': orderlist,
        'item': {'r': r, 'g': g, 'b': b},
        'address': address,
        'profit': profit
    }

    return dic


def makeOrderSet(direction, current_address=0, ordersetid=0, DumpedOrderList=None, profit=0):
    """
    A set of 'DumpedOrder's processed until the robot leaves LZ and then returns to LZ for loading
    :param int ordersetid:
    :param list DumpedOrderList: A list of 'DumpedOrder's in order of optimal path.
    :param str path:
    :param int profit:
    """
    r = g = b = 0
    if DumpedOrderList == []:
        lst = []
        path, direction = make_short_path(current_address, 0, direction)
        path = path[1:]
    else:
        lst = DumpedOrderList
        r = count_color(DumpedOrderList, 'r')
        g = count_color(DumpedOrderList, 'g')
        b = count_color(DumpedOrderList, 'b')
        address_set = set([do['address'] for do in DumpedOrderList])
        address_set = list([add for add in address_set if add in set(range(1, 7))])
        path, direction = make_path(direction=direction,
                                    current_address=current_address,
                                    order_address=address_set)
        do_dict = {dumped_order['address']: dumped_order for dumped_order in lst}
        lst = [do_dict[address] for address in path if address in set(range(1, 7))]
        profit = sum([do['profit'] for do in lst])
    dummy = makeDumpedOrder(dummy=True)
    lst.append(dummy)
    path_string = stringify_path(path)
    dic = {
        'id': ordersetid,
        'dumporders': lst,
        'path': path_string,
        'profit': profit,
        'item': {'r': r, 'g': g, 'b': b},
        'last_direction': direction
    }
    return dic


def makeOrderGroup(ordergroupID=0, OrderSetList=None):
    """
    Set of ‘OrderSet’s that will process all pending orders in the DB
    :param list OrderSetList:A list of ‘OrderSet’s in order of OrderSet.profit. The OrderSet with the higher profit is processed first.
    """
    if OrderSetList is None:
        lst = []
        profit = 0
    else:
        lst = OrderSetList
        profit = 0
        for os in OrderSetList:
            profit += os['profit']
    dic = {
        'id': ordergroupID,
        'ordersets': lst,
        'profit': profit
    }
    return dic