from __future__ import division
import matplotlib.pyplot as plt
from config import *

gv = {gen:{"ts":[], "value":[]} for gen in GEN}
lq = {load:{"ts":[], "value":[]} for load in [4]}
bv = {bus:{"ts":[], "value":[]} for bus in PILOT_BUS}

lines = open("data/process_order_with_chronos_and_delay.txt", "r").readlines()
for line in lines:
    d = line.split(",")
    if len(d) == 1: continue
    assert(len(d) == 6)
    
    ts = float(d[0])
    objtype = d[2]
    objid = int(d[3])
    value = float(d[5])

    for X, Y in [("gen", gv), ("bus", bv), ("load", lq)]:
        if objtype == X:
            assert(objid in Y)
            Y[objid]["ts"].append(float(ts))
            Y[objid]["value"].append(float(value))

fig = plt.figure()

fig.add_subplot(311)
for gen in gv:
    plt.plot(gv[gen]["ts"], [gvi / BUS_VM[gen] for gvi in gv[gen]["value"]], "-o", markersize=3, label=gen)
plt.legend(ncol=2)
plt.ylabel("Generator bus voltage \n(relative change)")
plt.grid()

fig.add_subplot(312)
for bus in bv:
    plt.plot(bv[bus]["ts"], [bvi / BUS_VM[bus] for bvi in bv[bus]["value"]], "-o", markersize=3, label=bus)
plt.ylabel("Pilot bus voltage \n(relative change)")
plt.legend(ncol=2)
plt.grid()

fig.add_subplot(313)
for load in lq:
    plt.plot(lq[load]["ts"], lq[load]["value"], "-o", markersize=3, label=load)
plt.ylabel("Disturbance")
plt.legend(ncol=2)
plt.grid()

plt.show()

