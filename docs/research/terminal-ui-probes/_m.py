import time,sys
t0=time.perf_counter()
def done(tag):
    d=dict(l.split(":",1) for l in open("/proc/self/status") if l.startswith("VmRSS"))
    sys.stderr.write("%s %.1f %.1f %d\n"%(tag,(time.perf_counter()-t0)*1000,int(d["VmRSS"].split()[0])/1024,len(sys.modules)))
