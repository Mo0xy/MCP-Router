import requests

try:
    r = requests.get("https://openrouter.ai/api/v1/chat/completions")
    print("Successo!")
except Exception as e:
    print("Errore:", e)
