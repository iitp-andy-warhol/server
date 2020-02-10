import mysql.connector
import time

host = 'localhost'
user = 'root'
passwd = 'pass'
dbname = 'orderdb'

if __name__ == "__main__":
    print('Pending Logger is Started')
    while True:
        cnx = mysql.connector.connect(host=host, user=user, password=passwd, database=dbname,
                                      auth_plugin='mysql_native_password')
        cursor = cnx.cursor()
        query = f"INSERT INTO pending (num_pending) SELECT count(*) FROM orders WHERE pending=1 and exp_id=(SELECT MAX(exp_id) FROM experiment);"
        cursor.execute(query)
        cnx.commit()

        time.sleep(5)