from _m import done
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
import os
kb=KeyBindings()
@kb.add("escape","enter")
def _(e): e.current_buffer.insert_text("\n")
with create_pipe_input() as inp:
    s=PromptSession("> ",multiline=False,history=FileHistory("/tmp/_pt_hist"),key_bindings=kb,input=inp,output=DummyOutput(),bottom_toolbar=lambda:"status",mouse_support=False)
    inp.send_text("hi\r")
    s.prompt()
done("pt_use")
