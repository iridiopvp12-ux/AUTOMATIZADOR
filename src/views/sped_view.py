import flet as ft
import os
import threading
import time
from datetime import datetime

# --- IMPORTS DAS LÓGICAS ---
# Certifique-se de que os arquivos existem na pasta src/utils/
from src.utils.sped_parser import process_sped_file
from src.utils.report_generator import generate_fiscal_report
from src.utils.sped_filter_logic import SpedFilterLogic
from src.utils.keys_extractor_logic import KeysExtractorLogic
from src.utils.sieg_manager import SiegManager
from src.utils.difal_logic import DifalLogic 

class SpedView(ft.Column):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_instance = page
        self.expand = True

        # --- Instância das Classes de Lógica ---
        self.filter_logic = SpedFilterLogic()
        self.keys_logic = KeysExtractorLogic()
        self.sieg_manager = SiegManager()
        self.difal_logic = DifalLogic()

        # --- Configuração dos File Pickers (Diálogos de Arquivo) ---
        self.open_file_picker = ft.FilePicker(on_result=self.on_open_file_result)
        self.save_file_picker = ft.FilePicker(on_result=self.on_save_file_result)
        self.folder_picker = ft.FilePicker(on_result=self.on_folder_result)

        # Adiciona os diálogos à página (obrigatório no Flet)
        if self.open_file_picker not in self.page_instance.overlay:
            self.page_instance.overlay.extend([
                self.open_file_picker, 
                self.save_file_picker, 
                self.folder_picker
            ])
        
        self.page_instance.update()

        # --- Estado da Aplicação (Variáveis de Controle) ---
        self.current_action = None 
        self.pending_input_path = None 
        self.pending_filter_dates = None
        self.keys_found_list = []
        
        # Caches para o relatório DIFAL
        self.difal_data_summary = []  
        self.difal_data_details = [] 
        self.difal_errors_list = [] # Lista de erros de leitura XML
        
        # Controle de Abas
        self.active_tab_label = "Menu"
        self.open_tabs = ["Menu"]
        self.tab_contents = {}

        # --- Layout Principal ---
        self.tabs_row = ft.Row(scroll=ft.ScrollMode.AUTO)
        self.content_area = ft.Container(expand=True, padding=20)

        self.controls = [
            ft.Container(
                content=self.tabs_row,
                border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300))
            ),
            self.content_area
        ]

        # Inicializa
        self.init_menu()
        self.render_tabs(initial=True)
        self.set_content("Menu", initial=True)

    # =========================================================================
    # SISTEMA DE NAVEGAÇÃO (ABAS)
    # =========================================================================
    def render_tabs(self, initial=False):
        self.tabs_row.controls = []
        for label in self.open_tabs:
            is_active = (label == self.active_tab_label)
            self.tabs_row.controls.append(self.create_tab_button(label, is_active))
        if not initial:
            self.tabs_row.update()

    def create_tab_button(self, label, is_active):
        color = ft.Colors.PRIMARY if is_active else ft.Colors.BLACK
        bg_color = ft.Colors.BLUE_50 if is_active else ft.Colors.TRANSPARENT
        icon = ft.Icons.MENU if label == "Menu" else ft.Icons.DESCRIPTION
        
        return ft.Container(
            padding=ft.padding.symmetric(horizontal=16, vertical=10),
            bgcolor=bg_color,
            border=ft.border.only(bottom=ft.BorderSide(2 if is_active else 0, color)),
            on_click=lambda e: self.switch_tab(label),
            ink=True,
            content=ft.Row([
                ft.Icon(icon, size=16, color=color),
                ft.Text(label, color=color, weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL)
            ], alignment=ft.MainAxisAlignment.CENTER)
        )

    def switch_tab(self, label):
        if label != self.active_tab_label:
            self.active_tab_label = label
            self.render_tabs()
            self.set_content(label)

    def set_content(self, label, initial=False):
        if label in self.tab_contents:
            self.content_area.content = self.tab_contents[label]
            if not initial:
                self.content_area.update()

    def init_menu(self):
        self.tab_contents["Menu"] = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                ft.Text("Automações SPED", size=30, weight=ft.FontWeight.BOLD),
                ft.Text("Selecione uma ferramenta:", color=ft.Colors.GREY_600),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Row(wrap=True, spacing=20, run_spacing=20, controls=[
                    self.create_card("SPED Contribuições", ft.Icons.TABLE_CHART, "Gerar planilha fiscal.", self.open_contrib_tab),
                    self.create_card("Filtro por Data", ft.Icons.DATE_RANGE, "Filtrar período do SPED.", self.open_filter_tab),
                    self.create_card("Extrator de Chaves", ft.Icons.VPN_KEY, "Extrair e Baixar XMLs.", self.open_keys_tab),
                    self.create_card("Relatório DIFAL", ft.Icons.MONETIZATION_ON, "Extrair totais de DIFAL/FCP.", self.open_difal_tab),
                ])
            ]
        )

    def create_card(self, title, icon, desc, on_click):
        return ft.Card(
            elevation=2,
            content=ft.Container(
                width=280, height=180, padding=20, ink=True, on_click=on_click, border_radius=10,
                content=ft.Column([
                    ft.Icon(icon, size=40, color=ft.Colors.PRIMARY),
                    ft.Text(title, size=18, weight="bold", text_align="center"),
                    ft.Text(desc, size=14, color=ft.Colors.GREY_600, text_align="center"),
                ], alignment="center", horizontal_alignment="center")
            )
        )

    # =========================================================================
    # HANDLERS DE ARQUIVOS (ABRIR, SALVAR, PASTA)
    # =========================================================================
    def request_open_file(self, action_type):
        self.current_action = action_type
        self.open_file_picker.pick_files(allow_multiple=False, allowed_extensions=["txt"])

    def on_open_file_result(self, e: ft.FilePickerResultEvent):
        if not e.files: return
        file_path = e.files[0].path
        
        if self.current_action == 'contrib':
            self.contrib_path_input.value = file_path
            self.contrib_path_input.update()
        elif self.current_action == 'filter':
            self.filter_path_input.value = file_path
            self.filter_path_input.update()
        elif self.current_action == 'keys':
            self.keys_path_input.value = file_path
            self.keys_path_input.update()

    def on_folder_result(self, e: ft.FilePickerResultEvent):
        if not e.path: return
        path = e.path

        if self.current_action == 'download_xml':
            self.run_download_thread(path)
        
        elif self.current_action == 'difal_folder':
            self.difal_folder_input.value = path
            self.difal_folder_input.update()

    def on_save_file_result(self, e: ft.FilePickerResultEvent):
        if not e.path: return
        output_path = e.path

        if self.current_action == 'filter':
            self.run_filter_logic_thread(output_path)
            
        elif self.current_action == 'keys':
            self.run_keys_logic_thread(output_path)
            
        elif self.current_action == 'save_difal':
            # Verifica o checkbox de detalhes
            incluir_detalhes = self.chk_detailed_report.value
            
            sucesso, msg = self.difal_logic.gerar_excel(
                self.difal_data_summary, 
                self.difal_data_details, 
                output_path, 
                incluir_detalhado=incluir_detalhes
            )
            
            if sucesso:
                self.difal_status.value = f"Arquivo salvo: {msg}"
                self.difal_status.color = "green"
            else:
                self.difal_status.value = f"Erro ao salvar: {msg}"
                self.difal_status.color = "red"
            self.difal_status.update()

    # =========================================================================
    # ABA 1: SPED CONTRIBUIÇÕES (Planilha)
    # =========================================================================
    def open_contrib_tab(self, e):
        label = "SPED Contribuições"
        if label not in self.open_tabs:
            self.open_tabs.append(label)
            self.contrib_status = ft.Text("Aguardando...", color=ft.Colors.GREY)
            self.contrib_path_input = ft.TextField(label="Arquivo SPED", width=400)
            
            self.tab_contents[label] = ft.Column([
                ft.Text(label, size=24, weight="bold"),
                ft.Divider(),
                ft.Row([
                    self.contrib_path_input,
                    ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=lambda _: self.request_open_file('contrib')),
                    ft.ElevatedButton("Gerar Excel", icon=ft.Icons.PLAY_ARROW, on_click=self.process_contrib)
                ]),
                ft.Container(content=self.contrib_status, padding=10, bgcolor=ft.Colors.GREY_100)
            ])
        self.switch_tab(label)

    def process_contrib(self, e):
        filepath = self.contrib_path_input.value
        if not filepath or not os.path.exists(filepath):
            self.contrib_status.value = "Arquivo inválido."
            self.contrib_status.color = "red"
            self.contrib_status.update()
            return

        self.contrib_status.value = "Processando..."
        self.contrib_status.color = "blue"
        self.contrib_status.update()

        def task():
            try:
                df = process_sped_file(filepath)
                if df is None or df.empty:
                    self.contrib_status.value = "Nenhum dado encontrado."
                    self.contrib_status.color = "red"
                else:
                    out_path = os.path.join(os.path.dirname(filepath), f"RELATORIO_{os.path.basename(filepath)}.xlsx")
                    if generate_fiscal_report(df, out_path):
                        self.contrib_status.value = f"Sucesso: {out_path}"
                        self.contrib_status.color = "green"
                    else:
                        self.contrib_status.value = "Erro ao salvar Excel."
                        self.contrib_status.color = "red"
            except Exception as ex:
                self.contrib_status.value = f"Erro: {ex}"
                self.contrib_status.color = "red"
            
            self.contrib_status.update()

        threading.Thread(target=task).start()

    # =========================================================================
    # ABA 2: FILTRO POR DATA
    # =========================================================================
    def open_filter_tab(self, e):
        label = "Filtro por Data"
        if label not in self.open_tabs:
            self.open_tabs.append(label)
            
            self.filter_path_input = ft.TextField(label="Arquivo SPED Original", width=400)
            self.start_date_input = ft.TextField(label="Data Início (DDMMAAAA)", width=150, hint_text="01012025")
            self.end_date_input = ft.TextField(label="Data Fim (DDMMAAAA)", width=150, hint_text="31012025")
            self.filter_status = ft.Text("Aguardando início...", color=ft.Colors.GREY)
            self.filter_progress = ft.ProgressBar(width=400, value=0)

            self.tab_contents[label] = ft.Column([
                ft.Text(label, size=24, weight="bold"),
                ft.Divider(),
                ft.Row([
                    self.filter_path_input,
                    ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=lambda _: self.request_open_file('filter'))
                ]),
                ft.Row([self.start_date_input, self.end_date_input]),
                ft.ElevatedButton("Filtrar e Salvar", icon=ft.Icons.SAVE, on_click=self.pre_process_filter),
                ft.Divider(),
                self.filter_status,
                self.filter_progress
            ])
        self.switch_tab(label)

    def pre_process_filter(self, e):
        if not self.filter_path_input.value or not os.path.exists(self.filter_path_input.value):
            self.filter_status.value = "Selecione um arquivo válido."
            self.filter_status.update()
            return
        
        try:
            d_ini = datetime.strptime(self.start_date_input.value, "%d%m%Y").date()
            d_fim = datetime.strptime(self.end_date_input.value, "%d%m%Y").date()
            if d_fim < d_ini: raise ValueError("Data fim menor que inicio")
            
            self.pending_filter_dates = (d_ini, d_fim)
            self.pending_input_path = self.filter_path_input.value
            self.current_action = 'filter'
            
            self.save_file_picker.save_file(
                dialog_title="Salvar SPED Filtrado",
                file_name=f"SPED_FILTRADO_{d_ini}_{d_ini}.txt",
                allowed_extensions=["txt"]
            )
        except ValueError:
            self.filter_status.value = "Datas inválidas. Use formato DDMMAAAA (ex: 01012025)."
            self.filter_status.color = "red"
            self.filter_status.update()

    def run_filter_logic_thread(self, output_path):
        self.filter_status.value = "Filtrando registros..."
        self.filter_status.color = "blue"
        self.filter_progress.value = 0
        self.filter_status.update()
        self.filter_progress.update()

        start_date, end_date = self.pending_filter_dates
        input_path = self.pending_input_path

        def progress_update(pct):
            self.filter_progress.value = pct / 100
            self.filter_progress.update()

        def task():
            success, msg = self.filter_logic.filter_sped_by_date(
                input_path, output_path, start_date, end_date, progress_callback=progress_update
            )
            self.filter_status.value = msg
            self.filter_status.color = "green" if success else "red"
            self.filter_progress.value = 1 if success else 0
            self.filter_status.update()
            self.filter_progress.update()

        threading.Thread(target=task).start()

    # =========================================================================
    # ABA 3: EXTRATOR DE CHAVES + DOWNLOAD
    # =========================================================================
    def open_keys_tab(self, e):
        label = "Extrator de Chaves"
        if label not in self.open_tabs:
            self.open_tabs.append(label)
            
            self.keys_path_input = ft.TextField(label="Arquivo SPED", width=400)
            self.keys_status = ft.Text("Aguardando...", color=ft.Colors.GREY)
            self.keys_progress = ft.ProgressBar(width=400, value=0)
            
            self.btn_download_sieg = ft.ElevatedButton(
                "Baixar XMLs na Sieg", 
                icon=ft.Icons.CLOUD_DOWNLOAD, 
                on_click=self.request_download_folder,
                disabled=True
            )

            self.tab_contents[label] = ft.Column([
                ft.Text(label, size=24, weight="bold"),
                ft.Divider(),
                ft.Row([
                    self.keys_path_input,
                    ft.IconButton(ft.Icons.FOLDER_OPEN, on_click=lambda _: self.request_open_file('keys'))
                ]),
                ft.Row([
                    ft.ElevatedButton("Extrair Chaves", icon=ft.Icons.VPN_KEY, on_click=self.pre_process_keys),
                    self.btn_download_sieg 
                ]),
                ft.Divider(),
                self.keys_status,
                self.keys_progress
            ])
        self.switch_tab(label)

    def pre_process_keys(self, e):
        if not self.keys_path_input.value or not os.path.exists(self.keys_path_input.value):
            self.keys_status.value = "Selecione um arquivo válido."
            self.keys_status.update()
            return

        self.pending_input_path = self.keys_path_input.value
        self.current_action = 'keys'
        
        self.save_file_picker.save_file(
            dialog_title="Salvar Lista de Chaves",
            file_name="CHAVES_EXTRAIDAS.txt",
            allowed_extensions=["txt"]
        )

    def run_keys_logic_thread(self, output_path):
        self.keys_status.value = "Extraindo chaves..."
        self.keys_progress.value = None
        self.keys_status.update()
        self.keys_progress.update()

        input_path = self.pending_input_path

        def task():
            try:
                resultado = self.keys_logic.extract_keys(input_path, output_path)
                
                if len(resultado) == 3:
                    success, msg, extracted_keys = resultado
                else:
                    success, msg = resultado
                    extracted_keys = []

                if success:
                    self.keys_found_list = extracted_keys
                    self.keys_status.value = f"{msg}\nPronto para baixar {len(self.keys_found_list)} XMLs."
                    self.keys_status.color = "green"
                    self.btn_download_sieg.disabled = False
                    self.btn_download_sieg.update()
                else:
                    self.keys_status.value = msg
                    self.keys_status.color = "red"
            except Exception as ex:
                self.keys_status.value = f"Erro fatal: {ex}"
                self.keys_status.color = "red"

            self.keys_progress.value = 0
            self.keys_status.update()
            self.keys_progress.update()

        threading.Thread(target=task).start()

    def request_download_folder(self, e):
        self.current_action = 'download_xml'
        self.folder_picker.get_directory_path()

    def run_download_thread(self, download_dir):
        if not self.keys_found_list:
            self.keys_status.value = "Nenhuma chave carregada."
            self.keys_status.update()
            return

        self.keys_status.value = "Iniciando downloads na Sieg..."
        self.keys_status.color = "blue"
        self.keys_progress.value = 0
        self.keys_status.update()
        self.keys_progress.update()

        def task():
            total = len(self.keys_found_list)
            success_count = 0
            errors = 0
            
            for i, chave in enumerate(self.keys_found_list):
                if i > 0 and i % 10 == 0:
                    time.sleep(1)

                ok, msg = self.sieg_manager.download_xml(chave, download_dir)
                
                if ok:
                    success_count += 1
                    print(f"[OK] Baixado: {chave}") 
                else:
                    errors += 1
                    print(f"[ERRO] Falha em {chave}: {msg}") 
                
                if i % 5 == 0:
                    pct = (i + 1) / total
                    self.keys_progress.value = pct
                    self.keys_status.value = f"Baixando... {i+1}/{total} (Sucesso: {success_count}, Erros: {errors})"
                    self.keys_status.update()
                    self.keys_progress.update()

            self.keys_status.value = f"Finalizado! Baixados: {success_count}, Falhas: {errors}."
            self.keys_status.color = "green" if errors == 0 else "orange"
            self.keys_progress.value = 1
            self.keys_status.update()
            self.keys_progress.update()

        threading.Thread(target=task).start()

    # =========================================================================
    # ABA 4: RELATÓRIO DIFAL / FCP (COMPLETA)
    # =========================================================================
    def open_difal_tab(self, e):
        label = "Relatório DIFAL"
        if label not in self.open_tabs:
            self.open_tabs.append(label)
            
            self.difal_folder_input = ft.TextField(label="Pasta dos XMLs", width=400)
            self.difal_status = ft.Text("Selecione a pasta para somar.", color=ft.Colors.GREY)
            
            # Checkbox Detalhado
            self.chk_detailed_report = ft.Checkbox(
                label="Incluir aba com relatório detalhado (Nota a Nota) no Excel", value=False 
            )

            # Botão Salvar
            self.btn_save_difal = ft.ElevatedButton(
                "Salvar Excel", icon=ft.Icons.SAVE_ALT, on_click=self.request_save_difal,
                disabled=True, bgcolor=ft.Colors.GREEN_100, color=ft.Colors.GREEN_900
            )

            # Botão de Erros (Invisível por padrão)
            self.btn_show_errors = ft.ElevatedButton(
                "Ver Arquivos com Erro", icon=ft.Icons.WARNING, bgcolor=ft.Colors.RED_100, 
                color=ft.Colors.RED_900, visible=False, on_click=self.show_error_dialog
            )

            # Tabela
            self.difal_table = ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("UF")),
                    ft.DataColumn(ft.Text("Total DIFAL"), numeric=True),
                    ft.DataColumn(ft.Text("Total FCP"), numeric=True),
                ],
                rows=[]
            )

            self.tab_contents[label] = ft.Column([
                ft.Text(label, size=24, weight="bold"),
                ft.Divider(),
                ft.Row([
                    self.difal_folder_input,
                    ft.IconButton(ft.Icons.FOLDER, on_click=lambda _: self.request_folder_difal()),
                    ft.ElevatedButton("Calcular Totais", icon=ft.Icons.CALCULATE, on_click=self.process_difal)
                ]),
                self.chk_detailed_report,
                ft.Row([self.btn_save_difal, self.btn_show_errors]),
                ft.Divider(),
                self.difal_status,
                
                # Container com Scroll para a tabela
                ft.Container(
                    content=ft.Column(
                        controls=[self.difal_table], 
                        scroll=ft.ScrollMode.AUTO
                    ), 
                    height=400, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=10, padding=10, expand=True
                )
            ])
        self.switch_tab(label)

    def request_folder_difal(self):
        self.current_action = 'difal_folder'
        self.folder_picker.get_directory_path()

    def request_save_difal(self, e):
        if not self.difal_data_summary:
            self.difal_status.value = "Não há dados para salvar."
            self.difal_status.update()
            return
        
        self.current_action = 'save_difal'
        self.save_file_picker.save_file(
            dialog_title="Salvar Relatório DIFAL",
            file_name=f"RELATORIO_DIFAL_{datetime.now().strftime('%d%m%Y')}.xlsx",
            allowed_extensions=["xlsx"]
        )

    def show_error_dialog(self, e):
        """Abre Popup com lista de erros"""
        lista_erro_visual = ft.ListView(expand=True, spacing=10, padding=20, auto_scroll=False)
        for erro in self.difal_errors_list:
            lista_erro_visual.controls.append(ft.Text(f"• {erro}", color="red", size=12))

        dlg = ft.AlertDialog(
            title=ft.Text("Arquivos Não Processados"),
            content=ft.Container(content=lista_erro_visual, width=500, height=300),
            actions=[ft.TextButton("Fechar", on_click=lambda e: self.page_instance.close_dialog())],
        )
        self.page_instance.dialog = dlg
        dlg.open = True
        self.page_instance.update()

    def process_difal(self, e):
        pasta = self.difal_folder_input.value
        if not pasta or not os.path.exists(pasta):
            self.difal_status.value = "Pasta inválida."
            self.difal_status.color = "red"
            self.difal_status.update()
            return

        self.difal_status.value = "Lendo XMLs e calculando..."
        self.difal_status.color = "blue"
        self.btn_save_difal.disabled = True
        self.btn_show_errors.visible = False
        self.btn_save_difal.update()
        self.btn_show_errors.update()
        self.difal_status.update()

        def task():
            # Retorna 5 valores: Sucesso, Msg, Resumo, Detalhes, Erros
            sucesso, msg, resumo, detalhes, erros = self.difal_logic.calcular_difal_por_pasta(pasta)
            
            if sucesso:
                self.difal_data_summary = resumo
                self.difal_data_details = detalhes
                self.difal_errors_list = erros
                
                self.difal_table.rows.clear()
                total_geral_difal = 0
                total_geral_fcp = 0

                for item in resumo:
                    val_difal = item['DIFAL']
                    val_fcp = item['FCP']
                    total_geral_difal += val_difal
                    total_geral_fcp += val_fcp

                    self.difal_table.rows.append(ft.DataRow(cells=[
                        ft.DataCell(ft.Text(item['UF'], weight="bold")),
                        ft.DataCell(ft.Text(f"R$ {val_difal:,.2f}")),
                        ft.DataCell(ft.Text(f"R$ {val_fcp:,.2f}")),
                    ]))
                
                self.difal_table.rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text("TOTAL GERAL", color="blue", weight="bold")),
                    ft.DataCell(ft.Text(f"R$ {total_geral_difal:,.2f}", color="blue", weight="bold")),
                    ft.DataCell(ft.Text(f"R$ {total_geral_fcp:,.2f}", color="blue", weight="bold")),
                ]))

                if erros:
                    self.difal_status.value = f"Finalizado com ALERTAS. {len(erros)} arquivos com erro."
                    self.difal_status.color = "orange"
                    self.btn_show_errors.visible = True
                else:
                    self.difal_status.value = f"Sucesso! {msg}"
                    self.difal_status.color = "green"
                
                self.btn_save_difal.disabled = False
                
            else:
                self.difal_status.value = f"Erro: {msg}"
                self.difal_status.color = "red"
            
            self.difal_status.update()
            self.difal_table.update()
            self.btn_save_difal.update()
            self.btn_show_errors.update()

        threading.Thread(target=task).start()