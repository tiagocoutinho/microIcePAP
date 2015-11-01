import gevent
import microIcePAP


import time
s = time.time()
#th_t = gevent.spawn(microIcePAP.get_axis, icepap, 1, dict(acctime=.25, velocity=10000))
#tth_t = gevent.spawn(microIcePAP.get_axis, icepap, 2, dict(acctime=.5, velocity=5000))
#th = th_t.get()
#tth = tth_t.get()
icepap = microIcePAP.IcePAP("icebcu2")
icepap.help
th = microIcePAP.get_axis(icepap, 1, dict(acctime=.25, velocity=10000))
tth = microIcePAP.get_axis(icepap, 2, dict(acctime=.5, velocity=5000))
dt = time.time() - s

print(th,tth,dt)

