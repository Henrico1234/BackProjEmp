from .core import CoreManager
import pandas as pd
from datetime import datetime

class MonthlyControlManager:
    def __init__(self, core_manager: CoreManager):
        self.core = core_manager

    def add_transaction(self, month_year: str, date: str, trans_type: str, description: str, category: str, value: float, payment_method: str = "Conta"):
        """
        Adiciona um novo lançamento (ganho ou despesa).
        month_year: MM-YYYY
        date:YYYY-MM-DD
        payment_method: 'Conta' ou 'Dinheiro em Mãos'
        """
        if not all([month_year, date, trans_type, description, category, value is not None, payment_method]):
            print("Dados incompletos para adicionar transação.")
            return False
        if not isinstance(value, (int, float)) or value < 0:
            print("Valor inválido para transação.")
            return False
        
        data = {
            'Data': date,
            'Tipo': trans_type,
            'Descricao': description,
            'Categoria': category,
            'Valor': float(value),
            'MeioPagamento': payment_method
        }
        return self.core.add_transaction(month_year, data)

    def add_transfer_transaction(self, month_year: str, value: float, from_method: str, to_method: str):
        """
        Registra uma transferência entre meios de pagamento (Conta e Dinheiro em Mãos).
        Cria duas transações: uma despesa na origem e um ganho no destino.
        """
        if not all([month_year, value is not None, from_method, to_method]):
            print("Dados incompletos para realizar transferência.")
            return False
        if not isinstance(value, (int, float)) or value <= 0:
            print("Valor inválido para transferência.")
            return False
        if from_method == to_method:
            print("Origem e destino da transferência não podem ser o mesmo.")
            return False

        today_date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Transação de Saída (Despesa na origem)
        success_out = self.add_transaction(
            month_year, today_date_str, 'Despesa', 
            f"Transferência para {to_method}", "Transferência", value, from_method
        )
        
        # Transação de Entrada (Ganho no destino)
        success_in = self.add_transaction(
            month_year, today_date_str, 'Ganho', 
            f"Transferência de {from_method}", "Transferência", value, to_method
        )
        
        return success_out and success_in

    def get_transactions_for_month(self, month_year: str):
        """Retorna um DataFrame com todas as transações de um dado mês/ano."""
        df = self.core.get_monthly_transactions(month_year)
        # Garante que as colunas esperadas existam para evitar KeyError
        expected_cols = ['ID', 'Data', 'Tipo', 'Descricao', 'Categoria', 'Valor', 'MeioPagamento']
        for col in expected_cols:
            if col not in df.columns:
                df[col] = "Conta" if col == 'MeioPagamento' else None 
        return df[expected_cols] if not df.empty else pd.DataFrame(columns=expected_cols)

    def calculate_monthly_balance(self, month_year: str):
        """Calcula o saldo total do mês (ganhos - despesas)."""
        df = self.get_transactions_for_month(month_year)
        if df.empty:
            return 0.0, 0.0, 0.0 # Ganhos, Despesas, Saldo

        gains = df[df['Tipo'].astype(str).str.lower() == 'ganho']['Valor'].sum()
        expenses = df[df['Tipo'].astype(str).str.lower() == 'despesa']['Valor'].sum()
        balance = gains - expenses
        return gains, expenses, balance

    def calculate_detailed_balance(self, month_year: str, payment_method: str):
        """
        Calcula o saldo (ganhos - despesas) para um meio de pagamento específico.
        payment_method: 'Conta' ou 'Dinheiro em Mãos'
        """
        df = self.get_transactions_for_month(month_year)
        if df.empty:
            return 0.0, 0.0, 0.0 # Ganhos, Despesas, Saldo
        
        filtered_df = df[df['MeioPagamento'].astype(str).str.lower() == payment_method.lower()]
        
        gains = filtered_df[filtered_df['Tipo'].astype(str).str.lower() == 'ganho']['Valor'].sum()
        expenses = filtered_df[filtered_df['Tipo'].astype(str).str.lower() == 'despesa']['Valor'].sum()
        balance = gains - expenses
        return gains, expenses, balance

    def update_transaction(self, month_year: str, transaction_id: str, new_data: dict):
        """Atualiza um lançamento existente."""
        if 'MeioPagamento' not in new_data:
            current_df = self.get_transactions_for_month(month_year)
            current_trans = current_df[current_df['ID'].astype(str) == transaction_id]
            if not current_trans.empty and 'MeioPagamento' in current_trans.columns:
                new_data['MeioPagamento'] = current_trans.iloc[0]['MeioPagamento']
            else:
                new_data['MeioPagamento'] = "Conta" # Padrão se não encontrar

        return self.core.update_transaction(month_year, transaction_id, new_data)

    def delete_transaction(self, month_year: str, transaction_id: str):
        """Exclui um lançamento."""
        return self.core.delete_transaction(month_year, transaction_id)

    def get_monthly_gains_expenses(self, month_year: str):
        """Retorna os totais de ganhos e despesas para o gráfico."""
        df = self.get_transactions_for_month(month_year)
        if df.empty:
            return {'Ganhos': 0, 'Despesas': 0}
        
        gains = df[df['Tipo'].astype(str).str.lower() == 'ganho']['Valor'].sum()
        expenses = df[df['Tipo'].astype(str).str.lower() == 'despesa']['Valor'].sum()
        return {'Ganhos': gains, 'Despesas': expenses}

    def get_expenses_by_category(self, month_year: str):
        """Retorna as despesas por categoria para o gráfico."""
        df = self.get_transactions_for_month(month_year)
        if df.empty:
            return pd.Series(dtype=float)
        
        expenses_df = df[df['Tipo'].astype(str).str.lower() == 'despesa']
        return expenses_df.groupby('Categoria')['Valor'].sum().sort_values(ascending=False)