*   [AgentChat](index.html)
*   [Core](../core-user-guide/index.html)
*   [Extensions](../extensions-user-guide/index.html)
*   [Studio](../autogenstudio-user-guide/index.html)
*   [API Reference](../../reference/index.html)
*   [.NET](https://microsoft.github.io/autogen/dotnet/)
*   [0.2 Docs](https://microsoft.github.io/autogen/0.2/)

Light Dark System Settings

*   [GitHub](https://github.com/microsoft/autogen)
*   [Discord](https://aka.ms/autogen-discord)
*   [Twitter](https://twitter.com/pyautogen)

*   [Installation](installation.html)
*   [Quickstart](quickstart.html)
*   [Migration Guide for v0.2 to v0.4](#)

Tutorial

*   [Introduction](tutorial/index.html)
*   [Models](tutorial/models.html)
*   [Messages](tutorial/messages.html)
*   [Agents](tutorial/agents.html)
*   [Teams](tutorial/teams.html)
*   [Human-in-the-Loop](tutorial/human-in-the-loop.html)
*   [Termination](tutorial/termination.html)
*   [Managing State](tutorial/state.html)

Advanced

*   [Custom Agents](custom-agents.html)
*   [Selector Group Chat](selector-group-chat.html)
*   [Swarm](swarm.html)
*   [Magentic-One](magentic-one.html)
*   [Memory](memory.html)
*   [Logging](logging.html)
*   [Serializing Components](serialize-components.html)

More

*   [Examples](examples/index.html)
    
    *   [Travel Planning](examples/travel-planning.html)
    *   [Company Research](examples/company-research.html)
    *   [Literature Review](examples/literature-review.html)
    

*   [API Reference](../../reference/python/autogen_agentchat.html)
*   [PyPi](https://pypi.org/project/autogen-agentchat/)
*   [Source](https://github.com/microsoft/autogen/tree/main/python/packages/autogen-agentchat)

*   [](../../index.html)
*   [AgentChat](index.html)
*   Migration...

Migration Guide for v0.2 to v0.4[#](#migration-guide-for-v0-2-to-v0-4 "Link to this heading")
=============================================================================================

This is a migration guide for users of the `v0.2.*` versions of `autogen-agentchat` to the `v0.4` version, which introduces a new set of APIs and features. The `v0.4` version contains breaking changes. Please read this guide carefully. We still maintain the `v0.2` version in the `0.2` branch; however, we highly recommend you upgrade to the `v0.4` version.

Note

We no longer have admin access to the `pyautogen` PyPI package, and the releases from that package are no longer from Microsoft since version 0.2.34. To continue use the `v0.2` version of AutoGen, install it using `autogen-agentchat~=0.2`. Please read our [clarification statement](https://github.com/microsoft/autogen/discussions/4217) regarding forks.

What is `v0.4`?[#](#what-is-v0-4 "Link to this heading")
--------------------------------------------------------

Since the release of AutoGen in 2023, we have intensively listened to our community and users from small startups and large enterprises, gathering much feedback. Based on that feedback, we built AutoGen `v0.4`, a from-the-ground-up rewrite adopting an asynchronous, event-driven architecture to address issues such as observability, flexibility, interactive control, and scale.

The `v0.4` API is layered: the [Core API](../core-user-guide/index.html) is the foundation layer offering a scalable, event-driven actor framework for creating agentic workflows; the [AgentChat API](index.html) is built on Core, offering a task-driven, high-level framework for building interactive agentic applications. It is a replacement for AutoGen `v0.2`.

Most of this guide focuses on `v0.4`’s AgentChat API; however, you can also build your own high-level framework using just the Core API.

New to AutoGen?[#](#new-to-autogen "Link to this heading")
----------------------------------------------------------

Jump straight to the [AgentChat Tutorial](tutorial/models.html) to get started with `v0.4`.

What’s in this guide?[#](#what-s-in-this-guide "Link to this heading")
----------------------------------------------------------------------

We provide a detailed guide on how to migrate your existing codebase from `v0.2` to `v0.4`.

See each feature below for detailed information on how to migrate.

- [Migration Guide for v0.2 to v0.4#](#migration-guide-for-v02-to-v04)
  - [What is `v0.4`?#](#what-is-v04)
  - [New to AutoGen?#](#new-to-autogen)
  - [What’s in this guide?#](#whats-in-this-guide)
  - [Model Client#](#model-client)
    - [Use component config#](#use-component-config)
    - [Use model client class directly#](#use-model-client-class-directly)
  - [Model Client for OpenAI-Compatible APIs#](#model-client-for-openai-compatible-apis)
  - [Model Client Cache#](#model-client-cache)
  - [Assistant Agent#](#assistant-agent)
  - [Multi-Modal Agent#](#multi-modal-agent)
  - [User Proxy#](#user-proxy)
  - [Conversable Agent and Register Reply#](#conversable-agent-and-register-reply)
  - [Save and Load Agent State#](#save-and-load-agent-state)
  - [Two-Agent Chat#](#two-agent-chat)
  - [Tool Use#](#tool-use)
  - [Chat Result#](#chat-result)
  - [Conversion between v0.2 and v0.4 Messages#](#conversion-between-v02-and-v04-messages)
  - [Group Chat#](#group-chat)
  - [Group Chat with Resume#](#group-chat-with-resume)
  - [Save and Load Group Chat State#](#save-and-load-group-chat-state)
  - [Group Chat with Tool Use#](#group-chat-with-tool-use)
  - [Group Chat with Custom Selector (Stateflow)#](#group-chat-with-custom-selector-stateflow)
  - [Nested Chat#](#nested-chat)
  - [Sequential Chat#](#sequential-chat)
  - [GPTAssistantAgent#](#gptassistantagent)
  - [Long Context Handling#](#long-context-handling)
  - [Observability and Control#](#observability-and-control)
  - [Code Executors#](#code-executors)
        

The following features currently in `v0.2` will be provided in the future releases of `v0.4.*` versions:

*   Model Client Cost [#4835](https://github.com/microsoft/autogen/issues/4835)
    
*   Teachable Agent
    
*   RAG Agent
    

We will update this guide when the missing features become available.

Model Client[#](#model-client "Link to this heading")
-----------------------------------------------------

In `v0.2` you configure the model client as follows, and create the `OpenAIWrapper` object.

from autogen.oai import OpenAIWrapper

config\_list \= \[
    {"model": "gpt-4o", "api\_key": "sk-xxx"},
    {"model": "gpt-4o-mini", "api\_key": "sk-xxx"},
\]

model\_client \= OpenAIWrapper(config\_list\=config\_list)

Copy to clipboard

> **Note**: In AutoGen 0.2, the OpenAI client would try configs in the list until one worked. 0.4 instead expects a specfic model configuration to be chosen.

In `v0.4`, we offer two ways to create a model client.

### Use component config[#](#use-component-config "Link to this heading")

AutoGen 0.4 has a [generic component configuration system](../core-user-guide/framework/component-config.html). Model clients are a great use case for this. See below for how to create an OpenAI chat completion client.

from autogen\_core.models import ChatCompletionClient

config \= {
    "provider": "OpenAIChatCompletionClient",
    "config": {
        "model": "gpt-4o",
        "api\_key": "sk-xxx" \# os.environ\["...'\]
    }
}

model\_client \= ChatCompletionClient.load\_component(config)

Copy to clipboard

### Use model client class directly[#](#use-model-client-class-directly "Link to this heading")

Open AI:

from autogen\_ext.models.openai import OpenAIChatCompletionClient

model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", api\_key\="sk-xxx")

Copy to clipboard

Azure OpenAI:

from autogen\_ext.models.openai import AzureOpenAIChatCompletionClient

model\_client \= AzureOpenAIChatCompletionClient(
    azure\_deployment\="gpt-4o",
    azure\_endpoint\="https://<your-endpoint>.openai.azure.com/",
    model\="gpt-4o",
    api\_version\="2024-09-01-preview",
    api\_key\="sk-xxx",
)

Copy to clipboard

Read more on [`OpenAIChatCompletionClient`](../../reference/python/autogen_ext.models.openai.html#autogen_ext.models.openai.OpenAIChatCompletionClient "autogen_ext.models.openai.OpenAIChatCompletionClient").

Model Client for OpenAI-Compatible APIs[#](#model-client-for-openai-compatible-apis "Link to this heading")
-----------------------------------------------------------------------------------------------------------

You can use a the `OpenAIChatCompletionClient` to connect to an OpenAI-Compatible API, but you need to specify the `base_url` and `model_info`.

from autogen\_ext.models.openai import OpenAIChatCompletionClient

custom\_model\_client \= OpenAIChatCompletionClient(
    model\="custom-model-name",
    base\_url\="https://custom-model.com/reset/of/the/path",
    api\_key\="placeholder",
    model\_info\={
        "vision": True,
        "function\_calling": True,
        "json\_output": True,
        "family": "unknown",
    },
)

Copy to clipboard

> **Note**: We don’t test all the OpenAI-Compatible APIs, and many of them works differently from the OpenAI API even though they may claim to suppor it. Please test them before using them.

Read about [Model Clients](tutorial/models.html) in AgentChat Tutorial and more detailed information on [Core API Docs](../core-user-guide/components/model-clients.html)

Support for other hosted models will be added in the future.

Model Client Cache[#](#model-client-cache "Link to this heading")
-----------------------------------------------------------------

In `v0.2`, you can set the cache seed through the `cache_seed` parameter in the LLM config. The cache is enabled by default.

llm\_config \= {
    "config\_list": \[{"model": "gpt-4o", "api\_key": "sk-xxx"}\],
    "seed": 42,
    "temperature": 0,
    "cache\_seed": 42,
}

Copy to clipboard

In `v0.4`, the cache is not enabled by default, to use it you need to use a [`ChatCompletionCache`](../../reference/python/autogen_ext.models.cache.html#autogen_ext.models.cache.ChatCompletionCache "autogen_ext.models.cache.ChatCompletionCache") wrapper around the model client.

You can use a [`DiskCacheStore`](../../reference/python/autogen_ext.cache_store.diskcache.html#autogen_ext.cache_store.diskcache.DiskCacheStore "autogen_ext.cache_store.diskcache.DiskCacheStore") or [`RedisStore`](../../reference/python/autogen_ext.cache_store.redis.html#autogen_ext.cache_store.redis.RedisStore "autogen_ext.cache_store.redis.RedisStore") to store the cache.

pip install \-U "autogen-ext\[openai, diskcache, redis\]"

Copy to clipboard

Here’s an example of using `diskcache` for local caching:

import asyncio
import tempfile

from autogen\_core.models import UserMessage
from autogen\_ext.models.openai import OpenAIChatCompletionClient
from autogen\_ext.models.cache import ChatCompletionCache, CHAT\_CACHE\_VALUE\_TYPE
from autogen\_ext.cache\_store.diskcache import DiskCacheStore
from diskcache import Cache

async def main():
    with tempfile.TemporaryDirectory() as tmpdirname:
        \# Initialize the original client
        openai\_model\_client \= OpenAIChatCompletionClient(model\="gpt-4o")

        \# Then initialize the CacheStore, in this case with diskcache.Cache.
        \# You can also use redis like:
        \# from autogen\_ext.cache\_store.redis import RedisStore
        \# import redis
        \# redis\_instance = redis.Redis()
        \# cache\_store = RedisCacheStore\[CHAT\_CACHE\_VALUE\_TYPE\](redis\_instance)
        cache\_store \= DiskCacheStore\[CHAT\_CACHE\_VALUE\_TYPE\](Cache(tmpdirname))
        cache\_client \= ChatCompletionCache(openai\_model\_client, cache\_store)

        response \= await cache\_client.create(\[UserMessage(content\="Hello, how are you?", source\="user")\])
        print(response)  \# Should print response from OpenAI
        response \= await cache\_client.create(\[UserMessage(content\="Hello, how are you?", source\="user")\])
        print(response)  \# Should print cached response

asyncio.run(main())

Copy to clipboard

Assistant Agent[#](#assistant-agent "Link to this heading")
-----------------------------------------------------------

In `v0.2`, you create an assistant agent as follows:

from autogen.agentchat import AssistantAgent

llm\_config \= {
    "config\_list": \[{"model": "gpt-4o", "api\_key": "sk-xxx"}\],
    "seed": 42,
    "temperature": 0,
}

assistant \= AssistantAgent(
    name\="assistant",
    system\_message\="You are a helpful assistant.",
    llm\_config\=llm\_config,
)

Copy to clipboard

In `v0.4`, it is similar, but you need to specify `model_client` instead of `llm_config`.

from autogen\_agentchat.agents import AssistantAgent
from autogen\_ext.models.openai import OpenAIChatCompletionClient

model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", api\_key\="sk-xxx", seed\=42, temperature\=0)

assistant \= AssistantAgent(
    name\="assistant",
    system\_message\="You are a helpful assistant.",
    model\_client\=model\_client,
)

Copy to clipboard

However, the usage is somewhat different. In `v0.4`, instead of calling `assistant.send`, you call `assistant.on_messages` or `assistant.on_messages_stream` to handle incoming messages. Furthermore, the `on_messages` and `on_messages_stream` methods are asynchronous, and the latter returns an async generator to stream the inner thoughts of the agent.

Here is how you can call the assistant agent in `v0.4` directly, continuing from the above example:

import asyncio
from autogen\_agentchat.messages import TextMessage
from autogen\_agentchat.agents import AssistantAgent
from autogen\_core import CancellationToken
from autogen\_ext.models.openai import OpenAIChatCompletionClient

async def main() \-> None:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", seed\=42, temperature\=0)

    assistant \= AssistantAgent(
        name\="assistant",
        system\_message\="You are a helpful assistant.",
        model\_client\=model\_client,
    )

    cancellation\_token \= CancellationToken()
    response \= await assistant.on\_messages(\[TextMessage(content\="Hello!", source\="user")\], cancellation\_token)
    print(response)

asyncio.run(main())

Copy to clipboard

The [`CancellationToken`](../../reference/python/autogen_core.html#autogen_core.CancellationToken "autogen_core.CancellationToken") can be used to cancel the request asynchronously when you call `cancellation_token.cancel()`, which will cause the `await` on the `on_messages` call to raise a `CancelledError`.

Read more on [Agent Tutorial](tutorial/agents.html) and [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent").

Multi-Modal Agent[#](#multi-modal-agent "Link to this heading")
---------------------------------------------------------------

The [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent") in `v0.4` supports multi-modal inputs if the model client supports it. The `vision` capability of the model client is used to determine if the agent supports multi-modal inputs.

import asyncio
from pathlib import Path
from autogen\_agentchat.messages import MultiModalMessage
from autogen\_agentchat.agents import AssistantAgent
from autogen\_core import CancellationToken, Image
from autogen\_ext.models.openai import OpenAIChatCompletionClient

async def main() \-> None:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", seed\=42, temperature\=0)

    assistant \= AssistantAgent(
        name\="assistant",
        system\_message\="You are a helpful assistant.",
        model\_client\=model\_client,
    )

    cancellation\_token \= CancellationToken()
    message \= MultiModalMessage(
        content\=\["Here is an image:", Image.from\_file(Path("test.png"))\],
        source\="user",
    )
    response \= await assistant.on\_messages(\[message\], cancellation\_token)
    print(response)

asyncio.run(main())

Copy to clipboard

User Proxy[#](#user-proxy "Link to this heading")
-------------------------------------------------

In `v0.2`, you create a user proxy as follows:

from autogen.agentchat import UserProxyAgent

user\_proxy \= UserProxyAgent(
    name\="user\_proxy",
    human\_input\_mode\="NEVER",
    max\_consecutive\_auto\_reply\=10,
    code\_execution\_config\=False,
    llm\_config\=False,
)

Copy to clipboard

This user proxy would take input from the user through console, and would terminate if the incoming message ends with “TERMINATE”.

In `v0.4`, a user proxy is simply an agent that takes user input only, there is no other special configuration needed. You can create a user proxy as follows:

from autogen\_agentchat.agents import UserProxyAgent

user\_proxy \= UserProxyAgent("user\_proxy")

Copy to clipboard

See [`UserProxyAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.UserProxyAgent "autogen_agentchat.agents.UserProxyAgent") for more details and how to customize the input function with timeout.

Conversable Agent and Register Reply[#](#conversable-agent-and-register-reply "Link to this heading")
-----------------------------------------------------------------------------------------------------

In `v0.2`, you can create a conversable agent and register a reply function as follows:

from typing import Any, Dict, List, Optional, Tuple, Union
from autogen.agentchat import ConversableAgent

llm\_config \= {
    "config\_list": \[{"model": "gpt-4o", "api\_key": "sk-xxx"}\],
    "seed": 42,
    "temperature": 0,
}

conversable\_agent \= ConversableAgent(
    name\="conversable\_agent",
    system\_message\="You are a helpful assistant.",
    llm\_config\=llm\_config,
    code\_execution\_config\={"work\_dir": "coding"},
    human\_input\_mode\="NEVER",
    max\_consecutive\_auto\_reply\=10,
)

def reply\_func(
    recipient: ConversableAgent,
    messages: Optional\[List\[Dict\]\] \= None,
    sender: Optional\[Agent\] \= None,
    config: Optional\[Any\] \= None,
) \-> Tuple\[bool, Union\[str, Dict, None\]\]:
    \# Custom reply logic here
    return True, "Custom reply"

\# Register the reply function
conversable\_agent.register\_reply(\[ConversableAgent\], reply\_func, position\=0)

\# NOTE: An async reply function will only be invoked with async send.

Copy to clipboard

Rather than guessing what the `reply_func` does, all its parameters, and what the `position` should be, in `v0.4`, we can simply create a custom agent and implement the `on_messages`, `on_reset`, and `produced_message_types` methods.

from typing import Sequence
from autogen\_core import CancellationToken
from autogen\_agentchat.agents import BaseChatAgent
from autogen\_agentchat.messages import TextMessage, ChatMessage
from autogen\_agentchat.base import Response

class CustomAgent(BaseChatAgent):
    async def on\_messages(self, messages: Sequence\[ChatMessage\], cancellation\_token: CancellationToken) \-> Response:
        return Response(chat\_message\=TextMessage(content\="Custom reply", source\=self.name))

    async def on\_reset(self, cancellation\_token: CancellationToken) \-> None:
        pass

    @property
    def produced\_message\_types(self) \-> Sequence\[type\[ChatMessage\]\]:
        return (TextMessage,)

Copy to clipboard

You can then use the custom agent in the same way as the [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent"). See [Custom Agent Tutorial](custom-agents.html) for more details.

Save and Load Agent State[#](#save-and-load-agent-state "Link to this heading")
-------------------------------------------------------------------------------

In `v0.2` there is no built-in way to save and load an agent’s state: you need to implement it yourself by exporting the `chat_messages` attribute of `ConversableAgent` and importing it back through the `chat_messages` parameter.

In `v0.4`, you can call `save_state` and `load_state` methods on agents to save and load their state.

import asyncio
import json
from autogen\_agentchat.messages import TextMessage
from autogen\_agentchat.agents import AssistantAgent
from autogen\_core import CancellationToken
from autogen\_ext.models.openai import OpenAIChatCompletionClient

async def main() \-> None:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", seed\=42, temperature\=0)

    assistant \= AssistantAgent(
        name\="assistant",
        system\_message\="You are a helpful assistant.",
        model\_client\=model\_client,
    )

    cancellation\_token \= CancellationToken()
    response \= await assistant.on\_messages(\[TextMessage(content\="Hello!", source\="user")\], cancellation\_token)
    print(response)

    \# Save the state.
    state \= await assistant.save\_state()

    \# (Optional) Write state to disk.
    with open("assistant\_state.json", "w") as f:
        json.dump(state, f)

    \# (Optional) Load it back from disk.
    with open("assistant\_state.json", "r") as f:
        state \= json.load(f)
        print(state) \# Inspect the state, which contains the chat history.

    \# Carry on the chat.
    response \= await assistant.on\_messages(\[TextMessage(content\="Tell me a joke.", source\="user")\], cancellation\_token)
    print(response)

    \# Load the state, resulting the agent to revert to the previous state before the last message.
    await assistant.load\_state(state)

    \# Carry on the same chat again.
    response \= await assistant.on\_messages(\[TextMessage(content\="Tell me a joke.", source\="user")\], cancellation\_token)

asyncio.run(main())

Copy to clipboard

You can also call `save_state` and `load_state` on any teams, such as [`RoundRobinGroupChat`](../../reference/python/autogen_agentchat.teams.html#autogen_agentchat.teams.RoundRobinGroupChat "autogen_agentchat.teams.RoundRobinGroupChat") to save and load the state of the entire team.

Two-Agent Chat[#](#two-agent-chat "Link to this heading")
---------------------------------------------------------

In `v0.2`, you can create a two-agent chat for code execution as follows:

from autogen.coding import LocalCommandLineCodeExecutor
from autogen.agentchat import AssistantAgent, UserProxyAgent

llm\_config \= {
    "config\_list": \[{"model": "gpt-4o", "api\_key": "sk-xxx"}\],
    "seed": 42,
    "temperature": 0,
}

assistant \= AssistantAgent(
    name\="assistant",
    system\_message\="You are a helpful assistant. Write all code in python. Reply only 'TERMINATE' if the task is done.",
    llm\_config\=llm\_config,
    is\_termination\_msg\=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)

user\_proxy \= UserProxyAgent(
    name\="user\_proxy",
    human\_input\_mode\="NEVER",
    max\_consecutive\_auto\_reply\=10,
    code\_execution\_config\={"code\_executor": LocalCommandLineCodeExecutor(work\_dir\="coding")},
    llm\_config\=False,
    is\_termination\_msg\=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
)

chat\_result \= user\_proxy.initiate\_chat(assistant, message\="Write a python script to print 'Hello, world!'")
\# Intermediate messages are printed to the console directly.
print(chat\_result)

Copy to clipboard

To get the same behavior in `v0.4`, you can use the [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent") and [`CodeExecutorAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.CodeExecutorAgent "autogen_agentchat.agents.CodeExecutorAgent") together in a [`RoundRobinGroupChat`](../../reference/python/autogen_agentchat.teams.html#autogen_agentchat.teams.RoundRobinGroupChat "autogen_agentchat.teams.RoundRobinGroupChat").

import asyncio
from autogen\_agentchat.agents import AssistantAgent, CodeExecutorAgent
from autogen\_agentchat.teams import RoundRobinGroupChat
from autogen\_agentchat.conditions import TextMentionTermination, MaxMessageTermination
from autogen\_agentchat.ui import Console
from autogen\_ext.code\_executors.local import LocalCommandLineCodeExecutor
from autogen\_ext.models.openai import OpenAIChatCompletionClient

async def main() \-> None:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", seed\=42, temperature\=0)

    assistant \= AssistantAgent(
        name\="assistant",
        system\_message\="You are a helpful assistant. Write all code in python. Reply only 'TERMINATE' if the task is done.",
        model\_client\=model\_client,
    )

    code\_executor \= CodeExecutorAgent(
        name\="code\_executor",
        code\_executor\=LocalCommandLineCodeExecutor(work\_dir\="coding"),
    )

    \# The termination condition is a combination of text termination and max message termination, either of which will cause the chat to terminate.
    termination \= TextMentionTermination("TERMINATE") | MaxMessageTermination(10)

    \# The group chat will alternate between the assistant and the code executor.
    group\_chat \= RoundRobinGroupChat(\[assistant, code\_executor\], termination\_condition\=termination)

    \# \`run\_stream\` returns an async generator to stream the intermediate messages.
    stream \= group\_chat.run\_stream(task\="Write a python script to print 'Hello, world!'")
    \# \`Console\` is a simple UI to display the stream.
    await Console(stream)

asyncio.run(main())

Copy to clipboard

Tool Use[#](#tool-use "Link to this heading")
---------------------------------------------

In `v0.2`, to create a tool use chatbot, you must have two agents, one for calling the tool and one for executing the tool. You need to initiate a two-agent chat for every user request.

from autogen.agentchat import AssistantAgent, UserProxyAgent, register\_function

llm\_config \= {
    "config\_list": \[{"model": "gpt-4o", "api\_key": "sk-xxx"}\],
    "seed": 42,
    "temperature": 0,
}

tool\_caller \= AssistantAgent(
    name\="tool\_caller",
    system\_message\="You are a helpful assistant. You can call tools to help user.",
    llm\_config\=llm\_config,
    max\_consecutive\_auto\_reply\=1, \# Set to 1 so that we return to the application after each assistant reply as we are building a chatbot.
)

tool\_executor \= UserProxyAgent(
    name\="tool\_executor",
    human\_input\_mode\="NEVER",
    code\_execution\_config\=False,
    llm\_config\=False,
)

def get\_weather(city: str) \-> str:
    return f"The weather in {city} is 72 degree and sunny."

\# Register the tool function to the tool caller and executor.
register\_function(get\_weather, caller\=tool\_caller, executor\=tool\_executor)

while True:
    user\_input \= input("User: ")
    if user\_input \== "exit":
        break
    chat\_result \= tool\_executor.initiate\_chat(
        tool\_caller,
        message\=user\_input,
        summary\_method\="reflection\_with\_llm", \# To let the model reflect on the tool use, set to "last\_msg" to return the tool call result directly.
    )
    print("Assistant:", chat\_result.summary)

Copy to clipboard

In `v0.4`, you really just need one agent – the [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent") – to handle both the tool calling and tool execution.

import asyncio
from autogen\_core import CancellationToken
from autogen\_ext.models.openai import OpenAIChatCompletionClient
from autogen\_agentchat.agents import AssistantAgent
from autogen\_agentchat.messages import TextMessage

def get\_weather(city: str) \-> str: \# Async tool is possible too.
    return f"The weather in {city} is 72 degree and sunny."

async def main() \-> None:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", seed\=42, temperature\=0)
    assistant \= AssistantAgent(
        name\="assistant",
        system\_message\="You are a helpful assistant. You can call tools to help user.",
        model\_client\=model\_client,
        tools\=\[get\_weather\],
        reflect\_on\_tool\_use\=True, \# Set to True to have the model reflect on the tool use, set to False to return the tool call result directly.
    )
    while True:
        user\_input \= input("User: ")
        if user\_input \== "exit":
            break
        response \= await assistant.on\_messages(\[TextMessage(content\=user\_input, source\="user")\], CancellationToken())
        print("Assistant:", response.chat\_message.content)

asyncio.run(main())

Copy to clipboard

When using tool-equipped agents inside a group chat such as [`RoundRobinGroupChat`](../../reference/python/autogen_agentchat.teams.html#autogen_agentchat.teams.RoundRobinGroupChat "autogen_agentchat.teams.RoundRobinGroupChat"), you simply do the same as above to add tools to the agents, and create a group chat with the agents.

Chat Result[#](#chat-result "Link to this heading")
---------------------------------------------------

In `v0.2`, you get a `ChatResult` object from the `initiate_chat` method. For example:

chat\_result \= tool\_executor.initiate\_chat(
    tool\_caller,
    message\=user\_input,
    summary\_method\="reflection\_with\_llm",
)
print(chat\_result.summary) \# Get LLM-reflected summary of the chat.
print(chat\_result.chat\_history) \# Get the chat history.
print(chat\_result.cost) \# Get the cost of the chat.
print(chat\_result.human\_input) \# Get the human input solicited by the chat.

Copy to clipboard

See [ChatResult Docs](https://microsoft.github.io/autogen/0.2/docs/reference/agentchat/chat#chatresult) for more details.

In `v0.4`, you get a [`TaskResult`](../../reference/python/autogen_agentchat.base.html#autogen_agentchat.base.TaskResult "autogen_agentchat.base.TaskResult") object from a `run` or `run_stream` method. The [`TaskResult`](../../reference/python/autogen_agentchat.base.html#autogen_agentchat.base.TaskResult "autogen_agentchat.base.TaskResult") object contains the `messages` which is the message history of the chat, including both agents’ private (tool calls, etc.) and public messages.

There are some notable differences between [`TaskResult`](../../reference/python/autogen_agentchat.base.html#autogen_agentchat.base.TaskResult "autogen_agentchat.base.TaskResult") and `ChatResult`:

*   The `messages` list in [`TaskResult`](../../reference/python/autogen_agentchat.base.html#autogen_agentchat.base.TaskResult "autogen_agentchat.base.TaskResult") uses different message format than the `ChatResult.chat_history` list.
    
*   There is no `summary` field. It is up to the application to decide how to summarize the chat using the `messages` list.
    
*   `human_input` is not provided in the [`TaskResult`](../../reference/python/autogen_agentchat.base.html#autogen_agentchat.base.TaskResult "autogen_agentchat.base.TaskResult") object, as the user input can be extracted from the `messages` list by filtering with the `source` field.
    
*   `cost` is not provided in the [`TaskResult`](../../reference/python/autogen_agentchat.base.html#autogen_agentchat.base.TaskResult "autogen_agentchat.base.TaskResult") object, however, you can calculate the cost based on token usage. It would be a great community extension to add cost calculation. See [community extensions](../extensions-user-guide/discover.html).
    

Conversion between v0.2 and v0.4 Messages[#](#conversion-between-v0-2-and-v0-4-messages "Link to this heading")
---------------------------------------------------------------------------------------------------------------

You can use the following conversion functions to convert between a v0.4 message in [`autogen_agentchat.base.TaskResult.messages`](../../reference/python/autogen_agentchat.base.html#autogen_agentchat.base.TaskResult.messages "autogen_agentchat.base.TaskResult.messages") and a v0.2 message in `ChatResult.chat_history`.

from typing import Any, Dict, List, Literal

from autogen\_agentchat.messages import (
    AgentEvent,
    ChatMessage,
    HandoffMessage,
    MultiModalMessage,
    StopMessage,
    TextMessage,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
    ToolCallSummaryMessage,
)
from autogen\_core import FunctionCall, Image
from autogen\_core.models import FunctionExecutionResult

def convert\_to\_v02\_message(
    message: AgentEvent | ChatMessage,
    role: Literal\["assistant", "user", "tool"\],
    image\_detail: Literal\["auto", "high", "low"\] \= "auto",
) \-> Dict\[str, Any\]:
    """Convert a v0.4 AgentChat message to a v0.2 message.

    Args:
        message (AgentEvent | ChatMessage): The message to convert.
        role (Literal\["assistant", "user", "tool"\]): The role of the message.
        image\_detail (Literal\["auto", "high", "low"\], optional): The detail level of image content in multi-modal message. Defaults to "auto".

    Returns:
        Dict\[str, Any\]: The converted AutoGen v0.2 message.
    """
    v02\_message: Dict\[str, Any\] \= {}
    if isinstance(message, TextMessage | StopMessage | HandoffMessage | ToolCallSummaryMessage):
        v02\_message \= {"content": message.content, "role": role, "name": message.source}
    elif isinstance(message, MultiModalMessage):
        v02\_message \= {"content": \[\], "role": role, "name": message.source}
        for modal in message.content:
            if isinstance(modal, str):
                v02\_message\["content"\].append({"type": "text", "text": modal})
            elif isinstance(modal, Image):
                v02\_message\["content"\].append(modal.to\_openai\_format(detail\=image\_detail))
            else:
                raise ValueError(f"Invalid multimodal message content: {modal}")
    elif isinstance(message, ToolCallRequestEvent):
        v02\_message \= {"tool\_calls": \[\], "role": "assistant", "content": None, "name": message.source}
        for tool\_call in message.content:
            v02\_message\["tool\_calls"\].append(
                {
                    "id": tool\_call.id,
                    "type": "function",
                    "function": {"name": tool\_call.name, "args": tool\_call.arguments},
                }
            )
    elif isinstance(message, ToolCallExecutionEvent):
        tool\_responses: List\[Dict\[str, str\]\] \= \[\]
        for tool\_result in message.content:
            tool\_responses.append(
                {
                    "tool\_call\_id": tool\_result.call\_id,
                    "role": "tool",
                    "content": tool\_result.content,
                }
            )
        content \= "\\n\\n".join(\[response\["content"\] for response in tool\_responses\])
        v02\_message \= {"tool\_responses": tool\_responses, "role": "tool", "content": content}
    else:
        raise ValueError(f"Invalid message type: {type(message)}")
    return v02\_message

def convert\_to\_v04\_message(message: Dict\[str, Any\]) \-> AgentEvent | ChatMessage:
    """Convert a v0.2 message to a v0.4 AgentChat message."""
    if "tool\_calls" in message:
        tool\_calls: List\[FunctionCall\] \= \[\]
        for tool\_call in message\["tool\_calls"\]:
            tool\_calls.append(
                FunctionCall(
                    id\=tool\_call\["id"\],
                    name\=tool\_call\["function"\]\["name"\],
                    arguments\=tool\_call\["function"\]\["args"\],
                )
            )
        return ToolCallRequestEvent(source\=message\["name"\], content\=tool\_calls)
    elif "tool\_responses" in message:
        tool\_results: List\[FunctionExecutionResult\] \= \[\]
        for tool\_response in message\["tool\_responses"\]:
            tool\_results.append(
                FunctionExecutionResult(
                    call\_id\=tool\_response\["tool\_call\_id"\],
                    content\=tool\_response\["content"\],
                    is\_error\=False,
                    name\=tool\_response\["name"\],
                )
            )
        return ToolCallExecutionEvent(source\="tools", content\=tool\_results)
    elif isinstance(message\["content"\], list):
        content: List\[str | Image\] \= \[\]
        for modal in message\["content"\]:  \# type: ignore
            if modal\["type"\] \== "text":  \# type: ignore
                content.append(modal\["text"\])  \# type: ignore
            else:
                content.append(Image.from\_uri(modal\["image\_url"\]\["url"\]))  \# type: ignore
        return MultiModalMessage(content\=content, source\=message\["name"\])
    elif isinstance(message\["content"\], str):
        return TextMessage(content\=message\["content"\], source\=message\["name"\])
    else:
        raise ValueError(f"Unable to convert message: {message}")

Copy to clipboard

Group Chat[#](#group-chat "Link to this heading")
-------------------------------------------------

In `v0.2`, you need to create a `GroupChat` class and pass it into a `GroupChatManager`, and have a participant that is a user proxy to initiate the chat. For a simple scenario of a writer and a critic, you can do the following:

from autogen.agentchat import AssistantAgent, GroupChat, GroupChatManager

llm\_config \= {
    "config\_list": \[{"model": "gpt-4o", "api\_key": "sk-xxx"}\],
    "seed": 42,
    "temperature": 0,
}

writer \= AssistantAgent(
    name\="writer",
    description\="A writer.",
    system\_message\="You are a writer.",
    llm\_config\=llm\_config,
    is\_termination\_msg\=lambda x: x.get("content", "").rstrip().endswith("APPROVE"),
)

critic \= AssistantAgent(
    name\="critic",
    description\="A critic.",
    system\_message\="You are a critic, provide feedback on the writing. Reply only 'APPROVE' if the task is done.",
    llm\_config\=llm\_config,
)

\# Create a group chat with the writer and critic.
groupchat \= GroupChat(agents\=\[writer, critic\], messages\=\[\], max\_round\=12)

\# Create a group chat manager to manage the group chat, use round-robin selection method.
manager \= GroupChatManager(groupchat\=groupchat, llm\_config\=llm\_config, speaker\_selection\_method\="round\_robin")

\# Initiate the chat with the editor, intermediate messages are printed to the console directly.
result \= editor.initiate\_chat(
    manager,
    message\="Write a short story about a robot that discovers it has feelings.",
)
print(result.summary)

Copy to clipboard

In `v0.4`, you can use the [`RoundRobinGroupChat`](../../reference/python/autogen_agentchat.teams.html#autogen_agentchat.teams.RoundRobinGroupChat "autogen_agentchat.teams.RoundRobinGroupChat") to achieve the same behavior.

import asyncio
from autogen\_agentchat.agents import AssistantAgent
from autogen\_agentchat.teams import RoundRobinGroupChat
from autogen\_agentchat.conditions import TextMentionTermination
from autogen\_agentchat.ui import Console
from autogen\_ext.models.openai import OpenAIChatCompletionClient

async def main() \-> None:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", seed\=42, temperature\=0)

    writer \= AssistantAgent(
        name\="writer",
        description\="A writer.",
        system\_message\="You are a writer.",
        model\_client\=model\_client,
    )

    critic \= AssistantAgent(
        name\="critic",
        description\="A critic.",
        system\_message\="You are a critic, provide feedback on the writing. Reply only 'APPROVE' if the task is done.",
        model\_client\=model\_client,
    )

    \# The termination condition is a text termination, which will cause the chat to terminate when the text "APPROVE" is received.
    termination \= TextMentionTermination("APPROVE")

    \# The group chat will alternate between the writer and the critic.
    group\_chat \= RoundRobinGroupChat(\[writer, critic\], termination\_condition\=termination, max\_turns\=12)

    \# \`run\_stream\` returns an async generator to stream the intermediate messages.
    stream \= group\_chat.run\_stream(task\="Write a short story about a robot that discovers it has feelings.")
    \# \`Console\` is a simple UI to display the stream.
    await Console(stream)

asyncio.run(main())

Copy to clipboard

For LLM-based speaker selection, you can use the [`SelectorGroupChat`](../../reference/python/autogen_agentchat.teams.html#autogen_agentchat.teams.SelectorGroupChat "autogen_agentchat.teams.SelectorGroupChat") instead. See [Selector Group Chat Tutorial](selector-group-chat.html) and [`SelectorGroupChat`](../../reference/python/autogen_agentchat.teams.html#autogen_agentchat.teams.SelectorGroupChat "autogen_agentchat.teams.SelectorGroupChat") for more details.

> **Note**: In `v0.4`, you do not need to register functions on a user proxy to use tools in a group chat. You can simply pass the tool functions to the [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent") as shown in the [Tool Use](#tool-use) section. The agent will automatically call the tools when needed. If your tool doesn’t output well formed response, you can use the `reflect_on_tool_use` parameter to have the model reflect on the tool use.

Group Chat with Resume[#](#group-chat-with-resume "Link to this heading")
-------------------------------------------------------------------------

In `v0.2`, group chat with resume is a bit complicated. You need to explicitly save the group chat messages and load them back when you want to resume the chat. See [Resuming Group Chat in v0.2](https://microsoft.github.io/autogen/0.2/docs/topics/groupchat/resuming_groupchat) for more details.

In `v0.4`, you can simply call `run` or `run_stream` again with the same group chat object to resume the chat. To export and load the state, you can use `save_state` and `load_state` methods.

import asyncio
import json
from autogen\_agentchat.agents import AssistantAgent
from autogen\_agentchat.teams import RoundRobinGroupChat
from autogen\_agentchat.conditions import TextMentionTermination
from autogen\_agentchat.ui import Console
from autogen\_ext.models.openai import OpenAIChatCompletionClient

def create\_team() \-> RoundRobinGroupChat:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", seed\=42, temperature\=0)

    writer \= AssistantAgent(
        name\="writer",
        description\="A writer.",
        system\_message\="You are a writer.",
        model\_client\=model\_client,
    )

    critic \= AssistantAgent(
        name\="critic",
        description\="A critic.",
        system\_message\="You are a critic, provide feedback on the writing. Reply only 'APPROVE' if the task is done.",
        model\_client\=model\_client,
    )

    \# The termination condition is a text termination, which will cause the chat to terminate when the text "APPROVE" is received.
    termination \= TextMentionTermination("APPROVE")

    \# The group chat will alternate between the writer and the critic.
    group\_chat \= RoundRobinGroupChat(\[writer, critic\], termination\_condition\=termination)

    return group\_chat

async def main() \-> None:
    \# Create team.
    group\_chat \= create\_team()

    \# \`run\_stream\` returns an async generator to stream the intermediate messages.
    stream \= group\_chat.run\_stream(task\="Write a short story about a robot that discovers it has feelings.")
    \# \`Console\` is a simple UI to display the stream.
    await Console(stream)

    \# Save the state of the group chat and all participants.
    state \= await group\_chat.save\_state()
    with open("group\_chat\_state.json", "w") as f:
        json.dump(state, f)

    \# Create a new team with the same participants configuration.
    group\_chat \= create\_team()

    \# Load the state of the group chat and all participants.
    with open("group\_chat\_state.json", "r") as f:
        state \= json.load(f)
    await group\_chat.load\_state(state)

    \# Resume the chat.
    stream \= group\_chat.run\_stream(task\="Translate the story into Chinese.")
    await Console(stream)

asyncio.run(main())

Copy to clipboard

Save and Load Group Chat State[#](#save-and-load-group-chat-state "Link to this heading")
-----------------------------------------------------------------------------------------

In `v0.2`, you need to explicitly save the group chat messages and load them back when you want to resume the chat.

In `v0.4`, you can simply call `save_state` and `load_state` methods on the group chat object. See [Group Chat with Resume](#group-chat-with-resume) for an example.

Group Chat with Tool Use[#](#group-chat-with-tool-use "Link to this heading")
-----------------------------------------------------------------------------

In `v0.2` group chat, when tools are involved, you need to register the tool functions on a user proxy, and include the user proxy in the group chat. The tool calls made by other agents will be routed to the user proxy to execute.

We have observed numerous issues with this approach, such as the the tool call routing not working as expected, and the tool call request and result cannot be accepted by models without support for function calling.

In `v0.4`, there is no need to register the tool functions on a user proxy, as the tools are directly executed within the [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent"), which publishes the response from the tool to the group chat. So the group chat manager does not need to be involved in routing tool calls.

See [Selector Group Chat Tutorial](selector-group-chat.html) for an example of using tools in a group chat.

Group Chat with Custom Selector (Stateflow)[#](#group-chat-with-custom-selector-stateflow "Link to this heading")
-----------------------------------------------------------------------------------------------------------------

In `v0.2` group chat, when the `speaker_selection_method` is set to a custom function, it can override the default selection method. This is useful for implementing a state-based selection method. For more details, see [Custom Sepaker Selection in v0.2](https://microsoft.github.io/autogen/0.2/docs/topics/groupchat/customized_speaker_selection).

In `v0.4`, you can use the [`SelectorGroupChat`](../../reference/python/autogen_agentchat.teams.html#autogen_agentchat.teams.SelectorGroupChat "autogen_agentchat.teams.SelectorGroupChat") with `selector_func` to achieve the same behavior. The `selector_func` is a function that takes the current message thread of the group chat and returns the next speaker’s name. If `None` is returned, the LLM-based selection method will be used.

Here is an example of using the state-based selection method to implement a web search/analysis scenario.

import asyncio
from typing import Sequence
from autogen\_agentchat.agents import AssistantAgent
from autogen\_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen\_agentchat.messages import AgentEvent, ChatMessage
from autogen\_agentchat.teams import SelectorGroupChat
from autogen\_agentchat.ui import Console
from autogen\_ext.models.openai import OpenAIChatCompletionClient

\# Note: This example uses mock tools instead of real APIs for demonstration purposes
def search\_web\_tool(query: str) \-> str:
    if "2006-2007" in query:
        return """Here are the total points scored by Miami Heat players in the 2006-2007 season:
        Udonis Haslem: 844 points
        Dwayne Wade: 1397 points
        James Posey: 550 points
        ...
        """
    elif "2007-2008" in query:
        return "The number of total rebounds for Dwayne Wade in the Miami Heat season 2007-2008 is 214."
    elif "2008-2009" in query:
        return "The number of total rebounds for Dwayne Wade in the Miami Heat season 2008-2009 is 398."
    return "No data found."

def percentage\_change\_tool(start: float, end: float) \-> float:
    return ((end \- start) / start) \* 100

def create\_team() \-> SelectorGroupChat:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o")

    planning\_agent \= AssistantAgent(
        "PlanningAgent",
        description\="An agent for planning tasks, this agent should be the first to engage when given a new task.",
        model\_client\=model\_client,
        system\_message\="""
        You are a planning agent.
        Your job is to break down complex tasks into smaller, manageable subtasks.
        Your team members are:
            Web search agent: Searches for information
            Data analyst: Performs calculations

        You only plan and delegate tasks - you do not execute them yourself.

        When assigning tasks, use this format:
        1. <agent> : <task>

        After all tasks are complete, summarize the findings and end with "TERMINATE".
        """,
    )

    web\_search\_agent \= AssistantAgent(
        "WebSearchAgent",
        description\="A web search agent.",
        tools\=\[search\_web\_tool\],
        model\_client\=model\_client,
        system\_message\="""
        You are a web search agent.
        Your only tool is search\_tool - use it to find information.
        You make only one search call at a time.
        Once you have the results, you never do calculations based on them.
        """,
    )

    data\_analyst\_agent \= AssistantAgent(
        "DataAnalystAgent",
        description\="A data analyst agent. Useful for performing calculations.",
        model\_client\=model\_client,
        tools\=\[percentage\_change\_tool\],
        system\_message\="""
        You are a data analyst.
        Given the tasks you have been assigned, you should analyze the data and provide results using the tools provided.
        """,
    )

    \# The termination condition is a combination of text mention termination and max message termination.
    text\_mention\_termination \= TextMentionTermination("TERMINATE")
    max\_messages\_termination \= MaxMessageTermination(max\_messages\=25)
    termination \= text\_mention\_termination | max\_messages\_termination

    \# The selector function is a function that takes the current message thread of the group chat
    \# and returns the next speaker's name. If None is returned, the LLM-based selection method will be used.
    def selector\_func(messages: Sequence\[AgentEvent | ChatMessage\]) \-> str | None:
        if messages\[\-1\].source != planning\_agent.name:
            return planning\_agent.name \# Always return to the planning agent after the other agents have spoken.
        return None

    team \= SelectorGroupChat(
        \[planning\_agent, web\_search\_agent, data\_analyst\_agent\],
        model\_client\=OpenAIChatCompletionClient(model\="gpt-4o-mini"), \# Use a smaller model for the selector.
        termination\_condition\=termination,
        selector\_func\=selector\_func,
    )
    return team

async def main() \-> None:
    team \= create\_team()
    task \= "Who was the Miami Heat player with the highest points in the 2006-2007 season, and what was the percentage change in his total rebounds between the 2007-2008 and 2008-2009 seasons?"
    await Console(team.run\_stream(task\=task))

asyncio.run(main())

Copy to clipboard

Nested Chat[#](#nested-chat "Link to this heading")
---------------------------------------------------

Nested chat allows you to nest a whole team or another agent inside an agent. This is useful for creating a hierarchical structure of agents or “information silos”, as the nested agents cannot communicate directly with other agents outside of the same group.

In `v0.2`, nested chat is supported by using the `register_nested_chats` method on the `ConversableAgent` class. You need to specify the nested sequence of agents using dictionaries, See [Nested Chat in v0.2](https://microsoft.github.io/autogen/0.2/docs/tutorial/conversation-patterns#nested-chats) for more details.

In `v0.4`, nested chat is an implementation detail of a custom agent. You can create a custom agent that takes a team or another agent as a parameter and implements the `on_messages` method to trigger the nested team or agent. It is up to the application to decide how to pass or transform the messages from and to the nested team or agent.

The following example shows a simple nested chat that counts numbers.

import asyncio
from typing import Sequence
from autogen\_core import CancellationToken
from autogen\_agentchat.agents import BaseChatAgent
from autogen\_agentchat.teams import RoundRobinGroupChat
from autogen\_agentchat.messages import TextMessage, ChatMessage
from autogen\_agentchat.base import Response

class CountingAgent(BaseChatAgent):
    """An agent that returns a new number by adding 1 to the last number in the input messages."""
    async def on\_messages(self, messages: Sequence\[ChatMessage\], cancellation\_token: CancellationToken) \-> Response:
        if len(messages) \== 0:
            last\_number \= 0 \# Start from 0 if no messages are given.
        else:
            assert isinstance(messages\[\-1\], TextMessage)
            last\_number \= int(messages\[\-1\].content) \# Otherwise, start from the last number.
        return Response(chat\_message\=TextMessage(content\=str(last\_number + 1), source\=self.name))

    async def on\_reset(self, cancellation\_token: CancellationToken) \-> None:
        pass

    @property
    def produced\_message\_types(self) \-> Sequence\[type\[ChatMessage\]\]:
        return (TextMessage,)

class NestedCountingAgent(BaseChatAgent):
    """An agent that increments the last number in the input messages
    multiple times using a nested counting team."""
    def \_\_init\_\_(self, name: str, counting\_team: RoundRobinGroupChat) \-> None:
        super().\_\_init\_\_(name, description\="An agent that counts numbers.")
        self.\_counting\_team \= counting\_team

    async def on\_messages(self, messages: Sequence\[ChatMessage\], cancellation\_token: CancellationToken) \-> Response:
        \# Run the inner team with the given messages and returns the last message produced by the team.
        result \= await self.\_counting\_team.run(task\=messages, cancellation\_token\=cancellation\_token)
        \# To stream the inner messages, implement \`on\_messages\_stream\` and use that to implement \`on\_messages\`.
        assert isinstance(result.messages\[\-1\], TextMessage)
        return Response(chat\_message\=result.messages\[\-1\], inner\_messages\=result.messages\[len(messages):\-1\])

    async def on\_reset(self, cancellation\_token: CancellationToken) \-> None:
        \# Reset the inner team.
        await self.\_counting\_team.reset()

    @property
    def produced\_message\_types(self) \-> Sequence\[type\[ChatMessage\]\]:
        return (TextMessage,)

async def main() \-> None:
    \# Create a team of two counting agents as the inner team.
    counting\_agent\_1 \= CountingAgent("counting\_agent\_1", description\="An agent that counts numbers.")
    counting\_agent\_2 \= CountingAgent("counting\_agent\_2", description\="An agent that counts numbers.")
    counting\_team \= RoundRobinGroupChat(\[counting\_agent\_1, counting\_agent\_2\], max\_turns\=5)
    \# Create a nested counting agent that takes the inner team as a parameter.
    nested\_counting\_agent \= NestedCountingAgent("nested\_counting\_agent", counting\_team)
    \# Run the nested counting agent with a message starting from 1.
    response \= await nested\_counting\_agent.on\_messages(\[TextMessage(content\="1", source\="user")\], CancellationToken())
    assert response.inner\_messages is not None
    for message in response.inner\_messages:
        print(message)
    print(response.chat\_message)

asyncio.run(main())

Copy to clipboard

You should see the following output:

source\='counting\_agent\_1' models\_usage\=None content\='2' type\='TextMessage'
source\='counting\_agent\_2' models\_usage\=None content\='3' type\='TextMessage'
source\='counting\_agent\_1' models\_usage\=None content\='4' type\='TextMessage'
source\='counting\_agent\_2' models\_usage\=None content\='5' type\='TextMessage'
source\='counting\_agent\_1' models\_usage\=None content\='6' type\='TextMessage'

Copy to clipboard

You can take a look at [`SocietyOfMindAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.SocietyOfMindAgent "autogen_agentchat.agents.SocietyOfMindAgent") for a more complex implementation.

Sequential Chat[#](#sequential-chat "Link to this heading")
-----------------------------------------------------------

In `v0.2`, sequential chat is supported by using the `initiate_chats` function. It takes input a list of dictionary configurations for each step of the sequence. See [Sequential Chat in v0.2](https://microsoft.github.io/autogen/0.2/docs/tutorial/conversation-patterns#sequential-chats) for more details.

Base on the feedback from the community, the `initiate_chats` function is too opinionated and not flexible enough to support the diverse set of scenarios that users want to implement. We often find users struggling to get the `initiate_chats` function to work when they can easily glue the steps together usign basic Python code. Therefore, in `v0.4`, we do not provide a built-in function for sequential chat in the AgentChat API.

Instead, you can create an event-driven sequential workflow using the Core API, and use the other components provided the AgentChat API to implement each step of the workflow. See an example of sequential workflow in the [Core API Tutorial](../core-user-guide/design-patterns/sequential-workflow.html).

We recognize that the concept of workflow is at the heart of many applications, and we will provide more built-in support for workflows in the future.

GPTAssistantAgent[#](#gptassistantagent "Link to this heading")
---------------------------------------------------------------

In `v0.2`, `GPTAssistantAgent` is a special agent class that is backed by the OpenAI Assistant API.

In `v0.4`, the equivalent is the [`OpenAIAssistantAgent`](../../reference/python/autogen_ext.agents.openai.html#autogen_ext.agents.openai.OpenAIAssistantAgent "autogen_ext.agents.openai.OpenAIAssistantAgent") class. It supports the same set of features as the `GPTAssistantAgent` in `v0.2` with more such as customizable threads and file uploads. See [`OpenAIAssistantAgent`](../../reference/python/autogen_ext.agents.openai.html#autogen_ext.agents.openai.OpenAIAssistantAgent "autogen_ext.agents.openai.OpenAIAssistantAgent") for more details.

Long Context Handling[#](#long-context-handling "Link to this heading")
-----------------------------------------------------------------------

In `v0.2`, long context that overflows the model’s context window can be handled by using the `transforms` capability that is added to an `ConversableAgent` after which is contructed.

The feedbacks from our community has led us to believe this feature is essential and should be a built-in component of [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent"), and can be used for every custom agent.

In `v0.4`, we introduce the [`ChatCompletionContext`](../../reference/python/autogen_core.model_context.html#autogen_core.model_context.ChatCompletionContext "autogen_core.model_context.ChatCompletionContext") base class that manages message history and provides a virtual view of the history. Applications can use built-in implementations such as [`BufferedChatCompletionContext`](../../reference/python/autogen_core.model_context.html#autogen_core.model_context.BufferedChatCompletionContext "autogen_core.model_context.BufferedChatCompletionContext") to limit the message history sent to the model, or provide their own implementations that creates different virtual views.

To use [`BufferedChatCompletionContext`](../../reference/python/autogen_core.model_context.html#autogen_core.model_context.BufferedChatCompletionContext "autogen_core.model_context.BufferedChatCompletionContext") in an [`AssistantAgent`](../../reference/python/autogen_agentchat.agents.html#autogen_agentchat.agents.AssistantAgent "autogen_agentchat.agents.AssistantAgent") in a chatbot scenario.

import asyncio
from autogen\_agentchat.messages import TextMessage
from autogen\_agentchat.agents import AssistantAgent
from autogen\_core import CancellationToken
from autogen\_core.model\_context import BufferedChatCompletionContext
from autogen\_ext.models.openai import OpenAIChatCompletionClient

async def main() \-> None:
    model\_client \= OpenAIChatCompletionClient(model\="gpt-4o", seed\=42, temperature\=0)

    assistant \= AssistantAgent(
        name\="assistant",
        system\_message\="You are a helpful assistant.",
        model\_client\=model\_client,
        model\_context\=BufferedChatCompletionContext(buffer\_size\=10), \# Model can only view the last 10 messages.
    )
    while True:
        user\_input \= input("User: ")
        if user\_input \== "exit":
            break
        response \= await assistant.on\_messages(\[TextMessage(content\=user\_input, source\="user")\], CancellationToken())
        print("Assistant:", response.chat\_message.content)

asyncio.run(main())

Copy to clipboard

In this example, the chatbot can only read the last 10 messages in the history.

Observability and Control[#](#observability-and-control "Link to this heading")
-------------------------------------------------------------------------------

In `v0.4` AgentChat, you can observe the agents by using the `on_messages_stream` method which returns an async generator to stream the inner thoughts and actions of the agent. For teams, you can use the `run_stream` method to stream the inner conversation among the agents in the team. Your application can use these streams to observe the agents and teams in real-time.

Both the `on_messages_stream` and `run_stream` methods takes a [`CancellationToken`](../../reference/python/autogen_core.html#autogen_core.CancellationToken "autogen_core.CancellationToken") as a parameter which can be used to cancel the output stream asynchronously and stop the agent or team. For teams, you can also use termination conditions to stop the team when a certain condition is met. See [Termination Condition Tutorial](tutorial/termination.html) for more details.

Unlike the `v0.2` which comes with a special logging module, the `v0.4` API simply uses Python’s `logging` module to log events such as model client calls. See [Logging](../core-user-guide/framework/logging.html) in the Core API documentation for more details.

Code Executors[#](#code-executors "Link to this heading")
---------------------------------------------------------

The code executors in `v0.2` and `v0.4` are nearly identical except the `v0.4` executors support async API. You can also use [`CancellationToken`](../../reference/python/autogen_core.html#autogen_core.CancellationToken "autogen_core.CancellationToken") to cancel a code execution if it takes too long. See [Command Line Code Executors Tutorial](../core-user-guide/components/command-line-code-executors.html) in the Core API documentation.

We also added `AzureContainerCodeExecutor` that can use Azure Container Apps (ACA) dynamic sessions for code execution. See [ACA Dynamic Sessions Code Executor Docs](../extensions-user-guide/azure-container-code-executor.html).

[

previous

Quickstart



](quickstart.html "previous page")[

next

Introduction

](tutorial/index.html "next page")

On this page

- [Migration Guide for v0.2 to v0.4#](#migration-guide-for-v02-to-v04)
  - [What is `v0.4`?#](#what-is-v04)
  - [New to AutoGen?#](#new-to-autogen)
  - [What’s in this guide?#](#whats-in-this-guide)
  - [Model Client#](#model-client)
    - [Use component config#](#use-component-config)
    - [Use model client class directly#](#use-model-client-class-directly)
  - [Model Client for OpenAI-Compatible APIs#](#model-client-for-openai-compatible-apis)
  - [Model Client Cache#](#model-client-cache)
  - [Assistant Agent#](#assistant-agent)
  - [Multi-Modal Agent#](#multi-modal-agent)
  - [User Proxy#](#user-proxy)
  - [Conversable Agent and Register Reply#](#conversable-agent-and-register-reply)
  - [Save and Load Agent State#](#save-and-load-agent-state)
  - [Two-Agent Chat#](#two-agent-chat)
  - [Tool Use#](#tool-use)
  - [Chat Result#](#chat-result)
  - [Conversion between v0.2 and v0.4 Messages#](#conversion-between-v02-and-v04-messages)
  - [Group Chat#](#group-chat)
  - [Group Chat with Resume#](#group-chat-with-resume)
  - [Save and Load Group Chat State#](#save-and-load-group-chat-state)
  - [Group Chat with Tool Use#](#group-chat-with-tool-use)
  - [Group Chat with Custom Selector (Stateflow)#](#group-chat-with-custom-selector-stateflow)
  - [Nested Chat#](#nested-chat)
  - [Sequential Chat#](#sequential-chat)
  - [GPTAssistantAgent#](#gptassistantagent)
  - [Long Context Handling#](#long-context-handling)
  - [Observability and Control#](#observability-and-control)
  - [Code Executors#](#code-executors)

[Edit on GitHub](https://github.com/microsoft/autogen/edit/main/python/packages/autogen-core/docs/src/user-guide/agentchat-user-guide/migration-guide.md)

[Show Source](../../_sources/user-guide/agentchat-user-guide/migration-guide.md.txt)