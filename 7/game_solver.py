import sys
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFormLayout, QComboBox, QGroupBox,
    QMessageBox, QListWidget
)


# ==============================================================================
# 1. МОДЕЛЬ
# ==============================================================================
class Game:
    def __init__(self, moves, threshold, comparator, s_min, s_max):
        self.moves = moves
        self.threshold = threshold
        self.comparator = comparator
        self.s_min = s_min
        self.s_max = s_max


    def f_any(self, s, p):
        if eval(f"{s} {self.comparator} {self.threshold}"): return p % 2 == 0
        if p == 0: return 0
        h = [self.f_any(eval(f"{s} {move}"), p-1) for move in self.moves]
        return any(h) if p % 2 else any(h)

    def f_all(self, s, p):
        if eval(f"{s} {self.comparator} {self.threshold}"): return p % 2 == 0
        if p == 0: return 0
        h = [self.f_all(eval(f"{s} {move}"), p-1) for move in self.moves]
        return any(h) if p % 2 else all(h)

    def get_game(self, win_step, conf):
        r = range(self.s_min, self.s_max)
        if conf == "any":
            self.g =  [s for s in r if self.f_any(s, win_step) == 1]
        else:
            self.g = [s for s in r if self.f_all(s, win_step) == 1]

    def get_game_last_step_wins_only(self, win_step, conf):
        r = range(self.s_min, self.s_max)
        if conf == "any":
            self.g =  [s for s in r if (self.f_any(s, win_step) == 1) and not (self.f_any(s, win_step - 2) == 1)]
        else:
            self.g = [s for s in r if (self.f_all(s, win_step) == 1 ) and not (self.f_all(s, win_step - 2) == 1)]




# ==============================================================================
# 2. ПРЕДСТАВЛЕНИЕ (View Widgets)
# ==============================================================================

class GameConfigWidget_1Pile(QWidget):
    """Виджет для настройки всех параметров игры."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Параметры игры
        params_group = QGroupBox("Параметры игры")
        form_layout = QFormLayout()
        self.threshold_input = QLineEdit("30")
        self.comparator_combo = QComboBox()
        self.comparator_combo.addItems(["≤ (меньше или равно)", "≥ (больше или равно)"])
        self.s_min_input = QLineEdit("1")
        self.s_max_input = QLineEdit("60")
        form_layout.addRow("Игра завершается при S:", self.comparator_combo)
        form_layout.addRow("Пороговое значение:", self.threshold_input)
        form_layout.addRow("Минимальное S для анализа:", self.s_min_input)
        form_layout.addRow("Максимальное S для анализа:", self.s_max_input)
        params_group.setLayout(form_layout)
        layout.addWidget(params_group)

        # Настройка ходов
        moves_group = QGroupBox("Ходы")
        moves_layout = QVBoxLayout()
        self.moves_list_widget = QListWidget()
        moves_layout.addWidget(self.moves_list_widget)

        # Панель добавления хода
        add_move_layout = QHBoxLayout()
        self.move_value_input = QLineEdit("+ 1")
        self.add_move_button = QPushButton("Добавить ход")
        self.add_move_button.clicked.connect(self.add_move)
        add_move_layout.addWidget(self.move_value_input)
        add_move_layout.addWidget(self.add_move_button)


        # Кнопка удаления
        self.remove_move_button = QPushButton("Удалить выбранный ход")
        self.remove_move_button.clicked.connect(self.remove_move)
        add_move_layout.addWidget(self.remove_move_button)

        add_g19_layout = QHBoxLayout()
        label_who = QLabel("19. Кто выиграл?")
        self.comparator_g19_player = QComboBox()
        self.comparator_g19_player.addItems(["Ваня", "Петя"])
        label_when = QLabel("Каким ходом?")
        self.g19_value_input = QLineEdit("1")
        self.comparator_g19 = QComboBox()
        self.comparator_g19.addItems(["При ошибке соперника", "При любых ходах соперника"])
        add_g19_layout.addWidget(label_who)
        add_g19_layout.addWidget(self.comparator_g19_player)
        add_g19_layout.addWidget(label_when)
        add_g19_layout.addWidget(self.g19_value_input)
        add_g19_layout.addWidget(self.comparator_g19)

        add_g20_layout = QHBoxLayout()
        label_who = QLabel("20. Кто выиграл?")
        self.comparator_g20_player = QComboBox()
        self.comparator_g20_player.addItems(["Петя", "Ваня"])
        label_when = QLabel("Каким ходом?")
        self.g20_value_input = QLineEdit("2")
        self.comparator_g20 = QComboBox()
        self.comparator_g20.addItems(["При любых ходах соперника", "При ошибке соперника"])
        add_g20_layout.addWidget(label_who)
        add_g20_layout.addWidget(self.comparator_g20_player)
        add_g20_layout.addWidget(label_when)
        add_g20_layout.addWidget(self.g20_value_input)
        add_g20_layout.addWidget(self.comparator_g20)

        add_g21_layout = QHBoxLayout()
        label_who = QLabel("21. Кто выиграл?")
        self.comparator_g21_player = QComboBox()
        self.comparator_g21_player.addItems(["Ваня", "Петя"])
        label_when = QLabel("Каким ходом?")
        self.g21_value_input = QLineEdit("2")
        self.comparator_g21 = QComboBox()
        self.comparator_g21.addItems(["При любых ходах соперника", "При ошибке соперника"])
        add_g21_layout.addWidget(label_who)
        add_g21_layout.addWidget(self.comparator_g21_player)
        add_g21_layout.addWidget(label_when)
        add_g21_layout.addWidget(self.g21_value_input)
        add_g21_layout.addWidget(self.comparator_g21)

        moves_layout.addLayout(add_move_layout)
        moves_layout.addLayout(add_g19_layout)
        moves_layout.addLayout(add_g20_layout)
        moves_layout.addLayout(add_g21_layout)
        moves_group.setLayout(moves_layout)
        layout.addWidget(moves_group)

        self.moves_list = []


    def add_move(self):
        """Создает и добавляет ход в список на основе выбора пользователя."""
        try:
            operation = self.move_value_input.text()

            for i in operation.split(','):
                self.moves_list.append(i)

            check_is_countable = eval("8" + self.moves_list[0])

            for i in self.moves_list:
                self.moves_list_widget.addItem(' '.join(i.split()))
        except ValueError:
            QMessageBox.warning(self, "Ошибка ввода", "Значение для хода должно быть набором операций /, *, +, - и целых чисел")


    def remove_move(self):
        """Удаляет выделенный ход из списка."""
        selected_items = self.moves_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            self.moves_list_widget.takeItem(self.moves_list_widget.row(item))
            self.moves_list.remove(item.text())

    def get_game(self):
        """Собирает все параметры из виджетов и возвращает объект Game."""
        try:
            threshold = int(self.threshold_input.text())
            comparator = "<=" if self.comparator_combo.currentIndex() == 0 else ">="
            s_min = int(self.s_min_input.text())
            s_max = int(self.s_max_input.text())



            if not self.moves_list:
                raise ValueError("Необходимо определить хотя бы один ход.")


            g19_conf = ((int(self.g19_value_input.text()) * 2) if self.comparator_g19_player.currentIndex() == 0 else (int(self.g19_value_input.text()) * 2 - 1), ("any" if self.comparator_g19.currentIndex() == 0 else "all"))
            g20_conf = ((int(self.g20_value_input.text()) * 2) if self.comparator_g20_player.currentIndex() == 1 else (int(self.g20_value_input.text()) * 2 - 1), ("any" if self.comparator_g20.currentIndex() == 1 else "all"))
            g21_conf = ((int(self.g21_value_input.text()) * 2) if self.comparator_g21_player.currentIndex() == 0 else (int(self.g21_value_input.text()) * 2 - 1), ("any" if self.comparator_g21.currentIndex() == 1 else "all"))

            g = Game(self.moves_list, threshold, comparator, s_min, s_max)

            lst = []

            for i in (g19_conf, g20_conf, g21_conf):
                g.get_game(*i)
                lst.append(list(map(str, g.g)))

            for i in (g19_conf, g20_conf, g21_conf):
                if i[0] > 2:
                    g.get_game_last_step_wins_only(*i)
                    lst.append(list(map(str, g.g)))
                else:
                    lst.append(" ")

            return lst

        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Ошибка конфигурации", f"Не удалось создать игру: {e}")
            return None


class ResultsWidget(QWidget):
    """Виджет для отображения результатов анализа."""

    def __init__(self):
        super().__init__()
        group = QGroupBox("Результаты")
        layout = QFormLayout(group)

        self.task19_label = QLineEdit()
        self.task20_label = QLineEdit()
        self.task21_label = QLineEdit()

        for label in (self.task19_label, self.task20_label, self.task21_label):
            label.setReadOnly(True)

        layout.addRow("Задание 19", self.task19_label)
        layout.addRow("Задание 20", self.task20_label)
        layout.addRow("Задание 21", self.task21_label)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(group)

    def format_ans(self, ans):
        if len(ans.split()) > 6:
            ans = ans.split()
            ans = ' '.join(ans[:3]) + f' ..(ещё {len(ans[3:-3])}).. ' + ' '.join(ans[-3:])
        return ans

    def update_results(self, results: dict):
        """Обновляет текстовые поля результатами."""
        ans_19 = str(results.get("19", "Не найдено"))
        ans_20 = str(results.get("20", "Не найдено"))
        ans_21 = str(results.get("21", "Не найдено"))

        ans_19 = self.format_ans(ans_19)
        ans_20 = self.format_ans(ans_20)
        ans_21 = self.format_ans(ans_21)

        ans_19a = str(results.get("19a", " "))
        ans_20a = str(results.get("20a", " "))
        ans_21a = str(results.get("21a", " "))

        ans_19a = self.format_ans(ans_19a)
        ans_20a = self.format_ans(ans_20a)
        ans_21a = self.format_ans(ans_21a)

        if ans_19a != " ":
            ans_19 += " " * 5 + "Когда выиграет последним ходом: " + ans_19a
        if ans_20a != " ":
            ans_20 += " " * 5 + "Когда выиграет последним ходом: " + ans_20a
        if ans_21a != " ":
            ans_21 += " " * 5 + "Когда выиграет последним ходом: " + ans_21a

        self.task19_label.setText(ans_19)
        self.task20_label.setText(ans_20)
        self.task21_label.setText(ans_21)

    def clear(self):
        """Очищает поля результатов."""
        self.task19_label.clear()
        self.task20_label.clear()
        self.task21_label.clear()


# ==============================================================================
# 3. КОНТРОЛЛЕР И ГЛАВНОЕ ОКНО (Controller & Main Window)
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализатор игр ЕГЭ")
        self.setMinimumSize(QSize(450, 600))

        # Центральный виджет и главный layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Создание дочерних виджетов (Views)
        self.config_widget = GameConfigWidget_1Pile()
        self.results_widget = ResultsWidget()

        # Кнопка для запуска анализа
        self.analyze_button = QPushButton("Провести анализ")
        self.analyze_button.setStyleSheet("font-size: 16px; padding: 10px;")

        # Добавление виджетов в layout
        main_layout.addWidget(self.config_widget)
        main_layout.addWidget(self.analyze_button)
        main_layout.addWidget(self.results_widget)

        # Связывание сигнала кнопки с методом-контроллером
        self.analyze_button.clicked.connect(self.run_analysis)

    def run_analysis(self):

        self.results_widget.clear()

        # 1. Получаем сконфигурированную игру из виджета
        game = self.config_widget.get_game()
        if game is None:
            # Ошибка уже была показана внутри get_game
            return

        # 2. Создаем анализатор и запускаем его
        try:
            for i in range(3):
                if len(game[i]) == 0: game[i] = ['Не', 'найдено']

            solutions = dict()
            solutions["19"] = ' '.join(game[0])
            solutions["20"] = ' '.join(game[1])
            solutions["21"] = ' '.join(game[2])
            solutions["19a"] = ' '.join(game[3])
            solutions["20a"] = ' '.join(game[4])
            solutions["21a"] = ' '.join(game[5])
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка анализа", f"Во время вычислений произошла ошибка: {e}"
            )
            return

        # 3. Обновляем виджет с результатами
        self.results_widget.update_results(solutions)
        QMessageBox.information(self, "Завершено", "Анализ успешно завершен!")


# ==============================================================================
# Точка входа
# ==============================================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())