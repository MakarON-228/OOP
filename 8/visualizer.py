"""
Визуализация результатов на числовой прямой.
Использует matplotlib для отрисовки.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from typing import Dict, List, Tuple, Optional
import math

from solver import Interval, SolverResult


class IntervalVisualizer:
    """Визуализатор интервалов на числовой прямой"""

    # Цветовая палитра
    COLORS = {
        'P': '#3498db',  # Синий
        'Q': '#e74c3c',  # Красный
        'R': '#2ecc71',  # Зелёный
        'S': '#9b59b6',  # Фиолетовый
        'T': '#f39c12',  # Оранжевый
        'default': '#95a5a6',  # Серый
    }

    TARGET_COLOR = '#27ae60'  # Зелёный для искомого множества
    TARGET_ALPHA = 0.8
    KNOWN_ALPHA = 0.5

    def __init__(self, figsize: Tuple[int, int] = (10, 4)):
        self.figsize = figsize
        self.figure: Optional[Figure] = None
        self.canvas: Optional[FigureCanvasQTAgg] = None

    def create_figure(self) -> Tuple[Figure, FigureCanvasQTAgg]:
        """Создаёт фигуру и canvas для встраивания в Qt"""
        self.figure = Figure(figsize=self.figsize, dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        return self.figure, self.canvas

    def plot(
            self,
            known_sets: Dict[str, Tuple[float, float]],
            result: SolverResult,
            target_name: str = 'A'
    ):
        """
        Отрисовывает все множества на числовой прямой.

        Args:
            known_sets: Известные множества
            result: Результат солвера
            target_name: Имя искомого множества
        """
        if self.figure is None:
            self.create_figure()

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Определяем границы отображения
        all_points = []
        for left, right in known_sets.values():
            all_points.extend([left, right])

        for interval in result.intervals:
            if not math.isinf(interval.left):
                all_points.append(interval.left)
            if not math.isinf(interval.right):
                all_points.append(interval.right)

        if all_points:
            x_min = min(all_points) - 5
            x_max = max(all_points) + 5
        else:
            x_min, x_max = -10, 10

        # Количество множеств для отображения
        n_sets = len(known_sets) + 1  # +1 для искомого
        y_positions = {}

        # Позиции для известных множеств
        for i, name in enumerate(sorted(known_sets.keys())):
            y_positions[name] = n_sets - i

        # Позиция для искомого множества (внизу)
        y_positions[target_name] = 0.5

        # Отрисовка известных множеств
        legend_handles = []

        for name, (left, right) in known_sets.items():
            y = y_positions[name]
            color = self.COLORS.get(name, self.COLORS['default'])

            # Рисуем отрезок
            rect = mpatches.FancyBboxPatch(
                (left, y - 0.3), right - left, 0.6,
                boxstyle="round,pad=0.02",
                facecolor=color,
                edgecolor='black',
                alpha=self.KNOWN_ALPHA,
                linewidth=1.5
            )
            ax.add_patch(rect)

            # Подпись
            ax.text(left - 1, y, name, fontsize=12, fontweight='bold',
                    ha='right', va='center')

            # Значения границ
            ax.text(left, y - 0.5, str(left), fontsize=9, ha='center')
            ax.text(right, y - 0.5, str(right), fontsize=9, ha='center')

            # Вертикальные линии на границах
            ax.axvline(x=left, color='gray', linestyle=':', alpha=0.5, linewidth=0.5)
            ax.axvline(x=right, color='gray', linestyle=':', alpha=0.5, linewidth=0.5)

            legend_handles.append(mpatches.Patch(
                color=color, alpha=self.KNOWN_ALPHA,
                label=f'{name} = [{left}, {right}]'
            ))

        # Отрисовка искомого множества
        if result.success and result.intervals:
            y = y_positions[target_name]

            for interval in result.intervals:
                left = interval.left if not math.isinf(interval.left) else x_min
                right = interval.right if not math.isinf(interval.right) else x_max

                rect = mpatches.FancyBboxPatch(
                    (left, y - 0.3), right - left, 0.6,
                    boxstyle="round,pad=0.02",
                    facecolor=self.TARGET_COLOR,
                    edgecolor='darkgreen',
                    alpha=self.TARGET_ALPHA,
                    linewidth=2
                )
                ax.add_patch(rect)

                # Границы
                if not math.isinf(interval.left):
                    ax.axvline(x=interval.left, color='green', linestyle='--',
                               alpha=0.7, linewidth=1)
                if not math.isinf(interval.right):
                    ax.axvline(x=interval.right, color='green', linestyle='--',
                               alpha=0.7, linewidth=1)

            # Подпись
            ax.text(x_min - 1, y, target_name, fontsize=12, fontweight='bold',
                    ha='right', va='center', color='darkgreen')

            # Легенда для искомого множества
            label = result.message.split(',')[0]  # Берём только часть с интервалами
            legend_handles.append(mpatches.Patch(
                color=self.TARGET_COLOR, alpha=self.TARGET_ALPHA,
                label=label
            ))

        # Настройка осей
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(-0.5, n_sets + 1)
        ax.set_yticks([])
        ax.set_xlabel('Числовая прямая', fontsize=11)
        ax.axhline(y=0, color='black', linewidth=0.5)

        # Числовая ось
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)

        # Легенда
        ax.legend(handles=legend_handles, loc='upper right', fontsize=9)

        # Заголовок
        if result.success:
            title = f"Результат: длина всех подходящих {target_name} = {result.total_length:.1f}"
        else:
            title = "Решение не найдено"
        ax.set_title(title, fontsize=12, fontweight='bold')

        self.figure.tight_layout()

        if self.canvas:
            self.canvas.draw()

    def clear(self):
        """Очищает фигуру"""
        if self.figure:
            self.figure.clear()
            if self.canvas:
                self.canvas.draw()


# Тестирование
if __name__ == "__main__":
    from solver import LogicSolver

    formula = "((x ∈ P) ≡ (x ∈ Q)) → ¬(x ∈ A)"
    known_sets = {'P': (5, 30), 'Q': (14, 23)}

    solver = LogicSolver(
        formula=formula,
        known_sets=known_sets,
        target_set='A',
        maximize=True,
        formula_true=True
    )

    result = solver.solve()

    viz = IntervalVisualizer()
    viz.create_figure()
    viz.plot(known_sets, result, 'A')

    plt.show()