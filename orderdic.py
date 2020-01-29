from utils import *

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
    else:
        address = 0


    dic = {
        'id': dumpid,
        'partial': PartialOrderList,
        'orderid': orderlist,
        'item': {'r': r, 'g': g, 'b': b},
        'address': address
    }

    return dic


def makeOrderSet(robot_status, ordersetid=0, DumpedOrderList=None, profit=0):
    """
    A set of 'DumpedOrder's processed until the robot leaves LZ and then returns to LZ for loading
    :param int ordersetid:
    :param list DumpedOrderList: A list of 'DumpedOrder's in order of optimal path.
    :param str path:
    :param int profit:
    """

    r = g = b = 0
    if DumpedOrderList is None:
        lst = []
        path = None
    else:
        lst = DumpedOrderList
        r = count_color(DumpedOrderList, 'r')
        g = count_color(DumpedOrderList, 'g')
        b = count_color(DumpedOrderList, 'b')
        address_set = set([do['address'] for do in DumpedOrderList])
        path = make_path(direction=robot_status['direction'],
                         current_address=robot_status['current_address'],
                         order_address=address_set)
    dummy = makeDumpedOrder(dummy=True)
    lst.append(dummy)
    dic = {
        'id': ordersetid,
        'dumporders': lst,
        'path': path,
        'profit': profit,
        'item': {'r': r, 'g': g, 'b': b}
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