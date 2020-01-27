import mysql.connector
import sys
import pandas as pd


action = sys.argv[1]

def db(action):
    cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=schema)
    cursor = cnx.cursor()

    if action == 'd':
        query = 'delete from orders where id != 000;'
        cursor.execute(query)
        cnx.commit()
        print('All rows have been deleted.')

    elif action == 's':
        query = f"SELECT {', '.join(colname)} " + "FROM orders"
        cursor.execute(query)
        pending = cursor.fetchall()
        pending = pd.DataFrame(pending, columns=colname)
        print(pending)

if __name__ == '__main__':
    host = 'localhost'
    user = 'root'
    passwd = 'pass'
    schema = 'orderdb'
    query = ''
    colname = ['id', 'address', 'red', 'green', 'blue', 'required_red', 'required_green',
                                'required_blue', 'orderdate']

    db(action)
