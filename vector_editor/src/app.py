from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsEllipseItem,
                               QGraphicsLineItem, QGraphicsTextItem,
                               QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QPushButton, QFileDialog, QMessageBox, QLabel, QFrame)
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QPainterPathStroker, QAction
from src.widgets.canvas import EditorCanvas
from PySide6.QtGui import QKeySequence, QAction
from src.widgets.properties import PropertiesPanel


class VectorEditorWindow(QMainWindow):
    def __init__(self):
        # Обязательный вызов конструктора родителя!
        # Без этого Qt-объект не будет создан в памяти C++
        super().__init__()

        self.setWindowTitle("Vector Editor")
        self.resize(800, 600)  # Начальный размер


        # Хороший тон: выносить настройку UI в отдельный метод
        self.canvas = EditorCanvas()
        self._init_ui()
        self._setup_layout()




    # Внутри метода _init_ui класса VectorEditorWindow (из app.py)

    def _init_ui(self):
        # 1. Создаем строку состояния
        self.statusBar().showMessage("Готов к работе")

        # 2. Создаем Меню
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")  # Амперсанд позволяет открывать меню через Alt+F

        # 3. Создаем Action (Действие)
        # Важно: Action не имеет визуального представления сам по себе,
        # он привязывается к меню или тулбару.
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Close the application")
        # connect - связываем сигнал с методом close() окна
        exit_action.triggered.connect(self.close)

        # Добавляем Action в меню
        file_menu.addAction(exit_action)

        # 4. Создаем Тулбар
        toolbar = self.addToolBar("Main Toolbar")
        toolbar.addAction(exit_action)  # Тот же самый экшен!

        # Храним текущее состояние
        self.current_tool = "line"

        group_action = QAction("Group", self)
        group_action.setShortcut(QKeySequence("Ctrl+G"))
        group_action.triggered.connect(self.canvas.group_selection)

        # Создаем Action для разгруппировки
        ungroup_action = QAction("Ungroup", self)
        ungroup_action.setShortcut(QKeySequence("Ctrl+U"))
        ungroup_action.triggered.connect(self.canvas.ungroup_selection)

        # Добавляем в меню Правка (Edit)
        edit_menu = self.menuBar().addMenu("&Edit")
        edit_menu.addAction(group_action)
        edit_menu.addAction(ungroup_action)

    def on_change_tool(self, tool_name):
        self.current_tool = tool_name
        print(f"Выбран инструмент: {tool_name}")

        # Визуальная логика "Радио-кнопок"
        # Если выбрали Line, отжимаем Rect, и наоборот.
        # (В будущем заменим это на QActionGroup, но сейчас полезно написать руками)

        for button in self.active_button_dict.values():
            button.setChecked(False)
        self.active_button_dict[tool_name].setChecked(True)

        # Передаем информацию в холст (он тоже должен знать, чем мы рисуем)
        self.canvas.set_tool(tool_name)

    def _setup_layout(self):
        # 1. Создаем главный контейнер
        container = QWidget()
        self.setCentralWidget(container)

        # 2. Основной лейаут (Горизонтальный: Слева панель, Справа холст)
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)  # Убираем отступы от краев окна

        # --- Левая панель (Палитра инструментов) ---
        tools_panel = QFrame()
        tools_panel.setFixedWidth(120)  # Фиксируем ширину
        tools_panel.setStyleSheet("background-color: #f0f0f0;")  # Временный цвет для наглядности

        # Создаем кнопки с сохранением ссылки, чтобы потом к ним обращаться
        self.btn_line = QPushButton("Line")
        self.btn_rect = QPushButton("Rect")
        self.btn_ellipse = QPushButton("Ellipse")
        self.btn_select = QPushButton("Select")

        # Делаем кнопки "залипающими" (Checkable)
        self.btn_line.setCheckable(True)
        self.btn_rect.setCheckable(True)
        self.btn_ellipse.setCheckable(True)
        self.btn_select.setCheckable(True)

        # По умолчанию активна Линия
        self.btn_select.setChecked(True)


        # СВЯЗЫВАЕМ СИГНАЛЫ
        # Обратите внимание: мы передаем lambda, чтобы передать параметр типа инструмента
        self.btn_line.clicked.connect(lambda: self.on_change_tool("line"))
        self.btn_rect.clicked.connect(lambda: self.on_change_tool("rect"))
        self.btn_ellipse.clicked.connect(lambda: self.on_change_tool("ellipse"))
        self.btn_select.clicked.connect(lambda: self.on_change_tool("select"))
        self.active_button_dict = {'line': self.btn_line, 'rect': self.btn_rect, 'ellipse': self.btn_ellipse, 'select': self.btn_select}


        # Внутри панели кнопки идут вертикально
        tools_layout = QVBoxLayout(tools_panel)
        tools_layout.addWidget(self.btn_line)
        tools_layout.addWidget(self.btn_rect)
        tools_layout.addWidget(self.btn_ellipse)
        tools_layout.addWidget(self.btn_select)
        tools_layout.addStretch()  # Пружина, которая прижмет кнопки наверх

        # --- Правая часть (Холст) ---
        # Пока используем заглушку, настоящий холст будет ниже
        canvas_placeholder = QFrame()
        canvas_placeholder.setStyleSheet("background-color: white;")

        # 3. Собираем всё вместе
        main_layout.addWidget(tools_panel)
        main_layout.addWidget(canvas_placeholder)

        # Инициализируем панель свойств
        # Передаем ей сцену, чтобы она могла подписаться на сигналы
        self.props_panel = PropertiesPanel(self.canvas.scene)

        # Добавляем в Layout
        # Предполагаем, что main_layout горизонтальный (QHBoxLayout)
        # [Инструменты] [ Холст ] [Свойства]
        main_layout.addWidget(self.props_panel)

        main_layout.addWidget(self.canvas)