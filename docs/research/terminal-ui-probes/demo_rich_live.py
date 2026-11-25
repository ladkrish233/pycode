# Live+Markdown streaming of a 45-line answer in a 24-row terminal; MODE env: default | visible | blocks
import os,sys,time
from _m import done
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
c=Console()
mode=os.environ.get("MODE","default")
md="# Answer\n\n"+"".join(f"- item {i} with **bold** and `code`\n" for i in range(40))+"\nEnd paragraph.\n"
c.print("shortcuts> ")
if mode=="blocks":
    # print each finished block once: scrollback stays clean
    buf=""
    for ln in md.splitlines(True):
        buf+=ln
        if ln.strip()=="" : c.print(Markdown(buf)); buf=""
    c.print(Markdown(buf))
else:
    with Live(Markdown(""),console=c,refresh_per_second=30,vertical_overflow=mode,transient=False) as live:
        acc=""
        for ln in md.splitlines(True):
            acc+=ln; live.update(Markdown(acc)); time.sleep(0.01)
done("demo_rich_live")
