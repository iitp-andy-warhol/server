def makeOrder(order):
    """
    An order.
    :param pd.DataFrame order: A row of pd.DataFrame like df.iloc[0]
    """
    dic = {
        'id': order['id'].values[0],
        'address': order['address'].values[0],
        'item': {'r': order['red'].values[0], 'g': order['green'].values[0], 'b': order['blue'].values[0]},
        'orderdate': order['orderdate'].values[0]
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
        'id': partialid,
        'orderid': Order['id'],
        'address': Order['address'],
        'item': {'r': r, 'g': g, 'b': b},
        'orderdate': Order['orderdate']
    }
    return dic


def makeDumpedOrder(dumpid=9999, PartialOrderList=[], dummy=False):
    """
    A set of ‘PartialOrder’s processed at one time by the robot delivering to one address.
    :param int dumpid: have to think about how to generate it
    :param list PartialOrderList: an list of PartialOrder dictionary
    :param dummy: True if dummy DumpedOrder
    """
    r = g = b = 0
    orderlist=[]
    if not dummy:
        for po in PartialOrderList:
            r += po['item']['r']
            g += po['item']['g']
            b += po['item']['b']
            orderlist.append(po['orderid'])

        address = PartialOrderList[0]['address']
    else:
        address = 0
        # if dummy address = 0


    dic = {
        'id': dumpid,
        'partial': PartialOrderList,
        'orderid': orderlist,
        'item': {'r': r, 'g': g, 'b': b},
        'address': address
    }

    return dic


def makeOrderSet(ordersetid=0, DumpedOrderList=None, path=None, profit=0):
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
    else:
        lst = DumpedOrderList
        for do in lst:
            r += do['item']['r']
            g += do['item']['g']
            b += do['item']['b']

    dummy = makeDumpedOrder(dummy=True)
    lst.append(dummy)
    dic = {
        'id': ordersetid,
        'dumporders': lst,
        'path': path + '0',
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