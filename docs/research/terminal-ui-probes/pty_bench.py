"""usage: python pty_bench.py <tools-python> <venv-python> <demo.py> [n]: median of n pty runs (24x80)."""
import subprocess,sys,re,statistics as s,os
tp,py,demo=sys.argv[1:4]; n=int(sys.argv[4]) if len(sys.argv)>4 else 9
d=os.path.dirname(os.path.abspath(__file__)); r=[]
for _ in range(n):
    e=subprocess.run([tp,d+"/pty_run.py",py,d+"/"+demo,"[]"],capture_output=True,text=True).stderr
    m=re.search(r"settled_ms=(\S+) first_prompt_ms=(\S+) child_rss_MB=(\S+)",e); r.append([float(x) for x in m.groups()])
print(demo,"settled_ms=%.0f first_prompt_ms=%.0f child_rss_MB=%.1f (median of %d)"%tuple([s.median(x[i] for x in r) for i in range(3)]+[n]))
