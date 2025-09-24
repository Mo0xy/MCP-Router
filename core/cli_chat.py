from typing import List, Tuple
from mcp.types import Prompt, PromptMessage
from anthropic.types import MessageParam
from core.chat import Chat  # Usa la versione aggiornata
from mcp_client import MCPClient
from core.openrouter import OpenRouterClient
from colorama import Fore, init

init(autoreset=True)


class CliChat(Chat):
    def __init__(
        self,
        doc_client: MCPClient,
        clients: dict[str, MCPClient],
        openRouterService: OpenRouterClient,
    ):
        super().__init__(openRouter_service=openRouterService, clients=clients)
        self.doc_client: MCPClient = doc_client

    async def list_prompts(self) -> list[Prompt]:
        """Lista i prompt disponibili dal client dei documenti"""
        try:
            return await self.doc_client.list_prompts()
        except Exception as e:
            print(f"{Fore.RED}Error listing prompts: {e}")
            return []

    async def list_docs_ids(self) -> list[str]:
        """Lista gli ID dei documenti disponibili"""
        try:
            return await self.doc_client.read_resource("docs://documents")
        except Exception as e:
            print(f"{Fore.RED}Error listing document IDs: {e}")
            return []

    async def get_doc_content(self, doc_id: str) -> str:
        """Ottiene il contenuto di un documento"""
        try:
            return await self.doc_client.read_resource(f"docs://documents/{doc_id}")
        except Exception as e:
            print(f"{Fore.RED}Error getting document content for {doc_id}: {e}")
            return ""

    async def get_prompt(self, command: str, doc_id: str) -> list[PromptMessage]:
        """Ottiene un prompt con parametri"""
        try:
            return await self.doc_client.get_prompt(command, {"doc_id": doc_id})
        except Exception as e:
            print(f"{Fore.RED}Error getting prompt {command}: {e}")
            return []

    async def _extract_resources(self, query: str) -> str:
        """
        Estrae e carica i contenuti dei documenti menzionati con @
        """
        print(f"{Fore.CYAN}Extracting resources from query: {query}")
        
        # Trova tutte le menzioni di documenti (parole che iniziano con @)
        mentions = [word[1:] for word in query.split() if word.startswith("@")]
        
        if not mentions:
            return ""
        
        print(f"{Fore.CYAN}Found mentions: {mentions}")
        
        try:
            doc_ids = await self.list_docs_ids()
            mentioned_docs: list[Tuple[str, str]] = []
            missing_docs: list[str] = []

            for m in mentions:
                if m in doc_ids:
                    print(f"{Fore.GREEN}Loading document: {m}")
                    content = await self.get_doc_content(m)
                    mentioned_docs.append((m, content))
                else:
                    missing_docs.append(m)

            if missing_docs:
                raise FileNotFoundError(missing_docs)

            resources = "".join(
                f'\n<document id="{doc_id}">\n{content}\n</document>\n'
                for doc_id, content in mentioned_docs
            )
            print(f"{Fore.GREEN}Loaded {len(mentioned_docs)} documents")
            return resources
            
        except Exception as e:
            print(f"{Fore.RED}Error extracting resources: {e}")
            return ""

    async def _process_command(self, query: str) -> bool:
        """
        Processa i comandi che iniziano con /
        """
        if not query.startswith("/"):
            return False

        try:
            words = query.split()
            if len(words) < 2:
                print(f"{Fore.RED}Command requires a document ID")
                return True  # Comando processato ma con errore
            
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
            return True  # Comando processato ma con errore

    async def _process_query(self, query: str):
        """
        Processa la query dell'utente
        """
        # Prova prima a processare come comando
        if await self._process_command(query):
            return

        # Altrimenti processa come query normale con estrazione di risorse
        try:
            added_resources = await self._extract_resources(query)

            if added_resources:
                prompt = f"""
The user has a question:
<query>
{query}
</query>

The following document context is available to help answer their question:
<context>
{added_resources}
</context>

Instructions:
- Answer the user's question directly and concisely using the provided document context
- Start with the exact information they need
- If the user mentions documents with @ (like @report.docx), use the content provided in the context
- Don't refer to or mention the "provided context" - just use the information naturally
- If you need to perform actions on documents (like editing), use the appropriate tools
"""
            else:
                prompt = query

            self.messages.append({"role": "user", "content": prompt})
            
        except Exception as e:
            print(f"{Fore.RED}Error processing query: {e}")
            # Fallback alla query originale
            self.messages.append({"role": "user", "content": query})


def convert_prompt_message_to_message_param(
    prompt_message: PromptMessage,
) -> MessageParam:
    """
    Converte un singolo PromptMessage in MessageParam
    """
    role = "user" if prompt_message.role == "user" else "assistant"
    content = prompt_message.content

    # Gestisci oggetti con tipo text
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

    # Gestisci liste di contenuti
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

    # Fallback per stringhe o altri tipi
    return {"role": role, "content": str(content)}


def convert_prompt_messages_to_message_params(
    prompt_messages: List[PromptMessage],
) -> List[MessageParam]:
    """
    Converte una lista di PromptMessage in MessageParam
    """
    return [
        convert_prompt_message_to_message_param(msg) for msg in prompt_messages
    ]