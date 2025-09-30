import sys
import asyncio
import warnings
import logging
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from mcp.client.session import RequestContext
from mcp.types import (
    CreateMessageRequestParams,
    CreateMessageResult,
    TextContent,
    Role
)
import json
from pydantic import AnyUrl
from colorama import Fore, Style, init
from core.openrouter import OpenRouterClient

init(autoreset=True)

class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict] = None,
        openrouter_client: Optional[OpenRouterClient] = None
    ):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
        self._openrouter_client = openrouter_client

        self._exit_stack: AsyncExitStack = AsyncExitStack()

    async def connect(self):
        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=self._env,
        )
        stdio_transport = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        stdio_read, stdio_write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(stdio_read, stdio_write, sampling_callback=self._sampling_callback)
        )
        await self._session.initialize()
        
    async def _sampling_callback(
        self, 
        context: RequestContext, 
        params: CreateMessageRequestParams
    ) -> CreateMessageResult:
        """
        Callback that handles sampling requests from the MCP server.
        Uses OpenRouter to call the AI model.
        """
        try:
            print(f"{Fore.YELLOW}🔄 Sampling request received...")
            
            # print("params", params)
            messages = []
            for msg in params.messages:
                # msg is a SamplingMessage with attributes: role, content
                role = msg.role  # 'user' or 'assistant'
                
                if hasattr(msg.content, 'text'):
                    text = msg.content.text
                else:
                    text = str(msg.content)
                
                messages.append({
                    "role": role,
                    "content": text
                })
            
            # print("\nextracted messages:", messages)
            print("calling OpenRouter for sampling...")
            response = await self._openrouter_client.chat(
                messages=messages,
                system=params.systemPrompt,
                temperature=getattr(params, 'temperature', 0.7),
                max_tokens=getattr(params, 'maxTokens', 1000)
            )
            
            print("extracting text from response...")
            
            # Extracts the text from the response
            response_text = self._openrouter_client.text_from_message(response)
            
            print("\nresponse text:", response_text)
            
            print(f"{Fore.GREEN}✅ Sampling completed")
            
            # Returns the result in MCP format
            
            msg_result = CreateMessageResult(
                role="assistant",
                model=self._openrouter_client.model,
                content=TextContent(
                    type="text",
                    text=response_text
                )
            )

            print(f"msg_result: {msg_result}")

            return msg_result
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error during sampling: {e}")
            return CreateMessageResult(
                role="assistant",
                model=self._openrouter_client.model,
                content=TextContent(
                    type="text",
                    text=f"Error during generation: {str(e)}"
                )
            )


    def session(self) -> ClientSession:
        if self._session is None:
            raise ConnectionError(
                "Client session not initialized or cache not populated. Call connect_to_server first."
            )
        return self._session

    async def list_tools(self) -> list[types.Tool]:
        result = await self.session().list_tools()
        return result.tools

    async def call_tool(
        self, tool_name: str, tool_input
    ) -> types.CallToolResult | None:
        return await self.session().call_tool(tool_name, tool_input)

    async def list_prompts(self) -> list[types.Prompt]:
        result = await self.session().list_prompts()
        return result.prompts
    
    async def list_resources(self) -> list[dict]:
        result = await self.session().list_resources()
        return [res.model_dump() for res in result.resources]

    async def get_prompt(self, prompt_name, args: dict[str, str]):
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages

    async def read_resource(self, uri: str) -> Any:
        result = await self.session().read_resource(AnyUrl(uri))
        resource = result.contents[0]
        print(Fore.CYAN + "\n Resource:", resource)

        if isinstance(resource, types.TextResourceContents):
            if resource.mimeType == "application/json":
                print(Fore.CYAN + "\n JSON Resource:", json.loads(resource.text))
                return json.loads(resource.text)
            
            try:
                parsed = json.loads(resource.text)
                print(Fore.CYAN + "\n Parsed as JSON (fallback):", parsed)
                return parsed
            except json.JSONDecodeError:
                print(Fore.CYAN + "\n Text Resource:", resource.text)
                return resource.text


    async def cleanup(self):
        self._session = None
        
        # Close the exit stack that manages all context managers
        await self._exit_stack.aclose()
        
        # On Windows, wait for subprocesses to fully close
        if sys.platform == "win32":
            await asyncio.sleep(0.3)

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

# For testing
async def main():
    async with MCPClient(
        # If using Python without UV, update command to 'python' and remove "run" from args.
        command="uv",
        args=["run", "mcp_server.py"],
    ) as client:
        result = await client.list_tools()
        print(Fore.LIGHTGREEN_EX + "Available tools:", result)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Force close any pending tasks
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No active loop, all good
            pass
        else:
            # If there is still a loop, cancel pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            if pending:
                loop.run_until_complete(asyncio.sleep(0.1))