import json
import asyncio
from typing import Optional, List, Dict, Any
from mcp.types import Tool
from mcp_client import MCPClient
from colorama import Fore, init

init(autoreset=True)


class ToolManager:
    """
    Tool Manager semplificato che evita le complessità di conversione
    e si concentra sulla robustezza dell'esecuzione
    """
    
    @classmethod
    async def get_all_tools(cls, clients: Dict[str, MCPClient]) -> List[Dict[str, Any]]:
        """Ottiene tutti i tool dai client MCP"""
        tools = []
        
        for client_name, client in clients.items():
            try:
                print(f"{Fore.CYAN}Getting tools from client: {client_name}")
                tool_models = await asyncio.wait_for(client.list_tools(), timeout=10.0)
                
                for tool in tool_models:
                    tool_dict = {
                        "name": tool.name,
                        "description": tool.description or f"Tool {tool.name}",
                        "input_schema": tool.inputSchema or {"type": "object", "properties": {}}
                    }
                    tools.append(tool_dict)
                    print(f"{Fore.GREEN}Added tool: {tool.name}")
                    
            except asyncio.TimeoutError:
                print(f"{Fore.RED}Timeout getting tools from {client_name}")
            except Exception as e:
                print(f"{Fore.RED}Error getting tools from {client_name}: {e}")
                
        print(f"{Fore.CYAN}Total tools available: {len(tools)}")
        return tools

    @classmethod
    async def find_client_for_tool(cls, clients: Dict[str, MCPClient], tool_name: str) -> Optional[MCPClient]:
        """Trova il client che contiene il tool specificato"""
        for client_name, client in clients.items():
            try:
                tools = await asyncio.wait_for(client.list_tools(), timeout=5.0)
                if any(tool.name == tool_name for tool in tools):
                    print(f"{Fore.GREEN}Found tool '{tool_name}' in client '{client_name}'")
                    return client
            except Exception as e:
                print(f"{Fore.YELLOW}Could not check tools in {client_name}: {e}")
                continue
        
        print(f"{Fore.RED}Tool '{tool_name}' not found in any client")
        return None

    @classmethod
    async def execute_single_tool(
        cls, 
        client: MCPClient, 
        tool_name: str, 
        tool_input: Dict[str, Any], 
        timeout_seconds: float = 25.0
    ) -> Dict[str, Any]:
        """
        Esegue un singolo tool e restituisce il risultato in formato standard
        """
        try:
            print(f"{Fore.CYAN}Executing tool '{tool_name}' with timeout {timeout_seconds}s")
            print(f"{Fore.CYAN}Input: {tool_input}")
            
            # Esegui il tool con timeout
            result = await asyncio.wait_for(
                client.call_tool(tool_name, tool_input), 
                timeout=timeout_seconds
            )
            
            # Processa il risultato
            if result is None:
                return {
                    "success": False,
                    "content": f"Tool '{tool_name}' returned no result",
                    "error": "No result returned"
                }
            
            # Estrai il contenuto dal risultato
            content = ""
            if hasattr(result, 'content') and result.content:
                content_parts = []
                for item in result.content:
                    if hasattr(item, 'text'):
                        content_parts.append(item.text)
                content = "\n".join(content_parts)
            
            # Se non c'è contenuto, usa la rappresentazione string dell'oggetto
            if not content:
                content = str(result)
            
            # Determina se c'è un errore
            is_error = False
            if hasattr(result, 'isError'):
                is_error = result.isError
            
            success = not is_error
            
            print(f"{Fore.GREEN}Tool '{tool_name}' executed successfully")
            print(f"{Fore.GREEN}Result: {content[:100]}...")  # Prime 100 caratteri
            
            return {
                "success": success,
                "content": content,
                "error": None if success else "Tool reported an error"
            }
            
        except asyncio.TimeoutError:
            error_msg = f"Tool '{tool_name}' timed out after {timeout_seconds} seconds"
            print(f"{Fore.RED}ERROR: {error_msg}")
            return {
                "success": False,
                "content": "",
                "error": error_msg
            }
            
        except Exception as e:
            error_msg = f"Tool '{tool_name}' failed: {str(e)}"
            print(f"{Fore.RED}ERROR: {error_msg}")
            return {
                "success": False,
                "content": "",
                "error": error_msg
            }

    @classmethod
    def get_timeout_for_tool(cls, tool_name: str) -> float:
        """Restituisce un timeout appropriato basato sul tipo di tool"""
        timeout_map = {
            # Tool di lettura - veloci
            "read_doc": 10.0,
            "get_doc_content": 10.0,
            "list_docs": 10.0,
            "server_status": 10.0,
            
            # Tool di modifica - medi
            "edit_doc": 20.0,
            
            # Tool complessi - lunghi
            "duplicate_doc": 30.0,
            
            # Tool di ricerca/analisi - molto lunghi
            "search": 45.0,
            "analyze": 60.0,
        }
        
        return timeout_map.get(tool_name, 25.0)  # Default 25 secondi

    @classmethod
    async def execute_tools_from_response(
        cls, 
        clients: Dict[str, MCPClient], 
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Esegue una lista di tool calls e restituisce i risultati
        
        Args:
            clients: Dizionario dei client MCP
            tool_calls: Lista di dict con format {"id": str, "name": str, "input": dict}
            
        Returns:
            Lista di risultati in formato standardizzato per OpenRouter
        """
        results = []
        
        print(f"{Fore.MAGENTA}Executing {len(tool_calls)} tool(s)")
        
        for i, tool_call in enumerate(tool_calls):
            tool_id = tool_call.get("id", f"tool_{i}")
            tool_name = tool_call.get("name", "unknown")
            tool_input = tool_call.get("input", {})
            
            print(f"{Fore.YELLOW}Tool {i+1}/{len(tool_calls)}: {tool_name} (ID: {tool_id})")
            
            # Trova il client appropriato
            client = await cls.find_client_for_tool(clients, tool_name)
            
            if not client:
                result = {
                    "tool_use_id": tool_id,
                    "type": "tool_result",
                    "content": json.dumps({
                        "error": f"Tool '{tool_name}' not found",
                        "available_tools": list(clients.keys())
                    }),
                    "is_error": True
                }
                results.append(result)
                continue
            
            # Esegui il tool
            timeout = cls.get_timeout_for_tool(tool_name)
            execution_result = await cls.execute_single_tool(
                client, tool_name, tool_input, timeout
            )
            
            # Converti nel formato richiesto da OpenRouter
            result = {
                "tool_use_id": tool_id,
                "type": "tool_result",
                "content": execution_result["content"] if execution_result["success"] else json.dumps({
                    "error": execution_result["error"],
                    "tool_name": tool_name
                }),
                "is_error": not execution_result["success"]
            }
            
            results.append(result)
            
            # Piccola pausa tra i tool per evitare sovraccarico
            if i < len(tool_calls) - 1:
                await asyncio.sleep(0.1)
        
        print(f"{Fore.GREEN}Completed execution of {len(results)} tool(s)")
        return results

    @classmethod
    async def test_connection(cls, clients: Dict[str, MCPClient]) -> Dict[str, bool]:
        """
        Testa la connettività di tutti i client
        """
        results = {}
        
        for client_name, client in clients.items():
            try:
                print(f"{Fore.CYAN}Testing connection to {client_name}...")
                tools = await asyncio.wait_for(client.list_tools(), timeout=5.0)
                results[client_name] = True
                print(f"{Fore.GREEN}{client_name}: OK ({len(tools)} tools)")
            except Exception as e:
                results[client_name] = False
                print(f"{Fore.RED}{client_name}: FAILED - {e}")
        
        return results