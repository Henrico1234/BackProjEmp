

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

from src.dependencies import monthly_control_manager

router = APIRouter(
    prefix="/api", 
    tags=["Controlo Mensal"]
)



class TransacaoPayload(BaseModel):
    """Define a "forma" dos dados que o frontend vai enviar."""
    Data: str
    Tipo: Literal['Ganho', 'Despesa']
    Descricao: str
    Categoria: str
    Valor: float
    MeioPagamento: str



@router.get("/transacoes/{month_year}")
def obter_transacoes_mensais(month_year: str):
    """
    Endpoint para obter todas as transações de um mês específico (MM-YYYY).
    """
    try:
        transacoes_df = monthly_control_manager.get_transactions_for_month(month_year)
        transacoes_json = transacoes_df.to_dict('records')
        return {"transacoes": transacoes_json}
    except Exception as e:
        print(f"Erro ao buscar transações: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar transações: {str(e)}")

@router.get("/saldos/{month_year}")
def obter_saldos_mensais(month_year: str):
    """
    Endpoint para obter os saldos de um mês específico (MM-YYYY).
    """
    try:
        _, _, balance_conta = monthly_control_manager.calculate_detailed_balance(month_year, "Conta")
        _, _, balance_maos = monthly_control_manager.calculate_detailed_balance(month_year, "Dinheiro em Mãos")
        total_gains, total_expenses, total_balance = monthly_control_manager.calculate_monthly_balance(month_year)

        saldos = {
            "saldo_conta": float(balance_conta),
            "saldo_maos": float(balance_maos),
            "ganhos_mes": float(total_gains),
            "despesas_mes": float(total_expenses),
            "saldo_liquido": float(total_balance)
        }
        return {"saldos": saldos}
    
    except Exception as e:
        print(f"Erro ao buscar saldos: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno ao buscar saldos: {str(e)}")

@router.post("/transacoes/{month_year}")
def adicionar_transacao(month_year: str, transacao: TransacaoPayload):
    """
    Endpoint para ADICIONAR uma nova transação a um mês.
    """
    try:
        success = monthly_control_manager.add_transaction(
            month_year=month_year,
            date=transacao.Data,
            trans_type=transacao.Tipo,
            description=transacao.Descricao,
            category=transacao.Categoria,
            value=transacao.Valor,
            payment_method=transacao.MeioPagamento
        )
        
        if success:
            return {"sucesso": True, "mensagem": "Transação adicionada!"}
        else:
            raise HTTPException(status_code=400, detail="Falha ao adicionar transação no backend.")
            
    except Exception as e:
        print(f"Erro ao adicionar transação: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/transacoes/{month_year}/{transaction_id}")
def excluir_transacao(month_year: str, transaction_id: str):
    """
    Endpoint para EXCLUIR uma transação específica.
    """
    try:
        success = monthly_control_manager.delete_transaction(
            month_year, 
            transaction_id
        )
        
        if success:
            return {"sucesso": True, "mensagem": "Transação excluída!"}
        else:
            raise HTTPException(status_code=404, detail="Transação não encontrada ou falha ao excluir.")
            
    except Exception as e:
        print(f"Erro ao excluir transação: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/transacoes/{month_year}/{transaction_id}")
def atualizar_transacao(month_year: str, transaction_id: str, transacao: TransacaoPayload):
    """
    Endpoint para ATUALIZAR uma transação existente.
    Recebe os novos dados da transação no "corpo" (body) do request.
    """
    try:
        new_data = transacao.model_dump() 
        
        success = monthly_control_manager.update_transaction(
            month_year=month_year,
            transaction_id=transaction_id,
            new_data=new_data 
        )
        
        if success:
            return {"sucesso": True, "mensagem": "Transação atualizada!"}
        else:
            raise HTTPException(status_code=404, detail="Transação não encontrada ou falha ao atualizar.")
            
    except Exception as e:
        print(f"Erro ao atualizar transação: {e}")
        raise HTTPException(status_code=500, detail=str(e))    