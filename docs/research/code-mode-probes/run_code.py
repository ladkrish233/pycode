import time,subprocess,os
from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelResponse,TextPart,ToolCallPart,ToolReturnPart
from pydantic_ai_harness.code_mode import CodeMode
rss=lambda p="self":int([l for l in open(f"/proc/{p}/status") if l.startswith("VmRSS")][0].split()[1])
def fn(msgs,info):
    if any(isinstance(p,ToolReturnPart) for m in msgs for p in m.parts if hasattr(m,'parts')): return ModelResponse(parts=[TextPart("done")])
    return ModelResponse(parts=[ToolCallPart("run_code",{"code":"x=sum(range(100))\nx"})])
a=Agent(FunctionModel(fn),capabilities=[CodeMode()])
@a.tool_plain
def f(x:int)->int: return x
t=time.perf_counter(); r=a.run_sync("hi")
ch=subprocess.run(["pgrep","-P",str(os.getpid())],capture_output=True,text=True).stdout.split()
print(round((time.perf_counter()-t)*1000),"ms", rss()//1024,"MB self", [rss(c)//1024 for c in ch],"MB children", r.output, str(r.all_messages()[-2])[:150].replace("\n"," "))
