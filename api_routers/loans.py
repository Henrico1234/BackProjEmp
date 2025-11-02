from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field # <--- CORREÇÃO AQUI
from typing import List, Optional

from src.modules.loans import LoanManager
from src.dependencies import get_loan_manager 

router = APIRouter(
    prefix="/api/loans",
    tags=["Loans"],
)

class LoanCreate(BaseModel):
    loan_type: str
    involved_party: str
    original_value: float
    interest_rate: float
    num_installments: int

class LoanResponse(BaseModel):
    ID: str
    Tipo: str
    ParteEnvolvida: str
    ValorOriginal: float
    Juros: float = Field(..., alias='Juros%')
    NumParcelas: int
    ParcelasPagas: int
    Status: str

class LoanPayment(BaseModel):
    month_year: str
    amount_paid: float

@router.post("/register/", status_code=201)
def register_new_loan(
    loan_data: LoanCreate,
    manager: LoanManager = Depends(get_loan_manager) 
):
    success = manager.register_loan(
        loan_data.loan_type,
        loan_data.involved_party,
        loan_data.original_value,
        loan_data.interest_rate,
        loan_data.num_installments
    )
    if not success:
        raise HTTPException(status_code=400, detail="Não foi possível registrar o empréstimo.")
    return {"message": "Empréstimo registrado com sucesso."}

@router.get("/active/", response_model=List[LoanResponse])
def get_active_loans_list(
    manager: LoanManager = Depends(get_loan_manager) 
):
    loans_df = manager.get_active_loans()
    if loans_df.empty:
        return []
    
    loans_df['ID'] = loans_df['ID'].astype(str)
    loans_df_renamed = loans_df.rename(columns={'Juros%': 'Juros'}) 
    return loans_df_renamed.to_dict(orient='records')


@router.post("/pay/{loan_id}/", status_code=200)
def pay_loan_installment(
    loan_id: str,
    payment_data: LoanPayment,
    manager: LoanManager = Depends(get_loan_manager) 
):
    success = manager.record_installment_payment(
        loan_id,
        payment_data.month_year,
        payment_data.amount_paid
    )
    if not success:
        raise HTTPException(status_code=400, detail="Falha ao registrar pagamento da parcela.")
    return {"message": "Pagamento de parcela registrado com sucesso."}

@router.delete("/delete/{loan_id}/", status_code=200)
def delete_single_loan(
    loan_id: str,
    manager: LoanManager = Depends(get_loan_manager) 
):
    success = manager.delete_loan(loan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Empréstimo não encontrado ou falha ao excluir.")
    return {"message": "Empréstimo excluído com sucesso."}