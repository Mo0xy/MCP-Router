#!/usr/bin/env python3

"""
Script per esplorare la struttura dell'SDK MCP
"""

try:
    import mcp
    print(f"✅ MCP version: {getattr(mcp, '__version__', 'unknown')}")
    print("\n=== MCP main module contents ===")
    for attr in sorted(dir(mcp)):
        if not attr.startswith('_'):
            print(f"  {attr}")
    
    print("\n=== Checking mcp.server ===")
    try:
        import mcp.server
        print("✅ mcp.server found")
        for attr in sorted(dir(mcp.server)):
            if not attr.startswith('_'):
                print(f"  mcp.server.{attr}")
    except ImportError as e:
        print(f"❌ mcp.server not found: {e}")
    
    print("\n=== Checking for FastMCP ===")
    try:
        from mcp.server.fastmcp import FastMCP
        print("✅ Found mcp.server.fastmcp.FastMCP")
    except ImportError:
        print("❌ mcp.server.fastmcp.FastMCP not found")
        try:
            from mcp.server import FastMCP
            print("✅ Found mcp.server.FastMCP")
        except ImportError:
            print("❌ FastMCP not found in mcp.server")
    
    print("\n=== Checking mcp.types ===")
    try:
        import mcp.types
        print("✅ mcp.types found")
        print("Available types:")
        for attr in sorted(dir(mcp.types)):
            if not attr.startswith('_') and attr[0].isupper():  # Probabilmente sono classi
                print(f"  {attr}")
    except ImportError as e:
        print(f"❌ mcp.types not found: {e}")
    
    print("\n=== Looking for prompt-related modules ===")
    import pkgutil
    for importer, modname, ispkg in pkgutil.iter_modules(mcp.__path__, mcp.__name__ + "."):
        print(f"  Found submodule: {modname}")
        if 'prompt' in modname.lower():
            print(f"    ⭐ Prompt-related: {modname}")

except ImportError as e:
    print(f"❌ Error importing mcp: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")