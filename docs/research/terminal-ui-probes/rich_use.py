from _m import done
import io
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.panel import Panel
from rich.spinner import Spinner
from rich.status import Status
c=Console(file=io.StringIO(),force_terminal=True,width=100)
md="# Title\n\nSome **bold** text and `code`.\n\n```python\nprint(1)\n```\n\n- a\n- b\n\n| a | b |\n|---|---|\n| 1 | 2 |\n"
c.print(Panel("> hello",expand=True))
acc=""
with Live(Markdown(""),console=c,refresh_per_second=20,transient=False) as live:
    for ch in md:
        acc+=ch; live.update(Markdown(acc))
with c.status("Thinking…"): pass
done("rich_use")
