"""
GUI-приложение на PySide6 для решения логических задач на числовой прямой.
"""

import sys
from typing import Dict, Tuple, Optional
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QGroupBox, QScrollArea, QMessageBox, QSplitter, QTextEdit,
    QGridLayout, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPalette

from formula_parser import parse_formula, get_sets_from_ast
from solver import LogicSolver, SolverResult
from visualizer import IntervalVisualizer


class SetInputWidget(QWidget):
    """Виджет для ввода одного отрезка"""

    removed = Signal(str)  # Сигнал удаления

    def __init__(self, name: str = "", left: str = "", right: str = "", removable: bool = True):
        super().__init__()
        self.name = name

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Имя множества
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("Имя")
        self.name_edit.setMaximumWidth(60)
        self.name_edit.setFont(QFont("Consolas", 11))

        # Левая граница
        layout.addWidget(QLabel("= ["))
        self.left_edit = QLineEdit(left)
        self.left_edit.setPlaceholderText("левая")
        self.left_edit.setMaximumWidth(80)

        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("= ["))
        layout.addWidget(self.left_edit)

        # Правая граница
        layout.addWidget(QLabel(","))
        self.right_edit = QLineEdit(right)
        self.right_edit.setPlaceholderText("правая")
        self.right_edit.setMaximumWidth(80)
        layout.addWidget(self.right_edit)
        layout.addWidget(QLabel("]"))

        # Кнопка удаления
        # if removable:
        #     self.remove_btn = QPushButton("✕")
        #     self.remove_btn.setMaximumWidth(30)
        #     self.remove_btn.setStyleSheet("color: red; font-weight: bold;")
        #     self.remove_btn.clicked.connect(self._on_remove)
        #     layout.addWidget(self.remove_btn)
        #
        layout.addStretch()

    def _on_remove(self):
        self.removed.emit(self.name_edit.text())
        self.deleteLater()

    def get_data(self) -> Optional[Tuple[str, float, float]]:
        """Возвращает данные отрезка или None при ошибке"""
        try:
            name = self.name_edit.text().strip()
            left = float(self.left_edit.text())
            right = float(self.right_edit.text())

            if not name:
                raise ValueError("Имя не может быть пустым")
            if left > right:
                raise ValueError(f"Левая граница больше правой для {name}")

            return (name, left, right)
        except ValueError:
            return None


class MainWindow(QMainWindow):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Солвер логических формул на числовой прямой")
        self.setMinimumSize(900, 700)

        self.set_widgets: list[SetInputWidget] = []
        self.visualizer = IntervalVisualizer(figsize=(9, 3))

        self._setup_ui()
        self._load_example()

    def _setup_ui(self):
        """Настройка интерфейса"""
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)

        # ===== Ввод формулы =====
        formula_group = QGroupBox("Логическая формула")
        formula_layout = QVBoxLayout(formula_group)

        self.formula_edit = QLineEdit()
        self.formula_edit.setFont(QFont("Consolas", 12))
        self.formula_edit.setPlaceholderText("Например: ((x ∈ P) ≡ (x ∈ Q)) → ¬(x ∈ A)")
        formula_layout.addWidget(self.formula_edit)

        # Подсказка по синтаксису
        hint = QLabel(
            "Операции: ¬ (NOT, !) | ∧ (AND, &) | ∨ (OR, |) | "
            "→ (->) | ≡ (<->, ==) | ⊕ (XOR, ^) | ∈ (in)"
        )
        hint.setStyleSheet("color: gray; font-size: 10px;")
        formula_layout.addWidget(hint)

        main_layout.addWidget(formula_group)

        # ===== Ввод отрезков =====
        sets_group = QGroupBox("Известные отрезки")
        sets_layout = QVBoxLayout(sets_group)

        # Контейнер для отрезков
        self.sets_container = QVBoxLayout()
        sets_layout.addLayout(self.sets_container)

        # Кнопка добавления
        # add_btn = QPushButton("+ Добавить отрезок")
        # add_btn.clicked.connect(self._add_set_widget)
        # sets_layout.addWidget(add_btn)

        main_layout.addWidget(sets_group)

        # ===== Параметры решения =====
        params_layout = QHBoxLayout()

        # Искомое множество
        target_group = QGroupBox("Искомое множество")
        target_layout = QHBoxLayout(target_group)
        self.target_edit = QLineEdit("A")
        self.target_edit.setMaximumWidth(80)
        self.target_edit.setFont(QFont("Consolas", 11))
        target_layout.addWidget(self.target_edit)
        target_layout.addStretch()
        params_layout.addWidget(target_group)

        # Оптимизация
        opt_group = QGroupBox("Оптимизация")
        opt_layout = QHBoxLayout(opt_group)
        self.opt_group = QButtonGroup()
        self.max_radio = QRadioButton("Максимум")
        self.min_radio = QRadioButton("Минимум")
        self.max_radio.setChecked(True)
        self.opt_group.addButton(self.max_radio)
        self.opt_group.addButton(self.min_radio)
        opt_layout.addWidget(self.max_radio)
        opt_layout.addWidget(self.min_radio)
        params_layout.addWidget(opt_group)

        # Условие на формулу
        cond_group = QGroupBox("Формула должна быть")
        cond_layout = QHBoxLayout(cond_group)
        self.cond_group = QButtonGroup()
        self.true_radio = QRadioButton("Истинна (=1)")
        self.false_radio = QRadioButton("Ложна (=0)")
        self.true_radio.setChecked(True)
        self.cond_group.addButton(self.true_radio)
        self.cond_group.addButton(self.false_radio)
        cond_layout.addWidget(self.true_radio)
        cond_layout.addWidget(self.false_radio)
        params_layout.addWidget(cond_group)

        main_layout.addLayout(params_layout)

        # ===== Кнопка решения =====
        self.solve_btn = QPushButton("🔍  РЕШИТЬ")
        self.solve_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.solve_btn.setMinimumHeight(50)
        self.solve_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c6ea4;
            }
        """)
        self.solve_btn.clicked.connect(self._solve)
        main_layout.addWidget(self.solve_btn)

        # ===== Результат =====
        result_group = QGroupBox("Результат")
        result_layout = QVBoxLayout(result_group)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(80)
        self.result_text.setFont(QFont("Consolas", 11))
        result_layout.addWidget(self.result_text)

        main_layout.addWidget(result_group)

        # ===== Визуализация =====
        viz_group = QGroupBox("Визуализация")
        viz_layout = QVBoxLayout(viz_group)

        _, canvas = self.visualizer.create_figure()
        viz_layout.addWidget(canvas)

        main_layout.addWidget(viz_group, stretch=1)

    def _add_set_widget(self, name: str = "", left: str = "", right: str = ""):
        """Добавляет виджет ввода отрезка"""
        widget = SetInputWidget(name, left, right)
        widget.removed.connect(self._remove_set_widget)
        self.sets_container.addWidget(widget)
        self.set_widgets.append(widget)

    def _remove_set_widget(self, name: str):
        """Удаляет виджет отрезка"""
        self.set_widgets = [w for w in self.set_widgets if w.name_edit.text() != name]

    def _load_example(self):
        """Загружает тестовый пример"""
        self.formula_edit.setText("((x ∈ P) ≡ (x ∈ Q)) → ¬(x ∈ A)")
        self._add_set_widget("P", "5", "30")
        self._add_set_widget("Q", "14", "23")
        self.target_edit.setText("A")

    def _get_known_sets(self) -> Optional[Dict[str, Tuple[float, float]]]:
        """Собирает данные о известных отрезках"""
        known_sets = {}

        for widget in self.set_widgets:
            data = widget.get_data()
            if data is None:
                return None
            name, left, right = data
            known_sets[name] = (left, right)

        return known_sets

    def _solve(self):
        """Запускает решение"""
        # Собираем входные данные
        formula = self.formula_edit.text().strip()
        if not formula:
            QMessageBox.warning(self, "Ошибка", "Введите формулу")
            return

        known_sets = self._get_known_sets()
        if known_sets is None:
            QMessageBox.warning(self, "Ошибка", "Проверьте ввод отрезков")
            return

        target = self.target_edit.text().strip()
        if not target:
            QMessageBox.warning(self, "Ошибка", "Укажите искомое множество")
            return

        maximize = self.max_radio.isChecked()
        formula_true = self.true_radio.isChecked()

        # Решаем
        try:
            solver = LogicSolver(
                formula=formula,
                known_sets=known_sets,
                target_set=target,
                maximize=maximize,
                formula_true=formula_true
            )

            result = solver.solve()

            # Выводим результат
            if result.success:
                self.result_text.setStyleSheet("color: green;")
                analysis = solver.get_analysis()

                details = f"Результат: {result.message}\n\n"
                details += "Анализ интервалов:\n"
                for ci in analysis:
                    details += f"  {ci}\n"

                self.result_text.setText(details)
            else:
                self.result_text.setStyleSheet("color: red;")
                self.result_text.setText(f"❌ {result.message}")

            # Визуализируем
            self.visualizer.plot(known_sets, result, target)

        except SyntaxError as e:
            QMessageBox.critical(self, "Ошибка синтаксиса", str(e))
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Неожиданная ошибка", str(e))


def main():
    app = QApplication(sys.argv)

    # Стиль приложения
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()