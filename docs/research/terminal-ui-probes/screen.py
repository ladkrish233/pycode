import sys,pyte
rows=int(sys.argv[2]) if len(sys.argv)>2 else 24
s=pyte.HistoryScreen(80,rows,history=2000,ratio=0.5); st=pyte.Stream(s); st.feed(open(sys.argv[1],"rb").read().decode("utf-8","replace"))
hist=["".join(c.data for c in (l[i] for i in range(80))).rstrip() for l in s.history.top]
print("\n".join(hist+["-----visible screen-----"]+[l.rstrip() for l in s.display]))
