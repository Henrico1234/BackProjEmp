import pandas as pd
from datetime import datetime
import uuid 

from .core import CoreManager, DEFAULT_LOANS_SHEET, DEFAULT_CATEGORIES_SHEET
from .monthly_control import MonthlyControlManager

class LoanManager:
    def __init__(self, core_manager: CoreManager, monthly_control_manager: MonthlyControlManager):
        self.core = core_manager
        self.monthly_control = monthly_control_manager

    def register_loan(self, loan_type: str, involved_party: str, original_value: float, interest_rate: float, num_installments: int):
        
        if not all([loan_type, involved_party, original_value is not None, interest_rate is not None, num_installments is not None]):
            print("Dados incompletos para registrar empréstimo.")
            return False
        if not isinstance(original_value, (int, float)) or original_value <= 0:
            print("Valor original inválido.")
            return False
        if not isinstance(interest_rate, (int, float)) or interest_rate < 0:
            print("Taxa de juros inválida.")
            return False
        if not isinstance(num_installments, int) or num_installments <= 0:
            print("Número de parcelas inválido.")
            return False

        
        transaction_type = None
        description = None
        
        meio_pagamento = "Conta"

        if loan_type == 'Recebido':
            transaction_type = 'Ganho'
            description = f"Empréstimo Recebido - {involved_party}"
        elif loan_type == 'Concedido':
            transaction_type = 'Despesa'
            description = f"Empréstimo Concedido - {involved_party}"
        
        if transaction_type:
            today = datetime.now().strftime("%Y-%m-%d")
            month_year = datetime.now().strftime("%m-%Y")
            
            if "Empréstimos" not in self.core.load_data(DEFAULT_CATEGORIES_SHEET)['Categoria'].tolist():
                self.core.add_category("Empréstimos")
            
            
            success_monthly_transaction = self.monthly_control.add_transaction(
                month_year, 
                today, 
                transaction_type, 
                description, 
                "Empréstimos", 
                float(original_value),
                meio_pagamento
            )
            
            if not success_monthly_transaction:
                print(f"Falha ao registrar a transação de {transaction_type} inicial do empréstimo. Abortando.")
                return False

        data = {
            'ID': str(uuid.uuid4()), 
            'Tipo': loan_type,
            'ParteEnvolvida': involved_party,
            'ValorOriginal': float(original_value),
            'Juros%': float(interest_rate),
            'NumParcelas': int(num_installments),
            'ParcelasPagas': 0, 
            'Status': 'Aberto'
        }
        
        return self.core.add_loan(data)

    def record_installment_payment(self, loan_id: str, month_year: str, amount_paid: float):
        
        df_loans = self.core.get_loans()
        if df_loans.empty:
            print("Erro: Nenhum empréstimo encontrado para registrar parcela.")
            return False
        
        df_loans['ID'] = df_loans['ID'].astype(str)
        loan_id = str(loan_id)

        loan_row_index = df_loans[df_loans['ID'] == loan_id].index
        if loan_row_index.empty:
            print(f"Erro: Empréstimo com ID '{loan_id}' não encontrado.")
            return False
        
        current_loan_data = df_loans.loc[loan_row_index[0]].to_dict()

        if current_loan_data['Status'] == 'Fechado':
            print("Este empréstimo já está fechado.")
            return False

        original_value = float(current_loan_data['ValorOriginal'])
        current_paid_installments = int(current_loan_data['ParcelasPagas'])
        total_installments = int(current_loan_data['NumParcelas'])
        juros_percent = float(current_loan_data['Juros%'])
        
        if not isinstance(amount_paid, (int, float)) or amount_paid <= 0:
            print("Valor pago inválido. Deve ser um número positivo.")
            return False
        
        valor_total_com_juros = original_value * (1 + juros_percent / 100)
        
        valor_parcela_minima = valor_total_com_juros / total_installments
        
        if amount_paid < (valor_parcela_minima - 0.01): 
            print(f"Erro: Valor pago (R$ {amount_paid:.2f}) é menor que o valor mínimo da parcela (R$ {valor_parcela_minima:.2f}).")
            return False
        
        
        transaction_type = 'Ganho' if current_loan_data['Tipo'] == 'Concedido' else 'Despesa'
        description = f"Pagamento/Recebimento de Empréstimo - {current_loan_data['ParteEnvolvida']}"
        today = datetime.now().strftime("%Y-%m-%d")
        
        meio_pagamento = "Conta" 

        if "Empréstimos" not in self.core.load_data(DEFAULT_CATEGORIES_SHEET)['Categoria'].tolist():
            self.core.add_category("Empréstimos")
        
        
        success_monthly_transaction = self.monthly_control.add_transaction(
            month_year, 
            today, 
            transaction_type, 
            description, 
            "Empréstimos", 
            amount_paid,
            meio_pagamento
        )

        if not success_monthly_transaction:
            print("Falha ao registrar a transação mensal para o empréstimo. Abortando operação.")
            return False

        new_paid_installments = current_paid_installments + 1
        remaining_value = original_value - amount_paid
        
        new_status = 'Aberto'
        new_valor_original = remaining_value

        if new_paid_installments >= total_installments or remaining_value < 0.01:
            new_status = 'Fechado'
            new_valor_original = 0 
            new_paid_installments = total_installments 
            print(f"Empréstimo '{loan_id}' pago totalmente e fechado.")
        else:
            print(f"Empréstimo '{loan_id}' parcialmente pago. Valor restante R$ {remaining_value:.2f}.")

        
        success_update = self.core.update_loan(loan_id, {
            'Status': new_status,
            'ParcelasPagas': new_paid_installments,
            'ValorOriginal': new_valor_original
        })
        
        if not success_update:
            print("Erro ao atualizar o empréstimo.")
            return False
            
        return True

    def delete_loan(self, loan_id: str):
        df = self.core.get_loans()
        if not df.empty:
            df['ID'] = df['ID'].astype(str)
            loan_id = str(loan_id)
            
            return self.core.save_data(df[df['ID'] != loan_id], DEFAULT_LOANS_SHEET)
        return False

    def get_active_loans(self):
        df = self.core.get_loans()
        if not df.empty:
            return df[df['Status'].astype(str).str.lower() == 'aberto'] 
        return pd.DataFrame()

    def get_loan_details(self, loan_id: str):
        df = self.core.get_loans()
        if not df.empty:
            df['ID'] = df['ID'].astype(str)
            loan_id = str(loan_id)
            loan_row = df[df['ID'] == loan_id]
            return loan_row.iloc[0].to_dict() if not loan_row.empty else None
        return None