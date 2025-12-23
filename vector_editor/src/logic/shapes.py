# src/logic/shapes.py
from abc import ABC, abstractmethod
from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtGui import QPen, QColor, QPainterPath
from PySide6.QtCore import Qt, QPointF
from PySide6.QtWidgets import QGraphicsItemGroup

# Получаем метаклассы
mc1 = type(QGraphicsPathItem)  # или Shiboken.ObjectType
mc2 = type(ABC)               # abc.ABCMeta

# Создаем объединенный метакласс
class CombinedMeta(mc1, mc2):
    pass

class Shape(QGraphicsPathItem, ABC, metaclass=CombinedMeta):
    def __init__(self, color: str = "black", stroke_width: int = 2):
        super().__init__()

        self.color = color
        self.stroke_width = stroke_width

        self._setup_pen()
        self._setup_flags()

    def _setup_pen(self):
        pen = QPen(QColor(self.color))
        pen.setWidth(self.stroke_width)
        self.setPen(pen)

    def _setup_flags(self):
        # Разрешаем выделение и перемещение
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable)
        # Разрешаем слать сигналы при изменении геометрии (пригодится позже)
        self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def change_sm_flags(self, flag: bool):
        if flag == True:
            self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable)
            self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable)
        else:
            self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsSelectable, False)
            self.setFlag(QGraphicsPathItem.GraphicsItemFlag.ItemIsMovable, False)

    @abstractmethod
    def set_geometry(self, start_point: QPointF, end_point: QPointF):
        """
        Метод для динамического обновления формы фигуры.
        Принимает две точки (старт рисования и текущее положение мыши).
        """
        pass

    def set_active_color(self, color: str):
        """Базовая реализация для Листьев (Line, Rect)"""
        self.color = color
        pen = self.pen()
        pen.setColor(QColor(color))
        self.setPen(pen)


    # --- Абстрактный интерфейс ---

    @property
    @abstractmethod
    def type_name(self) -> str:
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        pass

    # --- Общие методы для всех фигур (не абстрактные) ---

    def set_stroke_width(self, width: int):
        pen = self.pen()
        pen.setWidth(width)
        self.setPen(pen)


class Rectangle(Shape):
    def __init__(self, x, y, w, h, color="black", stroke_width=2):
        # 1. Инициализация родителя (настройка ручки, флагов)
        super().__init__(color, stroke_width)

        # 2. Сохраняем "Бизнес-данные"
        # Они нужны нам для сохранения в файл (to_dict)
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        # 3. Создаем визуальное представление
        self._create_geometry()

    def _create_geometry(self):
        # Создаем векторный путь
        path = QPainterPath()
        path.addRect(self.x, self.y, self.w, self.h)

        # Передаем путь в движок Qt
        self.setPath(path)

    # --- Реализация Абстрактных методов ---

    @property
    def type_name(self) -> str:
        return "rect"

    def to_dict(self) -> dict:
        return {
            "type": self.type_name,
            # Сохраняем позицию (важно для детей группы)
            "pos": [self.x(), self.y()],
            "props": {
                # Сохраняем геометрию (размеры)
                # Для rect это координаты внутри его локальной системы
                "x": self.rect().x(),
                "y": self.rect().y(),
                "w": self.rect().width(),
                "h": self.rect().height(),
                "color": self.pen().color().name()
            }
        }

    def set_geometry(self, start_point, end_point):
        # 1. Сохраняем новые координаты (для будущего сохранения)
        self.x = min(start_point.x(), end_point.x())
        self.y = min(start_point.y(), end_point.y())
        self.w = abs(end_point.x() - start_point.x())
        self.h = abs(end_point.y() - start_point.y())

        # 2. Перестраиваем путь (QPainterPath)
        path = QPainterPath()
        path.addRect(self.x, self.y, self.w, self.h)

        # 3. Обновляем визуальное представление
        self.setPath(path)


class Line(Shape):
    def __init__(self, x1, y1, x2, y2, color="black", stroke_width=2):
        super().__init__(color, stroke_width)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        self._create_geometry()

    def _create_geometry(self):
        path = QPainterPath()
        # Инструкция: встань в начало
        path.moveTo(self.x1, self.y1)
        # Инструкция: проведи черту до конца
        path.lineTo(self.x2, self.y2)

        self.setPath(path)

    @property
    def type_name(self) -> str:
        return "line"

    def to_dict(self) -> dict:
        return {
            "type": self.type_name,
            "props": {
                "x1": self.x1, "y1": self.y1,
                "x2": self.x2, "y2": self.y2,
                "color": self.pen().color().name(),
                "stroke_width": self.pen().width()
            }
        }

    def set_geometry(self, start_point, end_point):
        self.x1 = start_point.x()
        self.y1 = start_point.y()
        self.x2 = end_point.x()
        self.y2 = end_point.y()

        path = QPainterPath()
        path.moveTo(self.x1, self.y1)
        path.lineTo(self.x2, self.y2)

        self.setPath(path)

class Ellipse(Shape):
    def __init__(self, x, y, w, h, color="black", stroke_width=2):
        super().__init__(color, stroke_width)
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self._create_geometry()

    def _create_geometry(self):
        path = QPainterPath()
        # Отличие только в методе: addEllipse вместо addRect
        path.addEllipse(self.x, self.y, self.w, self.h)
        self.setPath(path)

    @property
    def type_name(self) -> str:
        return "ellipse"

    def to_dict(self) -> dict:
        return {
            "type": self.type_name,
            # Сохраняем позицию (важно для детей группы)
            "pos": [self.x(), self.y()],
            "props": {
                # Сохраняем геометрию (размеры)
                # Для rect это координаты внутри его локальной системы
                "x": self.rect().x(),
                "y": self.rect().y(),
                "w": self.rect().width(),
                "h": self.rect().height(),
                "color": self.pen().color().name()
            }
        }

    def set_geometry(self, start_point, end_point):
        # 1. Сохраняем новые координаты (для будущего сохранения)
        self.x = min(start_point.x(), end_point.x())
        self.y = min(start_point.y(), end_point.y())
        self.w = abs(end_point.x() - start_point.x())
        self.h = abs(end_point.y() - start_point.y())

        # 2. Перестраиваем путь (QPainterPath)
        path = QPainterPath()
        path.addEllipse(self.x, self.y, self.w, self.h)

        # 3. Обновляем визуальное представление
        self.setPath(path)


class Group(QGraphicsItemGroup):
    def __init__(self):
        # 1. Инициализируем Qt-часть
        super().__init__()

        # 2. Настраиваем флаги
        # Группа должна быть выделяемой и перемещаемой
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItemGroup.GraphicsItemFlag.ItemIsMovable, True)

        # ВАЖНО: setHandlesChildEvents(True) заставляет группу перехватывать
        # события мыши, адресованные её детям.
        # Если кликнуть по линии внутри группы, событие получит сама группа.
        self.setHandlesChildEvents(True)
        self.x = self.pos().x()
        self.y = self.pos().y()

    @property
    def type_name(self) -> str:
        return "group"

    # --- РЕАЛИЗАЦИЯ ПАТТЕРНА COMPOSITE ---

    def set_geometry(self, start, end):
        # Группу нельзя создать растягиванием мыши (как квадрат),
        # поэтому метод оставляем пустым или выбрасываем ошибку.
        pass

    def set_active_color(self, color: str):
        """
        Рекурсивно меняет цвет всех детей.
        Внешний код (Canvas) просто вызывает group.set_active_color("red"),
        не зная, что внутри 50 объектов.
        """
        for child in self.childItems():
            # Проверяем, является ли ребенок "нашим" (унаследован от Shape)
            if isinstance(child, Shape):
                child.set_active_color(color)

            # Если внутри группы есть другая группа, этот код сработает рекурсивно!

    def to_dict(self) -> dict:
        """
        Рекурсивная сериализация.
        Группа сохраняет себя как список словарей своих детей.
        """
        children_data = []
        for child in self.childItems():
            if isinstance(child, Shape):
                children_data.append(child.to_dict())

        return {
            "type": self.type_name,
            # Позиция самой группы важна, так как дети живут в локальных координатах
            "x": self.pos().x(),
            "y": self.pos().y(),
            "children": children_data
        }

    def set_stroke_width(self, width: int):
        for child in self.childItems():
            if isinstance(child, Shape):
                child.set_stroke_width(width)