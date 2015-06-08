from queue import Queue
from threading import Thread, Condition
from time import sleep
from math import sqrt
import sched, time

class EventLoop():

    def __init__(self):
        self.wqueue = Queue()
        self.lock = Condition()
        self.s = sched.scheduler(time.time, time.sleep);

    def start(self):
        def _start():
            def checkwait():
                with(self.lock):
                    while not self.wqueue.empty():
                        time, task = self.wqueue.get();
                        self.s.enter(time, 1,task);

            while True:
                self.s.run(False)
                checkwait();
        Thread(target=_start).start()


    def run(self, action):
        with(self.lock):
            self.wqueue.put([0,action])

    def wait(self, time, callback):
        with(self.lock):
            self.wqueue.put([time, callback]);

    def read_file(self, filename, callback):
        def to_run():
            f = open(filename, 'r')
            res = f.read()
            # TODO: why not just use
            # callback(res)
            self.run(lambda: callback(res))
        Thread(target = to_run).start()

def my_print(message):
    print(message)

def printer(message):
    def res():
        print(message)
    return res

if __name__ == '__main__':
    e = EventLoop()
    e.start()
    res = 0;
    def fn(res):
        res = 5;
    e.run(lambda: fn(res));
    print(res);
    e.wait(3, printer('tralala'));
    e.run(printer('tralala'));
    def ex1():
        e.run(printer('ahoj'))
        e.run(printer('svet'))
        e.run(printer(':)'))
    ex1()


    def ex2():
        e.wait(1, printer('Ich'))
        e.wait(2, printer('bin'))
        e.wait(3, printer('scheduled'))
        print('ejchuchu!')
    #ex2()

    def ex3():
        e.read_file('dummy.txt', my_print)
        print('ejchuchu!')
    #ex3()

    def ex4():

        def cb1():
            print('Ich')
            e.wait(1, cb2)

        def cb2():
            print('bin')
            e.wait(1, cb3)

        def cb3():
            print('in der')
            e.wait(1, cb4)

        def cb4():
            print('Callback-Holle :(')

        e.wait(1, cb1)

    ex4()

    def freeze():
        def cb():
            print('tututu')
            e.run(cb)
        e.run(cb)
        def cb2():
            print('aaaaaa')
            e.run(cb2)
        e.run(cb2)
    #freeze()

    def is_prime(n, cb):
        chunk_size = 100
        def trynk(n, k):
            if k > sqrt(n):
                e.run(lambda: cb(True))
                return
            for i in range(k, k + chunk_size):
                if n%i == 0:
                    e.run(lambda: cb(False))
                    return
            e.run(lambda: trynk(n, k + chunk_size))
        e.run(lambda: trynk(n, 2))

