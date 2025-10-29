
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_routers import categories
from api_routers import monthly_control

app = FastAPI(
    title="API de Finanças Pessoais",
    description="Backend modularizado para o gerenciador financeiro."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def ler_raiz():
    """ Endpoint inicial para testar se a API está no ar. """
    return {"status": "API de Finanças online e modularizada!"}
app.include_router(categories.router)
app.include_router(monthly_control.router)
if __name__ == "__main__":
    print("Iniciando servidor da API em http://127.0.0.1:8000")
    print("Acesse http://127.0.0.1:8000/docs para ver a documentação interativa da API")
    
    uvicorn.run(
        "api_main:app", 
        host="0.0.0.0",
        port=8000, 
        reload=True,
        reload_dirs=["./", "./api_routers", "./src"] 
    )