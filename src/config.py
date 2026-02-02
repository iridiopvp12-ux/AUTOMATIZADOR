import os

# Try to load environment variables from .env file, but don't crash if python-dotenv is missing
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Aviso: O pacote 'python-dotenv' não está instalado. O arquivo .env não será carregado.")
    print("Para corrigir, execute: pip install -r requirements.txt")

# Credenciais
SIEG_API_KEY = os.getenv("SIEG_API_KEY", "")
SIEG_EMAIL = os.getenv("SIEG_EMAIL", "")

# Configurações de Download
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
