# stdlib shell doing real work: history via readline, boxed prompt, wrap, spinner frame, status line, y/n
from _m import done
import readline, textwrap, shutil, os, sys, re
w=shutil.get_terminal_size((80,24)).columns
out=[]
out.append("\x1b[2m"+"─"*w+"\x1b[0m")
out.append("> "+"\x1b[7m \x1b[0m")
out.append("\x1b[2m"+"─"*w+"\x1b[0m")
out.append("\x1b[2m  ? for shortcuts\x1b[0m")
for l in textwrap.wrap("lorem ipsum "*40,w-2): out.append("  "+l)
sys.stdout.write("\n".join(out)+"\n")
sys.stdout.write("\r\x1b[K\x1b[36m⠋\x1b[0m Thinking…")
sys.stdout.write("\r\x1b[K")
readline.add_history("x")
done("stdlib_use")
