import mysql.connector
import sys
import pandas as pd


exp_id = sys.argv[1]
action = sys.argv[2]

try:
    orderid = sys.argv[3]
except:
    orderid = None

def db(exp_id, action, orderid):
    cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=schema, auth_plugin='mysql_native_password')
    cursor = cnx.cursor()

    if action in ['d']:
        if orderid is None:
            query = f'delete from orders where id != 000 and exp_id = {exp_id};'
            orderid = 'All'
        else:
            query = f'delete from orders where id ={orderid} and exp_id = {exp_id};'
        cursor.execute(query)
        cnx.commit()
        print(f'id = {orderid} row(s) have been deleted.')

    elif action in ['s']:
        if orderid is None:
            query = f"SELECT {', '.join(colname)} " + f"FROM orders WHERE exp_id = {exp_id};"
        else:
            query = f"SELECT {', '.join(colname)} " + f"FROM orders WHERE id={orderid} and exp_id={exp_id};"

        cursor.execute(query)
        pending = cursor.fetchall()
        pending = pd.DataFrame(pending, columns=colname)
        print(pending)

    elif action in ['sa']:

        if orderid is None:
            query = f"SELECT * FROM orders WHERE exp_id={exp_id};"
        else:
            query = f"SELECT * FROM orders WHERE id={orderid} and exp_id={exp_id};"

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

    db(exp_id, action, orderid)
