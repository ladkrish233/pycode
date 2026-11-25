"""usage: python run.py <venv-python> <probe.py> [runs]. Fresh process per run, median of ms / RSS MB."""
import subprocess,sys,statistics,os
py,p=sys.argv[1],sys.argv[2]; n=int(sys.argv[3]) if len(sys.argv)>3 else 9
d=os.path.dirname(os.path.abspath(__file__)); p=os.path.join(d,p)
env={**os.environ,"PYTHONDONTWRITEBYTECODE":""}
def one():
    r=subprocess.run([py,"-s",p],capture_output=True,text=True,env=env,cwd="/")
    return r.stderr.strip().splitlines()[-1].split()
one()  # warm .pyc
rs=[one() for _ in range(n)]
f=lambda i:statistics.median(float(x[i]) for x in rs)
print(f"{rs[0][0]:15s} ms={f(1):.1f} rss={f(2):.1f}MB mods={rs[0][3]}  (n={n}, ms range {min(float(x[1]) for x in rs):.1f}-{max(float(x[1]) for x in rs):.1f})")
