#!/usr/bin/env python3
"""
MCP Router - Main entry point
"""
import asyncio
import sys
import os
from dotenv import load_dotenv
from typing import Dict
from core.cli import CliApp  
from core.cli_chat import CliChat
from core.openrouter import OpenRouterClient
from mcp_client import MCPClient
from core.tools import ToolManager
from contextlib import AsyncExitStack
from mcp_client import MCPClient
from core.cli_chat import CliChat
from core.cli import CliApp
from core.openrouter import OpenRouterClient
from core.openrouter import warmup_model
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)
load_dotenv()
async def test_system_health(clients: Dict[str, MCPClient], openrouter_client: OpenRouterClient):
    """Test the health of all system components"""
    print(f"{Fore.CYAN}=== System Health Check ===")
    
    # Test OpenRouter connection
    try:
        test_messages = [{"role": "user", "content": "Hello"}]
        response = await openrouter_client.chat(test_messages, max_tokens=10)
        print(f"{Fore.GREEN}✓ OpenRouter: Connected")
    except Exception as e:
        print(f"{Fore.RED}✗ OpenRouter: Failed - {e}")
        return False
    
    # Test MCP clients
    health_results = await ToolManager.test_connection(clients)
    all_healthy = all(health_results.values())
    
    if all_healthy:
        print(f"{Fore.GREEN}✓ All systems healthy")
        return True
    else:
        print(f"{Fore.YELLOW}⚠ Some clients have issues")
        return False

async def main():
    """Main entry point"""
    print(f"{Fore.LIGHTCYAN_EX}Starting MCP Router v3...")
    
    # Get OpenRouter API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print(f"{Fore.RED}ERROR: OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)
    
    # Initialize OpenRouter client with improved settings
    model = os.getenv("MODEL", "mistralai/mistral-7b-instruct")
    print(f"{Fore.CYAN}Using OpenRouter model: {model}")
    print(f"{Fore.CYAN}Using OpenRouter API key: {api_key[:20]}...")
    
    openrouter_client = OpenRouterClient(
        model=model, 
        api_key=api_key,
        default_timeout=120.0
    )
    
    await warmup_model(openrouter_client)
    
    # Initialize MCP clients
    clients = {}
    
    try:
        # Document client
        print(f"{Fore.CYAN}Initializing document MCP client...")
        hr_client = MCPClient(
            command="uv",
            args=["run", "mcp_server.py"],
            openrouter_client=openrouter_client
        )
        await hr_client.connect()
        clients["human_resources"] = hr_client
        print(f"{Fore.GREEN}✓ Human Resources client connected")
        
        # Test system health
        if await test_system_health(clients, openrouter_client):
            print(f"{Fore.GREEN}✓ System health check passed")
        else:
            print(f"{Fore.YELLOW}⚠ System health check had warnings")
        
        # Initialize CLI chat
        cli_chat = CliChat(
            mcp_client=hr_client,
            clients=clients,
            openRouterService=openrouter_client
        )
        
        # Initialize and run CLI app
        cli_app = CliApp(cli_chat)
        await cli_app.initialize()
        
        print(f"{Fore.LIGHTGREEN_EX}✓ MCP Router initialized successfully")
        print(f"{Fore.LIGHTGREEN_EX}Available commands:")
        print(f"{Fore.LIGHTGREEN_EX}  - Use @ to reference documents (e.g., @report.pdf)")
        print(f"{Fore.LIGHTGREEN_EX}  - Use / for prompts (e.g., /summarize)")
        print(f"{Fore.LIGHTGREEN_EX}  - Ctrl+C to exit")
        print(f"{Fore.LIGHTGREEN_EX}=================================")
        
        await cli_app.run()
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Shutting down...")
    except Exception as e:
        print(f"{Fore.RED}ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        print(f"{Fore.CYAN}Cleaning up...")
        for client in clients.values():
            try:
                await client.cleanup()
            except Exception as e:
                print(f"{Fore.YELLOW}Warning during cleanup: {e}")
        print(f"{Fore.GREEN}✓ Cleanup completed")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    asyncio.run(main())