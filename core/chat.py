import asyncio
from typing import List, Dict, Any
from core.openrouter import OpenRouterClient, OpenRouterMessage
from mcp_client import MCPClient
from core.tools import ToolManager  # Usa il nostro tool manager semplificato
from anthropic.types import MessageParam
from colorama import Fore, Style, init

init(autoreset=True)


class Chat:
    def __init__(self, openRouter_service: OpenRouterClient, clients: dict[str, MCPClient]):
        self.openRouter_service: OpenRouterClient = openRouter_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[MessageParam] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(self, query: str) -> str:
        final_text_response = ""
        max_iterations = 5  # Previene loop infiniti
        iteration = 0

        await self._process_query(query)

        while iteration < max_iterations:
            iteration += 1
            print(f"{Fore.CYAN}Iteration {iteration}/{max_iterations}")

            try:
                # Ottieni i tool disponibili
                available_tools = await ToolManager.get_all_tools(self.clients)
                print(f"{Fore.CYAN}Available tools: {[t['name'] for t in available_tools]}")

                # Usa il metodo con retry per maggiore robustezza
                response = await self.openRouter_service.chat_with_retry(
                    messages=self.messages,
                    tools=available_tools,
                    max_tokens=1000,
                    temperature=0.4,
                    max_retries=2
                )

                # DEBUG: Aggiungi subito qui
                print(f"{Fore.RED}=== ITERATION {iteration} DEBUG ===")
                print(f"{Fore.RED}Response received: {response is not None}")
                print(f"{Fore.RED}Stop reason: {response.stop_reason if response else 'None'}")
                print(f"{Fore.RED}Content blocks: {len(response.content) if response else 0}")

                # Aggiungi la risposta dell'assistant
                self.openRouter_service.add_assistant_message(self.messages, response)

                # Estrai il testo della risposta se presente
                text_response = self.openRouter_service.text_from_message(response)
                if text_response.strip():
                    print(f"{Fore.LIGHTBLUE_EX}Assistant: {text_response}")

                if response.stop_reason == "tool_use":
                    print(f"{Fore.MAGENTA}Tool use detected, executing tools...")
                    print(f"{Fore.MAGENTA}Stop reason: {response.stop_reason}")
                    print(f"{Fore.MAGENTA}Text response: '{text_response}'")
                    print(f"{Fore.MAGENTA}Should break: {response.stop_reason != 'tool_use'}")

                    # Estrai i tool calls dal response
                    tool_calls = []
                    for block in response.content:
                        if block.get("type") == "tool_use":
                            tool_calls.append({
                                "id": block.get("id", ""),
                                "name": block.get("name", ""),
                                "input": block.get("input", {})
                            })

                    if tool_calls:
                        # Esegui i tool con il nostro manager semplificato
                        tool_results = await ToolManager.execute_tools_from_response(
                            self.clients, tool_calls
                        )

                        print(f"{Fore.GREEN}Tools executed: {len(tool_results)} results")

                        # Aggiungi i risultati dei tool ai messaggi
                        self.openRouter_service.add_user_message(self.messages, tool_results)
                    else:
                        print(f"{Fore.YELLOW}No tool calls found in response")
                        break

                else:
                    # Fine della conversazione
                    final_text_response = text_response
                    break

            except Exception as e:
                error_msg = f"Error in iteration {iteration}: {str(e)}"
                print(f"{Fore.RED}ERROR: {error_msg}")

                if iteration >= max_iterations:
                    final_text_response = f"Sorry, I encountered an error: {error_msg}"
                    break
                else:
                    # Prova ancora una volta
                    print(f"{Fore.YELLOW}Retrying after error...")
                    await asyncio.sleep(2)
                    continue

        if iteration >= max_iterations and not final_text_response:
            final_text_response = (
                "Conversation reached maximum iterations. "
                "Please try again with a simpler request."
            )

        return final_text_response or "I apologize, but I couldn't generate a response."


# class MockToolUse:
#     """Mock class per simulare tool_use di Anthropic"""
#     def __init__(self, id: str, name: str, input: dict):
#         self.type = "tool_use"
#         self.id = id
#         self.name = name
#         self.input = input
