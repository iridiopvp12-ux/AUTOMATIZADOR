import requests
import base64
import os

class SiegClient:
    def __init__(self, api_key, email):
        self.api_key = api_key
        self.email = email
        self.base_url = "https://api.sieg.com/api" # Confirme a URL base no Swagger
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def baixar_por_chave(self, chave, tipo_arquivo="xml"):
        """
        Tenta baixar o XML ou PDF de uma chave específica.
        tipo_arquivo: 'xml' ou 'pdf'
        """
        # Endpoint hipotético - A Sieg costuma ter endpoints como 'Download/Xml' passando a chave no body
        # ou 'Download/Pdf'. Ajuste conforme a documentação exata deles.
        if tipo_arquivo == "xml":
            endpoint = f"{self.base_url}/Download/Xml" # Exemplo
        else:
            endpoint = f"{self.base_url}/Download/Pdf" # Exemplo, as vezes é 'Print/Pdf'

        payload = {
            "Chaves": [chave], # A maioria aceita lista
            "TipoXml": "NFe" # Pode precisar detectar se é CTe pela chave (modelo 57)
        }
        
        # Ajuste para CTe se a chave tiver modelo 57 (posições 20 a 22 da chave)
        if len(chave) == 44 and chave[20:22] == '57':
             payload["TipoXml"] = "CTe"

        try:
            response = requests.post(endpoint, json=payload, headers=self.headers, timeout=10)
            if response.status_code == 200:
                dados = response.json()
                # A estrutura de retorno depende da Sieg. 
                # Geralmente vem algo como { "xmls": [ { "xmlBase64": "..." } ] }
                if tipo_arquivo == "xml":
                    return dados.get('xmls', [{}])[0].get('xmlBase64')
                else:
                    return dados.get('pdfs', [{}])[0].get('pdfBase64')
            return None
        except Exception as e:
            print(f"Erro ao baixar {chave}: {e}")
            return None

    def salvar_arquivo(self, conteudo_b64, caminho_completo):
        if not conteudo_b64: return False
        try:
            bytes_data = base64.b64decode(conteudo_b64)
            with open(caminho_completo, "wb") as f:
                f.write(bytes_data)
            return True
        except:
            return False