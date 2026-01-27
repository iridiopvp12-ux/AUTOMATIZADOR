import pandas as pd
import os

def process_sped_file(filepath):
    """
    Lê um arquivo SPED (TXT) e agrega dados por Bloco, CFOP e CST.
    Suporta Blocos C, D e A.
    Retorna um DataFrame pronto para o relatório.
    """
    
    # Estrutura do mapa de dados:
    # Chave: (Bloco, CFOP, CST_PIS, Aliq_PIS, CST_COFINS, Aliq_COFINS)
    # Valor: Dicionário com somatórios
    data_map = {}

    try:
        with open(filepath, 'r', encoding='latin-1') as f:
            for line in f:
                if not line.startswith('|'):
                    continue

                parts = line.split('|')
                if len(parts) < 2:
                    continue

                reg_type = parts[1]

                # ==========================================================
                # BLOCO C: C170 (Itens de Documento)
                # ==========================================================
                if reg_type == 'C170':
                    if len(parts) < 32: continue
                    
                    # Campos Base
                    vl_item = _to_float(parts[7])
                    cfop = parts[11]
                    vl_icms = _to_float(parts[15])
                    
                    # --- NOVO: Captura do ICMS ST (Campo 18 - Índice 18) ---
                    vl_icms_st = _to_float(parts[18])
                    
                    vl_ipi = _to_float(parts[24])

                    # PIS (Índices padrão SPED Contribuições)
                    cst_pis = parts[25]
                    vl_bc_pis = _to_float(parts[26])
                    aliq_pis = _to_float(parts[27])
                    vl_pis = _to_float(parts[30])

                    # COFINS
                    cst_cofins = parts[31]
                    vl_bc_cofins = _to_float(parts[32])
                    aliq_cofins = _to_float(parts[33])
                    vl_cofins = _to_float(parts[36])

                    _add_to_map(data_map, 'C', cfop, cst_pis, aliq_pis, cst_cofins, aliq_cofins,
                                vl_item, vl_icms, vl_icms_st, vl_ipi,
                                vl_bc_pis, vl_pis, vl_bc_cofins, vl_cofins)

                # ==========================================================
                # BLOCO A: A170 (Itens de Documento - Serviços)
                # ==========================================================
                elif reg_type == 'A170':
                    # A170 tem PIS e COFINS na mesma linha, similar ao C170
                    # Layout: 1:REG, 5:VL_ITEM, 7:CST_PIS, 8:BC_PIS, 9:ALIQ_PIS, 10:VL_PIS, 
                    # 11:CST_COFINS, 12:BC_COFINS, 13:ALIQ_COFINS, 14:VL_COFINS
                    if len(parts) < 15: continue

                    vl_item = _to_float(parts[5])
                    cfop = "SERV" # Bloco A geralmente não tem CFOP, usamos um placeholder
                    
                    # Bloco A não costuma ter ICMS/IPI
                    vl_icms = 0.0
                    vl_icms_st = 0.0
                    vl_ipi = 0.0

                    cst_pis = parts[7]
                    vl_bc_pis = _to_float(parts[8])
                    aliq_pis = _to_float(parts[9])
                    vl_pis = _to_float(parts[10])

                    cst_cofins = parts[11]
                    vl_bc_cofins = _to_float(parts[12])
                    aliq_cofins = _to_float(parts[13])
                    vl_cofins = _to_float(parts[14])

                    _add_to_map(data_map, 'A', cfop, cst_pis, aliq_pis, cst_cofins, aliq_cofins,
                                vl_item, vl_icms, vl_icms_st, vl_ipi,
                                vl_bc_pis, vl_pis, vl_bc_cofins, vl_cofins)

                # ==========================================================
                # BLOCO D: Transportes (D100 -> D101/D105) e Comms (D500 -> D501/D505)
                # ==========================================================
                # No Bloco D (Contribuições), os valores costumam estar nos filhos (101/105 ou 501/505)
                
                # --- D101 / D501 (PIS) ---
                elif reg_type in ('D101', 'D501'):
                    # Layout D101: 2:IND_NAT, 3:VL_ITEM, 4:CST_PIS, 5:BC_PIS, 6:ALIQ, 7:VL_PIS
                    if len(parts) < 8: continue
                    
                    vl_item = _to_float(parts[3])
                    cfop = "TRANSP" if reg_type == 'D101' else "TELECOM"
                    
                    cst_pis = parts[4]
                    vl_bc_pis = _to_float(parts[5])
                    aliq_pis = _to_float(parts[6])
                    vl_pis = _to_float(parts[7])
                    
                    # Registramos apenas a parte do PIS, COFINS fica vazio nesta linha
                    _add_to_map(data_map, 'D', cfop, cst_pis, aliq_pis, None, 0.0,
                                vl_item, 0.0, 0.0, 0.0,
                                vl_bc_pis, vl_pis, 0.0, 0.0)

                # --- D105 / D505 (COFINS) ---
                elif reg_type in ('D105', 'D505'):
                    # Layout D105: 2:IND_NAT, 3:VL_ITEM, 4:CST_COF, 5:BC_COF, 6:ALIQ, 7:VL_COF
                    if len(parts) < 8: continue
                    
                    vl_item = _to_float(parts[3])
                    cfop = "TRANSP" if reg_type == 'D105' else "TELECOM"
                    
                    cst_cofins = parts[4]
                    vl_bc_cofins = _to_float(parts[5])
                    aliq_cofins = _to_float(parts[6])
                    vl_cofins = _to_float(parts[7])
                    
                    # Registramos apenas a parte da COFINS
                    _add_to_map(data_map, 'D', cfop, None, 0.0, cst_cofins, aliq_cofins,
                                vl_item, 0.0, 0.0, 0.0,
                                0.0, 0.0, vl_bc_cofins, vl_cofins)

    except Exception as e:
        print(f"Error processing file: {e}")
        return None

    # Convert to DataFrame
    rows = []
    for key, values in data_map.items():
        bloco, cfop, cst_pis, aliq_pis, cst_cofins, aliq_cofins = key
        row = {
            'Bloco': bloco,
            'CFOP': cfop,
            'Valor_Item': values['Valor_Item'],
            'Valor_ICMS': values['Valor_ICMS'],
            'Valor_ICMS_ST': values['Valor_ICMS_ST'], # Adicionado
            'Valor_IPI': values['Valor_IPI'],
            'CST_PIS': cst_pis if cst_pis else '-',
            'Base_PIS': values['Base_PIS'],
            'Aliq_PIS': aliq_pis,
            'Valor_PIS': values['Valor_PIS'],
            'CST_COFINS': cst_cofins if cst_cofins else '-',
            'Base_COFINS': values['Base_COFINS'],
            'Aliq_COFINS': aliq_cofins,
            'Valor_COFINS': values['Valor_COFINS']
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    return df

def _add_to_map(data_map, bloco, cfop, cst_pis, aliq_pis, cst_cofins, aliq_cofins,
                vl_item, vl_icms, vl_icms_st, vl_ipi,
                vl_bc_pis, vl_pis, vl_bc_cofins, vl_cofins):
    
    key = (bloco, cfop, cst_pis, aliq_pis, cst_cofins, aliq_cofins)

    if key not in data_map:
        data_map[key] = {
            'Valor_Item': 0.0, 'Valor_ICMS': 0.0, 'Valor_ICMS_ST': 0.0, 'Valor_IPI': 0.0,
            'Base_PIS': 0.0, 'Valor_PIS': 0.0,
            'Base_COFINS': 0.0, 'Valor_COFINS': 0.0
        }

    data_map[key]['Valor_Item'] += vl_item
    data_map[key]['Valor_ICMS'] += vl_icms
    data_map[key]['Valor_ICMS_ST'] += vl_icms_st # Soma o novo campo
    data_map[key]['Valor_IPI'] += vl_ipi
    data_map[key]['Base_PIS'] += vl_bc_pis
    data_map[key]['Valor_PIS'] += vl_pis
    data_map[key]['Base_COFINS'] += vl_bc_cofins
    data_map[key]['Valor_COFINS'] += vl_cofins

def _to_float(val_str):
    if not val_str:
        return 0.0
    try:
        return float(val_str.replace(',', '.'))
    except ValueError:
        return 0.0