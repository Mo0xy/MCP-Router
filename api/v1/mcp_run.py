import os
import sys
import asyncio
from contextlib import AsyncExitStack
import traceback
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

from mcp_client import MCPClient
from core.cli_chat import CliChat
from core.openrouter import OpenRouterClient

# Logging configuration for debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_env():
    load_dotenv()
    model = os.getenv("MODEL", "")
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "")

    assert model, "Error: model cannot be empty. Update .env"
    assert openrouter_api_key, "Error: OPENROUTER_API_KEY cannot be empty. Update .env"

    return model, openrouter_api_key

# original async version
async def run_mcp_async(prompt: str) -> str:
    model, _ = init_env()
    openrouter_service = OpenRouterClient(model=model)

    command, args = (
        ("uv", ["run", "mcp_server.py"])
        if os.getenv("USE_UV", "0") == "1"
        else ("python", ["mcp_server.py"])
    )

    async with AsyncExitStack() as stack:
        try:
            doc_client = await stack.enter_async_context(
                MCPClient(command=command, args=args)
            )
        except Exception as e:
            logger.error(f"Exception occurred: {e}")
            print("Exception occurred:", e, file=sys.stderr)
            
            # Writes and overwrites the file every time
            with open("logs/error_log.txt", "w", encoding="utf-8") as f:
                f.write("Exception occurred:\n")
                f.write(traceback.format_exc())
            
            return str(e)

        clients = {"doc_client": doc_client}

        chat = CliChat(
            doc_client=doc_client,
            clients=clients,
            openRouterService=openrouter_service,
        )

        response = await chat.run(prompt)
        return response

# SOLUTION 1: Run in a new loop in a separate thread
def run_mcp_in_new_thread(prompt: str) -> str:
    """
    Runs MCP in a separate thread with a new asyncio loop.
    This avoids conflicts with the uvicorn/FastAPI loop.
    """
    def thread_target():
        # Force new asyncio loop on Windows
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # Create new loop for this thread
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        
        try:
            return new_loop.run_until_complete(run_mcp_async(prompt))
        except Exception as e:
            logger.error(f"Error in thread: {e}")
            with open("error_log.txt", "w", encoding="utf-8") as f:
                f.write("Exception occurred in thread:\n")
                f.write(traceback.format_exc())
            return f"Error: {str(e)}"
        finally:
            new_loop.close()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(thread_target)
        return future.result(timeout=60)

# SOLUTION 2: Async version for FastAPI with correct loop handling
async def run_mcp_async_for_fastapi(prompt: str) -> str:
    """
    Async version that should work with FastAPI.
    Uses asyncio.create_subprocess_exec instead of AnyIO to avoid conflicts.
    """
    try:
        model, _ = init_env()
        openrouter_service = OpenRouterClient(model=model)

        # Start the MCP server in a separate subprocess
        command = "uv" if os.getenv("USE_UV", "0") == "1" else "python"
        args = ["run", "mcp_server.py"] if command == "uv" else ["mcp_server.py"]
        
        # Use asyncio.create_subprocess_exec instead of AnyIO
        process = await asyncio.create_subprocess_exec(
            command, *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Simulate MCP connection - this is a simplified example
        # In reality, you should adapt MCPClient to use asyncio.subprocess
        
        # For now, use the thread-based solution
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: run_mcp_in_new_thread(prompt)
        )
        
    except Exception as e:
        logger.error(f"Error in async FastAPI version: {e}")
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write("Exception occurred in FastAPI async:\n")
            f.write(traceback.format_exc())
        return f"Error: {str(e)}"

# SYNCHRONOUS version to use in FastAPI - UPDATED
def run_mcp(prompt: str) -> str:
    """
    Synchronous version for FastAPI that uses a separate thread to avoid conflicts.
    """
    try:
        return run_mcp_in_new_thread(prompt)
    except Exception as e:
        logger.error(f"Error in run_mcp: {e}")
        with open("error_log.txt", "w", encoding="utf-8") as f:
            f.write("Exception occurred:\n")
            f.write(traceback.format_exc())
        return f"Error starting MCPClient: {str(e)}"

# ALTERNATIVE SOLUTION: Use asyncio.run_coroutine_threadsafe
def run_mcp_with_thread_safe(prompt: str) -> str:
    """
    Alternative that uses run_coroutine_threadsafe to run
    the coroutine in a thread with a dedicated loop.
    """
    def target():
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            return loop.run_until_complete(run_mcp_async(prompt))
        finally:
            loop.close()
    
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(target)
        return future.result(timeout=60)