from _m import done
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
a=Agent(TestModel()); a.run_sync("hi")
from prompt_toolkit import PromptSession
from prompt_toolkit.shortcuts import confirm
done("pai_pt")
