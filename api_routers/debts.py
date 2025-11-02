from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional
import pandas as pd
from datetime import date

from src.modules.debts import DebtManager
from src.dependencies import get_debt_manager 

router = APIRouter(
    prefix="/api/debts",
    tags=["Debts"],
)

class DebtCreate(BaseModel):
    description: str
    value: float
    due_date: str
    status: str
    recurrence: str
    recurrence_months: int
    category: str

class DebtResponse(BaseModel):
    ID: str
    Descricao: str
    Valor: float
    DataVencimento: date
    Status: str
    Recorrencia: str
    RecorrenciaMeses: int
    Categoria: str

class DebtPay(BaseModel):
    current_month_year_for_transaction: str

@router.post("/add/", status_code=201)
def add_new_debt(
    debt_data: DebtCreate,
    manager: DebtManager = Depends(get_debt_manager) 
):
    success = manager.add_debt(
        debt_data.description,
        debt_data.value,
        debt_data.due_date,
        debt_data.status,
        debt_data.recurrence,
        debt_data.recurrence_months,
        debt_data.category
    )
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível adicionar a dívida.")
    return {"message": "Dívida(s) adicionada(s) com sucesso."}

@router.get("/list/", response_model=List[DebtResponse])
def get_debts_list(
    month_year_filter: Optional[str] = Query(None, pattern=r"^\d{2}-\d{4}$"),
    manager: DebtManager = Depends(get_debt_manager) 
):
    debts_df = manager.get_all_debts(month_year_filter)
    if debts_df.empty:
        return []
    debts_df['ID'] = debts_df['ID'].astype(str)
    return debts_df.to_dict(orient='records')

@router.get("/dashboard/", response_model=List[DebtResponse])
def get_dashboard_debts(
    days_ahead: int = 7,
    manager: DebtManager = Depends(get_debt_manager) 
):
    debts_df = manager.get_upcoming_or_overdue_debts(days_ahead)
    if debts_df.empty:
        return []
    debts_df['ID'] = debts_df['ID'].astype(str)
    return debts_df.to_dict(orient='records')

@router.put("/pay/{debt_id}/", status_code=200)
def pay_debt(
    debt_id: str,
    payload: DebtPay,
    manager: DebtManager = Depends(get_debt_manager) 
):
    success = manager.mark_debt_as_paid(
        debt_id, 
        payload.current_month_year_for_transaction
    )
    if not success:
        raise HTTPException(status_code=400, detail="Falha ao marcar dívida como paga ou ao registrar a transação.")
    return {"message": "Dívida paga e transação registrada com sucesso."}

@router.delete("/delete/{debt_id}/", status_code=200)
def delete_single_debt(
    debt_id: str,
    manager: DebtManager = Depends(get_debt_manager) 
):
    success = manager.delete_debt(debt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dívida não encontrada ou falha ao excluir.")
    return {"message": "Dívida excluída com sucesso."}