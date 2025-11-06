import pandas as pd
import sqlite3
from datetime import datetime
import os
import uuid 
import sys 

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    _base_path = sys._MEIPASS
else:
    _base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

DB_DIR = 'data' 
DB_FILE_NAME = 'financas.db'
DB_FILE = os.path.join(_base_path, DB_DIR, DB_FILE_NAME)

DEFAULT_CATEGORIES_SHEET = 'Categorias'
DEFAULT_BUDGET_SHEET = 'OrcamentoMensal'
DEFAULT_LOANS_SHEET = 'Empréstimos' 
DEFAULT_DEBTS_SHEET = 'DívidasFuturas' 

class CoreManager:
    def __init__(self):
        self._ensure_db_file_exists()
        self._initialize_database()

    def _ensure_db_file_exists(self):
        db_folder_path = os.path.dirname(DB_FILE)
        if not os.path.exists(db_folder_path):
            os.makedirs(db_folder_path)
            print(f"Diretório '{db_folder_path}' criado.")

    def _create_connection(self):
        try:
            conn = sqlite3.connect(DB_FILE, isolation_level=None)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"Erro ao conectar ao banco de dados {DB_FILE}: {e}")
            return None

    def _initialize_database(self):
        
        create_table_queries = [
            """
            CREATE TABLE IF NOT EXISTS Categorias (
                Categoria TEXT PRIMARY KEY NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Orcamentos (
                MesAno TEXT NOT NULL,
                Categoria TEXT NOT NULL,
                Limite REAL NOT NULL,
                PRIMARY KEY (MesAno, Categoria),
                FOREIGN KEY (Categoria) REFERENCES Categorias (Categoria) ON DELETE CASCADE
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Emprestimos (
                ID TEXT PRIMARY KEY NOT NULL,
                Tipo TEXT NOT NULL,
                ParteEnvolvida TEXT NOT NULL,
                ValorOriginal REAL NOT NULL,
                "Juros%" REAL NOT NULL,
                NumParcelas INTEGER NOT NULL,
                ParcelasPagas INTEGER NOT NULL,
                Status TEXT NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Dividas (
                ID TEXT PRIMARY KEY NOT NULL,
                Descricao TEXT,
                Valor REAL,
                DataVencimento TEXT,
                Status TEXT,
                Recorrencia TEXT,
                RecorrenciaMeses INTEGER,
                Categoria TEXT,
                FOREIGN KEY (Categoria) REFERENCES Categorias (Categoria) ON DELETE SET NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS Transacoes (
                ID TEXT PRIMARY KEY NOT NULL,
                MesAno TEXT NOT NULL,
                Data TEXT,
                Tipo TEXT,
                Descricao TEXT,
                Categoria TEXT,
                Valor REAL,
                MeioPagamento TEXT,
                FOREIGN KEY (Categoria) REFERENCES Categorias (Categoria) ON DELETE SET NULL
            );
            """
        ]
        
        try:
            with self._create_connection() as conn:
                cursor = conn.cursor()
                for query in create_table_queries:
                    cursor.execute(query)
                print("Verificação de tabelas do banco de dados concluída.")
        except Exception as e:
            print(f"Erro ao inicializar tabelas: {e}")


    def get_monthly_transactions(self, month_year: str):
        """Retorna os lançamentos de um mês específico."""
        query = "SELECT ID, Data, Tipo, Descricao, Categoria, Valor, MeioPagamento FROM Transacoes WHERE MesAno = ?;"
        try:
            with self._create_connection() as conn:
                df = pd.read_sql_query(query, conn, params=(month_year,))

                expected_cols = ['ID', 'Data', 'Tipo', 'Descricao', 'Categoria', 'Valor', 'MeioPagamento']
                for col in expected_cols:
                    if col not in df.columns:
                        df[col] = None

                if 'ID' in df.columns:
                    df['ID'] = df['ID'].astype(str)

                return df
        except Exception as e:
            print(f"Erro ao carregar transações para '{month_year}': {e}")
            return pd.DataFrame(columns=['ID', 'Data', 'Tipo', 'Descricao', 'Categoria', 'Valor', 'MeioPagamento'])

    def add_transaction(self, month_year: str, data: dict):
        """Adiciona um novo lançamento à tabela de transações."""
        data['ID'] = str(uuid.uuid4())
        data['MesAno'] = month_year 
        
        query = """
        INSERT INTO Transacoes (ID, MesAno, Data, Tipo, Descricao, Categoria, Valor, MeioPagamento)
        VALUES (:ID, :MesAno, :Data, :Tipo, :Descricao, :Categoria, :Valor, :MeioPagamento);
        """
        try:
            with self._create_connection() as conn:
                conn.execute(query, data)
            print(f"Transação {data['ID']} adicionada para o mês {month_year}.")
            return True
        except Exception as e:
            print(f"Erro ao adicionar transação: {e}")
            return False

    def update_transaction(self, month_year: str, transaction_id: str, new_data: dict):

        set_clause = ", ".join([f"{key} = :{key}" for key in new_data.keys()])
        query = f"UPDATE Transacoes SET {set_clause} WHERE ID = :ID;"
        
        new_data['ID'] = str(transaction_id)
        
        try:
            with self._create_connection() as conn:
                conn.execute(query, new_data)
            return True
        except Exception as e:
            print(f"Erro ao atualizar transação {transaction_id}: {e}")
            return False

    def delete_transaction(self, month_year: str, transaction_id: str):
        query = "DELETE FROM Transacoes WHERE ID = ?;"
        try:
            with self._create_connection() as conn:
                conn.execute(query, (str(transaction_id),))
            return True
        except Exception as e:
            print(f"Erro ao excluir transação {transaction_id}: {e}")
            return False


    def get_categories(self):
        query = "SELECT Categoria FROM Categorias;"
        try:
            with self._create_connection() as conn:
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Erro ao buscar categorias: {e}")
            return pd.DataFrame(columns=['Categoria'])

    def add_category(self, category_name: str):
        query = "INSERT INTO Categorias (Categoria) VALUES (?);"
        try:
            with self._create_connection() as conn:
                conn.execute(query, (category_name,))
            return True
        except Exception as e: 
            print(f"Erro ao adicionar categoria '{category_name}': {e}")
            return False

    def remove_category(self, category_name: str):
        query = "DELETE FROM Categorias WHERE Categoria = ?;"
        try:
            with self._create_connection() as conn:
                conn.execute(query, (category_name,))
            return True
        except Exception as e:
            print(f"Erro ao remover categoria '{category_name}': {e}")
            return False



    def get_budgets(self):
        query = "SELECT MesAno, Categoria, Limite FROM Orcamentos;"
        try:
            with self._create_connection() as conn:
                df = pd.read_sql_query(query, conn)
                return df
        except Exception as e:
            print(f"Erro ao buscar orçamentos: {e}")
            return pd.DataFrame(columns=['MesAno', 'Categoria', 'Limite'])

    def set_budget(self, month_year: str, category: str, limit: float):
        
        query = """
        INSERT INTO Orcamentos (MesAno, Categoria, Limite)
        VALUES (?, ?, ?)
        ON CONFLICT(MesAno, Categoria) DO UPDATE SET Limite = excluded.Limite;
        """
        try:
            with self._create_connection() as conn:
                conn.execute(query, (month_year, category, limit))
            return True
        except Exception as e:
            print(f"Erro ao definir orçamento: {e}")
            return False

    def get_loans(self):
        query = 'SELECT ID, Tipo, ParteEnvolvida, ValorOriginal, "Juros%", NumParcelas, ParcelasPagas, Status FROM Emprestimos;'
        try:
            with self._create_connection() as conn:
                df = pd.read_sql_query(query, conn)
                df['ID'] = df['ID'].astype(str) 
                return df
        except Exception as e:
            print(f"Erro ao buscar empréstimos: {e}")
            return pd.DataFrame(columns=['ID', 'Tipo', 'ParteEnvolvida', 'ValorOriginal', 'Juros%', 'NumParcelas', 'ParcelasPagas', 'Status'])

    def add_loan(self, data: dict):
        query = """
        INSERT INTO Emprestimos (ID, Tipo, ParteEnvolvida, ValorOriginal, "Juros%", NumParcelas, ParcelasPagas, Status)
        VALUES (:ID, :Tipo, :ParteEnvolvida, :ValorOriginal, :Juros, :NumParcelas, :ParcelasPagas, :Status);
        """
        data['Juros'] = data.pop('Juros%', 0.0) 
        try:
            with self._create_connection() as conn:
                conn.execute(query, data)
            return True
        except Exception as e:
            print(f"Erro ao adicionar empréstimo: {e}")
            return False

    def update_loan(self, loan_id: str, new_data: dict):
        if 'Juros%' in new_data:
            new_data['"Juros%"'] = new_data.pop('Juros%')

        set_clause = ", ".join([f'"{key}" = :{key}' for key in new_data.keys()])
        query = f"UPDATE Emprestimos SET {set_clause} WHERE ID = :ID;"
        new_data['ID'] = str(loan_id)
        
        try:
            with self._create_connection() as conn:
                conn.execute(query, new_data)
            return True
        except Exception as e:
            print(f"Erro ao atualizar empréstimo {loan_id}: {e}")
            return False


    def get_debts(self):
        query = "SELECT ID, Descricao, Valor, DataVencimento, Status, Recorrencia, RecorrenciaMeses, Categoria FROM Dividas;"
        try:
            with self._create_connection() as conn:
                df = pd.read_sql_query(query, conn)
                df['ID'] = df['ID'].astype(str)
                return df
        except Exception as e:
            print(f"Erro ao buscar dívidas: {e}")
            return pd.DataFrame(columns=['ID', 'Descricao', 'Valor', 'DataVencimento', 'Status', 'Recorrencia', 'RecorrenciaMeses', 'Categoria'])

    def add_debt(self, data: dict):
        if 'ID' not in data:
            data['ID'] = str(uuid.uuid4())
            
        query = """
        INSERT INTO Dividas (ID, Descricao, Valor, DataVencimento, Status, Recorrencia, RecorrenciaMeses, Categoria)
        VALUES (:ID, :Descricao, :Valor, :DataVencimento, :Status, :Recorrencia, :RecorrenciaMeses, :Categoria);
        """
        try:
            with self._create_connection() as conn:
                conn.execute(query, data)
            return True
        except Exception as e:
            print(f"Erro ao adicionar dívida: {e}")
            return False

    def update_debt(self, debt_id: str, new_data: dict):
        set_clause = ", ".join([f"{key} = :{key}" for key in new_data.keys()])
        query = f"UPDATE Dividas SET {set_clause} WHERE ID = :ID;"
        new_data['ID'] = str(debt_id)
        
        try:
            with self._create_connection() as conn:
                conn.execute(query, new_data)
            return True
        except Exception as e:
            print(f"Erro ao atualizar dívida {debt_id}: {e}")
            return False

    def delete_debt(self, debt_id: str):
        query = "DELETE FROM Dividas WHERE ID = ?;"
        try:
            with self._create_connection() as conn:
                conn.execute(query, (str(debt_id),))
            return True
        except Exception as e:
            print(f"Erro ao excluir dívida {debt_id}: {e}")
            return False

    
    def load_data(self, sheet_name):
        print(f"Aviso: load_data('{sheet_name}') chamado (método antigo). Redirecionando...")
        if sheet_name == DEFAULT_CATEGORIES_SHEET:
            return self.get_categories()
        if sheet_name == DEFAULT_BUDGET_SHEET:
            return self.get_budgets()
        if sheet_name == DEFAULT_LOANS_SHEET:
            return self.get_loans()
        if sheet_name == DEFAULT_DEBTS_SHEET:
            return self.get_debts()
        if len(sheet_name) == 7 and sheet_name[2] == '-':
            return self.get_monthly_transactions(sheet_name)
        return pd.DataFrame()

    def save_data(self, df, sheet_name):
        print(f"Aviso: save_data('{sheet_name}') chamado (método antigo). Operação ignorada (autocommit ativado).")
        return True

    def create_monthly_sheet(self, month_year):
        print(f"Aviso: create_monthly_sheet('{month_year}') chamado (método antigo). Operação ignorada.")
        return True