import os
import requests
import base64
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from src.config import SIEG_API_KEY, SIEG_EMAIL, DOWNLOAD_TIMEOUT, MAX_RETRIES

class SiegManager:
    def __init__(self):
        # Endpoint v1 conforme sua documentação
        self.url_xml = "https://api.sieg.com/BaixarXml"
        self.url_pdf = "https://api.sieg.com/api/Arquivos/GerarDanfeViaXml"
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        retries = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def download_xml(self, chave_acesso, output_dir):
        if not SIEG_API_KEY or not SIEG_EMAIL:
            return False, "Credenciais (API Key ou E-mail) não configuradas."

        chave_acesso = chave_acesso.strip()
        
        # 1. Define xmlType (1=NFe, 2=CTe)
        xml_type = 1 
        if len(chave_acesso) == 44:
            modelo = chave_acesso[20:22]
            if modelo == "57":
                xml_type = 2 

        # 2. Parâmetros na URL (Query String)
        # ADICIONADO: 'email', pois o erro 401 indica falta de dados do usuário.
        # ADICIONADO: 'api_key' com o nome exato da sua documentação.
        params = {
            "xmlType": xml_type,
            "downloadEvent": "false",
            "api_key": SIEG_API_KEY,
            "email": SIEG_EMAIL  # Fundamental para evitar o Erro 401
        }

        # 3. Body: A chave deve ir entre aspas no corpo (JSON String)
        payload = json.dumps(chave_acesso) 
        
        headers = {
            'Content-Type': 'application/json'
        }

        try:
            response = self.session.post(
                self.url_xml, 
                params=params, 
                data=payload, 
                headers=headers, 
                timeout=DOWNLOAD_TIMEOUT
            )

            if response.status_code == 200:
                xml_content = response.text.strip()
                
                # Se o retorno não começar com <, pode ser uma mensagem de erro em texto
                if not xml_content.startswith("<"):
                    if "Erro" in xml_content or "não" in xml_content.lower():
                        return False, f"Sieg: {xml_content}"
                    # Limpa aspas extras se vier "<?xml...?>"
                    xml_content = xml_content.strip('"')

                # Salva o XML
                caminho_xml = os.path.join(output_dir, f"{chave_acesso}.xml")
                with open(caminho_xml, "w", encoding="utf-8") as f:
                    f.write(xml_content)
                
                # Tenta gerar o PDF automaticamente após baixar o XML
                msg_pdf = self._gerar_pdf_via_xml(xml_content, chave_acesso, output_dir)
                
                return True, f"XML Baixado. {msg_pdf}"

            elif response.status_code == 401:
                # Agora o log vai mostrar a mensagem real da Sieg
                return False, f"Erro 401 (Não Autorizado): {response.text}"
            
            elif response.status_code == 400:
                return False, f"Erro 400 (Requisição Inválida): {response.text}"
                
            else:
                return False, f"Erro HTTP {response.status_code}"

        except Exception as e:
            return False, f"Erro: {str(e)}"

    def _gerar_pdf_via_xml(self, xml_string, chave, output_dir):
        try:
            # Converte para base64 conforme documentação
            xml_b64 = base64.b64encode(xml_string.encode('utf-8')).decode('utf-8')
            url_pdf_auth = f"{self.url_pdf}?api_key={SIEG_API_KEY}"
            payload = {"ArquivoXml": xml_b64}

            response = self.session.post(
                url_pdf_auth,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=DOWNLOAD_TIMEOUT
            )

            if response.status_code == 200:
                pdf_b64 = response.text.strip().strip('"')
                pdf_bytes = base64.b64decode(pdf_b64)
                caminho_pdf = os.path.join(output_dir, f"{chave}.pdf")
                with open(caminho_pdf, "wb") as f:
                    f.write(pdf_bytes)
                return "PDF Gerado."
            return "Sem PDF."
        except:
            return "Erro no PDF."