from src.logic.shapes import Rectangle, Line, Ellipse, Group

class ShapeFactory:
    @staticmethod
    def create_shape(shape_type: str, start_point, end_point, color: str):
        """
        start_point, end_point: QPointF (координаты сцены)
        """
        x1, y1 = start_point.x(), start_point.y()
        x2, y2 = end_point.x(), end_point.y()

        # Для линий нам нужны именно точки начала и конца (даже если тянем назад)
        if shape_type == 'line':
            return Line(x1, y1, x2, y2, color)

        # Для прямоугольных фигур (Rect, Ellipse) нужна нормализация
        x = min(x1, x2)
        y = min(y1, y2)
        w = abs(x2 - x1)
        h = abs(y2 - y1)

        if shape_type == 'rect':
            return Rectangle(x, y, w, h, color)
        elif shape_type == 'ellipse':
            return Ellipse(x, y, w, h, color)
        else:
            # Важно: Фабрика должна сообщать, если её попросили невозможного
            raise ValueError(f"Неизвестный тип фигуры: {shape_type}")

    def from_dict(data: dict):
        """
        Восстанавливает объект (или дерево объектов) из словаря.
        """
        shape_type = data.get("type")

        if shape_type == "group":
            return ShapeFactory._create_group(data)
        elif shape_type in ["rect", "line", "ellipse"]:
            return ShapeFactory._create_primitive(data)
        else:
            raise ValueError(f"Unknown type: {shape_type}")

    @staticmethod
    def _create_primitive(data: dict):
        props = data.get("props", {})
        shape_type = data.get("type")

        # Создаем объекты, используя данные из JSON
        # Примечание: тут можно упростить, если унифицировать конструкторы,
        # но для наглядности распишем:
        if shape_type == "rect":
            # Важно: цвет и толщину тоже надо достать
            color = props.get("color", "black")
            obj = Rectangle(props['x'], props['y'], props['w'], props['h'], color)

        elif shape_type == "line":
            color = props.get("color", "black")
            obj = Line(props['x1'], props['y1'], props['x2'], props['y2'], color)

        elif shape_type == "ellipse":
            color = props.get("color", "black")
            obj = Ellipse(props['x'], props['y'], props['w'], props['h'], color)

        # Восстанавливаем позицию объекта, если она была сохранена отдельно
        # (для примитивов внутри группы это критично)
        # Если в JSON сохранялись x/y как pos объекта:
        if "pos" in data:
            obj.setPos(data["pos"][0], data["pos"][1])

        return obj

    @staticmethod
    def _create_group(data: dict):
        group = Group()

        # 1. Восстанавливаем позицию самой группы
        x, y = data.get("pos", [0, 0])
        group.setPos(x, y)

        # 2. Рекурсивно восстанавливаем детей
        children_data = data.get("children", [])
        for child_dict in children_data:
            # РЕКУРСИЯ: Фабрика вызывает сама себя
            child_item = ShapeFactory.from_dict(child_dict)

            # 3. Добавляем в группу
            # Сначала добавляем, чтобы установить отцовство
            group.addToGroup(child_item)

            # Если координаты ребенка сохранены как "pos" в JSON:
            if "pos" in child_dict:
                cx, cy = child_dict["pos"]
                child_item.setPos(cx, cy)
                # Так как item уже в группе, setPos задает локальные координаты!

        return group