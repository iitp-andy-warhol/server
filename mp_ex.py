from multiprocessing import Process
import multiprocessing as mp
import os
import time

def f(name,ll,dd,kk,oo):

    while True:
        print('hello', name,ll,dd,kk.value,oo[:])
        time.sleep(1)



if __name__ == '__main__':

    l = mp.Manager().list([3,4,5])
    j = mp.Manager().dict({'11':5})
    k = mp.Value('i',3)
    o = mp.Array('i',[3,4,5])

    ns = mp.Manager().Namespace()
    ns.l = [1,2,3,4,5]

    p = Process(target=f, args=('bob',l,j,k,o))
    p.start()
    # p.join()
    # while True:
    #     print(l)
    #     time.sleep(0.1)