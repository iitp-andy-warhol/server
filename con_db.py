import mysql.connector
import sys
import pandas as pd


action = sys.argv[1]

try:
    orderid = sys.argv[2]
except:
    orderid = None

def db(action, orderid):
    cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=schema)
    cursor = cnx.cursor()

    if action in ['d','ㅇ']:
        if orderid is None:
            query = 'delete from orders where id != 000;'
            orderid = 'All'
        else:
            query = f'delete from orders where id ={orderid};'
        cursor.execute(query)
        cnx.commit()
        print(f'id = {orderid} row(s) have been deleted.')

    elif action in ['s', 'ㄴ']:
        if orderid is None:
            query = f"SELECT {', '.join(colname)} " + "FROM orders;"
        else:
            query = f"SELECT {', '.join(colname)} " + f"FROM orders WHERE id={orderid};"

        cursor.execute(query)
        pending = cursor.fetchall()
        pending = pd.DataFrame(pending, columns=colname)
        print(pending)

    elif action in ['sa', 'ㄴㅁ']:

        if orderid is None:
            query = f"SELECT * FROM orders;"
        else:
            query = f"SELECT * FROM orders WHERE id={orderid};"

        cursor.execute(query)
        pending = cursor.fetchall()
        pending = pd.DataFrame(pending, columns=fulcolname)
        print(pending)

if __name__ == '__main__':
    host = 'localhost'
    user = 'root'
    passwd = 'pass'
    schema = 'orderdb'
    query = ''
    colname = ['id', 'address', 'red', 'green', 'blue', 'required_red', 'required_green',
                                'required_blue', 'orderdate']
    fulcolname = ['id', 'exp_id', 'customer', 'address', 'orderdate', 'r', 'g', 'b', 'f_r', 'f_g', 'f_b', 'r_r', 'r_g', 'r_b',
                  'pending', 'filldate', 'tot_item']

    db(action, orderid)
