from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from src.dependencies import category_manager

router = APIRouter(
    prefix="/api/categorias",
    tags=["Categorias"]      
)


class CategoriaPayload(BaseModel):
    nome: str 


@router.get("/")
def obter_categorias():
    """
    Endpoint para obter a lista de todas as categorias.
    """
    try:
        categorias = category_manager.get_all_categories()
        return {"categorias": categorias}
    except Exception as e:
        print(f"Erro ao buscar categorias: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
def adicionar_categoria(payload: CategoriaPayload):
    """
    Endpoint para adicionar uma nova categoria.
    Recebe o nome da categoria no corpo (body) da requisição.
    """
    try:
        nome_categoria = payload.nome.strip()
        if not nome_categoria:
            raise HTTPException(status_code=400, detail="Nome da categoria não pode ser vazio.")

        success = category_manager.add_category(nome_categoria)

        if success:
            return {"sucesso": True, "mensagem": f"Categoria '{nome_categoria}' adicionada."}
        else:

            raise HTTPException(status_code=409, detail=f"Categoria '{nome_categoria}' já existe ou erro ao salvar.")

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Erro ao adicionar categoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{category_name}")
def remover_categoria(
    category_name: str = Path(..., title="O nome da categoria a ser removida", min_length=1)
):
    """
    Endpoint para remover uma categoria específica.
    O nome da categoria vem na própria URL.
    """
    try:
        import urllib.parse
        nome_decodificado = urllib.parse.unquote(category_name)

        fixed_categories = ["Empréstimos", "Ganhos", "Contas Fixas", "Boletos", "Transferência"]
        if nome_decodificado in fixed_categories:
            raise HTTPException(status_code=403, detail=f"A categoria '{nome_decodificado}' não pode ser removida.")

        success = category_manager.remove_category(nome_decodificado)

        if success:
            return {"sucesso": True, "mensagem": f"Categoria '{nome_decodificado}' removida."}
        else:
            raise HTTPException(status_code=404, detail=f"Categoria '{nome_decodificado}' não encontrada ou erro ao remover.")

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        print(f"Erro ao remover categoria: {e}")
        raise HTTPException(status_code=500, detail=str(e))