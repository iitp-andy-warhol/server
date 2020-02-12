import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt

host = 'localhost'
user = 'root'
passwd = 'pass'
dbname = 'orderdb'
cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=dbname,
                              auth_plugin='mysql_native_password')
cursor = cnx.cursor()
query = f"SELECT num_pending FROM pending WHERE exp_id=(SELECT MAX(exp_id) FROM experiment);"
cursor.execute(query)
num_pending_list = list(pd.DataFrame(cursor.fetchall(), columns=['ls'])['ls'])

while True:
    try:
        num_pending_list.remove(0)
    except:
        num_pending_list.insert(0, 0)
        num_pending_list.append(0)
        break
plt.plot(num_pending_list)
plt.ylabel('# pending orders')
plt.show()