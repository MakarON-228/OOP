from PySide6.QtGui import QUndoCommand


class AddShapeCommand(QUndoCommand):
    def __init__(self, scene, item):
        """
        :param scene: Сцена, куда добавляем
        :param item: Сама фигура (созданная, но еще не добавленная)
        """
        super().__init__()
        self.scene = scene
        self.item = item

        # Текст для отображения в истории (например, в меню "Undo Add Rectangle")
        # Если у фигуры есть наш метод type_name, используем его
        name = "Shape"
        if hasattr(item, "type_name"):
            name = item.type_name
        self.setText(f"Add {name}")

    def redo(self):
        # Выполняется при первом добавлении И при Ctrl+Y (Redo)

        # Проверка: если предмет уже на сцене, повторно добавлять нельзя (будет краш)
        if self.item.scene() != self.scene:
            self.scene.addItem(self.item)

    def undo(self):
        # Выполняется при Ctrl+Z (Undo)
        self.scene.removeItem(self.item)
        # Фигура исчезла с экрана, но self.item хранит её в памяти!