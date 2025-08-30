from core.openrouter import OpenRouterClient
from mcp_client import MCPClient
from core.tools import ToolManager
from anthropic.types import MessageParam
from colorama import Fore, Style, init

init(autoreset=True) 

# from openrouter import OpenRouterClient


class Chat:
    def __init__(self, openRouter_service: OpenRouterClient, clients: dict[str, MCPClient]):
        self.openRouter_service: OpenRouterClient = openRouter_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[MessageParam] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(
        self,
        query: str,
    ) -> str:
        final_text_response = ""

        await self._process_query(query)

        while True:
            response = await self.openRouter_service.chat(
                messages=self.messages,
                tools=await ToolManager.get_all_tools(self.clients),
            )

            self.openRouter_service.add_assistant_message(self.messages, response)

            if response.stop_reason == "tool_use":
                print(self.openRouter_service.text_from_message(response))
                tool_result_parts = await ToolManager.execute_tool_requests(
                    self.clients, response
                )
                print(Fore.LIGHTGREEN_EX + "using tools:", tool_result_parts)

                self.openRouter_service.add_user_message(
                    self.messages, tool_result_parts
                )
            else:
                final_text_response = self.openRouter_service.text_from_message(
                    response
                )
                break

        return final_text_response
