from _m import done
import sys
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.styles import Style
import shutil
kb=KeyBindings()
@kb.add("escape","enter")
def _(e): e.current_buffer.insert_text("\n")
w=shutil.get_terminal_size().columns
rule="─"*w
h=InMemoryHistory(); h.append_string("earlier")
s=PromptSession(ANSI("\x1b[2m"+rule+"\x1b[0m\n> "),multiline=False,history=h,key_bindings=kb,
  bottom_toolbar=ANSI("\x1b[2m"+rule+"\n  ? for shortcuts\x1b[0m"),style=Style.from_dict({"bottom-toolbar":"noreverse"}),
  prompt_continuation="  ")
t=s.prompt()
ok=confirm("Run `ls`?")
sys.stdout.write(repr((t,ok))+"\n")
done("demo_pt")
