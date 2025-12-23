from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel,
                               QSpinBox, QPushButton, QFrame, QHBoxLayout, QDoubleSpinBox)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QColorDialog


class PropertiesPanel(QWidget):
    def __init__(self, scene):
        super().__init__()
        self.scene = scene  # Сохраняем ссылку на сцену, чтобы читать данные

        self._init_ui()

        # --- PATTERN OBSERVER ---
        # Подписываемся на события изменения выделения в сцене
        self.scene.selectionChanged.connect(self.on_selection_changed)

    def _init_ui(self):
        # Ограничиваем ширину панели, чтобы она не занимала пол-экрана
        self.setFixedWidth(200)
        self.setStyleSheet("background-color: #f0f0f0; border-left: 1px solid #ccc;")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)  # Прижимаем элементы к верху

        # Заголовок
        title = QLabel("Свойства")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        self.lbl_type = QLabel('')
        layout.addWidget(self.lbl_type)

        # 1. Настройка Толщины
        layout.addWidget(QLabel("Толщина обводки:"))
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 50)  # Мин 1, Макс 50 пикселей
        self.spin_width.valueChanged.connect(self.on_width_changed)
        layout.addWidget(self.spin_width)

        # 2. Индикатор Цвета
        layout.addWidget(QLabel("Цвет линии:"))
        self.btn_color = QPushButton()
        self.btn_color.setFixedHeight(30)
        self.btn_color.clicked.connect(self.on_color_clicked)
        # Пока просто заглушка, цвет настроим кодом
        layout.addWidget(self.btn_color)

        # Добавляем пружину, чтобы пустое место было внизу
        layout.addStretch()

        # Исходное состояние: панель выключена, так как ничего не выделено
        self.setEnabled(False)

        geo_layout = QHBoxLayout()

        self.spin_x = QDoubleSpinBox()
        self.spin_x.setRange(-10000, 10000)
        self.spin_x.setPrefix("X: ")
        self.spin_x.valueChanged.connect(self.on_geo_changed)

        self.spin_y = QDoubleSpinBox()
        self.spin_y.setRange(-10000, 10000)
        self.spin_y.setPrefix("Y: ")
        self.spin_y.valueChanged.connect(self.on_geo_changed)

        geo_layout.addWidget(self.spin_x)
        geo_layout.addWidget(self.spin_y)
        layout.addLayout(geo_layout)

    def on_selection_changed(self):
        """Вызывается автоматически при клике по фигурам"""
        selected_items = self.scene.selectedItems()

        # Сценарий 1: Ничего не выделено (кликнули в пустоту)
        if not selected_items:
            self.setEnabled(False)  # Дизаблим всю панель
            # Можно сбросить значения в дефолт
            self.spin_width.setValue(1)
            self.btn_color.setStyleSheet("background-color: transparent")
            return

        # Сценарий 2: Что-то выделено
        self.setEnabled(True)  # Включаем панель

        # Берем первый элемент ("Lead Selection")
        item = selected_items[0]

        self.spin_x.blockSignals(True)
        self.spin_y.blockSignals(True)

        self.spin_x.setValue(item.x)
        self.spin_y.setValue(item.y)

        self.spin_x.blockSignals(False)
        self.spin_y.blockSignals(False)

        current_width = 1
        current_color = "#000000"

        # Блокируем: "Спинбокс, молчи, пока я тебя настраиваю"
        self.spin_width.blockSignals(True)
        self.spin_width.setValue(current_width)
        # Разблокируем: "Теперь можешь реагировать на действия пользователя"
        self.spin_width.blockSignals(False)

        # Проверяем, есть ли у объекта метод pen (карандаш)
        if hasattr(item, "pen") and item.pen() is not None:
            current_width = item.pen().width()
            current_color = item.pen().color().name()  # Возвращает hex string "#RRGGBB"

        if hasattr(item, "type_name"):
            type_text = item.type_name.capitalize()  # "Rect" -> "Rect"
        else:
            # Вариант 2: Через имя класса Python
            type_text = type(item).__name__

            # Если выделено много объектов
        if len(selected_items) > 1:
            type_text += f" (+{len(selected_items) - 1})"

        self.lbl_type.setText(type_text)

        # Важнейший момент для Части 2 (предотвращение цикла),
        # но хорошая привычка писать сразу:
        self.spin_width.blockSignals(True)
        self.spin_width.setValue(current_width)
        self.spin_width.blockSignals(False)

        # Красим кнопку, используя CSS
        # border: none убирает стандартную выпуклость кнопки
        self.btn_color.setStyleSheet(f"background-color: {current_color}; border: 1px solid gray;")

    def on_width_changed(self, value):
        """
        Вызывается, когда пользователь меняет значение в SpinBox.
        value: int (новая толщина)
        """
        selected_items = self.scene.selectedItems()

        for item in selected_items:
            # Нам нужно изменить толщину пера, сохранив его цвет и стиль.

            # 1. Проверяем, есть ли у предмета перо (Group vs Shape)
            # В идеале у Group должен быть метод set_pen_width, но если нет:
            if hasattr(item, "pen"):
                # Получаем копию текущего пера
                new_pen = item.pen()
                # Меняем толщину
                new_pen.setWidth(value)
                # Применяем обратно
                item.setPen(new_pen)

            # Если это Группа и у нас реализован Composite (Модуль 4),
            # то мы должны вызвать специальный метод группы, который раздаст
            # настройку детям. Допустим, мы добавили set_stroke_width в Shape:
            elif hasattr(item, "set_stroke_width"):
                item.set_stroke_width(value)

        # Важно: Заставляем сцену перерисоваться (иногда Qt ленится)
        self.scene.update()

    def on_color_clicked(self):
        """Открывает диалог выбора цвета"""

        # 1. Запускаем диалог.
        # getColor - статический метод, возвращает объект QColor.
        # Можно передать начальный цвет (например, текущий цвет кнопки).
        color = QColorDialog.getColor(title="Выберите цвет линии")

        # 2. Проверяем, выбрал ли пользователь цвет (или нажал Cancel/Esc)
        if color.isValid():
            hex_color = color.name()  # Получаем строку вида "#FF0000"

            # А. Обновляем вид самой кнопки (Визуальный отклик)
            self.btn_color.setStyleSheet(
                f"background-color: {hex_color}; border: 1px solid gray;"
            )

            # Б. Обновляем модель (Фигуры)
            selected_items = self.scene.selectedItems()
            for item in selected_items:
                # Используем метод set_active_color из Модуля 4 (интерфейс Shape)
                # Он работает и для примитивов, и для групп (рекурсивно)!
                if hasattr(item, "set_active_color"):
                    item.set_active_color(hex_color)
                elif hasattr(item, "setPen"):
                    # Fallback для стандартных QGraphicsItem, если они есть
                    pen = item.pen()
                    pen.setColor(color)
                    item.setPen(pen)

    def on_geo_changed(self, value):
        # Этот метод срабатывает и для X, и для Y
        selected_items = self.scene.selectedItems()
        for item in selected_items:
            # item.setPos(x, y)
            # Берем текущие значения из спинбоксов
            new_x = self.spin_x.value()
            new_y = self.spin_y.value()
            item.setPos(new_x, new_y)

        self.scene.update()

    def update_width_ui(self, selected_items):
        self.spin_width.blockSignals(True)

        first_width = -1
        is_mixed = False

        # Проверяем все объекты
        for i, item in enumerate(selected_items):
            if not hasattr(item, "pen"): continue

            w = item.pen().width()

            if i == 0:
                first_width = w
            else:
                if w != first_width:
                    is_mixed = True
                    break

        if is_mixed:
            # Qt Hack: Ставим особое значение, которое означает "Разные"
            # SpinBox не умеет писать текст "Mixed", поэтому ставим -1 (если min=0)
            # Или просто оставляем значение первого, но красим фон спинбокса в желтый
            self.spin_width.setValue(first_width)
            self.spin_width.setStyleSheet("background-color: #fffacd;")  # LightYellow
            self.spin_width.setToolTip("Выбраны объекты с разной толщиной")
        else:
            self.spin_width.setValue(first_width)
            self.spin_width.setStyleSheet("")  # Сброс стиля
            self.spin_width.setToolTip("")

        self.spin_width.blockSignals(False)
