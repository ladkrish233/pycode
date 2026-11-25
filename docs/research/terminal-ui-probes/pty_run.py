"""Drive a script in a 24x80 pty. Records: time to first prompt bytes, time to quiet (settled), child RSS at settle,
then sends keys (list of (delay,bytes)) and dumps final screen via pyte if available. Answers cursor-position queries."""
import pyte,os,pty,sys,time,select,struct,fcntl,termios,json
py,script=sys.argv[1],sys.argv[2]; keys=json.loads(sys.argv[3]) if len(sys.argv)>3 else []
rows=int(os.environ.get("ROWS",24))
pid,fd=pty.fork()
if pid==0:
    os.chdir("/"); os.execv(py,[py,"-s",script])
fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack("HHHH",rows,80,0,0))
scr=pyte.Screen(80,rows); stm=pyte.ByteStream(scr)
t0=time.perf_counter(); data=b""; first=None; last=None; rss=None
def rd(timeout):
    global data,last,first
    r,_,_=select.select([fd],[],[],timeout)
    if not r: return False
    try: b=os.read(fd,65536)
    except OSError: return False
    data+=b; last=time.perf_counter()
    if first is None and b"shortcuts" in data: first=last
    stm.feed(b.replace(b"\x1b[6n",b""))
    if b"\x1b[6n" in b: os.write(fd,b"\x1b[%d;%dR"%(scr.cursor.y+1,scr.cursor.x+1))
    return True
while True:
    if not rd(0.06) and first: break
    if time.perf_counter()-t0>10: break
settle=(last-t0)*1000
print(repr(data[-300:]),file=sys.stderr) if os.environ.get("DBG") else None
try:
    st=dict(l.split(":",1) for l in open(f"/proc/{pid}/status") if l.startswith("VmRSS")); rss=int(st["VmRSS"].split()[0])/1024
except Exception: rss=float("nan")
print(f"settled_ms={settle:.0f} first_prompt_ms={(first-t0)*1000:.0f} child_rss_MB={rss:.1f}",file=sys.stderr)
for d,k in keys:
    time.sleep(d); os.write(fd,k.encode().decode("unicode_escape").encode("latin1") if False else k.encode())
    while rd(0.15): pass
time.sleep(0.3)
while rd(0.3): pass
try: os.waitpid(pid,os.WNOHANG)
except: pass
open(os.environ.get("DUMP","/dev/null"),"wb").write(data)
