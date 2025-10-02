from typing import List, Tuple
from mcp.types import Prompt, PromptMessage
from anthropic.types import MessageParam
from core.chat import Chat  # Use the updated version
from mcp_client import MCPClient
from core.openrouter import OpenRouterClient
from colorama import Fore, init

init(autoreset=True)


class CliChat(Chat):
    def __init__(
        self,
        mcp_client: MCPClient,
        clients: dict[str, MCPClient],
        openRouterService: OpenRouterClient,
    ):
        super().__init__(openRouter_service=openRouterService, clients=clients)
        self.mcp_client: MCPClient = mcp_client

    async def list_prompts(self) -> list[Prompt]:
        """List available prompts from the document client"""
        try:
            return await self.mcp_client.list_prompts()
        except Exception as e:
            print(f"{Fore.RED}Error listing prompts: {e}")
            return []
        
    async def list_tools(self) -> list[str]:
        """List available tools from the document client"""
        try:
            tools = await self.mcp_client.list_tools()
            return [tool.name for tool in tools]
        except Exception as e:
            print(f"{Fore.RED}Error listing tools: {e}")
            return []
        
    async def list_resources(self) -> list[dict]:
        """List available resources"""
        try:
            return await self.mcp_client.list_resources()
        except Exception as e:
            print(f"{Fore.RED}Error listing resources: {e}")
            return []

    async def get_prompt(self, command: str, doc_id: str) -> list[PromptMessage]:
        """Get a prompt with parameters"""
        try:
            return await self.mcp_client.get_prompt(command, {"doc_id": doc_id})
        except Exception as e:
            print(f"{Fore.RED}Error getting prompt {command}: {e}")
            return []

    async def _extract_resources(self, query: str) -> str:
        """
        Extracts and loads the contents of resources mentioned with @ (not just documents)
        """
        print(f"{Fore.CYAN}Extracting resources from query: {query}")

        # Find all resource mentions (words starting with @)
        mentions = [word[1:] for word in query.split() if word.startswith("@")]

        if not mentions:
            return ""

        print(f"{Fore.CYAN}Found mentions: {mentions}")

        try:
            resources_list = await self.list_resources()
            # Create an id->resource map for fast lookup
            resource_map = {res.get("id", ""): res for res in resources_list}
            mentioned_resources: list[Tuple[str, str, str]] = []
            missing_resources: list[str] = []

            for m in mentions:
                resource = resource_map.get(m)
                if resource:
                    resource_type = resource.get("type", "unknown")
                    print(f"{Fore.GREEN}Loading resource: {m} (type: {resource_type})")
                    # Try to read the resource content
                    try:
                        content = await self.mcp_client.read_resource(resource.get("uri", m))
                    except Exception as e:
                        print(f"{Fore.YELLOW}Error loading resource {m}: {e}")
                        content = ""
                    mentioned_resources.append((m, resource_type, content))
                else:
                    missing_resources.append(m)

            if missing_resources:
                raise FileNotFoundError(missing_resources)

            resources = "".join(
                f'\n<resource id="{res_id}" type="{res_type}">\n{content}\n</resource>\n'
                for res_id, res_type, content in mentioned_resources
            )
            print(f"{Fore.GREEN}Loaded {len(mentioned_resources)} resources")
            return resources

        except Exception as e:
            print(f"{Fore.RED}Error extracting resources: {e}")
            return ""

    async def _process_command(self, query: str) -> bool:
        """
        Processes commands that start with /
        """
        if not query.startswith("/"):
            return False

        try:
            words = query.split()
            if len(words) < 2:
                print(f"{Fore.RED}Command requires a document ID")
                return True  # Command processed but with error
            
            command = words[0].replace("/", "")
            doc_id = words[1]
            
            print(f"{Fore.CYAN}Processing command: {command} with doc_id: {doc_id}")

            messages = await self.get_prompt(command, doc_id)
            
            if messages:
                converted_messages = convert_prompt_messages_to_message_params(messages)
                self.messages.extend(converted_messages)
                print(f"{Fore.GREEN}Added {len(converted_messages)} prompt messages")
            else:
                print(f"{Fore.YELLOW}No messages returned from prompt {command}")
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Error processing command: {e}")
            return True  # Command processed but with error

    async def _process_query(self, query: str):
        """
        Processes the user's query
        """
        # First try to process as a command
        if await self._process_command(query):
            return

        # Otherwise process as a normal query with resource extraction
        try:
            added_resources = await self._extract_resources(query)

            if added_resources:
                prompt = f"""
The user has a question:
<query>
{query}
</query>

The following resource context is available to help answer their question:
<context>
{added_resources}
</context>

Instructions:
- Answer the user's question directly and concisely using the provided resource context
- Start with the exact information they need
- If the user mentions resources with @ (like @report.docx), use the content provided in the context
- Don't refer to or mention the "provided context" - just use the information naturally
- If you need to perform actions on resources (like editing), use the appropriate tools
"""
            else:
                prompt = query

            self.messages.append({"role": "user", "content": prompt})
            
        except Exception as e:
            print(f"{Fore.RED}Error processing query: {e}")
            # Fallback to the original query
            self.messages.append({"role": "user", "content": query})


def convert_prompt_message_to_message_param(
    prompt_message: PromptMessage,
) -> MessageParam:
    """
    Converts a single PromptMessage to MessageParam
    """
    role = "user" if prompt_message.role == "user" else "assistant"
    content = prompt_message.content

    # Handle objects with type text
    if isinstance(content, dict) or hasattr(content, "__dict__"):
        content_type = (
            content.get("type", None)
            if isinstance(content, dict)
            else getattr(content, "type", None)
        )
        if content_type == "text":
            content_text = (
                content.get("text", "")
                if isinstance(content, dict)
                else getattr(content, "text", "")
            )
            return {"role": role, "content": content_text}

    # Handle lists of content
    if isinstance(content, list):
        text_blocks = []
        for item in content:
            if isinstance(item, dict) or hasattr(item, "__dict__"):
                item_type = (
                    item.get("type", None)
                    if isinstance(item, dict)
                    else getattr(item, "type", None)
                )
                if item_type == "text":
                    item_text = (
                        item.get("text", "")
                        if isinstance(item, dict)
                        else getattr(item, "text", "")
                    )
                    text_blocks.append({"type": "text", "text": item_text})

        if text_blocks:
            return {"role": role, "content": text_blocks}

    # Fallback for strings or other types
    return {"role": role, "content": str(content)}


def convert_prompt_messages_to_message_params(
    prompt_messages: List[PromptMessage],
) -> List[MessageParam]:
    """
    Converts a list of PromptMessage to MessageParam
    """
    return [
        convert_prompt_message_to_message_param(msg) for msg in prompt_messages
    ]