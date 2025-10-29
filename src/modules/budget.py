from .core import CoreManager, DEFAULT_BUDGET_SHEET
import pandas as pd

class BudgetManager:
    def __init__(self, core_manager: CoreManager, monthly_control_manager):
        self.core = core_manager
        self.monthly_control = monthly_control_manager

    def set_budget_limit(self, month_year: str, category: str, limit: float):
        """Define ou atualiza o limite mensal para uma categoria."""
        if not all([month_year, category, limit is not None]):
            print("Dados incompletos para definir orçamento.")
            return False
        if not isinstance(limit, (int, float)) or limit < 0:
            print("Limite de orçamento inválido.")
            return False
        return self.core.set_budget(month_year, category, float(limit))

    def get_budgets_for_month(self, month_year: str):
        """Retorna os orçamentos definidos para um mês específico."""
        df = self.core.get_budgets()
        if not df.empty:
            df['MesAno'] = df['MesAno'].astype(str)
            df['Categoria'] = df['Categoria'].astype(str)
            return df[df['MesAno'] == month_year]
        return pd.DataFrame(columns=['MesAno', 'Categoria', 'Limite'])

    def check_budget_exceeded(self, month_year: str):
        """Verifica se alguma categoria excedeu o orçamento."""
        budgets_df = self.get_budgets_for_month(month_year)
        if budgets_df.empty:
            return []

        expenses_by_category = self.monthly_control.get_expenses_by_category(month_year)
        
        exceeded_budgets = []
        for index, row in budgets_df.iterrows():
            category = row['Categoria']
            limit = row['Limite']
            current_expense = expenses_by_category.get(category, 0)
            
            if current_expense > limit:
                exceeded_budgets.append({
                    'Categoria': category,
                    'Limite': limit,
                    'GastoAtual': current_expense,
                    'Excedente': current_expense - limit
                })
        return exceeded_budgets

    def delete_budget(self, month_year: str, category: str):
        """Exclui um orçamento específico para um dado mês e categoria."""
        df = self.core.get_budgets()
        if not df.empty:
            df['MesAno'] = df['MesAno'].astype(str)
            df['Categoria'] = df['Categoria'].astype(str)
            
            # Filtra a linha que deve ser excluída
            df = df[~((df['MesAno'] == month_year) & (df['Categoria'] == category))]
            
            return self.core.save_data(df, DEFAULT_BUDGET_SHEET)
        return False