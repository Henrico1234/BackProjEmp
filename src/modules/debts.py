# src/modules/debts.py

import pandas as pd
from datetime import datetime, timedelta
from .core import CoreManager, DEFAULT_DEBTS_SHEET # Importar DEFAULT_DEBTS_SHEET
from .monthly_control import MonthlyControlManager # Importar para lançar pagamentos e recorrências

class DebtManager:
    def __init__(self, core_manager: CoreManager, monthly_control_manager: MonthlyControlManager): 
        self.core = core_manager
        self.monthly_control = monthly_control_manager 

    def add_debt(self, description: str, value: float, due_date: str, status: str, recurrence: str, recurrence_months: int, category: str): 
        """
        Adiciona uma nova dívida futura/boleto.
        Se for recorrente, gera as entradas para os próximos meses.
        recurrence_months: Número de meses para gerar a recorrência (se 'Mensal' ou 'Anual').
        """
        if not all([description, value is not None, due_date, status, recurrence, category]):
            print("Dados incompletos para adicionar dívida.")
            return False
        if not isinstance(value, (int, float)) or value <= 0:
            print("Valor inválido para dívida.")
            return False
        if recurrence in ["Mensal", "Anual"] and (not isinstance(recurrence_months, int) or recurrence_months <= 0):
            print("Número de meses para recorrência inválido.")
            return False

        current_due_date = datetime.strptime(due_date, "%Y-%m-%d").date()
        generated_count = 0

        # Para dívidas únicas, apenas adiciona uma vez
        if recurrence == "Unica":
            data = {
                'Descricao': description,
                'Valor': float(value),
                'DataVencimento': current_due_date.strftime("%Y-%m-%d"),
                'Status': status,
                'Recorrencia': recurrence,
                'RecorrenciaMeses': 0, 
                'Categoria': category
            }
            if self.core.add_debt(data):
                generated_count += 1
        else: # Recorrência Mensal ou Anual
            for i in range(recurrence_months):
                new_due_date = current_due_date
                if recurrence == "Mensal":
                    # Adiciona 'i' meses à data de vencimento
                    year = current_due_date.year + (current_due_date.month + i -1) // 12
                    month = (current_due_date.month + i -1) % 12 + 1
                    day = min(current_due_date.day, self._days_in_month(year, month))
                    new_due_date = datetime(year, month, day).date()
                elif recurrence == "Anual":
                    new_due_date = datetime(current_due_date.year + i, current_due_date.month, current_due_date.day).date()
                
                data = {
                    'Descricao': description,
                    'Valor': float(value),
                    'DataVencimento': new_due_date.strftime("%Y-%m-%d"),
                    'Status': status, 
                    'Recorrencia': recurrence,
                    'RecorrenciaMeses': recurrence_months, 
                    'Categoria': category
                }
                if self.core.add_debt(data):
                    generated_count += 1
                else:
                    print(f"Falha ao adicionar recorrência {i+1} de dívida.")
                    return False 
        return generated_count > 0 

    def _days_in_month(self, year, month):
        """Retorna o número de dias em um dado mês/ano, lidando com anos bissextos."""
        if month == 2:
            if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                return 29
            return 28
        elif month in [4, 6, 9, 11]:
            return 30
        return 31

    def get_all_debts(self, month_year_filter: str = None): 
        """
        Retorna todas as dívidas futuras.
        Se month_year_filter for fornecido (MM-YYYY), filtra por esse mês/ano.
        """
        df = self.core.get_debts()
        if df.empty:
            return pd.DataFrame(columns=['ID', 'Descricao', 'Valor', 'DataVencimento', 'Status', 'Recorrencia', 'RecorrenciaMeses', 'Categoria'])

        if 'DataVencimento' in df.columns:
            df['DataVencimento'] = pd.to_datetime(df['DataVencimento'], errors='coerce').dt.date
            df = df.dropna(subset=['DataVencimento'])
        else: 
            df['DataVencimento'] = None

        if month_year_filter:
            filter_month = int(month_year_filter[:2])
            filter_year = int(month_year_filter[3:])
            
            df = df[
                (df['DataVencimento'].apply(lambda x: x.month == filter_month if x else False)) &
                (df['DataVencimento'].apply(lambda x: x.year == filter_year if x else False))
            ]
        
        expected_cols = ['ID', 'Descricao', 'Valor', 'DataVencimento', 'Status', 'Recorrencia', 'RecorrenciaMeses', 'Categoria']
        for col in expected_cols:
            if col not in df.columns:
                df[col] = None 
        
        return df

    def update_debt(self, debt_id: str, new_data: dict):
        """Atualiza uma dívida futura existente."""
        if 'DataVencimento' in new_data and isinstance(new_data['DataVencimento'], datetime.date):
            new_data['DataVencimento'] = new_data['DataVencimento'].strftime("%Y-%m-%d")
        return self.core.update_debt(debt_id, new_data)

    def delete_debt(self, debt_id: str):
        """Exclui uma dívida futura."""
        return self.core.delete_debt(debt_id)

    def mark_debt_as_paid(self, debt_id: str, current_month_year_for_transaction: str):
        """
        Marca uma dívida como 'Pago' e gera um lançamento de despesa no gerenciamento mensal.
        current_month_year_for_transaction: Mês/Ano atual da GUI para registrar o pagamento.
        """
        success_update_debt = self.update_debt(debt_id, {'Status': 'Pago'})

        if success_update_debt:
            debt_details = self.get_all_debts().loc[self.get_all_debts()['ID'].astype(str) == debt_id].iloc[0]
            
            transaction_date = datetime.now().strftime("%Y-%m-%d") 
            description = f"Pagamento Dívida: {debt_details['Descricao']}"
            category = debt_details['Categoria']
            value = debt_details['Valor']

            if category not in self.monthly_control.core.get_categories()['Categoria'].tolist():
                self.monthly_control.core.add_category(category)

            # Lança o pagamento como uma despesa no gerenciamento mensal
            success_monthly_transaction = self.monthly_control.add_transaction(
                current_month_year_for_transaction, 
                transaction_date,
                'Despesa',
                description,
                category,
                value,
                'Conta' # Pagamentos de dívidas geralmente saem da conta
            )
            return success_monthly_transaction
        return False

    def get_upcoming_or_overdue_debts(self, days_ahead: int = 7):
        """
        Retorna dívidas futuras com vencimento próximo (dias_ahead) ou atrasadas.
        Define o status 'Atrasado' para dívidas vencidas e abertas.
        """
        debts_df = self.get_all_debts() 
        if debts_df.empty:
            return pd.DataFrame()

        today = datetime.now().date()
        
        # Atualiza o status para 'Atrasado' e persiste no Excel
        for idx in debts_df.index:
            row = debts_df.loc[idx]
            if str(row['Status']).lower() == 'aberto' and pd.notna(row['DataVencimento']) and row['DataVencimento'] < today:
                debts_df.loc[idx, 'Status'] = 'Atrasado'
                self.core.update_debt(row['ID'], {'Status': 'Atrasado'})
        
        # Recarrega o DF para garantir que as alterações de status foram persistidas e refletidas
        debts_df = self.get_all_debts() 

        upcoming_or_overdue = debts_df[
            (debts_df['Status'].astype(str).str.lower() != 'pago') & 
            (
                (debts_df['DataVencimento'] <= today + timedelta(days=days_ahead)) | 
                (debts_df['DataVencimento'] < today) 
            )
        ].sort_values(by='DataVencimento')

        return upcoming_or_overdue