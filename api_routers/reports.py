from fastapi import APIRouter, Depends, HTTPException, Query
# Importe o FileResponse de fastapi.responses
from fastapi.responses import FileResponse 
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime

from src.modules.reports import ReportManager
from src.dependencies import get_report_manager 

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"],
)

class SummaryResponse(BaseModel):
    Ganhos_Totais: float
    Despesas_Totais: float
    Saldo_Total: float
    Despesas_por_Categoria: Dict[str, float]
    Ganhos_por_Categoria: Dict[str, float]

def validate_dates(start_date: str, end_date: str):
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        if end_dt < start_dt:
            raise HTTPException(status_code=400, detail="A data final deve ser posterior à data inicial.")
        return start_dt, end_dt
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD.")

@router.get("/summary/", response_model=SummaryResponse)
def get_financial_summary(
    start_date: str = Query(..., example="2025-01-01"),
    end_date: str = Query(..., example="2025-12-31"),
    category: Optional[str] = Query(None, example="Alimentação"),
    manager: ReportManager = Depends(get_report_manager)
):
    start_dt, end_dt = validate_dates(start_date, end_date)
    
    summary_dict = manager.generate_financial_summary(start_dt, end_dt, category)
    
    return {
        "Ganhos_Totais": summary_dict['Ganhos Totais'],
        "Despesas_Totais": summary_dict['Despesas Totais'],
        "Saldo_Total": summary_dict['Saldo Total'],
        "Despesas_por_Categoria": summary_dict['Despesas por Categoria'].to_dict(),
        "Ganhos_por_Categoria": summary_dict['Ganhos por Categoria'].to_dict()
    }

@router.get("/export/pdf/", response_class=FileResponse)
def export_summary_pdf(
    start_date: str = Query(..., example="2025-01-01"),
    end_date: str = Query(..., example="2025-12-31"),
    category: Optional[str] = Query(None, example="Alimentação"),
    manager: ReportManager = Depends(get_report_manager)
):
    start_dt, end_dt = validate_dates(start_date, end_date)
    summary_dict = manager.generate_financial_summary(start_dt, end_dt, category)
    
    pdf_filename = f"relatorio_{start_date}_a_{end_date}.pdf"
    success = manager.export_summary_to_pdf(summary_dict, filename=pdf_filename)
    
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao gerar o arquivo PDF.")
    
    return FileResponse(
        path=f"data/{pdf_filename}",
        media_type='application/pdf',
        filename=pdf_filename
    )

@router.get("/export/csv/", response_class=FileResponse)
def export_summary_csv(
    start_date: str = Query(..., example="2025-01-01"),
    end_date: str = Query(..., example="2025-12-31"),
    category: Optional[str] = Query(None, example="Alimentação"),
    manager: ReportManager = Depends(get_report_manager)
):
    start_dt, end_dt = validate_dates(start_date, end_date)
    summary_dict = manager.generate_financial_summary(start_dt, end_dt, category)
    
    csv_filename = f"relatorio_{start_date}_a_{end_date}.csv"
    success = manager.export_summary_to_csv(summary_dict, filename=csv_filename)
    
    if not success:
        raise HTTPException(status_code=500, detail="Falha ao gerar o arquivo CSV.")
    
    return FileResponse(
        path=f"data/{csv_filename}",
        media_type='text/csv',
        filename=csv_filename
    )