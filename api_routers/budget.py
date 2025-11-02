from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import List
import pandas as pd

from src.modules.budget import BudgetManager
from src.dependencies import get_budget_manager 

router = APIRouter(
    prefix="/api/budget",
    tags=["Budget"],
)

class BudgetLimit(BaseModel):
    category: str
    limit: float

class BudgetResponse(BudgetLimit):
    MesAno: str

class BudgetExceededResponse(BaseModel):
    Categoria: str
    Limite: float
    GastoAtual: float
    Excedente: float

@router.post("/{month_year}/", status_code=201)
def set_budget(
    month_year: str, 
    budget_data: BudgetLimit,
    manager: BudgetManager = Depends(get_budget_manager) 
):
    success = manager.set_budget_limit(
        month_year, budget_data.category, budget_data.limit
    )
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível definir o orçamento.")
    return {"message": "Orçamento definido com sucesso."}

@router.get("/{month_year}/", response_model=List[BudgetResponse])
def get_budgets(
    month_year: str, 
    manager: BudgetManager = Depends(get_budget_manager) 
):
    budgets_df = manager.get_budgets_for_month(month_year)
    if budgets_df.empty:
        return []
    return budgets_df.to_dict(orient='records')

@router.get("/check/{month_year}/", response_model=List[BudgetExceededResponse])
def check_budgets(
    month_year: str, 
    manager: BudgetManager = Depends(get_budget_manager) 
):
    exceeded_list = manager.check_budget_exceeded(month_year)
    return exceeded_list

@router.delete("/{month_year}/{category_name}/", status_code=200)
def delete_budget_route(
    month_year: str,
    category_name: str,
    manager: BudgetManager = Depends(get_budget_manager) 
):
    success = manager.delete_budget(month_year, category_name)
    if not success:
        raise HTTPException(status_code=404, detail="Orçamento não encontrado ou falha ao excluir.")
    return {"message": "Orçamento excluído com sucesso."}