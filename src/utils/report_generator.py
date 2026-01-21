import pandas as pd
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side

def generate_fiscal_report(df: pd.DataFrame, output_path: str):
    """
    Generates an Excel report from the aggregated SPED data.
    """
    if df is None or df.empty:
        return False

    wb = Workbook()
    ws = wb.active
    ws.title = "Consolidação CST_CFOP"

    # Headers
    headers_top = [
        "Bloco", "CFOP", "CST",
        "PIS/PASEP", "", "", "", # Group Header
        "COFINS", "", "", ""     # Group Header
    ]

    headers_sub = [
        "", "", "", # Bloco, CFOP, CST (Merged usually or repeated)
        "Base de Cálculo", "Alíquota (%)", "Valor", "CST", # PIS fields (CST PIS is usually same as main CST or separate?)
                                                           # Wait, the image showed one CST column for PIS and one for COFINS.
                                                           # My DF has CST_PIS and CST_COFINS.
                                                           # The image shows "CST" column for PIS section, and "CST" for COFINS section.
                                                           # Wait, looking at image:
                                                           # Col 1: Bloco, Col 2: CFOP, Col 3: CST (PIS?), Col 4: Base PIS...
                                                           # Col 8: CST (COFINS?), Col 9: Base COFINS...
        "Base de Cálculo", "Alíquota (%)", "Valor"
    ]

    # We need to map our DF columns to this layout
    # DF Columns: Bloco, CFOP, CST_PIS, Base_PIS, Aliq_PIS, Valor_PIS, CST_COFINS, Base_COFINS, Aliq_COFINS, Valor_COFINS

    # Write Main Header (Row 1) - Title?
    ws.merge_cells('A1:K1')
    ws['A1'] = "REGISTROS FISCAIS - CONSOLIDAÇÃO DAS OPERAÇÕES POR BLOCO, CFOP E CST"
    ws['A1'].font = Font(bold=True, size=12)
    ws['A1'].alignment = Alignment(horizontal='center')

    # Write Group Headers (Row 3 - assuming row 2 has company info like image, skipping for simplicity or adding placeholders)
    # Let's start table at Row 3

    # Merging for PIS/PASEP and COFINS headers
    # PIS: Cols D, E, F, G (CST, Base, Aliq, Val)?
    # Image: Col 3 is CST. Then Base, Aliq, Qty, Aliq_Reais, Valor.
    # My parser extracts CST, Base, Aliq_Perc, Valor.
    # So I will adapt columns:
    # A: Bloco
    # B: CFOP
    # C: CST (PIS)
    # D: Base PIS
    # E: Aliq PIS
    # F: Valor PIS
    # G: CST (COFINS)
    # H: Base COFINS
    # I: Aliq COFINS
    # J: Valor COFINS

    ws.merge_cells('C2:F2')
    ws['C2'] = "PIS/PASEP"
    ws['C2'].alignment = Alignment(horizontal='center')

    ws.merge_cells('G2:J2')
    ws['G2'] = "COFINS"
    ws['G2'].alignment = Alignment(horizontal='center')

    # Sub Headers (Row 3)
    cols = ["Bloco", "CFOP", "CST", "Base Calc", "Aliq %", "Valor", "CST", "Base Calc", "Aliq %", "Valor"]
    for i, col in enumerate(cols):
        ws.cell(row=3, column=i+1, value=col).font = Font(bold=True)

    # Data (Row 4+)
    for r_idx, row in df.iterrows():
        ws.cell(row=r_idx+4, column=1, value=row['Bloco'])
        ws.cell(row=r_idx+4, column=2, value=row['CFOP'])
        ws.cell(row=r_idx+4, column=3, value=row['CST_PIS'])
        ws.cell(row=r_idx+4, column=4, value=row['Base_PIS']).number_format = '#,##0.00'
        ws.cell(row=r_idx+4, column=5, value=row['Aliq_PIS']).number_format = '0.00'
        ws.cell(row=r_idx+4, column=6, value=row['Valor_PIS']).number_format = '#,##0.00'

        ws.cell(row=r_idx+4, column=7, value=row['CST_COFINS'])
        ws.cell(row=r_idx+4, column=8, value=row['Base_COFINS']).number_format = '#,##0.00'
        ws.cell(row=r_idx+4, column=9, value=row['Aliq_COFINS']).number_format = '0.00'
        ws.cell(row=r_idx+4, column=10, value=row['Valor_COFINS']).number_format = '#,##0.00'

    # Auto-adjust column widths
    from openpyxl.utils import get_column_letter

    for i, col in enumerate(ws.columns, 1):
        max_length = 0
        column_letter = get_column_letter(i)
        for cell in col:
            try:
                # Skip checking merged cells content if they are not the top-left
                if isinstance(cell,  pd.DataFrame): # safety check? No, cell is openpyxl cell
                    pass
                if cell.value:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[column_letter].width = adjusted_width

    wb.save(output_path)
    return True
