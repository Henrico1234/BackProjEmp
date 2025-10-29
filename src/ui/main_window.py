import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import pandas as pd

# Importar os módulos de gerenciamento
from src.modules.core import CoreManager, DEFAULT_CATEGORIES_SHEET, DEFAULT_BUDGET_SHEET, DEFAULT_LOANS_SHEET, DEFAULT_DEBTS_SHEET 
from src.modules.categories import CategoryManager
from src.modules.monthly_control import MonthlyControlManager
from src.modules.budget import BudgetManager
from src.modules.loans import LoanManager
from src.modules.reports import ReportManager
from src.modules.debts import DebtManager 

# Importações para elementos da UI
from src.ui.dialogs import AddEditTransactionDialog, AddEditLoanDialog, RecordInstallmentDialog
import src.ui.graphs as graphs_module 


class FinanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Finanças Pessoais")
        self.geometry("1200x800")
        self.minsize(900, 600)

        # Configuração de Estilos (Removido o 'style' do LabelFrame diretamente na criação)
        self.style = ttk.Style(self)
        self.style.theme_use('clam') # Tema base

        self.style.configure('.', font=('Segoe UI', 9)) 
        self.style.configure('TButton', font=('Segoe UI', 10, 'bold')) 
        self.style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold')) 

        # Estilo para a label dentro do LabelFrame (não para o LabelFrame em si)
        self.style.configure('TLabelFrame.Label', font=('Segoe UI', 11, 'bold'), foreground='#333333')

        self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#333333')

        self.style.map('Add.TButton', background=[('active', '#4CAF50'), ('!disabled', '#66BB6A')]) 
        self.style.map('Transfer.TButton', background=[('active', '#2196F3'), ('!disabled', '#42A5F5')]) 
        self.style.map('Danger.TButton', background=[('active', '#FF5252'), ('!disabled', '#EF5350')]) 
        self.style.map('Primary.TButton', background=[('active', '#78909C'), ('!disabled', '#90A4AE')]) 
        
        self.style.configure('Treeview', background='#ffffff', fieldbackground='#ffffff', foreground='#333333')
        self.style.map('Treeview', background=[('selected', '#B0E0E6')]) 
        self.style.configure('Treeview.Heading', background='#E0E0E0', foreground='#333333', relief='flat')
        self.style.map('Treeview.Heading', background=[('active', '#CCCCCC')])


        self.core_manager = CoreManager()
        self.category_manager = CategoryManager(self.core_manager)
        self.monthly_control_manager = MonthlyControlManager(self.core_manager)
        self.budget_manager = BudgetManager(self.core_manager, self.monthly_control_manager)
        self.loan_manager = LoanManager(self.core_manager, self.monthly_control_manager)
        self.report_manager = ReportManager(self.core_manager, self.monthly_control_manager)
        self.debt_manager = DebtManager(self.core_manager, self.monthly_control_manager) 

        self._current_month_year = datetime.now().strftime("%m-%Y")
        
        self._create_widgets()
        self._load_initial_data()
        self._update_monthly_view()

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """Método chamado ao tentar fechar a janela, garantindo o salvamento final."""
        self._manual_save_all_data(show_message=False)
        self.destroy()

    def _create_widgets(self):
        top_controls_frame = ttk.Frame(self, padding="10 10 10 0") 
        top_controls_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(top_controls_frame, text="Mês/Ano:", style='Header.TLabel').pack(side=tk.LEFT, padx=5)
        
        self.month_var = tk.StringVar(value=datetime.now().strftime("%m"))
        self.month_combo = ttk.Combobox(top_controls_frame, textvariable=self.month_var,
                                       values=[f"{i:02d}" for i in range(1, 13)], state="readonly", width=5)
        self.month_combo.pack(side=tk.LEFT, padx=2)
        self.month_combo.bind("<<ComboboxSelected>>", self._on_month_year_change)

        self.year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        self.year_combo = ttk.Combobox(top_controls_frame, textvariable=self.year_var,
                                      values=[str(y) for y in range(datetime.now().year - 5, datetime.now().year + 5)],
                                      state="readonly", width=7)
        self.year_combo.pack(side=tk.LEFT, padx=2)
        self.year_combo.bind("<<ComboboxSelected>>", self._on_month_year_change)

        save_now_button = ttk.Button(top_controls_frame, text="Salvar Agora", command=self._manual_save_all_data, style='Primary.TButton')
        save_now_button.pack(side=tk.RIGHT, padx=10)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady="0 10")

        self._create_monthly_tab()
        self._create_loans_tab()
        self._create_debts_tab()
        self._create_budget_tab()
        self._create_categories_tab()
        self._create_reports_tab() 
        
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

    def _on_month_year_change(self, event=None):
        selected_month = self.month_var.get()
        selected_year = self.year_var.get()
        self._current_month_year = f"{selected_month}-{selected_year}"
        print(f"Mês/Ano alterado para: {self._current_month_year}")
        self._update_monthly_view()
        self._update_budget_view()
        self._update_debts_view()

    def _on_tab_change(self, event):
        selected_tab = self.notebook.tab(self.notebook.select(), "text")
        if selected_tab == "Relatórios":
            self._update_report_category_combobox()
        elif selected_tab == "Dívidas Futuras / Boletos":
            self._update_debts_view()

    def _load_initial_data(self):
        if "Empréstimos" not in self.category_manager.get_all_categories():
            self.category_manager.add_category("Empréstimos")
        if "Ganhos" not in self.category_manager.get_all_categories():
            self.category_manager.add_category("Ganhos")
        if "Contas Fixas" not in self.category_manager.get_all_categories():
            self.category_manager.add_category("Contas Fixas")
        if "Boletos" not in self.category_manager.get_all_categories():
            self.category_manager.add_category("Boletos")
        
        self._update_category_comboboxes()
    
    def _manual_save_all_data(self, show_message=True):
        """Tenta salvar explicitamente todos os dados em todas as abas principais.
           show_message: Se True, exibe messagebox de sucesso/erro.
        """
        success_all = True
        
        try:
            # 1. Salvar Transações do Mês Atual (se houver alguma)
            monthly_df = self.monthly_control_manager.get_transactions_for_month(self._current_month_year)
            if not monthly_df.empty: 
                if not self.core_manager.save_data(monthly_df, self._current_month_year):
                    success_all = False

            # 2. Salvar Categorias
            current_categories_df = self.core_manager.get_categories()
            if not current_categories_df.empty:
                if not self.core_manager.save_data(current_categories_df, DEFAULT_CATEGORIES_SHEET):
                    success_all = False
            else:
                 if not self.core_manager.save_data(pd.DataFrame(columns=['Categoria']), DEFAULT_CATEGORIES_SHEET):
                     success_all = False

            # 3. Salvar Orçamentos (todos os orçamentos)
            current_budgets_df = self.core_manager.get_budgets()
            if not current_budgets_df.empty:
                if not self.core_manager.save_data(current_budgets_df, DEFAULT_BUDGET_SHEET):
                    success_all = False
            else:
                if not self.core_manager.save_data(pd.DataFrame(columns=['MesAno', 'Categoria', 'Limite']), DEFAULT_BUDGET_SHEET):
                    success_all = False

            # 4. Salvar Empréstimos (todos os empréstimos)
            current_loans_df = self.core_manager.get_loans()
            if not current_loans_df.empty:
                if not self.core_manager.save_data(current_loans_df, DEFAULT_LOANS_SHEET):
                    success_all = False
            else:
                if not self.core_manager.save_data(pd.DataFrame(columns=['ID', 'Tipo', 'ParteEnvolvida', 'ValorOriginal', 'Juros%', 'NumParcelas', 'ParcelasPagas', 'Status']), DEFAULT_LOANS_SHEET):
                    success_all = False

            # 5. Salvar Dívidas Futuras
            current_debts_df = self.core_manager.get_debts()
            if not current_debts_df.empty:
                if not self.core_manager.save_data(current_debts_df, DEFAULT_DEBTS_SHEET):
                    success_all = False
            else:
                if not self.core_manager.save_data(pd.DataFrame(columns=['ID', 'Descricao', 'Valor', 'DataVencimento', 'Status', 'Recorrencia', 'Categoria']), DEFAULT_DEBTS_SHEET):
                    success_all = False

        except Exception as e:
            print(f"Erro geral durante o salvamento manual: {e}")
            success_all = False
        
        if show_message:
            if success_all:
                messagebox.showinfo("Salvamento", "Todos os dados foram salvos com sucesso!")
            else:
                messagebox.showerror("Salvamento", "Ocorreu um erro ao salvar alguns dados. Verifique o console para mais detalhes.")
        
        return success_all

    # --- Aba Gerenciamento Mensal ---
    def _create_monthly_tab(self):
        self.monthly_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.monthly_tab, text="Gerenciamento Mensal")

        # Usar grid para o layout principal da aba mensal
        self.monthly_tab.grid_rowconfigure(0, weight=0) 
        self.monthly_tab.grid_rowconfigure(1, weight=0) 
        self.monthly_tab.grid_rowconfigure(2, weight=0) 
        self.monthly_tab.grid_rowconfigure(3, weight=1) 
        self.monthly_tab.grid_columnconfigure(0, weight=1) 
        self.monthly_tab.grid_columnconfigure(1, weight=1) 

        # 1. Card: Registrar Transação
        transaction_card = ttk.LabelFrame(self.monthly_tab, text="Registrar Transação", padding="15")
        transaction_card.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5) 

        transaction_card.grid_columnconfigure(1, weight=1)
        transaction_card.grid_columnconfigure(3, weight=1)
        transaction_card.grid_columnconfigure(5, weight=1)

        ttk.Label(transaction_card, text="Data:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.monthly_date_entry = DateEntry(transaction_card, width=12, background='light gray', 
                                             foreground='black', borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.monthly_date_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.monthly_date_entry.set_date(datetime.now())

        ttk.Label(transaction_card, text="Tipo:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.monthly_type_var = tk.StringVar(value="Despesa")
        self.monthly_type_combo = ttk.Combobox(transaction_card, textvariable=self.monthly_type_var,
                                              values=["Ganho", "Despesa"], state="readonly", width=10)
        self.monthly_type_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(transaction_card, text="Valor (R$):").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.monthly_value_entry = ttk.Entry(transaction_card, width=15)
        self.monthly_value_entry.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(transaction_card, text="Descrição:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.monthly_description_entry = ttk.Entry(transaction_card, width=30)
        self.monthly_description_entry.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(transaction_card, text="Categoria:").grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        self.monthly_category_var = tk.StringVar()
        self.monthly_category_combo = ttk.Combobox(transaction_card, textvariable=self.monthly_category_var,
                                                  values=self.category_manager.get_all_categories(), state="readonly")
        self.monthly_category_combo.grid(row=1, column=4, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(transaction_card, text="Meio Pagamento:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.monthly_payment_method_var = tk.StringVar(value="Conta")
        self.monthly_payment_method_combo = ttk.Combobox(transaction_card, textvariable=self.monthly_payment_method_var,
                                                          values=["Conta", "Dinheiro em Mãos"], state="readonly", width=15)
        self.monthly_payment_method_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        add_button = ttk.Button(transaction_card, text="Adicionar Lançamento", command=self._add_monthly_transaction, style='Add.TButton')
        add_button.grid(row=2, column=2, columnspan=4, sticky=(tk.W, tk.E), padx=5, pady=2)


        # 2. Card: Realizar Transferência
        transfer_card = ttk.LabelFrame(self.monthly_tab, text="Realizar Transferência", padding="15")
        transfer_card.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5) 

        transfer_card.grid_columnconfigure(1, weight=1)
        transfer_card.grid_columnconfigure(3, weight=1)
        transfer_card.grid_columnconfigure(5, weight=1)

        ttk.Label(transfer_card, text="Valor (R$):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.transfer_value_entry = ttk.Entry(transfer_card, width=15)
        self.transfer_value_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(transfer_card, text="De:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.transfer_from_var = tk.StringVar(value="Conta")
        self.transfer_from_combo = ttk.Combobox(transfer_card, textvariable=self.transfer_from_var,
                                                values=["Conta", "Dinheiro em Mãos"], state="readonly", width=10)
        self.transfer_from_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(transfer_card, text="Para:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.transfer_to_var = tk.StringVar(value="Dinheiro em Mãos")
        self.transfer_to_combo = ttk.Combobox(transfer_card, textvariable=self.transfer_to_var, 
                                              values=["Conta", "Dinheiro em Mãos"], state="readonly", width=15)
        self.transfer_to_combo.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=5, pady=2)

        transfer_button = ttk.Button(transfer_card, text="Realizar Transferência", command=self._perform_transfer, style='Transfer.TButton')
        transfer_button.grid(row=0, column=6, sticky=(tk.W, tk.E), padx=5, pady=2)


        # 3. Card: Saldos Mensais
        balance_card = ttk.LabelFrame(self.monthly_tab, text="Saldos Mensais", padding="15")
        balance_card.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N), padx=5, pady=5) 

        balance_card.grid_columnconfigure(0, weight=1)

        self.account_balance_label = ttk.Label(balance_card, text="Saldo em Conta: R$ 0.00", font=("Segoe UI", 10, 'bold'), foreground="#2196F3")
        self.account_balance_label.grid(row=0, column=0, sticky=tk.W, pady=2, padx=5)
        
        self.cash_balance_label = ttk.Label(balance_card, text="Saldo em Mãos: R$ 0.00", font=("Segoe UI", 10, 'bold'), foreground="#8B008B")
        self.cash_balance_label.grid(row=1, column=0, sticky=tk.W, pady=2, padx=5)

        self.gains_label = ttk.Label(balance_card, text="Ganhos do Mês: R$ 0.00", font=("Segoe UI", 10, 'bold'), foreground="#4CAF50")
        self.gains_label.grid(row=2, column=0, sticky=tk.W, pady=2, padx=5)
        
        self.expenses_label = ttk.Label(balance_card, text="Despesas do Mês: R$ 0.00", font=("Segoe UI", 10, 'bold'), foreground="#F44336")
        self.expenses_label.grid(row=3, column=0, sticky=tk.W, pady=2, padx=5)

        self.balance_label = ttk.Label(balance_card, text="Saldo Líquido: R$ 0.00", font=("Segoe UI", 12, 'bold'))
        self.balance_label.grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)


        # 4. Card: Lançamentos do Mês (Tabela)
        table_card = ttk.LabelFrame(self.monthly_tab, text="Lançamentos do Mês", padding="15")
        table_card.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5) 
        table_card.grid_rowconfigure(0, weight=1)
        table_card.grid_columnconfigure(0, weight=1)


        self.monthly_tree = ttk.Treeview(table_card, columns=("ID", "Data", "Tipo", "Descricao", "Categoria", "Valor", "MeioPagamento"), show="headings")
        self.monthly_tree.heading("ID", text="ID")
        self.monthly_tree.heading("Data", text="Data")
        self.monthly_tree.heading("Tipo", text="Tipo")
        self.monthly_tree.heading("Descricao", text="Descrição")
        self.monthly_tree.heading("Categoria", text="Categoria")
        self.monthly_tree.heading("Valor", text="Valor (R$)")
        self.monthly_tree.heading("MeioPagamento", text="Meio Pagamento")

        self.monthly_tree.column("ID", width=30, anchor=tk.CENTER)
        self.monthly_tree.column("Data", width=80, anchor=tk.CENTER)
        self.monthly_tree.column("Tipo", width=60, anchor=tk.CENTER)
        self.monthly_tree.column("Descricao", width=150, anchor=tk.W) 
        self.monthly_tree.column("Categoria", width=100, anchor=tk.W)
        self.monthly_tree.column("Valor", width=80, anchor=tk.E)
        self.monthly_tree.column("MeioPagamento", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_card, orient="vertical", command=self.monthly_tree.yview)
        self.monthly_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.monthly_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.monthly_tree.bind("<Double-1>", self._on_transaction_double_click)
        
        monthly_action_buttons_frame = ttk.Frame(table_card)
        monthly_action_buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        edit_transaction_button = ttk.Button(monthly_action_buttons_frame, text="Editar Selecionado", command=self._edit_selected_transaction, style='Primary.TButton')
        edit_transaction_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        delete_transaction_button = ttk.Button(monthly_action_buttons_frame, text="Excluir Selecionado", command=self._delete_selected_transaction, style='Danger.TButton')
        delete_transaction_button.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # 5. Card: Gráficos e Lembretes
        graphs_and_reminders_card = ttk.LabelFrame(self.monthly_tab, text="Gráficos e Lembretes", padding="15")
        graphs_and_reminders_card.grid(row=2, column=1, rowspan=3, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5) 

        graphs_and_reminders_card.grid_rowconfigure(0, weight=1) 
        graphs_and_reminders_card.grid_rowconfigure(1, weight=1) 
        graphs_and_reminders_card.grid_columnconfigure(0, weight=1)


        self.gains_expenses_graph_frame = ttk.Frame(graphs_and_reminders_card) 
        self.gains_expenses_graph_frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.gains_expenses_plotter = graphs_module.GraphPlotter(self.gains_expenses_graph_frame)

        self.debt_reminders_frame = ttk.Frame(graphs_and_reminders_card) 
        self.debt_reminders_frame.grid(row=1, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), pady=(10,0))
    def _update_balances_display(self, balances_info):
        """Calcula e atualiza os rótulos de saldo na aba mensal com base nos dados fornecidos."""
        # Extrair os valores do dicionário, usando 0.0 como padrão se a chave não existir
        account_balance = balances_info.get('Saldo em Conta', 0.0)
        cash_balance = balances_info.get('Saldo em Mãos', 0.0)
        gains = balances_info.get('Ganhos', 0.0)
        expenses = balances_info.get('Despesas', 0.0)
        net_balance = balances_info.get('Saldo Liquido', 0.0)

        # Atualizar os textos dos labels com os valores formatados para o padrão brasileiro (R$)
        self.account_balance_label.config(text=f"Saldo em Conta: R$ {account_balance:.2f}".replace('.', ','))
        self.cash_balance_label.config(text=f"Saldo em Mãos: R$ {cash_balance:.2f}".replace('.', ','))
        self.gains_label.config(text=f"Ganhos do Mês: R$ {gains:.2f}".replace('.', ','))
        self.expenses_label.config(text=f"Despesas do Mês: R$ {expenses:.2f}".replace('.', ','))
        self.balance_label.config(text=f"Saldo Líquido: R$ {net_balance:.2f}".replace('.', ','))
        
        # Mudar a cor do saldo líquido com base no valor (positivo/negativo)
        if net_balance > 0:
            self.balance_label.config(foreground="#4CAF50") # Verde
        elif net_balance < 0:
            self.balance_label.config(foreground="#F44336") # Vermelho
        else:
            self.balance_label.config(foreground="black") # Preto

    def _update_monthly_view(self):
        transactions_df = self.monthly_control_manager.get_transactions_for_month(self._current_month_year)
        
        for item in self.monthly_tree.get_children():
            self.monthly_tree.delete(item)

        if not transactions_df.empty:
            transactions_df = transactions_df.sort_values(by=['ID'], ascending=[True])
            
            for _, row in transactions_df.iterrows():
                valor_formatado = f"R$ {row['Valor']:.2f}".replace('.', ',')
                tags = ()
                if str(row['Tipo']).lower() == 'ganho':
                    tags = ('ganho',)
                elif str(row['Tipo']).lower() == 'despesa':
                    tags = ('despesa',)
                
                data_exibicao = str(row['Data']) if pd.notna(row['Data']) else "N/A"
                meio_pagamento_exibicao = str(row['MeioPagamento']) if 'MeioPagamento' in row and pd.notna(row['MeioPagamento']) else "N/A"

                self.monthly_tree.insert("", tk.END, iid=str(row['ID']), values=(
                    row['ID'], data_exibicao, row['Tipo'], row['Descricao'], row['Categoria'], valor_formatado, meio_pagamento_exibicao
                ), tags=tags)
        
        self.monthly_tree.tag_configure('ganho', foreground='green')
        self.monthly_tree.tag_configure('despesa', foreground='red')
        
        # Estilo para linhas alternadas
        for i, item in enumerate(self.monthly_tree.get_children()):
            base_tags = self.monthly_tree.item(item, 'tags')
            if i % 2 == 0:
                self.monthly_tree.item(item, tags=list(base_tags) + ['evenrow'])
            else:
                self.monthly_tree.item(item, tags=list(base_tags) + ['oddrow'])
        
        self.style.configure('evenrow', background='#F0F0F0')
        self.style.configure('oddrow', background='#FFFFFF')

        # --- CORREÇÃO E OTIMIZAÇÃO AQUI ---
        # 1. Busca os dados UMA VEZ usando o método correto
        balances_and_gains_data = self.monthly_control_manager.get_monthly_gains_expenses(self._current_month_year)
        
        # 2. Passa os dados para atualizar os labels de saldo
        self._update_balances_display(balances_and_gains_data)
        
        # 3. Reutiliza os mesmos dados para plotar o gráfico
        self.gains_expenses_plotter.plot_gains_vs_expenses(balances_and_gains_data['Ganhos'], balances_and_gains_data['Despesas'])

        self._update_category_comboboxes()
        self._update_graphs_and_reminders_area()


    def _add_monthly_transaction(self):
        date_str = self.monthly_date_entry.get_date().strftime('%Y-%m-%d')
        trans_type = self.monthly_type_var.get()
        description = self.monthly_description_entry.get().strip()
        category = self.monthly_category_var.get()
        value_str = self.monthly_value_entry.get().strip().replace(',', '.')
        payment_method = self.monthly_payment_method_var.get()

        if not description or not category or not value_str or not payment_method:
            messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos da transação (incluindo Meio Pagamento).")
            return
        try:
            value = float(value_str)
            if value <= 0:
                messagebox.showwarning("Valor Inválido", "O valor deve ser um número positivo.")
                return
        except ValueError:
            messagebox.showwarning("Valor Inválido", "Por favor, insira um valor numérico válido para o valor.")
            return

        success = self.monthly_control_manager.add_transaction(
            self._current_month_year, date_str, trans_type, description, category, value, payment_method
        )
        if success:
            messagebox.showinfo("Sucesso", "Lançamento adicionado com sucesso!")
            self._clear_monthly_transaction_fields()
            self._update_monthly_view()
            self._update_budget_view()
        else:
            messagebox.showerror("Erro", "Falha ao adicionar lançamento.")

    def _perform_transfer(self):
        transfer_value_str = self.transfer_value_entry.get().strip().replace(',', '.')
        transfer_from = self.transfer_from_var.get()
        transfer_to = self.transfer_to_var.get()

        if not transfer_value_str:
            messagebox.showwarning("Valor Vazio", "Por favor, insira um valor para a transferência.")
            return
        if transfer_from == transfer_to:
            messagebox.showwarning("Transferência Inválida", "Origem e Destino da transferência não podem ser o mesmo.")
            return

        try:
            transfer_value = float(transfer_value_str)
            if transfer_value <= 0:
                messagebox.showwarning("Valor Inválido", "O valor da transferência deve ser positivo.")
                return
        except ValueError:
            messagebox.showwarning("Valor Inválido", "Por favor, insira um valor numérico válido para a transferência.")
            return
        
        success = self.monthly_control_manager.add_transfer_transaction(
            self._current_month_year, transfer_value, transfer_from, transfer_to
        )
        
        if success:
            messagebox.showinfo("Sucesso", f"Transferência de R$ {transfer_value:,.2f} de {transfer_from} para {transfer_to} realizada!")
            self.transfer_value_entry.delete(0, tk.END)
            self._update_monthly_view()
        else:
            messagebox.showerror("Erro", "Falha ao realizar transferência.")


    def _get_selected_monthly_transaction_id(self):
        selected_item = self.monthly_tree.selection()
        if not selected_item:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione um lançamento na tabela.")
            return None
        return selected_item[0]

    def _edit_selected_transaction(self):
        item_id = self._get_selected_monthly_transaction_id()
        if not item_id:
            return

        transactions_df = self.monthly_control_manager.get_transactions_for_month(self._current_month_year)
        transaction_data_series = transactions_df[transactions_df['ID'].astype(str) == item_id]
        
        if transaction_data_series.empty:
            messagebox.showerror("Erro", "Lançamento não encontrado para edição.")
            return

        transaction_data = transaction_data_series.iloc[0].to_dict()

        payment_methods = ["Conta", "Dinheiro em Mãos"]
        dialog = AddEditTransactionDialog(self, self.category_manager.get_all_categories(), transaction_data, payment_methods=payment_methods)
        self.wait_window(dialog)
        
        if dialog.result:
            if messagebox.askyesno("Confirmar Edição", "Deseja realmente atualizar este lançamento?"):
                success = self.monthly_control_manager.update_transaction(
                    self._current_month_year, item_id, dialog.result
                )
                if success:
                    messagebox.showinfo("Sucesso", "Lançamento atualizado com sucesso!")
                    self._update_monthly_view()
                    self._update_budget_view()
                else:
                    messagebox.showerror("Erro", "Falha ao atualizar lançamento.")

    def _delete_selected_transaction(self):
        item_id = self._get_selected_monthly_transaction_id()
        if not item_id:
            return

        item_values = self.monthly_tree.item(item_id, 'values')
        description = item_values[3] if len(item_values) > 3 else "este lançamento"

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir '{description}'?"):
            success = self.monthly_control_manager.delete_transaction(
                self._current_month_year, item_id
            )
            if success:
                messagebox.showinfo("Sucesso", "Lançamento excluído com sucesso!")
                self._update_monthly_view()
                self._update_budget_view()
            else:
                messagebox.showerror("Erro", "Falha ao excluir lançamento.")

    def _on_transaction_double_click(self, event):
        self._edit_selected_transaction()

    def _clear_monthly_transaction_fields(self):
        self.monthly_description_entry.delete(0, tk.END)
        self.monthly_value_entry.delete(0, tk.END)
        self.monthly_date_entry.set_date(datetime.now())
        self.monthly_type_var.set("Despesa")
        self.monthly_payment_method_var.set("Conta")
        categories = self.category_manager.get_all_categories()
        if categories:
            self.monthly_category_combo.set(categories[0])

    def _update_graphs_and_reminders_area(self):
        """Atualiza a área de gráficos e lembretes na aba de Gerenciamento Mensal."""
        upcoming_debts = self.debt_manager.get_upcoming_or_overdue_debts(days_ahead=30) 
        
        if not upcoming_debts.empty:
            self._display_debt_reminders(upcoming_debts)
        else:
            self._display_expenses_by_category_graph()

    def _display_debt_reminders(self, upcoming_debts_df):
        """Mostra os lembretes de dívidas no frame de lembretes."""
        # Limpa o frame correto
        for widget in self.debt_reminders_frame.winfo_children(): # <-- CORRIGIDO
            widget.destroy()

        # Adiciona widgets ao frame correto
        ttk.Label(self.debt_reminders_frame, text="Lembretes de Dívidas:", style='Header.TLabel').pack(pady=5) # <-- CORRIGIDO
        
        self.debt_reminders_text = tk.Text(self.debt_reminders_frame, height=10, wrap=tk.WORD, font=('Segoe UI', 9), # <-- CORRIGIDO
                                            background='#ffffff', foreground='#333333', relief='flat', padx=5, pady=5)
        self.debt_reminders_text.pack(fill=tk.BOTH, expand=True)
        self.debt_reminders_text.config(state=tk.DISABLED)

        reminders_content = []
        if not upcoming_debts_df.empty:
            for _, debt in upcoming_debts_df.iterrows():
                status_text = ""
                debt_due_date = pd.to_datetime(debt['DataVencimento']).date() if pd.notna(debt['DataVencimento']) else None
                
                if str(debt['Status']).lower() == 'atrasado':
                    status_text = "!!! ATRASADO !!!"
                elif debt_due_date and debt_due_date < datetime.now().date(): 
                    status_text = "VENCIDO"
                elif debt_due_date and debt_due_date <= datetime.now().date() + timedelta(days=7): 
                    status_text = "Venc. Próximo"
                else:
                    status_text = "Em aberto"

                reminders_content.append(
                    f"{status_text} - {debt['Descricao']}: R$ {debt['Valor']:.2f} (Venc.: {debt_due_date.strftime('%d/%m/%Y') if debt_due_date else 'N/A'})"
                )
        
        if reminders_content:
            self.debt_reminders_text.config(state=tk.NORMAL)
            self.debt_reminders_text.delete(1.0, tk.END)
            for line in reminders_content:
                self.debt_reminders_text.insert(tk.END, line + "\n")
                if "ATRASADO" in line:
                    self.debt_reminders_text.tag_add("atrasado", "end-2l", "end-1c")
                    self.debt_reminders_text.tag_config("atrasado", foreground="red", font=('Segoe UI', 9, 'bold'))
                elif "VENCIDO" in line:
                    self.debt_reminders_text.tag_add("vencido", "end-2l", "end-1c")
                    self.debt_reminders_text.tag_config("vencido", foreground="orange", font=('Segoe UI', 9, 'bold'))
                elif "Venc. Próximo" in line:
                    self.debt_reminders_text.tag_add("proximo", "end-2l", "end-1c")
                    self.debt_reminders_text.tag_config("proximo", foreground="blue", font=('Segoe UI', 9, 'bold'))
            self.debt_reminders_text.config(state=tk.DISABLED)
        else:
            self.debt_reminders_text.config(state=tk.NORMAL)
            self.debt_reminders_text.delete(1.0, tk.END)
            self.debt_reminders_text.insert(tk.END, "Nenhuma dívida próxima ou atrasada.")
            self.debt_reminders_text.config(state=tk.DISABLED)

    def _display_expenses_by_category_graph(self):
        """Mostra o gráfico de despesas por categoria no frame de lembretes."""
        # Limpa o frame correto
        for widget in self.debt_reminders_frame.winfo_children(): # <-- CORRIGIDO
            widget.destroy() 
        
        # Adiciona o gráfico ao frame correto
        self.expenses_category_plotter = graphs_module.GraphPlotter(self.debt_reminders_frame) # <-- CORRIGIDO
        expenses_by_category_data = self.monthly_control_manager.get_expenses_by_category(self._current_month_year)
        self.expenses_category_plotter.plot_expenses_by_category(expenses_by_category_data)


    # --- Aba Categorias ---
    def _create_categories_tab(self):
        self.categories_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.categories_tab, text="Categorias")

        # Frame para adicionar nova categoria
        add_cat_frame = ttk.LabelFrame(self.categories_tab, text="Adicionar Nova Categoria", padding="15")
        add_cat_frame.pack(side=tk.TOP, fill=tk.X, pady=10)
        add_cat_frame.grid_columnconfigure(1, weight=1)
        add_cat_frame.grid_columnconfigure(2, weight=0)

        ttk.Label(add_cat_frame, text="Nome da Categoria:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.new_category_entry = ttk.Entry(add_cat_frame, width=30)
        self.new_category_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        add_cat_button = ttk.Button(add_cat_frame, text="Adicionar", command=self._add_category, style='Add.TButton')
        add_cat_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)

        # Frame para listar categorias existentes
        list_cat_frame = ttk.LabelFrame(self.categories_tab, text="Categorias Existentes", padding="15")
        list_cat_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=10)
        list_cat_frame.grid_rowconfigure(0, weight=1)
        list_cat_frame.grid_columnconfigure(0, weight=1)

        # CRIA os widgets da lista PRIMEIRO
        self.category_listbox = tk.Listbox(list_cat_frame, height=10, background='#ffffff', foreground='#333333', relief='flat', selectbackground='#B0E0E6', selectforeground='#333333')
        self.category_listbox.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W), padx=5, pady=5)

        cat_scrollbar = ttk.Scrollbar(list_cat_frame, orient="vertical", command=self.category_listbox.yview)
        self.category_listbox.configure(yscrollcommand=cat_scrollbar.set)
        cat_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        remove_cat_button = ttk.Button(list_cat_frame, text="Remover Selecionada", command=self._remove_category, style='Danger.TButton')
        remove_cat_button.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=5)

        # AGORA, com tudo criado, atualiza a lista com os dados
        self._update_category_list() # <-- CORRIGIDO: Adicionado 'self.' e movido para o final

    def _add_category(self):
        category_name = self.new_category_entry.get().strip()
        if not category_name:
            messagebox.showwarning("Campo Vazio", "Por favor, digite o nome da categoria.")
            return

        if self.category_manager.add_category(category_name):
            messagebox.showinfo("Sucesso", f"Categoria '{category_name}' adicionada.")
            self.new_category_entry.delete(0, tk.END)
            self._update_category_list()
            self._update_category_comboboxes()
            self._update_report_category_combobox()
        else:
            messagebox.showwarning("Categoria Existente", f"A categoria '{category_name}' já existe ou houve um erro.")

    def _remove_category(self):
        selected_index = self.category_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma categoria para remover.")
            return
        
        category_name = self.category_listbox.get(selected_index[0])
        
        fixed_categories = ["Empréstimos", "Ganhos", "Contas Fixas", "Boletos", "Transferência"] 
        if category_name in fixed_categories:
            messagebox.showwarning("Categoria Fixa", f"A categoria '{category_name}' não pode ser removida.")
            return

        if messagebox.askyesno("Confirmar Remoção", f"Tem certeza que deseja remover a categoria '{category_name}'?"):
            if self.category_manager.remove_category(category_name):
                messagebox.showinfo("Sucesso", f"Categoria '{category_name}' removida.")
                self._update_category_list()
                self._update_category_comboboxes()
                self._update_report_category_combobox()
            else:
                messagebox.showerror("Erro", "Falha ao remover a categoria.")

    def _update_category_list(self):
        self.category_listbox.delete(0, tk.END)
        categories = self.category_manager.get_all_categories()
        for cat in categories:
            self.category_listbox.insert(tk.END, cat)

    def _update_category_comboboxes(self):
        categories = self.category_manager.get_all_categories()
        self.monthly_category_combo['values'] = categories
        if categories:
            if self.monthly_category_var.get() not in categories:
                self.monthly_category_combo.set(categories[0])
        else:
            self.monthly_category_combo.set("")

        self.budget_category_combo['values'] = categories
        if categories:
            if self.budget_category_var.get() not in categories:
                self.budget_category_combo.set(categories[0])
        else:
            self.budget_category_combo.set("")
        if hasattr(self, 'debts_category_combo'):
            self.debts_category_combo['values'] = categories
            if categories:
                if self.debts_category_var.get() not in categories:
                    self.debts_category_combo.set(categories[0])
            else:
                self.debts_category_combo.set("")


    # --- Aba Orçamento ---
    def _create_budget_tab(self):
        self.budget_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.budget_tab, text="Orçamento")

        set_budget_frame = ttk.LabelFrame(self.budget_tab, text="Definir Orçamento por Categoria", padding="15")
        set_budget_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        set_budget_frame.grid_columnconfigure(1, weight=1) 
        set_budget_frame.grid_columnconfigure(3, weight=1) 
        set_budget_frame.grid_columnconfigure(4, weight=0)

        ttk.Label(set_budget_frame, text="Categoria:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.budget_category_var = tk.StringVar()
        self.budget_category_combo = ttk.Combobox(set_budget_frame, textvariable=self.budget_category_var,
                                                  values=self.category_manager.get_all_categories(), state="readonly", width=25)
        self.budget_category_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(set_budget_frame, text="Limite (R$):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.budget_limit_entry = ttk.Entry(set_budget_frame, width=15)
        self.budget_limit_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5, pady=2)

        set_budget_button = ttk.Button(set_budget_frame, text="Definir Limite", command=self._set_budget_limit, style='Primary.TButton')
        set_budget_button.grid(row=0, column=4, sticky=(tk.W, tk.E), padx=5, pady=2)

        view_budget_frame = ttk.LabelFrame(self.budget_tab, text="Orçamentos do Mês", padding="15")
        view_budget_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=10)

        view_budget_frame.grid_rowconfigure(0, weight=1)
        view_budget_frame.grid_columnconfigure(0, weight=1)

        self.budget_tree = ttk.Treeview(view_budget_frame, columns=("Categoria", "Limite", "GastoAtual", "Status"), show="headings")
        self.budget_tree.heading("Categoria", text="Categoria")
        self.budget_tree.heading("Limite", text="Limite (R$)")
        self.budget_tree.heading("GastoAtual", text="Gasto Atual (R$)")
        self.budget_tree.heading("Status", text="Status")

        self.budget_tree.column("Categoria", width=150, anchor=tk.W)
        self.budget_tree.column("Limite", width=100, anchor=tk.E)
        self.budget_tree.column("GastoAtual", width=120, anchor=tk.E)
        self.budget_tree.column("Status", width=100, anchor=tk.CENTER)

        budget_scrollbar = ttk.Scrollbar(view_budget_frame, orient="vertical", command=self.budget_tree.yview)
        self.budget_tree.configure(yscrollcommand=budget_scrollbar.set)
        budget_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.budget_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.budget_tree.bind("<Double-1>", self._on_budget_double_click)

        budget_action_buttons_frame = ttk.Frame(view_budget_frame)
        budget_action_buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        edit_budget_button = ttk.Button(budget_action_buttons_frame, text="Editar Orçamento", command=self._edit_selected_budget, style='Primary.TButton')
        edit_budget_button.pack(side=tk.LEFT, pady=2, fill=tk.X, expand=True)

        delete_budget_button = ttk.Button(budget_action_buttons_frame, text="Excluir Orçamento", command=self._delete_selected_budget, style='Danger.TButton')
        delete_budget_button.pack(side=tk.LEFT, pady=2, fill=tk.X, expand=True)

        self._update_budget_view()


    def _set_budget_limit(self):
        category = self.budget_category_var.get()
        limit_str = self.budget_limit_entry.get().strip().replace(',', '.')

        if not category or not limit_str:
            messagebox.showwarning("Campos Vazios", "Por favor, selecione uma categoria e insira um limite.")
            return
        
        try:
            limit = float(limit_str)
            if limit < 0:
                messagebox.showwarning("Valor Inválido", "O limite do orçamento deve ser um número não negativo.")
                return
        except ValueError:
            messagebox.showwarning("Valor Inválida", "Por favor, insira um valor numérico válido.")
            return

        success = self.budget_manager.set_budget_limit(self._current_month_year, category, limit)
        if success:
            messagebox.showinfo("Sucesso", f"Orçamento para '{category}' definido como R$ {limit:,.2f} para o mês {self._current_month_year}.")
            self.budget_limit_entry.delete(0, tk.END)
            self._update_budget_view()
        else:
            messagebox.showerror("Erro", "Falha ao definir orçamento.")

    def _update_budget_view(self):
        for item in self.budget_tree.get_children():
            self.budget_tree.delete(item)

        budgets_df = self.budget_manager.get_budgets_for_month(self._current_month_year)
        expenses_by_category = self.monthly_control_manager.get_expenses_by_category(self._current_month_year)
        
        all_relevant_categories = set(budgets_df['Categoria'].tolist() if not budgets_df.empty else [])
        all_relevant_categories.update(expenses_by_category.index.tolist())

        for cat in sorted(list(all_relevant_categories)):
            limit = budgets_df[budgets_df['Categoria'] == cat]['Limite'].iloc[0] if cat in budgets_df['Categoria'].values else None
            current_expense = expenses_by_category.get(cat, 0)

            status = "Sem Limite"
            tags = ('neutral',)
            limit_display = "N/A"

            if limit is not None:
                limit_display = f"R$ {limit:,.2f}".replace('.', ',')
                if current_expense > limit:
                    status = f"Excedido em R$ {current_expense - limit:,.2f}".replace('.', ',')
                    tags = ('exceeded',)
                else:
                    status = "Dentro do Limite"
                    tags = ('within_limit',)
            
            self.budget_tree.insert("", tk.END, iid=cat, values=(
                cat, limit_display, f"R$ {current_expense:,.2f}".replace('.', ','), status
            ), tags=tags)
        # Estilo para linhas alternadas
        for i, item in enumerate(self.budget_tree.get_children()):
            if i % 2 == 0:
                self.budget_tree.item(item, tags=('evenrow',))
            else:
                self.budget_tree.item(item, tags=('oddrow',))


    def _get_selected_budget_category(self):
        selected_item = self.budget_tree.selection()
        if not selected_item:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione um orçamento na tabela.")
            return None
        return selected_item[0]

    def _edit_selected_budget(self):
        category = self._get_selected_budget_category()
        if not category:
            return

        budgets_df = self.budget_manager.get_budgets_for_month(self._current_month_year)
        current_limit = budgets_df[budgets_df['Categoria'] == category]['Limite'].iloc[0] if category in budgets_df['Categoria'].values else 0.0

        edit_dialog = tk.Toplevel(self)
        edit_dialog.title(f"Editar Orçamento: {category}")
        edit_dialog.grab_set()
        
        edit_dialog.grid_columnconfigure(1, weight=1)

        ttk.Label(edit_dialog, text="Categoria:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        ttk.Label(edit_dialog, text=category, font=('Segoe UI', 10, 'bold')).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Label(edit_dialog, text="Novo Limite (R$):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        new_limit_entry = ttk.Entry(edit_dialog)
        new_limit_entry.insert(0, str(current_limit))
        new_limit_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)


        def save_edit():
            new_limit_str = new_limit_entry.get().strip().replace(',', '.')
            try:
                new_limit = float(new_limit_str)
                if new_limit < 0:
                    messagebox.showwarning("Valor Inválido", "O limite deve ser um número não negativo.")
                    return
                
                if messagebox.askyesno("Confirmar Edição", f"Deseja alterar o limite de '{category}' para R$ {new_limit:,.2f}?"):
                    success = self.budget_manager.set_budget_limit(self._current_month_year, category, new_limit)
                    if success:
                        messagebox.showinfo("Sucesso", "Orçamento atualizado!")
                        self._update_budget_view()
                        edit_dialog.destroy()
                    else:
                        messagebox.showerror("Erro", "Falha ao atualizar orçamento.")
            except ValueError:
                messagebox.showwarning("Valor Inválida", "Por favor, insira um valor numérico válido.")

        button_frame = ttk.Frame(edit_dialog)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Salvar", command=save_edit, style='Primary.TButton').pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(button_frame, text="Cancelar", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=5, expand=True)


    def _delete_selected_budget(self):
        category = self._get_selected_budget_category()
        if not category:
            return
        
        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o orçamento para '{category}' deste mês?"):
            success = self.budget_manager.delete_budget(self._current_month_year, category)
            if success:
                messagebox.showinfo("Sucesso", "Orçamento excluído com sucesso!")
                self._update_budget_view()
            else:
                messagebox.showerror("Erro", "Falha ao excluir orçamento. Verifique o console.")

    def _on_budget_double_click(self, event):
        self._edit_selected_budget()


    # --- Aba Empréstimos ---
    def _create_loans_tab(self):
        self.loans_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.loans_tab, text="Empréstimos")

        register_loan_frame = ttk.LabelFrame(self.loans_tab, text="Registrar Novo Empréstimo", padding="15")
        register_loan_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        register_loan_button = ttk.Button(register_loan_frame, text="Novo Empréstimo", command=self._add_loan, style='Add.TButton')
        register_loan_button.pack(pady=5)

        list_loans_frame = ttk.LabelFrame(self.loans_tab, text="Empréstimos Registrados", padding="15")
        list_loans_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=10)

        list_loans_frame.grid_rowconfigure(0, weight=1)
        list_loans_frame.grid_columnconfigure(0, weight=1)

        self.loans_tree = ttk.Treeview(list_loans_frame, columns=("ID", "Tipo", "ParteEnvolvida", "ValorOriginal", "Juros%", "NumParcelas", "ParcelasPagas", "Status"), show="headings")
        self.loans_tree.heading("ID", text="ID")
        self.loans_tree.heading("Tipo", text="Tipo")
        self.loans_tree.heading("ParteEnvolvida", text="Parte Envolvida")
        self.loans_tree.heading("ValorOriginal", text="Valor Original")
        self.loans_tree.heading("Juros%", text="Juros (%)")
        self.loans_tree.heading("NumParcelas", text="Nº Parcelas")
        self.loans_tree.heading("ParcelasPagas", text="Parcelas Pagas")
        self.loans_tree.heading("Status", text="Status")

        self.loans_tree.column("ID", width=30, anchor=tk.CENTER)
        self.loans_tree.column("Tipo", width=60, anchor=tk.CENTER)
        self.loans_tree.column("ParteEnvolvida", width=120, anchor=tk.W)
        self.loans_tree.column("ValorOriginal", width=100, anchor=tk.E)
        self.loans_tree.column("Juros%", width=60, anchor=tk.E)
        self.loans_tree.column("NumParcelas", width=80, anchor=tk.CENTER)
        self.loans_tree.column("ParcelasPagas", width=80, anchor=tk.CENTER)
        self.loans_tree.column("Status", width=70, anchor=tk.CENTER)

        loans_scrollbar = ttk.Scrollbar(list_loans_frame, orient="vertical", command=self.loans_tree.yview)
        self.loans_tree.configure(yscrollcommand=loans_scrollbar.set)
        loans_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.loans_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.loans_tree.bind("<Double-1>", self._on_loan_double_click)

        loan_action_buttons_frame = ttk.Frame(list_loans_frame)
        loan_action_buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        record_payment_button = ttk.Button(loan_action_buttons_frame, text="Registrar Pagamento/Recebimento de Parcela", command=self._record_installment, style='Primary.TButton')
        record_payment_button.pack(side=tk.LEFT, pady=2, fill=tk.X, expand=True)

        edit_loan_button = ttk.Button(loan_action_buttons_frame, text="Editar Selecionado", command=self._edit_selected_loan, style='Primary.TButton')
        edit_loan_button.pack(side=tk.LEFT, pady=2, fill=tk.X, expand=True)

        delete_loan_button = ttk.Button(loan_action_buttons_frame, text="Excluir Selecionado", command=self._delete_selected_loan, style='Danger.TButton')
        delete_loan_button.pack(side=tk.LEFT, pady=2, fill=tk.X, expand=True)
        
        self._update_loans_view()

    def _add_loan(self):
        dialog = AddEditLoanDialog(self)
        self.wait_window(dialog)

        if dialog.result:
            success = self.loan_manager.register_loan(
                dialog.result['Tipo'],
                dialog.result['ParteEnvolvida'],
                dialog.result['ValorOriginal'],
                dialog.result['Juros%'],
                dialog.result['NumParcelas']
            )
            if success:
                messagebox.showinfo("Sucesso", "Empréstimo/Dívida registrado com sucesso!")
                self._update_loans_view()
            else:
                messagebox.showerror("Erro", "Falha ao registrar empréstimo/dívida. Verifique o console.")

    def _record_installment(self):
        selected_item = self.loans_tree.selection()
        if not selected_item:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione um empréstimo para registrar o pagamento.")
            return
        
        loan_id = selected_item[0] 
        loan_details = self.loan_manager.get_loan_details(loan_id)

        if not loan_details:
            messagebox.showerror("Erro", "Detalhes do empréstimo não encontrados.")
            return
        
        if loan_details['Status'] == 'Fechado':
            messagebox.showwarning("Empréstimo Fechado", "Este empréstimo já está fechado.")
            return

        dialog = RecordInstallmentDialog(self, loan_details)
        self.wait_window(dialog)

        if dialog.result_amount is not None:
            success = self.loan_manager.record_installment_payment(
                loan_id, dialog.result_month_year, dialog.result_amount # Passa o mês/ano do diálogo
            )
            if success:
                messagebox.showinfo("Sucesso", "Parcela registrada com sucesso! Verifique a aba 'Gerenciamento Mensal' e a lista de empréstimos.")
                self._update_loans_view()
                self._update_monthly_view() 
                self._update_budget_view() 
            else:
                messagebox.showerror("Erro", "Falha ao registrar a parcela. Verifique o console para mais detalhes.")
        else:
            print("Registro de parcela cancelado ou valor inválido.")

    def _get_selected_loan_id(self):
        selected_item = self.loans_tree.selection()
        if not selected_item:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione um empréstimo na tabela.")
            return None
        return selected_item[0]

    def _edit_selected_loan(self):
        loan_id = self._get_selected_loan_id()
        if not loan_id:
            return

        loan_details = self.loan_manager.get_loan_details(loan_id)
        
        if not loan_details:
            messagebox.showerror("Erro", "Empréstimo não encontrado para edição.")
            return

        dialog = AddEditLoanDialog(self, loan_details)
        self.wait_window(dialog)
        
        if dialog.result:
            if messagebox.askyesno("Confirmar Edição", "Deseja realmente atualizar este empréstimo?"):
                success = self.core_manager.update_loan(loan_id, {
                    'Tipo': dialog.result['Tipo'],
                    'ParteEnvolvida': dialog.result['ParteEnvolvida'],
                    'ValorOriginal': dialog.result['ValorOriginal'],
                    'Juros%': dialog.result['Juros%'],
                    'NumParcelas': dialog.result['NumParcelas']
                })
                if success:
                    messagebox.showinfo("Sucesso", "Empréstimo atualizado com sucesso!")
                    self._update_loans_view()
                else:
                    messagebox.showerror("Erro", "Falha ao atualizar empréstimo.")

    def _delete_selected_loan(self):
        loan_id = self._get_selected_loan_id()
        if not loan_id:
            return

        item_values = self.loans_tree.item(loan_id, 'values')
        involved_party = item_values[2] if len(item_values) > 2 else "este empréstimo" 

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir o empréstimo com '{involved_party}'?"):
            success = self.loan_manager.delete_loan(loan_id)
            if success:
                messagebox.showinfo("Sucesso", "Empréstimo excluído com sucesso!")
                self._update_loans_view()
            else:
                messagebox.showerror("Erro", "Falha ao excluir empréstimo. Verifique o console.")

    def _on_loan_double_click(self, event):
        self._edit_selected_loan()

    def _update_loans_view(self):
        for item in self.loans_tree.get_children():
            self.loans_tree.delete(item)

        loans_df = self.loan_manager.core.get_loans() 
        
        if not loans_df.empty:
            for _, row in loans_df.iterrows():
                # Garante que valor_original e juros são floats, ou 0.0 se forem None/NaN
                valor_original = float(row.get('ValorOriginal', 0.0)) if pd.notna(row.get('ValorOriginal')) else 0.0
                juros = float(row.get('Juros%', 0.0)) if pd.notna(row.get('Juros%')) else 0.0

                self.loans_tree.insert("", tk.END, iid=str(row['ID']), values=(
                    row['ID'], row['Tipo'], row['ParteEnvolvida'], 
                    f"R$ {valor_original:,.2f}".replace('.', ','), f"{juros:.2f}",
                    row['NumParcelas'], row['ParcelasPagas'], row['Status']
                ))
        # Estilo para linhas alternadas
        for i, item in enumerate(self.loans_tree.get_children()):
            if i % 2 == 0:
                self.loans_tree.item(item, tags=('evenrow',))
            else:
                self.loans_tree.item(item, tags=('oddrow',))

    # --- NOVO: Aba de Dívidas Futuras / Boletos ---
    def _create_debts_tab(self):
        self.debts_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.debts_tab, text="Dívidas Futuras / Boletos")

        # Removendo o 'style' do LabelFrame
        add_debt_frame = ttk.LabelFrame(self.debts_tab, text="Registrar Nova Dívida/Boleto", padding="15")
        add_debt_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        add_debt_frame.grid_columnconfigure(1, weight=1)
        add_debt_frame.grid_columnconfigure(3, weight=1)
        add_debt_frame.grid_columnconfigure(5, weight=1)

        ttk.Label(add_debt_frame, text="Descrição:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.debts_description_entry = ttk.Entry(add_debt_frame, width=30)
        self.debts_description_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(add_debt_frame, text="Valor (R$):").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.debts_value_entry = ttk.Entry(add_debt_frame, width=15)
        self.debts_value_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(add_debt_frame, text="Vencimento:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=2)
        self.debts_due_date_entry = DateEntry(add_debt_frame, width=12, background='light gray',
                                             foreground='black', borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.debts_due_date_entry.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.debts_due_date_entry.set_date(datetime.now().date())

        ttk.Label(add_debt_frame, text="Recorrência:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.debts_recurrence_var = tk.StringVar(value="Unica")
        self.debts_recurrence_combo = ttk.Combobox(add_debt_frame, textvariable=self.debts_recurrence_var,
                                                   values=["Unica", "Mensal", "Anual"], state="readonly", width=10)
        self.debts_recurrence_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(add_debt_frame, text="Nº de Meses (para recorrência):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=2)
        self.debts_recurrence_months_entry = ttk.Entry(add_debt_frame, width=15)
        self.debts_recurrence_months_entry.insert(0, "1")
        self.debts_recurrence_months_entry.grid(row=1, column=3, sticky=(tk.W, tk.E), padx=5, pady=2)

        ttk.Label(add_debt_frame, text="Categoria:").grid(row=1, column=4, sticky=tk.W, padx=5, pady=2)
        self.debts_category_var = tk.StringVar()
        self.debts_category_combo = ttk.Combobox(add_debt_frame, textvariable=self.debts_category_var,
                                                 values=self.category_manager.get_all_categories(), state="readonly", width=25)
        self.debts_category_combo.grid(row=1, column=5, sticky=(tk.W, tk.E), padx=5, pady=2)
        if self.category_manager.get_all_categories():
            self.debts_category_combo.set(self.category_manager.get_all_categories()[0])

        add_debt_button = ttk.Button(add_debt_frame, text="Adicionar Dívida", command=self._add_debt, style='Add.TButton')
        add_debt_button.grid(row=2, column=0, columnspan=6, sticky=(tk.W, tk.E), padx=5, pady=5)

        view_debts_frame = ttk.LabelFrame(self.debts_tab, text="Dívidas Futuras e Boletos", padding="15")
        view_debts_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=10)

        view_debts_frame.grid_rowconfigure(0, weight=1)
        view_debts_frame.grid_columnconfigure(0, weight=1)

        self.debts_tree = ttk.Treeview(view_debts_frame, columns=("ID", "Descricao", "Valor", "Vencimento", "Status", "Recorrencia", "Categoria"), show="headings")
        self.debts_tree.heading("ID", text="ID")
        self.debts_tree.heading("Descricao", text="Descrição")
        self.debts_tree.heading("Valor", text="Valor (R$)")
        self.debts_tree.heading("Vencimento", text="Vencimento")
        self.debts_tree.heading("Status", text="Status")
        self.debts_tree.heading("Recorrencia", text="Recorrência")
        self.debts_tree.heading("Categoria", text="Categoria")

        self.debts_tree.column("ID", width=30, anchor=tk.CENTER)
        self.debts_tree.column("Descricao", width=150, anchor=tk.W)
        self.debts_tree.column("Valor", width=80, anchor=tk.E)
        self.debts_tree.column("Vencimento", width=90, anchor=tk.CENTER)
        self.debts_tree.column("Status", width=70, anchor=tk.CENTER)
        self.debts_tree.column("Recorrencia", width=70, anchor=tk.CENTER)
        self.debts_tree.column("Categoria", width=100, anchor=tk.W)

        debts_scrollbar = ttk.Scrollbar(view_debts_frame, orient="vertical", command=self.debts_tree.yview)
        self.debts_tree.configure(yscrollcommand=debts_scrollbar.set)
        debts_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.debts_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))

        self.debts_tree.bind("<Double-1>", self._on_debt_double_click)

        debt_action_buttons_frame = ttk.Frame(view_debts_frame)
        debt_action_buttons_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        mark_paid_debt_button = ttk.Button(debt_action_buttons_frame, text="Marcar como Pago", command=self._mark_debt_as_paid, style='Primary.TButton')
        mark_paid_debt_button.pack(side=tk.LEFT, pady=2, fill=tk.X, expand=True)

        edit_debt_button = ttk.Button(debt_action_buttons_frame, text="Editar Selecionado", command=self._edit_selected_debt, style='Primary.TButton')
        edit_debt_button.pack(side=tk.LEFT, pady=2, fill=tk.X, expand=True)

        delete_debt_button = ttk.Button(debt_action_buttons_frame, text="Excluir Selecionado", command=self._delete_selected_debt_action, style='Danger.TButton')
        delete_debt_button.pack(side=tk.LEFT, pady=2, fill=tk.X, expand=True)

        self.debts_tree.tag_configure('atrasado', foreground='red', font=('Segoe UI', 9, 'bold'))
        self.debts_tree.tag_configure('vencido', foreground='orange', font=('Segoe UI', 9, 'bold'))
        self.debts_tree.tag_configure('pago', foreground='#607D8B', font=('Segoe UI', 9, 'italic'))
        self.debts_tree.tag_configure('aberto', foreground='#333333')

        self._update_debts_view()

    def _add_debt(self):
        description = self.debts_description_entry.get().strip()
        value_str = self.debts_value_entry.get().strip().replace(',', '.')
        due_date_obj = self.debts_due_date_entry.get_date()
        due_date_str = due_date_obj.strftime('%Y-%m-%d')
        recurrence = self.debts_recurrence_var.get()
        recurrence_months_str = self.debts_recurrence_months_entry.get().strip() 
        category = self.debts_category_var.get()

        if not description or not value_str or not category:
            messagebox.showwarning("Campos Vazios", "Por favor, preencha todos os campos obrigatórios para a dívida.")
            return
        
        try:
            value = float(value_str)
            if value <= 0:
                messagebox.showwarning("Valor Inválido", "O valor deve ser um número positivo.")
                return
        except ValueError:
            messagebox.showwarning("Valor Inválido", "Por favor, insira um valor numérico válido para o valor.")
            return

        recurrence_months = 0
        if recurrence in ["Mensal", "Anual"]:
            try:
                recurrence_months = int(recurrence_months_str)
                if recurrence_months <= 0:
                    messagebox.showwarning("Meses Inválidos", "O número de meses para recorrência deve ser maior que zero.")
                    return
            except ValueError:
                messagebox.showwarning("Meses Inválidos", "Por favor, insira um número inteiro válido para 'Nº de Meses'.")
                return

        success = self.debt_manager.add_debt(description, value, due_date_str, 'Aberto', recurrence, recurrence_months, category)
        if success:
            messagebox.showinfo("Sucesso", "Dívida(s) adicionada(s) com sucesso!")
            self._clear_debt_fields()
            self._update_debts_view()
            self._update_monthly_view() 
        else:
            messagebox.showerror("Erro", "Falha ao adicionar dívida.")

    def _clear_debt_fields(self):
        self.debts_description_entry.delete(0, tk.END)
        self.debts_value_entry.delete(0, tk.END)
        self.debts_due_date_entry.set_date(datetime.now().date())
        self.debts_recurrence_var.set("Unica")
        self.debts_recurrence_months_entry.delete(0, tk.END)
        self.debts_recurrence_months_entry.insert(0, "1")
        categories = self.category_manager.get_all_categories()
        if categories:
            self.debts_category_combo.set(categories[0])

    def _update_debts_view(self):
        for item in self.debts_tree.get_children():
            self.debts_tree.delete(item)

        # Filtrar dívidas pelo mês e ano selecionados na GUI
        all_debts_df = self.debt_manager.get_all_debts(month_year_filter=self._current_month_year)
        
        if not all_debts_df.empty:
            for _, debt in all_debts_df.iterrows():
                valor_formatado = f"R$ {debt['Valor']:.2f}".replace('.', ',')
                vencimento_formatado = debt['DataVencimento'].strftime('%d/%m/%Y') if pd.notna(debt['DataVencimento']) else "N/A"
                
                tags = ('aberto',)
                if str(debt['Status']).lower() == 'atrasado':
                    tags = ('atrasado',)
                elif str(debt['Status']).lower() == 'pago':
                    tags = ('pago',)
                elif pd.notna(debt['DataVencimento']) and debt['DataVencimento'] < datetime.now().date() and str(debt['Status']).lower() == 'aberto':
                    tags = ('vencido',)

                self.debts_tree.insert("", tk.END, iid=str(debt['ID']), values=(
                    debt['ID'], debt['Descricao'], valor_formatado, vencimento_formatado,
                    debt['Status'], debt['Recorrencia'], debt['Categoria']
                ), tags=tags)
        # Estilo para linhas alternadas
        for i, item in enumerate(self.debts_tree.get_children()):
            if i % 2 == 0:
                self.debts_tree.item(item, tags=('evenrow',))
            else:
                self.debts_tree.item(item, tags=('oddrow',))
        
    def _get_selected_debt_id(self):
        selected_item = self.debts_tree.selection()
        if not selected_item:
            messagebox.showwarning("Nenhuma Seleção", "Por favor, selecione uma dívida na tabela.")
            return None
        return selected_item[0]

    def _mark_debt_as_paid(self):
        debt_id = self._get_selected_debt_id()
        if not debt_id:
            return

        debt_details = self.debt_manager.get_all_debts()
        debt_row = debt_details[debt_details['ID'].astype(str) == debt_id].iloc[0]
        
        if str(debt_row['Status']).lower() == 'pago':
            messagebox.showinfo("Dívida já Paga", "Esta dívida já foi marcada como paga.")
            return

        if messagebox.askyesno("Confirmar Pagamento", f"Deseja marcar '{debt_row['Descricao']}' como PAGA e registrar o pagamento em {self._current_month_year}?"):
            success = self.debt_manager.mark_debt_as_paid(debt_id, self._current_month_year)
            if success:
                messagebox.showinfo("Sucesso", "Dívida marcada como PAGA e lançamento adicionado!")
                self._update_debts_view()
                self._update_monthly_view() 
            else:
                messagebox.showerror("Erro", "Falha ao marcar dívida como paga.")

    def _edit_selected_debt(self):
        debt_id = self._get_selected_debt_id()
        if not debt_id:
            return

        debt_details = self.debt_manager.get_all_debts()
        debt_row = debt_details[debt_details['ID'].astype(str) == debt_id].iloc[0].to_dict()

        edit_dialog = tk.Toplevel(self)
        edit_dialog.title(f"Editar Dívida: {debt_row['Descricao']}")
        edit_dialog.grab_set()

        edit_dialog.grid_columnconfigure(1, weight=1)

        ttk.Label(edit_dialog, text="Descrição:").grid(row=0, column=0, sticky=tk.W, pady=5, padx=5)
        desc_entry = ttk.Entry(edit_dialog, width=40)
        desc_entry.insert(0, debt_row['Descricao'])
        desc_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Label(edit_dialog, text="Valor (R$):").grid(row=1, column=0, sticky=tk.W, pady=5, padx=5)
        value_entry = ttk.Entry(edit_dialog, width=40)
        value_entry.insert(0, str(debt_row['Valor']))
        value_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Label(edit_dialog, text="Vencimento:").grid(row=2, column=0, sticky=tk.W, pady=5, padx=5)
        due_date_entry = DateEntry(edit_dialog, width=38, background='light gray', foreground='black', borderwidth=1,
                                    date_pattern='dd/mm/yyyy', locale='pt_BR')
        if pd.notna(debt_row['DataVencimento']):
            due_date_entry.set_date(debt_row['DataVencimento'])
        due_date_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Label(edit_dialog, text="Recorrência:").grid(row=3, column=0, sticky=tk.W, pady=5, padx=5)
        recurrence_var = tk.StringVar(value=debt_row['Recorrencia'])
        recurrence_combo = ttk.Combobox(edit_dialog, textvariable=recurrence_var,
                                        values=["Unica", "Mensal", "Anual"], state="readonly", width=38)
        recurrence_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)

        ttk.Label(edit_dialog, text="Nº de Meses (para recorrência):").grid(row=4, column=0, sticky=tk.W, pady=5, padx=5)
        recurrence_months_entry = ttk.Entry(edit_dialog, width=38)
        if 'RecorrenciaMeses' in debt_row and pd.notna(debt_row['RecorrenciaMeses']):
            recurrence_months_entry.insert(0, str(int(debt_row['RecorrenciaMeses'])))
        else:
            recurrence_months_entry.insert(0, "1")
        recurrence_months_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)


        ttk.Label(edit_dialog, text="Categoria:").grid(row=5, column=0, sticky=tk.W, pady=5, padx=5)
        category_var = tk.StringVar(value=debt_row['Categoria'])
        category_combo = ttk.Combobox(edit_dialog, textvariable=category_var,
                                      values=self.category_manager.get_all_categories(), state="readonly", width=38)
        category_combo.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)


        def save_edit():
            new_description = desc_entry.get().strip()
            new_value_str = value_entry.get().strip().replace(',', '.')
            new_due_date_obj = due_date_entry.get_date()
            new_due_date_str = new_due_date_obj.strftime('%Y-%m-%d')
            new_recurrence = recurrence_var.get()
            new_category = category_var.get()
            new_recurrence_months_str = recurrence_months_entry.get().strip() 

            try:
                new_value = float(new_value_str)
                if new_value <= 0:
                    messagebox.showwarning("Entrada Inválida", "O valor deve ser um número positivo.")
                    return
            except ValueError:
                messagebox.showwarning("Entrada Inválida", "Por favor, insira um valor numérico válido para o valor.")
                return
            
            new_recurrence_months = 0
            if new_recurrence in ["Mensal", "Anual"]:
                try:
                    new_recurrence_months = int(new_recurrence_months_str)
                    if new_recurrence_months <= 0:
                        messagebox.showwarning("Meses Inválidos", "O número de meses para recorrência deve ser maior que zero.")
                        return
                except ValueError:
                    messagebox.showwarning("Meses Inválidos", "Por favor, insira um número inteiro válido para 'Nº de Meses'.")
                    return


            if not new_description or not new_category:
                messagebox.showwarning("Dados Faltando", "Descrição e Categoria são obrigatórias.")
                return

            if messagebox.askyesno("Confirmar Edição", f"Deseja atualizar a dívida '{debt_row['Descricao']}'?"):
                success = self.debt_manager.update_debt(debt_id, {
                    'Descricao': new_description,
                    'Valor': new_value,
                    'DataVencimento': new_due_date_str,
                    'Recorrencia': new_recurrence,
                    'RecorrenciaMeses': new_recurrence_months, 
                    'Categoria': new_category
                })
                if success:
                    messagebox.showinfo("Sucesso", "Dívida atualizada!")
                    self._update_debts_view()
                    self._update_monthly_view() 
                    edit_dialog.destroy()
                else:
                    messagebox.showerror("Erro", "Falha ao atualizar dívida.")
        
        button_frame = ttk.Frame(edit_dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="Salvar", command=save_edit, style='Primary.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=edit_dialog.destroy).pack(side=tk.LEFT, padx=5)

    def _delete_selected_debt_action(self): 
        debt_id = self._get_selected_debt_id()
        if not debt_id:
            return

        debt_details = self.debt_manager.get_all_debts()
        debt_row = debt_details[debt_details['ID'].astype(str) == debt_id].iloc[0]
        description = debt_row['Descricao']

        if messagebox.askyesno("Confirmar Exclusão", f"Tem certeza que deseja excluir a dívida '{description}'?"):
            success = self.debt_manager.delete_debt(debt_id)
            if success:
                messagebox.showinfo("Sucesso", "Dívida excluída com sucesso!")
                self._update_debts_view()
                self._update_monthly_view()
            else:
                messagebox.showerror("Erro", "Falha ao excluir dívida. Verifique o console.")

    def _on_debt_double_click(self, event):
        self._edit_selected_debt()


    # --- Aba Relatórios ---
    def _create_reports_tab(self):
        self.reports_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.reports_tab, text="Relatórios")

        filter_frame = ttk.LabelFrame(self.reports_tab, text="Filtros do Relatório", padding="15")
        filter_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        filter_frame.grid_columnconfigure(1, weight=1)
        filter_frame.grid_columnconfigure(3, weight=1)

        ttk.Label(filter_frame, text="Data Inicial:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.report_start_date_entry = DateEntry(filter_frame, width=12, background='light gray',
                                                foreground='black', borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.report_start_date_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.report_start_date_entry.set_date(datetime(datetime.now().year, 1, 1))

        ttk.Label(filter_frame, text="Data Final:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=2)
        self.report_end_date_entry = DateEntry(filter_frame, width=12, background='light gray',
                                              foreground='black', borderwidth=1, date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.report_end_date_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5, pady=2)
        self.report_end_date_entry.set_date(datetime.now())

        ttk.Label(filter_frame, text="Categoria:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.report_category_var = tk.StringVar(value="Todas")
        self.report_category_combo = ttk.Combobox(filter_frame, textvariable=self.report_category_var,
                                                  values=[], state="readonly", width=25)
        self.report_category_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        self._update_report_category_combobox()

        generate_report_button = ttk.Button(filter_frame, text="Gerar Relatório", command=self._generate_report, style='Primary.TButton')
        generate_report_button.grid(row=1, column=2, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        summary_frame = ttk.LabelFrame(self.reports_tab, text="Resumo Financeiro", padding="15")
        summary_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

        self.report_gains_label = ttk.Label(summary_frame, text="Ganhos Totais: R$ 0.00", font=("Segoe UI", 11, "bold"), foreground="green")
        self.report_gains_label.pack(anchor=tk.W, pady=2)
        self.report_expenses_label = ttk.Label(summary_frame, text="Despesas Totais: R$ 0.00", font=("Segoe UI", 11, "bold"), foreground="red")
        self.report_expenses_label.pack(anchor=tk.W, pady=2)
        self.report_balance_label = ttk.Label(summary_frame, text="Saldo Total: R$ 0.00", font=("Segoe UI", 12, "bold"))
        self.report_balance_label.pack(anchor=tk.W, pady=5)

        ttk.Label(summary_frame, text="Despesas por Categoria:").pack(anchor=tk.W, pady=2)
        self.report_expenses_by_category_text = tk.Text(summary_frame, height=5, wrap=tk.WORD, font=("Segoe UI", 9),
                                                          background='#ffffff', foreground='#333333', relief='flat', padx=5, pady=5)
        self.report_expenses_by_category_text.pack(fill=tk.X, expand=True, padx=5, pady=2)
        self.report_expenses_by_category_text.config(state=tk.DISABLED)

        ttk.Label(summary_frame, text="Ganhos por Categoria:").pack(anchor=tk.W, pady=2)
        self.report_gains_by_category_text = tk.Text(summary_frame, height=5, wrap=tk.WORD, font=("Segoe UI", 9),
                                                       background='#ffffff', foreground='#333333', relief='flat', padx=5, pady=5)
        self.report_gains_by_category_text.pack(fill=tk.X, expand=True, padx=5, pady=2)
        self.report_gains_by_category_text.config(state=tk.DISABLED)

        export_buttons_frame = ttk.Frame(self.reports_tab)
        export_buttons_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        export_csv_button = ttk.Button(export_buttons_frame, text="Exportar para CSV", command=self._export_report_csv, style='Primary.TButton')
        export_csv_button.pack(side=tk.LEFT, padx=5, expand=True)

        export_pdf_button = ttk.Button(export_buttons_frame, text="Exportar para PDF", command=self._export_report_pdf, style='Primary.TButton')
        export_pdf_button.pack(side=tk.LEFT, padx=5, expand=True)
        

    def _update_report_category_combobox(self):
        all_categories_for_report = ["Todas"] + self.category_manager.get_all_categories()
        self.report_category_combo['values'] = all_categories_for_report
        if self.report_category_var.get() not in all_categories_for_report:
            self.report_category_var.set("Todas")


    def _generate_report(self):
        start_date_obj = self.report_start_date_entry.get_date()
        end_date_obj = self.report_end_date_entry.get_date()
        category_filter = self.report_category_var.get()

        if start_date_obj > end_date_obj:
            messagebox.showwarning("Datas Inválidas", "A data inicial não pode ser posterior à data final.")
            return

        summary = self.report_manager.generate_financial_summary(start_date_obj, end_date_obj, category_filter)

        self.report_gains_label.config(text=f"Ganhos Totais: R$ {summary['Ganhos Totais']:,.2f}".replace('.', ','))
        self.report_expenses_label.config(text=f"Despesas Totais: R$ {summary['Despesas Totais']:,.2f}".replace('.', ','))
        
        balance_color = "black"
        if summary['Saldo Total'] > 0:
            balance_color = "green"
        elif summary['Saldo Total'] < 0:
            balance_color = "red"
        self.report_balance_label.config(text=f"Saldo Total: R$ {summary['Saldo Total']:,.2f}".replace('.', ','), foreground=balance_color)

        self.report_expenses_by_category_text.config(state=tk.NORMAL)
        self.report_expenses_by_category_text.delete(1.0, tk.END)
        if not summary['Despesas por Categoria'].empty:
            for cat, val in summary['Despesas por Categoria'].items():
                self.report_expenses_by_category_text.insert(tk.END, f"- {cat}: R$ {val:,.2f}\n".replace('.', ','))
        else:
            self.report_expenses_by_category_text.insert(tk.END, "Nenhuma despesa para exibir.\n")
        self.report_expenses_by_category_text.config(state=tk.DISABLED)

        self.report_gains_by_category_text.config(state=tk.NORMAL)
        self.report_gains_by_category_text.delete(1.0, tk.END)
        if not summary['Ganhos por Categoria'].empty:
            for cat, val in summary['Ganhos por Categoria'].items():
                self.report_gains_by_category_text.insert(tk.END, f"- {cat}: R$ {val:,.2f}\n".replace('.', ','))
        else:
            self.report_gains_by_category_text.insert(tk.END, "Nenhum ganho para exibir.\n")
        self.report_gains_by_category_text.config(state=tk.DISABLED)


    def _export_report_csv(self):
        start_date_obj = self.report_start_date_entry.get_date()
        end_date_obj = self.report_end_date_entry.get_date()
        category_filter = self.report_category_var.get()

        if start_date_obj > end_date_obj:
            messagebox.showwarning("Datas Inválidas", "A data inicial não pode ser posterior à data final.")
            return

        summary_data = self.report_manager.generate_financial_summary(start_date_obj, end_date_obj, category_filter)
        
        filename = f"relatorio_financeiro_{start_date_obj.strftime('%Y%m%d')}_a_{end_date_obj.strftime('%Y%m%d')}"
        if category_filter.lower() != "todas":
            filename += f"_{category_filter.replace(' ', '_')}"
        filename += ".csv"

        if self.report_manager.export_summary_to_csv(summary_data, filename=filename):
            messagebox.showinfo("Exportar CSV", f"Relatório exportado com sucesso para '{filename}' na pasta 'data/' do programa.")
        else:
            messagebox.showerror("Erro ao Exportar", "Ocorreu um erro ao exportar o relatório para CSV. Verifique o console.")
            
    def _export_report_pdf(self):
        start_date_obj = self.report_start_date_entry.get_date()
        end_date_obj = self.report_end_date_entry.get_date()
        category_filter = self.report_category_var.get()

        if start_date_obj > end_date_obj:
            messagebox.showwarning("Datas Inválidas", "A data inicial não pode ser posterior à data final.")
            return

        summary_data = self.report_manager.generate_financial_summary(start_date_obj, end_date_obj, category_filter)
        
        filename = f"relatorio_financeiro_{start_date_obj.strftime('%Y%m%d')}_a_{end_date_obj.strftime('%Y%m%d')}"
        if category_filter.lower() != "todas":
            filename += f"_{category_filter.replace(' ', '_')}"
        filename += ".pdf"

        if self.report_manager.export_summary_to_pdf(summary_data, filename=filename):
            messagebox.showinfo("Exportar PDF", f"Relatório exportado com sucesso para '{filename}' na pasta 'data/' do programa.")
        else:
            messagebox.showerror("Erro ao Exportar", "Ocorreu um erro ao exportar o relatório para PDF. Verifique o console.")