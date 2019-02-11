from __future__ import division
import threading
from threading import Event, Thread, Lock
import time
import random
import os
import logging

from pss_driver import MatPowerDriver

READ = "read"
WRITE = "write"


class Request():
    def __init__(self, ts, reqtype, objtype, objid, fieldtype, value=""):
        self.ts = ts
        self.reqtype = reqtype  # either READ or WRITE
        self.objtype = objtype  # gen, bus, load, etc.
        self.objid = objid
        self.fieldtype = fieldtype # p, q, v, angle, etc.
        self.value = value
        self.event = Event()

    
    def to_string(self):
        return ",".join([self.ts, self.reqtype, self.objtype,
                         self.objid, self.fieldtype, self.value])


def rpc_read(ts, objtype, objid, fieldtype):
    global requests, reqlock

    request = Request(ts, READ, objtype, objid, fieldtype)
    threadname = request.to_string()
    logging.info("Read thread <%s> started!"%threadname)

    reqlock.acquire()

    try:
        requests.append(request)
        openfile = open("request_order.txt", "a")
        openfile.write(threadname + "\n")
        openfile.close()

    finally:
        reqlock.release()

    request.event.wait()
    
    logging.info("Read thread <%s> returns <%s>."%(threadname, request.value))


def rpc_write(ts, objtype, objid, fieldtype, value):
    global requests, reqlock

    request = Request(ts, WRITE, objtype, objid, fieldtype, value)
    threadname = request.to_string()
    logging.info("Write thread <%s> started!"%threadname)

    reqlock.acquire()

    try:
        requests.append(request)
        openfile = open("request_order.txt", "a")
        openfile.write(threadname + "\n")
        openfile.close()

    finally:
        reqlock.release()

    request.event.wait()
    
    logging.info("Write thread <%s> completed."%threadname)
        
    
def rpc_process():
    global requests, reqlock, mp
    logging.info("Process thread started with %d requests!"%len(requests))
    
    reqlock.acquire()
    try:
        openfile = open("process_order.txt", "a")
        openfile.write("---------------\n")

        while len(requests) > 0:
            # Pop the earliest request from request list
            timestamps = [request.ts for request in requests]
            idx = timestamps.index(min(timestamps))
            request = requests.pop(idx)

            # Process the request
            if request.reqtype == READ:
                request.value = mp.read(request.objtype, request.objid, request.fieldtype)
                request.event.set()

            elif request.reqtype == WRITE:
                mp.write(request.objtype, request.objid, request.fieldtype, request.value)
                mp.run_pf()
                request.event.set()

            openfile.write(request.to_string() + "\n")
            
    finally:
        reqlock.release()
        openfile.close()
        
    logging.info("Process thread completed!")
    

##################################################

requests = []
reqlock = Lock()
mp = MatPowerDriver("data")
mp.open("data/case39")

logging.basicConfig(level=logging.DEBUG)

try:
    while True:
        choice = random.randint(0,3)
        ts = str(time.time() + 4 * (0.5 - random.random()))
        
        if choice == 0:
            # busid = str(random.randint(1,39))
            busid = "1"
            threading.Thread(target=rpc_read, args=(ts,"bus",busid,"v",)).start()
            
        elif choice == 1:
            # genid = str(random.randint(30,39))
            genid = "30"
            genv = str(1 + 0.1 * random.random())
            threading.Thread(target=rpc_write, args=(ts,"gen",genid,"v",genv,)).start()
            
        else:
            threading.Thread(target=rpc_process).start()
            
        time.sleep(1)
        
except KeyboardInterrupt:
    exit()
    
