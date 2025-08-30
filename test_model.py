import asyncio
import os
import httpx
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

async def test_model():
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    print(f"\nUsing OpenRouter API key: {api_key}\n")
    model = os.getenv("MODEL", "")
    print(f"\nUsing OpenRouter model: {model}\n")
    
    assert api_key, "OPENROUTER_API_KEY must be set in .env"
    assert model, "MODEL must be set in .env"
    
    # Definisci headers e data correttamente
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Hello"
            }
        ],
        "max_tokens": 50
    }
    
    try:
        async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
            response = await client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
            assert False, f"Failed to connect to OpenRouter API. Status: {response.status_code}, Response: {response.text}"
        
        response_data = response.json()
        print(f"\nResponse from OpenRouter API: {response_data}\n")
        
        return response_data
        
    except httpx.TimeoutException:
        print("Request timed out")
        raise
    except httpx.ConnectError as e:
        print(f"Connection error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


async def main():
    await test_model()


if __name__ == "__main__":
    asyncio.run(main())