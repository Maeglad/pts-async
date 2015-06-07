from eventloop import EventLoop, my_print, printer
from functools import partial
import pdb
import queue
# https://promisesaplus.com/


class Promise():
    """
    Promises are bound to one (singleton) instance of EventLoop (stored in variable `e`). Maybe it's not perfect, but it's ok
    for the purpose of this assignment
    """

    """
    states - did not work for some reason replaced with strings
    """
    PENDING = 0;
    FULFILLED = 1;
    REJECTED = 2;


    def __init__(self, resolver):
        self.state = 'PENDING';
        self.value = None;
        self.values = [];
        self.callbacks = [];
        self.errorcallbacks = [];
        self.specialCall = None;
        self.count = 0;
        if(resolver != None):
            resolver(self.resolve, self.reject);

    def setCount(self, val=0):
        self.count = val;

    def setList(self, list_of_promises):
        self.list_of_promises = list_of_promises;

    def setValueCall(value, call):# will call specialCall when fulfilled with value instead of self.value
        if(self.state == 'PENDING'):
           self.override = value;
           self.specialCall = call;


    def fulfill(self, value):
        if(self.state != 'PENDING'):
            return;
        if(self.count != 0):
            self.values.append(value);
            if(self.count == len(self.values)):
                self.value = self.values;
            else:
                return;
#        print('fulfilled');
        self.state = 'FULFILLED';
        if(self.count == 0):
            self.value = value;
        else: ## this aproach is not cleanest but i cant be picky right now

            values = [];
            for i in range(len(self.list_of_promises)):
                values.append(self.list_of_promises[i].value);
            self.value = values;

        callbacks = self.callbacks;
        self.callbacks = None;
 #       print(len(callbacks));
        for call in callbacks:
  #          print('callbacks salled');
            e.run(lambda: call(self.value));



    def reject(self, value):
        if(self.state != 'PENDING'):
            return;
        if(not isinstance(value, Exception)):
            return;

        self.state = 'REJECTED';
        self.value = value;
        errorcalls = self.errorcallbacks;
        self.errorcallbacks = None;
        for call in errorcalls:
            call(self.value);
    """
        [RESOLVE](promise, x)
            x is value -> fulfill with x
            x is promise -> adopt promise state
                -> pending -> wait and adopt
                -> finished -> finish
            x is promise-like - has then method resp. done
                -> "promisify(x)" and adopt state
            x is function -> not promise-like
                -> fulfill promise with x
    """
    def resolve(self, x):
        if(self.state == 'FULFILLED'): # maybe some kind of error would be better
            return;
        if(isinstance(x, Promise)):
            x.done(self.resolve, self.reject);
        else:
            self.fulfill(x);

    def done(self, onFulfill, onReject):
        #if(onFulfill is None):
   #         print('None');
        if(self.state == 'PENDING'):
            if(onFulfill is not None):
                self.callbacks.append(onFulfill);
  #              print(self.callbacks);
            if(onReject is not None):
                self.errorcallbacks.append(onReject);
            return;

        if(self.state == 'FULFILLED'):
            e.run(onFulfill(self.value));

        if(self.state == REJECTED):
            e.run(onReject(self.value));




    def then(self, then_fn):

        p = Promise(None);
        def successCall(value):

            if( hasattr(then_fn, '__call__') ):
                e.run(lambda: p.resolve(then_fn(self.value)));

            else:
                e.run(lambda: p.resolve(self.value));

        self.done(successCall, None); # errorcall is missing so none
        return p;

    def delayed(time, val = None):
        """
        creates promise which fulfills after time `time` with value `val`; this is a complete
        implementation, no TODO here.
        """
        def resolver(resolve, reject):
            e.wait(time, lambda: resolve(val))

        return Promise(resolver)

    def read_file(filename):
        """
        creates promise which fulfills with the content of a given file
        """
        #TODO
        pass

    def all(list_of_promises):
        """
        Promise.all(list_of_promises) returns a new promise which fulfills when all the promises from
        the given list fulfill. Result is a list cotaining values of individual promises in
        list_of_promises. Similar to bluebird's Promise.all
        """

        p = Promise(None);
        p.setCount(len(list_of_promises));
        p.setList(list_of_promises);
        for pr in list_of_promises:
            pr.then(p.resolve);

        return p;


    def foreach(iterable, get_promise):
        """
        executes `get_promise` on each element from `iterable`. Results from `get_promise` are
        waited for within the iteration.

        foreach pseudocode:

        for elem in iterable:
            p = get_promise(elem)
            wait for p to fulfill, then continue

        """
        # can change to list of promises and agregate through all if return is wanted as list
        x = iter(iterable);
        val = next(x);
        def resolver(resolve, reject):
            e.run(lambda: resolve(get_promise(val)));
        p = Promise(resolver);
        def _foreach(iterator,p):
            try:
                elem = next(iterator);
                #print(elem);
                p = p.then(lambda v: get_promise(elem));
                _foreach(iterator,p);
            except StopIteration:
                return

        #promise_list = [];

        _foreach(x,p);
        # you may find helpful this piece of code

        return p;


def print_inc_wait(res):
    print(res)
    res += 1
    return Promise.delayed(1, res)

def test1():
    """
    basic promise functionality.

    should print begin, 0, 1, 2, 3 in one second intervals
    moreover, `then` should return Promise object
    """
    p = Promise.delayed(1,0) \
    .then(print_inc_wait) \
    .then(print_inc_wait) \
    .then(print_inc_wait) \
    .then(my_print)
    print('begin')
    assert(isinstance(p, Promise))

def test2():
    """
    Test if promises are flattening returning values correctly.

    Two snippets in this test should behave indistinguishibly from the outside world;
    both should print '1' after 1 second delay
    """
    Promise.delayed(1,0) \
    .then(lambda x: x+1) \
    .then(my_print)

    Promise.delayed(1,0) \
    .then(lambda x: Promise.delayed(1, x+1)) \
    .then(my_print)

def test3():
    """
    Two "Promise chains" may be run at once

    should print 1 1 [delay] 2 2 [delay] 3 3
    """
    def get_promise():
        return Promise.delayed(1,0) \
            .then(print_inc_wait) \
            .then(print_inc_wait) \
            .then(print_inc_wait)

    get_promise()
    get_promise()

def test4():
    """
    creating new Promise works as it should
    """
    def resolver(resolve, reject):
        e.wait(2, lambda: resolve(10))

    # ugly long line, what should I do about it?
    Promise(resolver).then(lambda res: my_print("should print this after 2 seconds, moreover, this should be 10: %d"%res))

def test5():
    """
    Tests Promise.all.

    Should print [0, 2, 4, 8, 10] after 5 seconds (because the last Promise from the given list
    fulfills after 5 seconds)
    """

    list_of_promises = [Promise.delayed(6-i, 2*i) for i in range(6)];
    Promise.all(list_of_promises).then(my_print);

def test6():
    """
    Tests foreach.

    Should print 1, [delay 1s], 2, [delay 2s], 3, [delay 3s], 4
    """

    def f(x):
        print('%d'%x)
        return Promise.delayed(x, x)

    Promise.foreach([1, 2, 3, 4], f)

e = EventLoop()
e.start()
#p = Promise(print_inc_wait());
#pdb.set_trace();
#test1()
#test2()
#test3()
#test4()
#test5()
test6()
