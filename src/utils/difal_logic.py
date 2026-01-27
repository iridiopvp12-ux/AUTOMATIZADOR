import os
import pandas as pd
import xml.etree.ElementTree as ET

class DifalLogic:
    def __init__(self):
        # Namespace padrão da NFe (versão 4.00 geralmente usa este)
        self.ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

    def calcular_difal_por_pasta(self, folder_path):
        """
        Lê XMLs de uma pasta e extrai valores de DIFAL e FCP.
        
        Retorna uma tupla com 5 elementos:
        1. Sucesso (bool)
        2. Mensagem (str)
        3. Lista Resumo (Agrupado por UF)
        4. Lista Detalhada (Nota a Nota)
        5. Lista de Erros (Arquivos que falharam)
        """
        resultados_uf = {}
        lista_detalhada = []
        lista_erros = []
        
        # Validação da pasta
        if not folder_path or not os.path.exists(folder_path):
            return False, "Pasta inválida ou não encontrada.", [], [], []

        # Lista apenas arquivos XML
        lista_arquivos = [f for f in os.listdir(folder_path) if f.lower().endswith('.xml')]
        total_arquivos = len(lista_arquivos)

        if total_arquivos == 0:
            return False, "Nenhum arquivo XML encontrado na pasta.", [], [], []

        # Itera sobre os arquivos
        for arquivo in lista_arquivos:
            caminho_completo = os.path.join(folder_path, arquivo)
            try:
                tree = ET.parse(caminho_completo)
                root = tree.getroot()
                
                # Tenta localizar a tag infNFe (pode estar dentro de nfeProc ou direto em NFe)
                inf_nfe = None
                if root.tag.endswith('NFe'): # XML apenas com a nota
                    inf_nfe = root.find('nfe:infNFe', self.ns)
                else: # XML de distribuição (nfeProc)
                    nfe = root.find('.//nfe:NFe', self.ns)
                    if nfe is not None:
                        inf_nfe = nfe.find('nfe:infNFe', self.ns)

                # Se não achou a tag principal, ignora
                if inf_nfe is None:
                    lista_erros.append(f"{arquivo}: Estrutura XML inválida (Tag infNFe não encontrada).")
                    continue

                # --- 1. Extração de Dados Cadastrais ---
                
                # Chave de Acesso (atributo Id da tag infNFe, remove o prefixo 'NFe')
                chave = inf_nfe.attrib.get('Id', '')[3:]
                
                # Número da Nota
                ide = inf_nfe.find('nfe:ide', self.ns)
                numero_nf = ide.find('nfe:nNF', self.ns).text if ide is not None else "S/N"
                
                # UF de Destino
                dest = inf_nfe.find('nfe:dest', self.ns)
                ender_dest = dest.find('nfe:enderDest', self.ns) if dest is not None else None
                
                uf_dest = "IND" # Indefinido
                if ender_dest is not None:
                    tag_uf = ender_dest.find('nfe:UF', self.ns)
                    if tag_uf is not None:
                        uf_dest = tag_uf.text

                # --- 2. Extração de Valores (DIFAL e FCP) ---
                v_difal = 0.0
                v_fcp = 0.0
                
                # Percorre todos os itens (produtos) da nota
                for det in inf_nfe.findall('nfe:det', self.ns):
                    imposto = det.find('nfe:imposto', self.ns)
                    if imposto is None: continue
                    
                    # O DIFAL da partilha (EC 87/15) fica no grupo ICMSUFDest
                    icms_uf_dest = imposto.find('nfe:ICMSUFDest', self.ns)
                    
                    if icms_uf_dest is not None:
                        # Valor do DIFAL (vICMSUFDest)
                        tag_difal = icms_uf_dest.find('nfe:vICMSUFDest', self.ns)
                        if tag_difal is not None and tag_difal.text:
                            v_difal += float(tag_difal.text)

                        # Valor do FCP (vFCPUFDest)
                        tag_fcp = icms_uf_dest.find('nfe:vFCPUFDest', self.ns)
                        if tag_fcp is not None and tag_fcp.text:
                            v_fcp += float(tag_fcp.text)
                
                # --- 3. Consolidação ---
                # Só adiciona se tiver algum valor relevante
                if v_difal > 0 or v_fcp > 0:
                    
                    # Adiciona ao Resumo por UF
                    if uf_dest not in resultados_uf:
                        resultados_uf[uf_dest] = {'difal': 0.0, 'fcp': 0.0}
                    
                    resultados_uf[uf_dest]['difal'] += v_difal
                    resultados_uf[uf_dest]['fcp'] += v_fcp

                    # Adiciona à Lista Detalhada
                    lista_detalhada.append({
                        "UF": uf_dest,
                        "Numero NF": numero_nf,
                        "Chave de Acesso": chave,
                        "Arquivo": arquivo,
                        "Valor DIFAL": v_difal,
                        "Valor FCP": v_fcp
                    })

            except Exception as e:
                # Captura erros de leitura (arquivo corrompido, tag faltando, etc)
                lista_erros.append(f"{arquivo}: {str(e)}")
                continue

        # Formata a lista de resumo para retorno (Lista de Dicionários)
        lista_resumo = []
        for uf in sorted(resultados_uf.keys()):
            valores = resultados_uf[uf]
            lista_resumo.append({
                "UF": uf,
                "DIFAL": valores['difal'],
                "FCP": valores['fcp']
            })
            
        msg_final = f"Processado {total_arquivos} arquivos."
        if lista_erros:
            msg_final += f" Atenção: {len(lista_erros)} arquivos com erro."

        return True, msg_final, lista_resumo, lista_detalhada, lista_erros

    def gerar_excel(self, dados_resumo, dados_detalhados, output_path, incluir_detalhado=False):
        """
        Gera um arquivo Excel com os dados processados.
        Pode criar múltiplas abas (Resumo e Detalhado).
        """
        try:
            if not dados_resumo:
                return False, "Não há dados consolidados para gerar o Excel."

            # Usa o ExcelWriter para gerenciar múltiplas abas
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                
                # --- ABA 1: RESUMO ---
                df_resumo = pd.DataFrame(dados_resumo)
                
                # Calcula totais gerais
                total_difal = df_resumo['DIFAL'].sum()
                total_fcp = df_resumo['FCP'].sum()
                
                # Adiciona linha de totais no final
                linha_total = pd.DataFrame([{
                    'UF': 'TOTAL GERAL', 
                    'DIFAL': total_difal, 
                    'FCP': total_fcp
                }])
                
                df_resumo = pd.concat([df_resumo, linha_total], ignore_index=True)
                
                # Salva a aba
                df_resumo.to_excel(writer, sheet_name='Resumo por UF', index=False)

                # --- ABA 2: DETALHADO (Opcional) ---
                if incluir_detalhado and dados_detalhados:
                    df_detalhe = pd.DataFrame(dados_detalhados)
                    df_detalhe.to_excel(writer, sheet_name='Relatório Detalhado', index=False)

            return True, "Relatório Excel gerado com sucesso!"

        except Exception as e:
            return False, f"Erro ao salvar Excel: {str(e)}"