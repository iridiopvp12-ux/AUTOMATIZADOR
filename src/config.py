import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Credenciais
SIEG_API_KEY = os.getenv("SIEG_API_KEY", "")
SIEG_EMAIL = os.getenv("SIEG_EMAIL", "")

# Configurações de Download
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
