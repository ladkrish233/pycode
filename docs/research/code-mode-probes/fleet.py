import sys,time
from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelResponse,TextPart
from pydantic_ai_harness.code_mode import CodeMode
rss=lambda:int([l for l in open("/proc/self/status") if l.startswith("VmRSS")][0].split()[1])
fm=FunctionModel(lambda m,i:ModelResponse(parts=[TextPart("ok")]))
def mk(cm):
    a=Agent(fm,capabilities=[CodeMode()] if cm else [])
    @a.tool_plain
    def f(x:int)->int: return x
    return a
cm=sys.argv[1]=="1"
mk(cm).run_sync("hi"); r0=rss()
t=time.perf_counter(); A=[mk(cm) for _ in range(50)]
for a in A: a.run_sync("hi")
print(round((rss()-r0)/50), "KB/agent", round((time.perf_counter()-t)*1000/50),"ms/agent", rss()//1024,"MB total")
