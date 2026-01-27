import os
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime

class XmlToExcelLogic:
    def __init__(self):
        # Namespace padrão da NFe
        self.ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

    def xml_folder_to_excel(self, folder_path, output_path):
        """
        Lê XMLs de uma pasta e gera um Excel com os dados principais.
        Retorna (sucesso: bool, mensagem: str)
        """
        if not folder_path or not os.path.exists(folder_path):
            return False, "Pasta de origem inválida."

        lista_dados = []
        arquivos_erro = []

        # Lista arquivos .xml
        try:
            arquivos = [f for f in os.listdir(folder_path) if f.lower().endswith('.xml')]
        except Exception as e:
            return False, f"Erro ao listar arquivos: {e}"

        if not arquivos:
            return False, "Nenhum arquivo XML encontrado na pasta."

        for arquivo in arquivos:
            caminho = os.path.join(folder_path, arquivo)
            try:
                tree = ET.parse(caminho)
                root = tree.getroot()

                # Localiza infNFe
                inf_nfe = None
                if root.tag.endswith('NFe'):
                    inf_nfe = root.find('nfe:infNFe', self.ns)
                else:
                    nfe = root.find('.//nfe:NFe', self.ns)
                    if nfe is not None:
                        inf_nfe = nfe.find('nfe:infNFe', self.ns)

                if inf_nfe is None:
                    arquivos_erro.append(f"{arquivo} (Tag infNFe não encontrada)")
                    continue

                # Extração de Campos
                chave = inf_nfe.attrib.get('Id', '')[3:]

                ide = inf_nfe.find('nfe:ide', self.ns)
                emit = inf_nfe.find('nfe:emit', self.ns)
                dest = inf_nfe.find('nfe:dest', self.ns)
                total = inf_nfe.find('nfe:total', self.ns)
                icms_tot = total.find('nfe:ICMSTot', self.ns) if total is not None else None

                # Helper para pegar texto seguro
                def get_text(elem, tag):
                    found = elem.find(f'nfe:{tag}', self.ns) if elem is not None else None
                    return found.text if found is not None else ""

                n_nf = get_text(ide, 'nNF')
                serie = get_text(ide, 'serie')
                dh_emi = get_text(ide, 'dhEmi')

                # Formata Data (se possível)
                data_emissao = dh_emi
                if dh_emi and len(dh_emi) >= 10:
                    try:
                        dt = datetime.fromisoformat(dh_emi[:19]) # Tenta pegar YYYY-MM-DDTHH:MM:SS
                        data_emissao = dt.strftime("%d/%m/%Y")
                    except:
                        data_emissao = dh_emi[:10] # Fallback

                emit_nome = get_text(emit, 'xNome')
                emit_cnpj = get_text(emit, 'CNPJ')

                dest_nome = get_text(dest, 'xNome')
                dest_cnpj = get_text(dest, 'CNPJ')

                v_nf = get_text(icms_tot, 'vNF')
                try:
                    v_nf = float(v_nf) if v_nf else 0.0
                except:
                    v_nf = 0.0

                lista_dados.append({
                    "Número": n_nf,
                    "Série": serie,
                    "Data Emissão": data_emissao,
                    "Emitente": emit_nome,
                    "CNPJ Emitente": emit_cnpj,
                    "Destinatário": dest_nome,
                    "CNPJ Destinatário": dest_cnpj,
                    "Valor Total": v_nf,
                    "Chave de Acesso": chave,
                    "Arquivo": arquivo
                })

            except Exception as e:
                arquivos_erro.append(f"{arquivo} ({str(e)})")

        if not lista_dados:
            msg = "Nenhum dado extraído."
            if arquivos_erro:
                msg += f" Erros em: {', '.join(arquivos_erro[:3])}..."
            return False, msg

        try:
            df = pd.DataFrame(lista_dados)
            # Ordena por data (se possível) ou número
            # df.sort_values(by="Número", inplace=True)

            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='XMLs', index=False)

            msg = f"Sucesso! {len(lista_dados)} XMLs processados."
            if arquivos_erro:
                msg += f" ({len(arquivos_erro)} erros)"
            return True, msg

        except Exception as e:
            return False, f"Erro ao salvar Excel: {e}"
