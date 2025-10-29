import pandas as pd
from datetime import datetime
import uuid 

# Importar as constantes diretamente do módulo core
from .core import CoreManager, DEFAULT_LOANS_SHEET, DEFAULT_CATEGORIES_SHEET # Adicionado DEFAULT_CATEGORIES_SHEET para a checagem de "Empréstimos"
from .monthly_control import MonthlyControlManager

class LoanManager:
    def __init__(self, core_manager: CoreManager, monthly_control_manager: MonthlyControlManager):
        self.core = core_manager
        self.monthly_control = monthly_control_manager

    def register_loan(self, loan_type: str, involved_party: str, original_value: float, interest_rate: float, num_installments: int):
        """
        Registra um novo empréstimo/dívida.
        Gera um ID único usando UUID.
        loan_type: 'Credor' ou 'Devedor'
        """
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

        data = {
            'ID': str(uuid.uuid4()), # Gera um ID UUID único para evitar conflitos
            'Tipo': loan_type,
            'ParteEnvolvida': involved_party,
            'ValorOriginal': float(original_value),
            'Juros%': float(interest_rate),
            'NumParcelas': int(num_installments),
            'ParcelasPagas': 0, # Inicialmente 0 parcelas pagas
            'Status': 'Aberto'
        }
        return self.core.add_loan(data)

    def record_installment_payment(self, loan_id: str, month_year: str, amount_paid: float):
        """
        Registra o pagamento/recebimento de uma parcela.
        Implementa a lógica de dividir o empréstimo se o valor pago for menor que o ValorOriginal.
        loan_id: ID do empréstimo a ser afetado.
        month_year: MM-YYYY (para registrar na aba mensal).
        amount_paid: Valor efetivamente pago/recebido para esta transação.
        """
        df_loans = self.core.get_loans()
        if df_loans.empty:
            print("Erro: Nenhum empréstimo encontrado para registrar parcela.")
            return False
        
        # Garante que 'ID' é string para comparação
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

        original_value = current_loan_data['ValorOriginal']
        current_paid_installments = current_loan_data['ParcelasPagas']
        total_installments = current_loan_data['NumParcelas']
        
        # Validação do valor pago
        if not isinstance(amount_paid, (int, float)) or amount_paid <= 0:
            print("Valor pago inválido. Deve ser um número positivo.")
            return False
        
        if amount_paid > original_value:
            print(f"Erro: Valor pago ({amount_paid}) excede o valor original do empréstimo ({original_value}).")
            return False

        # 1. Registrar a transação mensal com o amount_paid
        transaction_type = 'Ganho' if current_loan_data['Tipo'] == 'Credor' else 'Despesa'
        description = f"Pagamento/Recebimento de Empréstimo - {current_loan_data['ParteEnvolvida']}"
        today = datetime.now().strftime("%Y-%m-%d")

        # Usar a constante DEFAULT_CATEGORIES_SHEET do core
        if "Empréstimos" not in self.core.load_data(DEFAULT_CATEGORIES_SHEET)['Categoria'].tolist():
            self.core.add_category("Empréstimos")
        
        # Adiciona a transação ao controle mensal
        success_monthly_transaction = self.monthly_control.add_transaction(
            month_year, today, transaction_type, description, "Empréstimos", amount_paid
        )

        if not success_monthly_transaction:
            print("Falha ao registrar a transação mensal para o empréstimo. Abortando operação.")
            return False

        # 2. Lógica para fechar o empréstimo atual e/ou criar um novo
        if amount_paid < original_value:
            # Pagamento parcial: Fechar o empréstimo atual e criar um novo para o restante
            remaining_value = original_value - amount_paid
            
            # Atualiza o empréstimo atual para 'Fechado'
            success_update_current = self.core.update_loan(loan_id, {
                'Status': 'Fechado',
                'ParcelasPagas': current_paid_installments + 1 # Incrementa parcela mesmo se for parcial
            })

            if not success_update_current:
                print("Erro ao fechar o empréstimo atual. Abortando criação do novo empréstimo.")
                return False

            # Cria um novo empréstimo com o valor restante
            new_loan_data = {
                'Tipo': current_loan_data['Tipo'],
                'ParteEnvolvida': current_loan_data['ParteEnvolvida'],
                'ValorOriginal': remaining_value,
                'Juros%': current_loan_data['Juros%'],
                'NumParcelas': current_loan_data['NumParcelas'], 
                'ParcelasPagas': 0,
                'Status': 'Aberto'
            }
            success_new_loan = self.register_loan(**new_loan_data) 

            if not success_new_loan:
                print("Erro ao criar um novo empréstimo para o valor restante.")
                return False
            
            print(f"Empréstimo '{loan_id}' parcialmente pago. Novo empréstimo criado com valor restante R$ {remaining_value:.2f}.")
            return True

        else: # amount_paid == original_value (pagamento total)
            # Marcar o empréstimo como 'Fechado'
            success_update = self.core.update_loan(loan_id, {
                'Status': 'Fechado',
                'ParcelasPagas': total_installments # Considera todas as parcelas pagas
            })
            if not success_update:
                print("Erro ao fechar o empréstimo com pagamento total.")
                return False
            print(f"Empréstimo '{loan_id}' pago totalmente e fechado.")
            return True

    # --- NOVO MÉTODO: Excluir Empréstimo do Excel ---
    def delete_loan(self, loan_id: str):
        """Exclui um empréstimo específico da aba de empréstimos."""
        df = self.core.get_loans()
        if not df.empty:
            df['ID'] = df['ID'].astype(str) # Garante que IDs são strings para comparação
            loan_id = str(loan_id)
            
            # Use a constante DEFAULT_LOANS_SHEET diretamente
            return self.core.save_data(df[df['ID'] != loan_id], DEFAULT_LOANS_SHEET) # Filtra e salva a aba atualizada
        return False

    def get_active_loans(self):
        """Retorna os empréstimos com status 'Aberto'."""
        df = self.core.get_loans()
        if not df.empty:
            return df[df['Status'].astype(str).str.lower() == 'aberto'] 
        return pd.DataFrame()

    def get_loan_details(self, loan_id: str):
        """Retorna os detalhes de um empréstimo específico."""
        df = self.core.get_loans()
        if not df.empty:
            df['ID'] = df['ID'].astype(str)
            loan_id = str(loan_id)
            loan_row = df[df['ID'] == loan_id]
            return loan_row.iloc[0].to_dict() if not loan_row.empty else None
        return None