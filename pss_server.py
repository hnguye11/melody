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


class Job():
    def __init__(self, request, reply, event):
        self.request = request
        self.reply = reply
        self.event = event

    
    def to_string(self):
        return ",".join([self.timestamp, self.reqtype, self.objtype,
                         self.objid, self.fieldtype, self.value])


class PSSServicer(pss_pb2_grpc.pssServicer): # a.k.a. the Proxy
    def __init__(self):
        self.jobs = []
        self.jobLock = Lock()   # thread-safe access to job list
        self.mp = MatPowerDriver("data")
        self.mp.open("data/case39")
        self.rlog = logging.getLogger("request_order")
        self.plog = logging.getLogger("process_order")

        
    def read(self, readRequest, context):
        self.rlog.info("%s %s"%(readRequest.timestamp, "Read"))

        event = Event()
        job = Job(readRequest, None, event)
        
        self.jobLock.acquire()
        try:
            self.jobs.append(job)
        finally:
            self.jobLock.release()

        event.wait()
        readResponse = job.reply
        
        return readResponse
    
        
    def write(self, writeRequest, context):
        self.rlog.info("%s %s"%(writeRequest.timestamp, "Write"))

        event = Event()
        job = Job(writeRequest, None, event)
        
        self.jobLock.acquire()            
        try:
            self.jobs.append(job)
        finally:
            self.jobLock.release()

        event.wait()
        writeStatus = job.reply
        
        return writeStatus
        
    
    def process(self, request, context):
        self.jobLock.acquire()
        self.rlog.info("Process id=%s"%request.id)
        
        status = pss_pb2.Status()
        status.id = request.id

        self.plog.info("Start batch processing")
        
        try:
            while len(self.jobs) > 0:
                # Pop the earliest job from job list
                timestamps = [job.request.timestamp for job in self.jobs]
                idx = timestamps.index(min(timestamps))
                job = self.jobs.pop(idx)
                request = job.request
                
                self.plog.info("timestamp=%s, type=%s"%(request.timestamp, type(request)))
                
                if type(request) == pss_pb2.ReadRequest:
                    readResponse = pss_pb2.ReadResponse()
                    
                    for req in request.request:
                        res = readResponse.response.add()
                        res.id = req.id
                        res.value = self.mp.read(req.objtype, req.objid, req.fieldtype)
                        self.plog.info("READ <%s,%s,%s,%s> returns <%s>"%(req.id, req.objtype, req.objid, req.fieldtype, res.value))
                    
                    job.reply = readResponse
                    job.event.set()

                elif type(request) == pss_pb2.WriteRequest:
                    writelist = [(req.objtype, req.objid, req.fieldtype, req.value) for req in request.request]
                    self.mp.write_multiple(writelist)
                    self.mp.run_pf()
                    
                    writeStatus = pss_pb2.WriteStatus()
                    
                    for req in request.request:
                        res = writeStatus.status.add()
                        res.id = req.id
                        res.status = pss_pb2.SUCCEEDED # TODO: get write status from pss
                        self.plog.info("WRITE <%s,%s,%s,%s,%s> returns <%s>"%(req.id, req.objtype, req.objid, req.fieldtype, req.value, res.status))
                    
                    job.reply = writeStatus
                    job.event.set()

        finally:
            self.jobLock.release()
            self.plog.info("Stop batch processing")
            
            status.status = pss_pb2.SUCCEEDED
            return status

        # self.reqlock.acquire()
        # logging.info("Process started with <%d> requests."%len(self.requests))
        
        # try:
        #     openfile = open(self.processlogfile, "a")
        #     openfile.write("--------------------\n")
            
        #     while len(self.requests) > 0:
        #         # Pop the earliest request from request list
        #         timestamps = [req.timestamp for req in self.requests]
        #         idx = timestamps.index(min(timestamps))
        #         req = self.requests.pop(idx)

        #         # Process the request
        #         if req.reqtype == READ:
        #             req.value = self.mp.read(req.objtype, req.objid, req.fieldtype)
        #             req.event.set()

        #         elif req.reqtype == WRITE:
        #             self.mp.write(req.objtype, req.objid, req.fieldtype, req.value)
        #             self.mp.run_pf()
        #             req.event.set()

        #         openfile.write(req.to_string() + "\n")

        #     openfile.close()

        #     openfile = open(self.requestlogfile, "a")
        #     openfile.write("--------------------\n")
        #     openfile.close()

        # finally:
        #     self.reqlock.release()
            
        # logging.info("Process completed.")
    
        # return pss_pb2.Status(status=pss_pb2.SUCCEEDED)
        
    
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # how many workers is sufficient?
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1000))
    pss_pb2_grpc.add_pssServicer_to_server(PSSServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    
    try:
        while True:
            time.sleep(10)
    
    except KeyboardInterrupt:
        server.stop(0)

