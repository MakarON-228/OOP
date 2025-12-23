from abc import ABC, abstractmethod
from src.logic.factory import ShapeFactory
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGraphicsView
from PySide6.QtCore import Qt
from src.logic.commands import AddShapeCommand

class Tool(ABC):
    def __init__(self, view):
        """
        :param view: Ссылка на экземпляр EditorCanvas.
        Нужна, чтобы инструмент мог взаимодействовать со сценой и видом.
        """
        self.view = view
        self.scene = view.scene

    @abstractmethod
    def mouse_press(self, event):
        """Обработка нажатия кнопки мыши"""
        pass

    @abstractmethod
    def mouse_move(self, event):
        """Обработка перемещения мыши"""
        pass

    @abstractmethod
    def mouse_release(self, event):
        """Обработка отпускания кнопки мыши"""
        pass


class SelectionTool(Tool):
    def mouse_press(self, event):
        # Важный момент: Мы вызываем стандартный метод класса QGraphicsView,
        # передавая ему наш экземпляр view (self.view).
        # Это то же самое, что super().mousePressEvent(event), если бы мы были внутри view.
        QGraphicsView.mousePressEvent(self.view, event)

        # Меняем курсор на "Сжатую руку" (Grabbing), если попали по объекту
        if self.view.scene.itemAt(self.view.mapToScene(event.pos()), self.view.transform()):
            self.view.setCursor(Qt.ClosedHandCursor)

    def mouse_move(self, event):
        # 1. Сначала вызываем стандартную обработку (на случай, если мы тащим объект)
        QGraphicsView.mouseMoveEvent(self.view, event)

        # 2. Дополнительная логика: проверка наведения
        # Проверяем, есть ли под мышкой объекты
        item = self.view.itemAt(event.pos())

        # Важно: меняем курсор только если мы НЕ тащим объект (левая кнопка не нажата)
        if not (event.buttons() & Qt.LeftButton):
            if item:
                self.view.setCursor(Qt.OpenHandCursor)
            else:
                self.view.setCursor(Qt.ArrowCursor)

    def mouse_release(self, event):
        QGraphicsView.mouseReleaseEvent(self.view, event)

        # Возвращаем курсор в обычное состояние (или OpenHand)
        self.view.setCursor(Qt.ArrowCursor)
        # (или запускаем логику проверки hover, см. пункт 3)


class CreationTool(Tool):
    def __init__(self, view, shape_type, undo_stack, color="black"):
        super().__init__(view)
        self.shape_type = shape_type
        self.color = color

        # Временное хранилище
        self.start_pos = None
        self.temp_shape = None  # Ссылка на рисуемую фигуру

        self.undo_stack = undo_stack

    def mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = self.view.mapToScene(event.pos())

            # 1. Создаем фигуру сразу (точка в точку)
            try:
                self.temp_shape = ShapeFactory.create_shape(
                    self.shape_type,
                    self.start_pos,
                    self.start_pos,  # End point = Start point
                    self.color
                )
                self.scene.addItem(self.temp_shape)
            except ValueError:
                pass

    def mouse_move(self, event):
        # 2. Если мы сейчас рисуем (есть активная фигура)
        if self.temp_shape and self.start_pos:
            current_pos = self.view.mapToScene(event.pos())

            # 3. Вызываем метод обновления геометрии
            self.temp_shape.set_geometry(self.start_pos, current_pos)

    def mouse_release(self, event):
        if event.button() == Qt.LeftButton:
            # 4. Завершаем рисование
            # Фигура уже на сцене и имеет правильную форму.
            # Просто очищаем ссылки.
            self.start_pos = None
            self.temp_shape = None