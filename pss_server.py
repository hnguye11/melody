from concurrent import futures
import time
import logging
import grpc
from threading import Event, Lock

import pss_pb2
import pss_pb2_grpc

from pss_driver import MatPowerDriver


READ = "read"
WRITE = "write"


class Request():
    def __init__(self, timestamp, reqtype, objtype, objid, fieldtype, value=""):
        self.timestamp = timestamp
        self.reqtype = reqtype  # either READ or WRITE
        self.objtype = objtype  # gen, bus, load, etc.
        self.objid = objid
        self.fieldtype = fieldtype # p, q, v, angle, etc.
        self.value = value
        self.event = Event()

    
    def to_string(self):
        return ",".join([self.timestamp, self.reqtype, self.objtype,
                         self.objid, self.fieldtype, self.value])


class PSSServicer(pss_pb2_grpc.pssServicer): # a.k.a. the Proxy
    def __init__(self):
        self.requests = []
        self.reqlock = Lock()   # thread-safe access to self.requests
        self.mp = MatPowerDriver("data")
        self.mp.open("data/case39")
        open("data/request_order.txt", "w").close()
        open("data/process_order.txt", "w").close()

        
    def read(self, request, context):
        req = Request(request.timestamp, READ, request.objtype,
                      request.objid, request.fieldtype)

        reqstr = req.to_string()
        print "Read <%s> started!"%reqstr

        self.reqlock.acquire()
        
        try:
            self.requests.append(req)
            openfile = open("data/request_order.txt", "a")
            openfile.write(reqstr + "\n")
            openfile.close()

        finally:
            self.reqlock.release()

        req.event.wait()

        print "Read <%s> returns <%s>."%(reqstr, req.value)
        
        return pss_pb2.Response(value=req.value)
    

    def write(self, request, context):
        req = Request(request.timestamp, WRITE, request.objtype,
                      request.objid, request.fieldtype, request.value)

        reqstr = req.to_string()
        print "Write <%s> started!"%reqstr

        self.reqlock.acquire()

        try:
            self.requests.append(req)
            openfile = open("data/request_order.txt", "a")
            openfile.write(reqstr + "\n")
            openfile.close()

        finally:
            self.reqlock.release()

        req.event.wait()

        print "Write <%s> completed."%reqstr

        return pss_pb2.Status(status=pss_pb2.SUCCEEDED)

    
    def process(self, request, context):
        print "Process started with %d requests!"%len(self.requests)

        self.reqlock.acquire()
        try:
            openfile = open("data/process_order.txt", "a")
            openfile.write("%f,process\n"%time.time())

            while len(self.requests) > 0:
                # Pop the earliest request from request list
                timestamps = [req.timestamp for req in self.requests]
                idx = timestamps.index(min(timestamps))
                req = self.requests.pop(idx)

                # Process the request
                if req.reqtype == READ:
                    req.value = self.mp.read(req.objtype, req.objid, req.fieldtype)
                    req.event.set()

                elif req.reqtype == WRITE:
                    self.mp.write(req.objtype, req.objid, req.fieldtype, req.value)
                    self.mp.run_pf()
                    req.event.set()

                openfile.write(req.to_string() + "\n")

        finally:
            self.reqlock.release()
            openfile.close()

        print "Process completed!"
    
        return pss_pb2.Status(status=pss_pb2.SUCCEEDED)
        
    
if __name__ == '__main__':
    logging.basicConfig()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=20))
    pss_pb2_grpc.add_pssServicer_to_server(PSSServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    
    try:
        while True:
            time.sleep(10)
    
    except KeyboardInterrupt:
        server.stop(0)

