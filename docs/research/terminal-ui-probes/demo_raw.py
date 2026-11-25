from _m import done
import sys; sys.path.insert(0,__import__("os").path.dirname(__file__))
import ui_raw
h=["earlier"]
t=ui_raw.read_box(h)
md=ui_raw.MdStream()
with ui_raw.Spinner(): __import__("time").sleep(0.2)
for ch in "# Title\n\nSome **bold** and `code`.\n\n```py\nprint(1)\n```\n\n- a\n- b\n":
    md.feed(ch)
md.flush()
ok=ui_raw.confirm("Run `ls`?")
sys.stdout.write(repr((t,ok))+"\n")
done("demo_raw")
