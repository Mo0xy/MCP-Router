import os
import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass


@dataclass
class OpenRouterMessage:
    """Struttura per rappresentare un messaggio compatibile con l'interfaccia Claude"""
    content: List[Dict[str, Any]]
    stop_reason: Optional[str] = None

    def __post_init__(self):
        # Assicurati che content sia sempre una lista
        if isinstance(self.content, str):
            self.content = [{"type": "text", "text": self.content}]
        elif isinstance(self.content, list) and len(self.content) > 0:
            # Se il primo elemento è una stringa, convertilo nel formato corretto
            if isinstance(self.content[0], str):
                self.content = [{"type": "text", "text": self.content[0]}]


class OpenRouterClient:
    """
    Client per OpenRouter che mantiene la compatibilità con l'interfaccia Claude
    """
    
    def __init__(self, model: str, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        
        if not self.api_key:
            raise ValueError("OpenRouter API key is required. Set OPENROUTER_API_KEY environment variable or pass it directly.")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def add_user_message(self, messages: List[Dict], message: Union[str, OpenRouterMessage, Dict]):
        """Aggiunge un messaggio utente alla lista dei messaggi"""
        if isinstance(message, OpenRouterMessage):
            # Estrai il testo dal messaggio OpenRouter
            content = self._extract_text_from_content(message.content)
        elif isinstance(message, dict):
            content = message.get("content", "")
            if isinstance(content, list):
                content = self._extract_text_from_content(content)
        else:
            content = str(message)
        
        user_message = {
            "role": "user",
            "content": content
        }
        messages.append(user_message)

    def add_assistant_message(self, messages: List[Dict], message: Union[str, OpenRouterMessage, Dict]):
        """Aggiunge un messaggio assistant alla lista dei messaggi"""
        if isinstance(message, OpenRouterMessage):
            content = self._extract_text_from_content(message.content)
        elif isinstance(message, dict):
            content = message.get("content", "")
            if isinstance(content, list):
                content = self._extract_text_from_content(content)
        else:
            content = str(message)
        
        assistant_message = {
            "role": "assistant",
            "content": content
        }
        messages.append(assistant_message)

    def text_from_message(self, message: OpenRouterMessage) -> str:
        """Estrae il testo da un messaggio OpenRouter"""
        return self._extract_text_from_content(message.content)

    def _extract_text_from_content(self, content: List[Dict[str, Any]]) -> str:
        """Estrae il testo da una lista di blocchi di contenuto"""
        text_blocks = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_blocks.append(block.get("text", ""))
            elif isinstance(block, dict) and "text" in block:
                text_blocks.append(block["text"])
            elif isinstance(block, str):
                text_blocks.append(block)
        return "\n".join(text_blocks)

    def _convert_messages_to_openrouter_format(self, messages: List[Dict]) -> List[Dict]:
        """Converte i messaggi nel formato OpenRouter"""
        openrouter_messages = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Se il contenuto è una lista di blocchi (formato Claude), estrailo
            if isinstance(content, list):
                content = self._extract_text_from_content(content)
            
            openrouter_messages.append({
                "role": role,
                "content": str(content)
            })
        
        return openrouter_messages

    async def chat(
        self,
        messages: List[Dict],
        system: Optional[str] = None,
        temperature: float = 0.4,
        stop_sequences: List[str] = None,
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        thinking_budget: int = 400,
        max_tokens: int = 500
    ) -> OpenRouterMessage:
        """
        Effettua una richiesta chat a OpenRouter
        
        Args:
            messages: Lista di messaggi nel formato Claude
            system: Messaggio di sistema (opzionale)
            temperature: Temperatura per la generazione (0.0-2.0)
            stop_sequences: Sequenze di stop (non sempre supportate)
            tools: Strumenti disponibili (convertiti in function calling se supportato)
            thinking: Flag per il thinking (ignorato, non supportato da OpenRouter)
            thinking_budget: Budget per il thinking (ignorato)
            max_tokens: Numero massimo di token da generare
        
        Returns:
            OpenRouterMessage: Messaggio di risposta
        """
        try:
            # Converte i messaggi nel formato OpenRouter
            openrouter_messages = self._convert_messages_to_openrouter_format(messages)
            
            # Aggiunge il messaggio di sistema se presente
            if system:
                openrouter_messages.insert(0, {
                    "role": "system",
                    "content": system
                })
            
            # Prepara il payload per OpenRouter
            payload = {
                "model": self.model,
                "messages": openrouter_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            # Aggiunge stop sequences se supportate
            if stop_sequences:
                payload["stop"] = stop_sequences
            
            # Aggiunge tools se supportati (function calling)
            if tools:
                payload["tools"] = self._convert_tools_to_openrouter_format(tools)
            
            # Effettua la richiesta
            async with httpx.AsyncClient(verify=False, timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
            
            response.raise_for_status()
            
            # Processa la risposta
            response_data = response.json()
            
            if "choices" not in response_data or not response_data["choices"]:
                raise Exception("No choices in response")
            
            choice = response_data["choices"][0]
            message_content = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason", "stop")
            
            # Mappa il finish_reason al formato Claude
            stop_reason_mapping = {
                "stop": "end_turn",
                "length": "max_tokens",
                "tool_calls": "tool_use",
                "function_call": "tool_use"
            }
            
            stop_reason = stop_reason_mapping.get(finish_reason, finish_reason)
            
            # Gestisce tool calls se presenti
            if "tool_calls" in choice.get("message", {}):
                tool_calls = choice["message"]["tool_calls"]
                content = []
                
                # Aggiunge il testo se presente
                if message_content:
                    content.append({"type": "text", "text": message_content})
                
                # Aggiunge i tool calls
                for tool_call in tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tool_call.get("id", ""),
                        "name": tool_call.get("function", {}).get("name", ""),
                        "input": json.loads(tool_call.get("function", {}).get("arguments", "{}"))
                    })
                
                return OpenRouterMessage(content=content, stop_reason=stop_reason)
            
            # Risposta normale
            return OpenRouterMessage(
                content=[{"type": "text", "text": message_content}],
                stop_reason=stop_reason
            )
            
        except httpx.TimeoutException as e:
            raise Exception(f"Request timeout: {e}")
        except httpx.ConnectError as e:
            raise Exception(f"Connection error: {e}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except json.JSONDecodeError as e:
            raise Exception(f"JSON decode error: {e}")
        except Exception as e:
            raise Exception(f"OpenRouter API error: {e}")

    def _convert_tools_to_openrouter_format(self, tools: List[Dict]) -> List[Dict]:
        """Converte i tools dal formato Claude al formato OpenRouter"""
        openrouter_tools = []
        
        for tool in tools:
            openrouter_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {})
                }
            }
            openrouter_tools.append(openrouter_tool)
        
        return openrouter_tools

    # Metodi sincroni wrapper per compatibilità con codice esistente
    def chat_sync(self, *args, **kwargs) -> OpenRouterMessage:
        """Wrapper sincrono per il metodo chat asincrono"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.chat(*args, **kwargs))


# Esempio di utilizzo
async def example_usage_async():
    """Esempio di utilizzo asincrono della classe OpenRouterClient"""
    
    # Inizializza il client (assicurati di avere OPENROUTER_API_KEY nell'ambiente)
    client = OpenRouterClient(model="mistralai/mistral-7b-instruct")
    
    # Crea una lista di messaggi
    messages = []
    
    # Aggiungi un messaggio utente
    client.add_user_message(messages, "Ciao!")
    
    try:
        # Effettua la richiesta
        response = await client.chat(
            messages=messages,
            temperature=0.4,
            max_tokens=150
        )
        
        # Estrai e stampa la risposta
        response_text = client.text_from_message(response)
        print(f"Risposta: {response_text}")
        
        # Aggiungi la risposta ai messaggi per continuare la conversazione
        client.add_assistant_message(messages, response)
        
        # Aggiungi un altro messaggio utente
        client.add_user_message(messages, "Puoi dirmi qualcosa di interessante?")
        
        # Nuova richiesta
        response2 = await client.chat(
            messages=messages,
            temperature=0.4,
            max_tokens=200
        )
        
        response2_text = client.text_from_message(response2)
        print(f"Risposta 2: {response2_text}")
        
    except Exception as e:
        print(f"Errore: {e}")


def example_usage_sync():
    """Esempio di utilizzo sincrono della classe OpenRouterClient"""
    
    # Inizializza il client (assicurati di avere OPENROUTER_API_KEY nell'ambiente)
    client = OpenRouterClient(model="mistralai/mistral-7b-instruct")
    
    # Crea una lista di messaggi
    messages = []
    
    # Aggiungi un messaggio utente
    client.add_user_message(messages, "Ciao! Come stai?")
    
    try:
        # Effettua la richiesta usando il wrapper sincrono
        response = client.chat_sync(
            messages=messages,
            temperature=0.4,
            max_tokens=150
        )
        
        # Estrai e stampa la risposta
        response_text = client.text_from_message(response)
        print(f"Risposta: {response_text}")
        
        # Aggiungi la risposta ai messaggi per continuare la conversazione
        client.add_assistant_message(messages, response)
        
        # Aggiungi un altro messaggio utente
        client.add_user_message(messages, "Puoi dirmi qualcosa di interessante?")
        
        # Nuova richiesta
        response2 = client.chat_sync(
            messages=messages,
            temperature=0.4,
            max_tokens=200
        )
        
        response2_text = client.text_from_message(response2)
        print(f"Risposta 2: {response2_text}")
        
    except Exception as e:
        print(f"Errore: {e}")


if __name__ == "__main__":
    # Usa la versione asincrona
    print("=== Esempio Asincrono ===")
    asyncio.run(example_usage_async())
    
    # print("\n=== Esempio Sincrono ===")
    # example_usage_sync()