import time;t0=time.perf_counter()
from pydantic_ai import Agent
a=Agent("anthropic:claude-sonnet-4-5",defer_model_check=True)
import os
d=dict(l.split(":",1) for l in open("/proc/self/status") if l.startswith(("VmRSS","VmHWM")))
print(round((time.perf_counter()-t0)*1000), int(d["VmRSS"].split()[0])//1, int(d["VmHWM"].split()[0]), len(__import__("sys").modules))
