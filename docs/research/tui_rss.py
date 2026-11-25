import os,pty,sys,time,signal,select,struct,fcntl,termios
name,*cmd=sys.argv[1:]
pid,fd=pty.fork()
if pid==0: os.execv(cmd[0],cmd)
fcntl.ioctl(fd,termios.TIOCSWINSZ,struct.pack("HHHH",40,120,0,0))
t=time.time();out=b""
def drain():
    global out
    while select.select([fd],[],[],0.1)[0]:
        try: d=os.read(fd,65536)
        except OSError: return
        if not d: return
        out+=d
        if b"\x1b[6n" in d: os.write(fd,b"\x1b[1;1R")  # answer cursor-position queries
while time.time()-t<10: drain()
def kids(p):
    r=[p]
    for d in os.listdir("/proc"):
        if d.isdigit():
            try:
                if int(open(f"/proc/{d}/stat").read().rsplit(")",1)[1].split()[1])==p: r+=kids(int(d))
            except Exception: pass
    return r
tot=0
for p in kids(pid):
    try: tot+=int([l for l in open(f"/proc/{p}/status") if l.startswith("VmRSS")][0].split()[1])
    except Exception: pass
alive=os.waitpid(pid,os.WNOHANG)[0]==0
print(name,"alive=",alive,"rss_kb_tree=",tot,"| out:",out[-150:].decode(errors="replace").replace("\x1b","")[:150].replace("\n"," "))
for p in kids(pid): 
    try: os.kill(p,signal.SIGKILL)
    except Exception: pass
