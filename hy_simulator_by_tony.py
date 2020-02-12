import pandas
import pymysql
import time
import datetime


class TimeInterval:

    _interval = None
    _before_date = None 
    _curr_date = None 
    _before_time = None
    _before_date = None 
    _curr_time = None 

    def __init__(self, before_date, curr_date): 
        self._before_date = before_date
        self._curr_date = curr_date 

    def getIneterval(self):
        _tmp_before = self._before_date.split(':')
        _tmp_curr = self._curr_date.split(':')
    
        _before_hour = int(_tmp_before[0].split(' ')[1])
        _before_minute = int(_tmp_before[1]) 
        _before_sec = int(_tmp_before[2])

        _curr_hour = int(_tmp_curr[0].split(' ')[1])
        _curr_minute = int(_tmp_curr[1])
        _curr_sec = int(_tmp_curr[2])


        self._before_time = _before_hour*3600 + _before_minute * 60 + _before_sec 
        #print(self._before_time)
        self._curr_time = _curr_hour*3600 + _curr_minute * 60 + _curr_sec 
        #print(self._curr_time)
        self._interval = self._curr_time - self._before_time 
        print("after "+ str(self._interval)+ " second")
        return self._interval

def ConnectDB(): 
    
    conn = pymysql.connect(host = 'localhost', user='root', password = '1234', db='orderdb', charset='utf8')
    curs = conn.cursor()
    
    csv_data = pandas.read_csv('./Server/Tony_orders.csv')
    df = csv_data[["customer","red","blue","green","pending","address","orderdate"]]
    #f = open('./Server/Quer y.txt','w') 
    
    _before_order_date = '2020-02-10 16:28:40'
    

    for row in df.iloc[:,:].values:
 
        _customer = row[0]
        _customer = "'"+_customer+"'"
        _red = row[1] 
        _blue = row[2]
        _green = row[3] 
        _pending = row[4] 
        _address = row[5] 
        _orderdate =row[6] 
        
        _interval =TimeInterval(_before_order_date, _orderdate).getIneterval()
        now = datetime.datetime.now()
        _nowDatetime = f"'{now.strftime('%Y-%m-%d %H:%M:%S')}'"
        #print(_nowDatetime)
        time.sleep(_interval)

        sql = 'INSERT INTO orders(customer,red, blue, green, pending, address, orderdate) values(%s,%d,%d,%d,1,%d,%s);' %(_customer,_red,_blue,_green,_address, _nowDatetime)
        #print(sql)

        #Dabin
        #insert into orders (customer, address, orderdate, red, green, blue) values ('test', '201', '2020-02-04 19:56:56', 4, 5, 6);
        
        curs.execute(sql)
        conn.commit()
        
        _before_order_date = _orderdate


def main():
    ConnectDB()
  
    
if __name__ == '__main__':
    main()

