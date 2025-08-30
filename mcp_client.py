import sys
import asyncio
import warnings
import logging
from typing import Optional, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import json
from pydantic import AnyUrl
from colorama import Fore, Style, init

init(autoreset=True)

class MCPClient:
    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict] = None,
    ):
        self._command = command
        self._args = args
        self._env = env
        self._session: Optional[ClientSession] = None
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
        # CORREZIONE: sintassi corretta per lo spacchettamento
        stdio_read, stdio_write = stdio_transport
        self._session = await self._exit_stack.enter_async_context(
            ClientSession(stdio_read, stdio_write)
        )
        await self._session.initialize()

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

    async def get_prompt(self, prompt_name, args: dict[str, str]):
        result = await self.session().get_prompt(prompt_name, args)
        return result.messages

    async def read_resource(self, uri: str) -> Any:
        result = await self.session().read_resource(AnyUrl(uri))
        resource = result.contents[0]
        print(Fore.CYAN + "\n Resource:", resource)

        if isinstance(resource, types.TextResourceContents):
            # Caso JSON
            if resource.mimeType == "application/json":
                print(Fore.CYAN + "\n JSON Resource:", json.loads(resource.text))
                return json.loads(resource.text)
            
            # Caso testo semplice
            try:
                # Se per caso è un JSON valido ma senza mimeType
                parsed = json.loads(resource.text)
                print(Fore.CYAN + "\n Parsed as JSON (fallback):", parsed)
                return parsed
            except json.JSONDecodeError:
                # Altrimenti è testo normale
                print(Fore.CYAN + "\n Text Resource:", resource.text)
                return resource.text


    async def cleanup(self):
        self._session = None
        
        # Chiudi l'exit stack che gestisce tutti i context manager
        await self._exit_stack.aclose()
        
        # Su Windows, aspetta che i subprocess si chiudano completamente
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
        print("\nInterrotto dall'utente")
    finally:
        # Forza la chiusura di eventuali task pending
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Nessun loop attivo, tutto ok
            pass
        else:
            # Se c'è ancora un loop, cancella i task pending
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            
            # Aspetta un momento per la pulizia
            if pending:
                loop.run_until_complete(asyncio.sleep(0.1))