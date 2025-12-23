from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QUndoStack
from src.logic.shapes import Rectangle, Line, Ellipse, Group
from src.logic.factory import ShapeFactory
from PySide6.QtWidgets import QGraphicsView, QGraphicsScene
from src.logic.tools import SelectionTool, CreationTool

class EditorCanvas(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.scene.setSceneRect(0, 0, 800, 600)
        self.setRenderHint(QPainter.Antialiasing, True)
        self.setMouseTracking(True)

        self.undo_stack = QUndoStack(self)

        # Опционально: ограничим историю 50 шагами, чтобы экономить память
        self.undo_stack.setUndoLimit(50)

        # 1. Инициализация инструментов
        # Создаем экземпляры один раз и храним их
        self.tools = {
            "select": SelectionTool(self),
            "rect": CreationTool(self, "rect", self.undo_stack),
            "line": CreationTool(self, "line", self.undo_stack),
            "ellipse": CreationTool(self, "ellipse", self.undo_stack)
        }

        # 2. Установка начального состояния
        self.current_tool = self.tools["select"]

    def set_tool(self, tool_name):
        if tool_name in self.tools:
            self.current_tool = self.tools[tool_name]

            # Логика смены курсора
            if tool_name == "select":
                self.setCursor(Qt.ArrowCursor)
            else:
                # Для инструментов рисования ставим крестик
                self.setCursor(Qt.CrossCursor)

        # (В будущем здесь добавим смену курсора)

    def group_selection(self):
        """Создает группу из выделенных элементов"""
        selected_items = self.scene.selectedItems()

        # Защита от дурака: не группируем пустоту
        if not selected_items:
            return
        # 1. Создаем группу
        group = Group()


        # 2. Сначала добавляем пустую группу на сцену!
        # Это важно для корректной инициализации координат.
        self.scene.addItem(group)

        # 3. Переносим элементы
        for item in selected_items:
            # Снимаем выделение с ребенка (теперь он часть целого)
            item.setSelected(False)

            # ВАЖНО: addToGroup делает "reparenting".
            # Она сама удаляет item со сцены и добавляет его в дети группы.
            # Она сама пересчитывает координаты item.pos(), чтобы он визуально остался на месте.
            group.addToGroup(item)

        # 4. Выделяем новую группу, чтобы пользователь видел результат
        group.setSelected(True)
        print("Группа создана")

    def ungroup_selection(self):
        """Разбивает выделенные группы на отдельные элементы"""
        selected_items = self.scene.selectedItems()

        for item in selected_items:
            # Проверяем, является ли элемент группой.
            # Обычный квадрат разгруппировать нельзя.
            if isinstance(item, Group):
                # ВАЖНО: destroyGroup удаляет сам объект item (группу) со сцены,
                # но его дети остаются на сцене (становятся сиротами).
                self.scene.destroyItemGroup(item)
                print("Группа расформирована")

    # --- ДЕЛЕГИРОВАНИЕ СОБЫТИЙ ---
    # Canvas теперь выступает просто как "Диспетчер"

    def mousePressEvent(self, event):
        self.current_tool.mouse_press(event)

    def mouseMoveEvent(self, event):
        self.current_tool.mouse_move(event)

    def mouseReleaseEvent(self, event):
        self.current_tool.mouse_release(event)


