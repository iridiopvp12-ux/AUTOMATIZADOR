import logging
from pathlib import Path
from typing import Callable, Optional, Tuple, Dict
from datetime import date
from collections import Counter

logger = logging.getLogger(__name__)

class SpedFilterLogic:
    def __init__(self):
        self.DOCUMENT_DATE_POSITIONS: Dict[str, int] = {
            'C100': 11, 'C300': 4, 'C350': 10, 'C405': 2, 'C500': 12, 
            'C600': 11, 'C700': 11, 'D100': 12, 'D300': 4, 'D350': 10, 
            'D400': 5, 'D500': 11, 'D600': 11, 'D700': 10,
        }
        self.BLOCK_OPENERS: Dict[str, str] = {
            '0001': '0', 'C001': 'C', 'D001': 'D', 'E001': 'E',
            'G001': 'G', 'H001': 'H', 'K001': 'K', '1001': '1', '9001': '9',
        }
        self.BLOCK_CLOSERS = {'0990', 'C990', 'D990', 'E990', 'G990', 'H990', 'K990', '1990', '9990'}
        self.BLOCKS_TO_FILTER = {'C', 'D'}

    def _parse_sped_date(self, date_str: str) -> Optional[date]:
        if not date_str or len(date_str) != 8: return None
        try:
            return date(int(date_str[4:8]), int(date_str[2:4]), int(date_str[0:2]))
        except (ValueError, TypeError, IndexError):
            return None

    def _format_date_sped(self, dt: date) -> str:
        return dt.strftime('%d%m%Y')

    def filter_sped_by_date(self, input_path: str, output_path: str, start_date: date, end_date: date, encoding: str = 'latin-1', progress_callback: Optional[Callable[[int], None]] = None) -> Tuple[bool, str]:
        lines_read = 0
        lines_written = 0
        record_counts = Counter()
        
        try:
            input_p = Path(input_path)
            total_lines = 0
            
            if progress_callback:
                try:
                    with open(input_p, 'r', encoding=encoding, errors='ignore') as f:
                        total_lines = sum(1 for _ in f)
                except: pass

            with open(input_p, 'r', encoding=encoding, errors='ignore') as infile, \
                 open(output_path, 'w', encoding=encoding) as outfile:

                current_block = None
                keep_current_doc = False
                first_line = True

                for line in infile:
                    lines_read += 1
                    if progress_callback and total_lines > 0 and lines_read % 5000 == 0:
                        progress_callback(min(int((lines_read / total_lines) * 100), 99))

                    line_stripped = line.strip()
                    if not line_stripped.startswith('|') or len(line_stripped) < 7: continue

                    parts = line_stripped.split('|')
                    if len(parts) < 3: continue
                    registro = parts[1]

                    if first_line and registro == '0000':
                        first_line = False
                        try:
                            parts[4] = self._format_date_sped(start_date)
                            parts[5] = self._format_date_sped(end_date)
                            outfile.write("|".join(parts) + "\n")
                            lines_written += 1
                            record_counts[registro] += 1
                            current_block = '0'
                        except:
                             outfile.write(line)
                             lines_written += 1
                             record_counts[registro] += 1
                             current_block = '0'
                        continue

                    if registro in self.BLOCK_OPENERS:
                        current_block = self.BLOCK_OPENERS[registro]

                    line_to_write = None

                    if current_block not in self.BLOCKS_TO_FILTER and current_block != '9':
                        line_to_write = line
                    elif current_block in self.BLOCKS_TO_FILTER:
                        if registro in self.DOCUMENT_DATE_POSITIONS:
                            keep_current_doc = False
                            date_to_check = None
                            try:
                                date_idx = self.DOCUMENT_DATE_POSITIONS[registro]
                                if len(parts) > date_idx and parts[date_idx]:
                                    date_to_check = self._parse_sped_date(parts[date_idx])
                                
                                if date_to_check and (start_date <= date_to_check <= end_date):
                                    line_to_write = line
                                    keep_current_doc = True
                            except: pass
                        elif registro in self.BLOCK_OPENERS or registro in self.BLOCK_CLOSERS:
                            line_to_write = line
                            keep_current_doc = False
                        elif keep_current_doc:
                            line_to_write = line

                    if line_to_write:
                        outfile.write(line_to_write)
                        lines_written += 1
                        record_counts[registro] += 1

                # Bloco 9 Recalc
                if '9001' not in record_counts: record_counts['9001'] = 0
                record_counts['9001'] += 1
                outfile.write("|9001|0|\n")
                lines_written += 1
                
                bloco_9_count = 0
                for reg, count in sorted(record_counts.items()):
                    if reg not in ['9990', '9999']:
                        outfile.write(f"|9900|{reg}|{count}|\n")
                        lines_written += 1
                        bloco_9_count += 1
                
                outfile.write(f"|9990|{bloco_9_count + 3}|\n")
                lines_written += 1
                outfile.write(f"|9999|{lines_written + 1}|\n")

            if progress_callback: progress_callback(100)
            return True, f"Sucesso! {lines_written} linhas geradas."

        except Exception as e:
            return False, str(e)