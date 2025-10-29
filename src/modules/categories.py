from .core import CoreManager, DEFAULT_CATEGORIES_SHEET

class CategoryManager:
    def __init__(self, core_manager: CoreManager):
        self.core = core_manager

    def get_all_categories(self):
        """Retorna uma lista de todas as categorias."""
        df = self.core.load_data(DEFAULT_CATEGORIES_SHEET)
        return df['Categoria'].tolist() if not df.empty else []

    def add_category(self, category_name: str):
        """Adiciona uma nova categoria. Retorna True se adicionado, False caso contrário."""
        if not category_name or not isinstance(category_name, str):
            print("Nome da categoria inválido.")
            return False
        return self.core.add_category(category_name)

    def remove_category(self, category_name: str):
        """Remove uma categoria. Retorna True se removido, False caso contrário."""
        # TODO: Adicionar categorias "fixas" que não podem ser removidas
        return self.core.remove_category(category_name)