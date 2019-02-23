from __future__ import division
import logging
import grpc
import time
import random
from google.protobuf.empty_pb2 import Empty
import threading
import logging
from config import *

import pss_pb2
import pss_pb2_grpc


def getid():
    return str(hash(time.time() + random.random()))


def rpc_read(readlist):
    channel = grpc.insecure_channel('localhost:50051')
    stub = pss_pb2_grpc.pssStub(channel)
    readRequest = pss_pb2.ReadRequest(timestamp=str(time.time()))
    print readRequest.timestamp
    
    ids = []
    for objtype, objid, fieldtype in readlist:
        req = readRequest.request.add()
        req.id = getid()
        req.objtype = objtype  
        req.objid = objid
        req.fieldtype = fieldtype
        req.value = ""
        ids.append(req.id)

    readResponse = stub.read(readRequest)    
    assert(req.id==res.id for req,res in zip(readRequest.request, readResponse.response))

    response = [float(res.value) for res in readResponse.response]
    
    logging.info("Read response %s: %s"%(readRequest.timestamp, str(response)))


def rpc_write(writelist):
    channel = grpc.insecure_channel('localhost:50051')
    stub = pss_pb2_grpc.pssStub(channel)
    writeRequest = pss_pb2.WriteRequest(timestamp=str(time.time()))
    print writeRequest.timestamp
    
    for objtype, objid, fieldtype, value in writelist:
        req = writeRequest.request.add()
        req.id = getid()
        req.objtype = objtype  
        req.objid = objid
        req.fieldtype = fieldtype
        req.value = value

    writeStatus = stub.write(writeRequest)
    assert(req.id==stt.id for req,stt in zip(writeRequest.request, writeStatus.status))

    status = [stt.status for stt in writeStatus.status]

    logging.info("Write status %s: %s"%(writeRequest.timestamp, str(status)))

    
def rpc_process():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = pss_pb2_grpc.pssStub(channel)
        request = pss_pb2.ProcessRequest(id=getid())
        status = stub.process(request)
        logging.info("Process status %s"%status.status)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    try:
        for choice in [0,1,0,2]:
            time.sleep(1)
            if choice == 0:
                readlist = [("bus", str(bus), "Vm") for bus in PILOT_BUS]
                # readlist = [("gen", str(gen), "Vg") for gen in GEN]
                threading.Thread(target=rpc_read, args=(readlist,)).start()

            elif choice == 1:
                writelist = [("gen", str(gen), "Vg", "1.0") for gen in GEN]
                threading.Thread(target=rpc_write, args=(writelist,)).start()

            elif choice == 2:
                threading.Thread(target=rpc_process).start()

        
    except KeyboardInterrupt:
        exit()

