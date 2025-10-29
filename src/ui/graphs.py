# src/ui/graphs.py

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #, NavigationToolbar2TkAgg
import pandas as pd
import tkinter as tk

class GraphPlotter:
    def __init__(self, master_frame):
        self.master_frame = master_frame
        self.figure = plt.Figure(figsize=(5, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.master_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def clear_plot(self):
        self.ax.clear()
        self.figure.canvas.draw_idle()

    def plot_gains_vs_expenses(self, gains: float, expenses: float):
        self.clear_plot()
        labels = ['Ganhos', 'Despesas']
        values = [gains, expenses]
        colors = ['#4CAF50', '#F44336'] # Verde para ganhos, Vermelho para despesas

        self.ax.bar(labels, values, color=colors)
        self.ax.set_title('Ganhos vs Despesas')
        self.ax.set_ylabel('Valor (R$)')
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_expenses_by_category(self, expenses_by_category: pd.Series):
        self.clear_plot()
        if expenses_by_category.empty:
            self.ax.text(0.5, 0.5, "Sem despesas por categoria para exibir", 
                         horizontalalignment='center', verticalalignment='center', 
                         transform=self.ax.transAxes, fontsize=10, color='gray')
            self.figure.canvas.draw()
            return

        categories = expenses_by_category.index.tolist()
        values = expenses_by_category.values.tolist()

        # Para um gráfico de pizza, você pode ajustar as cores e formatar porcentagens
        self.ax.pie(values, labels=categories, autopct='%1.1f%%', startangle=90, 
                    pctdistance=0.85, wedgeprops=dict(width=0.4), colors=plt.cm.Paired.colors)
        
        # Desenha um círculo central para fazer um donut chart
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        self.ax.add_artist(centre_circle)

        self.ax.set_title('Despesas por Categoria')
        self.ax.axis('equal')  # Garante que o gráfico de pizza seja um círculo.
        self.figure.tight_layout()
        self.canvas.draw()