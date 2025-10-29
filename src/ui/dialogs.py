# src/ui/dialogs.py

import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime

class AddEditTransactionDialog(tk.Toplevel):
    def __init__(self, parent, categories, transaction_data=None, payment_methods=None): # NOVO: payment_methods
        super().__init__(parent)
        self.title("Adicionar/Editar Transação" if transaction_data is None else "Editar Transação")
        self.geometry("450x350") # Ajustado para caber mais campos
        self.grab_set()  
        self.trans_data = transaction_data
        self.result = None 

        self._create_widgets(categories, payment_methods) 
        if self.trans_data:
            self._load_data()

    def _create_widgets(self, categories, payment_methods):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Descrição:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.description_entry = ttk.Entry(main_frame, width=40)
        self.description_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(main_frame, text="Valor:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.value_entry = ttk.Entry(main_frame, width=40)
        self.value_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(main_frame, text="Tipo:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="Despesa")
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, values=["Ganho", "Despesa"], state="readonly")
        self.type_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(main_frame, text="Categoria:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(main_frame, textvariable=self.category_var, values=categories, state="readonly")
        self.category_combo.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        if categories:
            self.category_combo.set(categories[0])

        ttk.Label(main_frame, text="Meio Pagamento:").grid(row=4, column=0, sticky=tk.W, pady=5) 
        self.payment_method_var = tk.StringVar(value="Conta")
        self.payment_method_combo = ttk.Combobox(main_frame, textvariable=self.payment_method_var, 
                                                 values=payment_methods if payment_methods else ["Conta", "Dinheiro em Mãos"], state="readonly")
        self.payment_method_combo.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(main_frame, text="Data:").grid(row=5, column=0, sticky=tk.W, pady=5) 
        self.date_entry = DateEntry(main_frame, width=38, background='light gray', foreground='black', borderwidth=1,
                                    date_pattern='dd/mm/yyyy', locale='pt_BR')
        self.date_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5)
        self.date_entry.set_date(datetime.now())

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=10) 

        save_button = ttk.Button(button_frame, text="Salvar", command=self._on_save)
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancelar", command=self.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        main_frame.grid_columnconfigure(1, weight=1)

    def _load_data(self):
        self.description_entry.insert(0, self.trans_data.get('Descricao', ''))
        self.value_entry.insert(0, str(self.trans_data.get('Valor', '')))
        self.type_var.set(self.trans_data.get('Tipo', 'Despesa'))
        self.category_var.set(self.trans_data.get('Categoria', ''))
        self.payment_method_var.set(self.trans_data.get('MeioPagamento', 'Conta')) 
        
        date_str = self.trans_data.get('Data')
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() 
                self.date_entry.set_date(date_obj)
            except ValueError:
                pass 

    def _on_save(self):
        description = self.description_entry.get().strip()
        value_str = self.value_entry.get().strip().replace(',', '.')
        trans_type = self.type_var.get()
        category = self.category_var.get()
        payment_method = self.payment_method_var.get() 
        date_obj = self.date_entry.get_date()
        date_str = date_obj.strftime('%Y-%m-%d')

        try:
            value = float(value_str)
            if value <= 0:
                tk.messagebox.showwarning("Entrada Inválida", "O valor deve ser um número positivo.")
                return
        except ValueError:
            tk.messagebox.showwarning("Entrada Inválida", "Por favor, insira um valor numérico válido.")
            return
        
        if not description or not category or not payment_method: 
            tk.messagebox.showwarning("Dados Faltando", "Por favor, preencha todos os campos obrigatórios.")
            return

        self.result = {
            'Descricao': description,
            'Valor': value,
            'Tipo': trans_type,
            'Categoria': category,
            'Data': date_str,
            'MeioPagamento': payment_method 
        }
        self.destroy() 

class AddEditLoanDialog(tk.Toplevel):
    def __init__(self, parent, loan_data=None):
        super().__init__(parent)
        self.title("Registrar Empréstimo" if loan_data is None else "Editar Empréstimo")
        self.geometry("450x350")
        self.grab_set()
        self.loan_data = loan_data
        self.result = None

        self._create_widgets()
        if self.loan_data:
            self._load_data()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Tipo (Credor/Devedor)
        ttk.Label(main_frame, text="Tipo:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar(value="Devedor")
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, values=["Credor", "Devedor"], state="readonly")
        self.type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)

        # Parte Envolvida
        ttk.Label(main_frame, text="Parte Envolvida:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.party_entry = ttk.Entry(main_frame, width=40)
        self.party_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)

        # Valor Original
        ttk.Label(main_frame, text="Valor Original (R$):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.value_entry = ttk.Entry(main_frame, width=40)
        self.value_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)

        # Juros (%)
        ttk.Label(main_frame, text="Juros (% ao ano):").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.interest_entry = ttk.Entry(main_frame, width=40)
        self.interest_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)

        # Número de Parcelas
        ttk.Label(main_frame, text="Nº de Parcelas:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.installments_entry = ttk.Entry(main_frame, width=40)
        self.installments_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=5)

        # Botões
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        save_button = ttk.Button(button_frame, text="Salvar", command=self._on_save)
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancelar", command=self.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

        main_frame.grid_columnconfigure(1, weight=1)

    def _load_data(self):
        self.type_var.set(self.loan_data.get('Tipo', 'Devedor'))
        self.party_entry.insert(0, self.loan_data.get('ParteEnvolvida', ''))
        self.value_entry.insert(0, str(self.loan_data.get('ValorOriginal', '')))
        self.interest_entry.insert(0, str(self.loan_data.get('Juros%', '')))
        self.installments_entry.insert(0, str(self.loan_data.get('NumParcelas', '')))

    def _on_save(self):
        loan_type = self.type_var.get()
        involved_party = self.party_entry.get().strip()
        original_value_str = self.value_entry.get().strip().replace(',', '.')
        interest_rate_str = self.interest_entry.get().strip().replace(',', '.')
        num_installments_str = self.installments_entry.get().strip()

        try:
            original_value = float(original_value_str)
            interest_rate = float(interest_rate_str)
            num_installments = int(num_installments_str)

            if original_value <= 0 or num_installments <= 0:
                tk.messagebox.showwarning("Entrada Inválida", "Valor original e número de parcelas devem ser positivos.")
                return
        except ValueError:
            tk.messagebox.showwarning("Entrada Inválida", "Por favor, insira valores numéricos válidos para valor, juros e parcelas.")
            return

        if not involved_party:
            tk.messagebox.showwarning("Dados Faltando", "Por favor, preencha a parte envolvida.")
            return

        self.result = {
            'Tipo': loan_type,
            'ParteEnvolvida': involved_party,
            'ValorOriginal': original_value,
            'Juros%': interest_rate,
            'NumParcelas': num_installments
        }
        self.destroy()

class RecordInstallmentDialog(tk.Toplevel):
    def __init__(self, parent, loan_details):
        super().__init__(parent)
        self.title("Registrar Pagamento de Parcela")
        self.geometry("300x250") # Aumentado para caber o seletor de mês/ano
        self.grab_set()
        self.loan_details = loan_details
        self.result_amount = None
        self.result_month_year = None # NOVO: Para retornar o mês/ano de registro

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=f"Empréstimo: {self.loan_details['ParteEnvolvida']} ({self.loan_details['Tipo']})").pack(pady=5)
        ttk.Label(main_frame, text=f"Parcelas pagas: {self.loan_details['ParcelasPagas']} de {self.loan_details['NumParcelas']}").pack(pady=5)

        ttk.Label(main_frame, text="Valor da Parcela (R$):").pack(pady=5)
        self.amount_entry = ttk.Entry(main_frame)
        self.amount_entry.pack(pady=5)

        # NOVO: Seleção de Mês/Ano para registro do pagamento
        month_year_frame = ttk.Frame(main_frame)
        month_year_frame.pack(pady=5)
        ttk.Label(month_year_frame, text="Registrar em:").pack(side=tk.LEFT, padx=2)
        self.month_var = tk.StringVar(value=datetime.now().strftime("%m"))
        ttk.Combobox(month_year_frame, textvariable=self.month_var,
                     values=[f"{i:02d}" for i in range(1, 13)], state="readonly", width=5).pack(side=tk.LEFT, padx=2)
        self.year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        ttk.Combobox(month_year_frame, textvariable=self.year_var,
                     values=[str(y) for y in range(datetime.now().year - 2, datetime.now().year + 2)], # Range de anos
                     state="readonly", width=7).pack(side=tk.LEFT, padx=2)


        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        record_button = ttk.Button(button_frame, text="Registrar", command=self._on_record)
        record_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancelar", command=self.destroy)
        cancel_button.pack(side=tk.LEFT, padx=5)

    def _on_record(self):
        amount_str = self.amount_entry.get().strip().replace(',', '.')
        selected_month_year = f"{self.month_var.get()}-{self.year_var.get()}"
        try:
            amount = float(amount_str)
            if amount <= 0:
                tk.messagebox.showwarning("Entrada Inválida", "O valor da parcela deve ser um número positivo.")
                return
            self.result_amount = amount
            self.result_month_year = selected_month_year # Retorna o mês/ano selecionado
            self.destroy()
        except ValueError:
            tk.messagebox.showwarning("Entrada Inválida", "Por favor, insira um valor numérico válido.")