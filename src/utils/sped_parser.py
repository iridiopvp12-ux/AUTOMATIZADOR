import pandas as pd
import os

def process_sped_file(filepath):
    """
    Reads a SPED Contribuições TXT file and aggregates data by CST and CFOP.
    Returns a DataFrame ready for the report.
    """

    # We are interested in items that contribute to PIS/COFINS.
    # Typically found in block C (C170 items), D (D100/D500 items), etc.
    # For this simplified implementation, we will focus on C170 (Items of NFe/NFCe)
    # and maybe C190 if C170 is absent (though C190 is consolidation).
    # The user request specifically mentioned "SPED Contribuições" and the image shows "REGISTROS FISCAIS".

    # Structure of relevant list:
    # { (Bloco, CFOP, CST_PIS, CST_COFINS, Aliq_PIS, Aliq_COFINS): { 'Base_PIS': 0, 'Valor_PIS': 0, 'Base_COFINS': 0, 'Valor_COFINS': 0 } }

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

                # We need to capture context from Parent records (C100) if needed (like Date),
                # but for pure consolidation by CST/CFOP, C170 is usually self-contained regarding values,
                # EXCEPT it links to C100.

                # C170: Itens do Documento (Código 01, 1B, 04 and 55)
                if reg_type == 'C170':
                    # Layout Guia Prático EFD-Contribuições:
                    # 1: REG (C170)
                    # 2: NUM_ITEM
                    # 3: COD_ITEM
                    # 4: DESCR_COMPL
                    # 5: QTD
                    # 6: UNID
                    # 7: VL_ITEM
                    # 8: VL_DESC
                    # 9: IND_MOV
                    # 10: CST_ICMS
                    # 11: CFOP
                    # 12: COD_NAT
                    # 13: VL_BC_ICMS
                    # 14: ALIQ_ICMS
                    # 15: VL_ICMS
                    # 16: VL_BC_ICMS_ST
                    # 17: ALIQ_ICMS_ST
                    # 18: VL_ICMS_ST
                    # 19: IND_APUR
                    # 20: CST_PIS
                    # 21: VL_BC_PIS
                    # 22: ALIQ_PIS_PERCENTUAL
                    # 23: QUANT_BC_PIS
                    # 24: ALIQ_PIS_REAIS
                    # 25: VL_PIS
                    # 26: CST_COFINS
                    # 27: VL_BC_COFINS
                    # 28: ALIQ_COFINS_PERCENTUAL
                    # 29: QUANT_BC_COFINS
                    # 30: ALIQ_COFINS_REAIS
                    # 31: VL_COFINS
                    # 32: COD_CTA

                    if len(parts) < 32: # Basic safety check
                        continue

                    # Extract fields (Index is Field# + 1 usually because split creates empty string at start)
                    # parts[0] is empty string if line starts with |
                    # parts[1] is 'C170'

                    cfop = parts[11]

                    # PIS
                    cst_pis = parts[20]
                    vl_bc_pis = _to_float(parts[21])
                    aliq_pis = _to_float(parts[22])
                    vl_pis = _to_float(parts[25])

                    # COFINS
                    cst_cofins = parts[26]
                    vl_bc_cofins = _to_float(parts[27])
                    aliq_cofins = _to_float(parts[28])
                    vl_cofins = _to_float(parts[31])

                    bloco = 'C' # Hardcoded for C170

                    key = (bloco, cfop, cst_pis, aliq_pis, cst_cofins, aliq_cofins)

                    if key not in data_map:
                        data_map[key] = {
                            'Base_PIS': 0.0, 'Valor_PIS': 0.0,
                            'Base_COFINS': 0.0, 'Valor_COFINS': 0.0
                        }

                    data_map[key]['Base_PIS'] += vl_bc_pis
                    data_map[key]['Valor_PIS'] += vl_pis
                    data_map[key]['Base_COFINS'] += vl_bc_cofins
                    data_map[key]['Valor_COFINS'] += vl_cofins

                # Add other blocks if necessary (D100 etc) in future steps

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
            'CST_PIS': cst_pis,
            'Base_PIS': values['Base_PIS'],
            'Aliq_PIS': aliq_pis,
            'Valor_PIS': values['Valor_PIS'],
            'CST_COFINS': cst_cofins,
            'Base_COFINS': values['Base_COFINS'],
            'Aliq_COFINS': aliq_cofins,
            'Valor_COFINS': values['Valor_COFINS']
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    return df

def _to_float(val_str):
    if not val_str:
        return 0.0
    try:
        return float(val_str.replace(',', '.'))
    except ValueError:
        return 0.0
