import logging
from pathlib import Path
from typing import Callable, Optional, Tuple, List, Set

logger = logging.getLogger(__name__)

class KeysExtractorLogic:
    def __init__(self):
        pass

    # Alterado o retorno para incluir a lista de chaves: Tuple[bool, str, List[str]]
    def extract_keys(self, input_path: str, output_path: str, progress_callback: Optional[Callable[[int], None]] = None) -> Tuple[bool, str, List[str]]:
        nfe_keys: Set[str] = set()
        cte_keys: Set[str] = set()
        lines_read = 0
        total_lines = 0
        
        try:
            input_p = Path(input_path)
            # Contagem de linhas para progresso
            if progress_callback:
                try:
                    with open(input_p, 'r', encoding='latin-1', errors='ignore') as f:
                        total_lines = sum(1 for _ in f)
                except: pass

            with open(input_p, 'r', encoding='latin-1', errors='ignore') as infile:
                for line in infile:
                    lines_read += 1
                    if progress_callback and total_lines > 0 and lines_read % 5000 == 0:
                        progress_callback(int((lines_read / total_lines) * 100))

                    line = line.strip()
                    if not line.startswith('|') or len(line.split('|')) < 3: continue
                    
                    parts = line.split('|')
                    reg = parts[1]

                    # Captura NFe (C100)
                    if reg == 'C100' and len(parts) > 9:
                        if parts[2] == '0': # 0 = Entrada (Geralmente baixamos XML de entrada)
                            chave = ''.join(filter(str.isdigit, parts[9]))
                            if len(chave) == 44: nfe_keys.add(chave)

                    # Captura CTe (D100)
                    elif reg == 'D100' and len(parts) > 10:
                        if parts[2] == '0': 
                            chave = ''.join(filter(str.isdigit, parts[10]))
                            if len(chave) == 44: cte_keys.add(chave)

            # Salva o arquivo TXT (como você já fazia)
            with open(output_path, 'w', encoding='utf-8') as outfile:
                if cte_keys:
                    outfile.write("=== CTe ===\n" + "\n".join(sorted(cte_keys)) + "\n\n")
                else: outfile.write("=== NENHUM CTe ===\n\n")
                
                if nfe_keys:
                    outfile.write("=== NFe ===\n" + "\n".join(sorted(nfe_keys)) + "\n")
                else: outfile.write("=== NENHUMA NFe ===\n")

            if progress_callback: progress_callback(100)
            
            # Retorna TODAS as chaves combinadas numa lista única para o download
            todas_chaves = list(nfe_keys) + list(cte_keys)
            
            return True, f"Sucesso!\nCTe: {len(cte_keys)}\nNFe: {len(nfe_keys)}", todas_chaves

        except Exception as e:
            return False, f"Erro: {str(e)}", []