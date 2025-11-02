# src/dependencies.py

"""
Este ficheiro centraliza a inicialização dos nossos gestores (lógica de negócio).
Qualquer parte da API (qualquer router) que precisar de aceder à lógica
de negócio irá importar estas instâncias.

Isto garante que temos apenas UMA instância de cada gestor (Singleton)
a ser partilhada por toda a aplicação.
"""

from src.modules.core import CoreManager
from src.modules.categories import CategoryManager
from src.modules.monthly_control import MonthlyControlManager
from src.modules.loans import LoanManager
from src.modules.debts import DebtManager
from src.modules.budget import BudgetManager
from src.modules.reports import ReportManager

# 1. Inicializa o Core
core_manager = CoreManager()

# 2. Inicializa todos os outros gestores que dependem do Core
# (Estamos a recriar o que o teu app.py antigo fazia, mas para a API)
category_manager = CategoryManager(core_manager)
monthly_control_manager = MonthlyControlManager(core_manager)
loan_manager = LoanManager(core_manager, monthly_control_manager)
debt_manager = DebtManager(core_manager, monthly_control_manager)
budget_manager = BudgetManager(core_manager, monthly_control_manager)
report_manager = ReportManager(core_manager, monthly_control_manager)

print("Dependências (Managers) inicializadas com sucesso.")


def get_budget_manager():
    """Retorna a instância singleton do BudgetManager."""
    return budget_manager

def get_debt_manager():
    """Retorna a instância singleton do DebtManager."""
    return debt_manager

def get_loan_manager():
    """Retorna a instância singleton do LoanManager."""
    return loan_manager

def get_report_manager():
    """Retorna a instância singleton do ReportManager."""
    return report_manager