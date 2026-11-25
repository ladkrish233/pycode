from _m import done
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
a=Agent(TestModel()); a.run_sync("hi")
import io
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
c=Console(file=io.StringIO(),force_terminal=True,width=100)
with Live(Markdown(""),console=c) as l: l.update(Markdown("# t\n\n**b** `c`\n\n```py\nx\n```"))
done("pai_rich")
