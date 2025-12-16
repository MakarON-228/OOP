import sys
import json
from itertools import permutations
from typing import Optional, List, Dict

from PySide6.QtWidgets import (QApplication, QGraphicsView, QGraphicsScene,
                               QGraphicsItem, QGraphicsEllipseItem,
                               QGraphicsLineItem, QGraphicsTextItem,
                               QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QPushButton, QFileDialog, QMessageBox, QLabel)
from PySide6.QtCore import Qt, QRectF, QLineF, QPointF, Signal, QObject
from PySide6.QtGui import QPen, QBrush, QColor, QPainter, QPainterPathStroker, QAction


# ==========================================
# 1. Configuration (Конфигурация)
# ==========================================
class GraphConfig:
    NODE_DIAMETER = 20  # Чуть больше, чтобы было виднее
    NODE_RADIUS = NODE_DIAMETER / 2
    EDGE_WIDTH = 2
    MIN_DISTANCE = 40

    COLOR_BG = QColor(40, 40, 40)
    COLOR_NODE = QColor(0, 255, 255)
    COLOR_NODE_ACTIVE = QColor(255, 0, 255)
    COLOR_EDGE = QColor(255, 255, 255)
    COLOR_TEXT = QColor(255, 255, 255)

    # Цвета для таблицы
    TABLE_BG = QColor(50, 50, 50)
    TABLE_TEXT = QColor(255, 255, 255)
    TABLE_DIAGONAL = QColor(80, 80, 80)  # Цвет диагонали


# ==========================================
# 2. Graph Visual Entities (Виджеты Графа)
# ==========================================
class EdgeItem(QGraphicsLineItem):
    def __init__(self, source_item, dest_item):
        super().__init__()
        self.source = source_item
        self.dest = dest_item
        self.setPen(QPen(GraphConfig.COLOR_EDGE, GraphConfig.EDGE_WIDTH))
        self.setZValue(0)
        self.update_geometry()

    def update_geometry(self):
        line = QLineF(self.source.scenePos(), self.dest.scenePos())
        self.setLine(line)

    def shape(self):
        path = super().shape()
        stroker = QPainterPathStroker()
        stroker.setWidth(10)
        return stroker.createStroke(path)


class NodeItem(QGraphicsEllipseItem):
    def __init__(self, name: str, x: float, y: float):
        rect = QRectF(-GraphConfig.NODE_RADIUS, -GraphConfig.NODE_RADIUS,
                      GraphConfig.NODE_DIAMETER, GraphConfig.NODE_DIAMETER)
        super().__init__(rect)
        self.name = name
        self.edges: List[EdgeItem] = []
        self.setBrush(QBrush(GraphConfig.COLOR_NODE))
        self.setPen(QPen(Qt.NoPen))
        self.setPos(x, y)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self._create_label(name)

    def _create_label(self, text: str):
        self.label = QGraphicsTextItem(text, self)
        self.label.setDefaultTextColor(GraphConfig.COLOR_TEXT)
        # Центрируем текст относительно узла
        dx = -10 if len(text) == 1 else -15
        self.label.setPos(dx, -30)
        # self.label.setFlag(QGraphicsItem.ItemIsMovable)
        self.label.setFlag(QGraphicsItem.ItemIgnoresTransformations)

    def set_highlighted(self, is_active: bool):
        color = GraphConfig.COLOR_NODE_ACTIVE if is_active else GraphConfig.COLOR_NODE
        self.setBrush(QBrush(color))

    def add_connection(self, edge: EdgeItem):
        self.edges.append(edge)

    def remove_connection(self, edge: EdgeItem):
        if edge in self.edges:
            self.edges.remove(edge)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionHasChanged and self.scene():
            for edge in self.edges:
                edge.update_geometry()
        return super().itemChange(change, value)


# ==========================================
# 3. Graph Logic Managers
# ==========================================
class ChainBuilder:
    def __init__(self):
        self.active_node: Optional[NodeItem] = None

    def start_or_continue(self, node: NodeItem) -> Optional[NodeItem]:
        prev_node = self.active_node
        if self.active_node:
            self.active_node.set_highlighted(False)
        self.active_node = node
        self.active_node.set_highlighted(True)
        return prev_node

    def reset(self):
        if self.active_node:
            self.active_node.set_highlighted(False)
            self.active_node = None


class GraphManager(QObject):
    # Сигнал об изменении количества узлов (для таблицы)
    node_count_changed = Signal(int)

    def __init__(self, scene: QGraphicsScene):
        super().__init__()
        self.scene = scene
        self.node_counter = 0

    def reset(self):
        self.node_counter = 0
        self.scene.clear()
        self.node_count_changed.emit(0)

    def generate_name(self) -> str:
        n = self.node_counter
        name = ""
        while n >= 0:
            name = chr(ord('A') + (n % 26)) + name
            n = n // 26 - 1
        self.node_counter += 1
        return name

    def create_node(self, pos: QPointF, name: str = None) -> NodeItem:
        if name is None:
            name = self.generate_name()
        else:
            # Если загружаем из файла, нужно обновить счетчик, чтобы новые имена не конфликтовали
            # Простая эвристика: увеличиваем счетчик
            self.node_counter += 1

        node = NodeItem(name, pos.x(), pos.y())
        self.scene.addItem(node)
        self.node_count_changed.emit(self.get_node_count())
        return node

    def create_edge(self, u: NodeItem, v: NodeItem):
        if u == v: return
        # Проверка дубликатов
        for edge in u.edges:
            if (edge.source == u and edge.dest == v) or (edge.source == v and edge.dest == u):
                return
        edge = EdgeItem(u, v)
        self.scene.addItem(edge)
        u.add_connection(edge)
        v.add_connection(edge)

    def delete_item(self, item: QGraphicsItem):
        if isinstance(item, NodeItem):
            for edge in list(item.edges):
                self.delete_item(edge)
            self.scene.removeItem(item)
            self.node_count_changed.emit(self.get_node_count())
        elif isinstance(item, EdgeItem):
            item.source.remove_connection(item)
            item.dest.remove_connection(item)
            self.scene.removeItem(item)
        elif isinstance(item, QGraphicsTextItem):
            parent = item.parentItem()
            if isinstance(parent, NodeItem):
                self.delete_item(parent)

    def get_node_count(self) -> int:
        return sum(1 for item in self.scene.items() if isinstance(item, NodeItem))

    def is_position_valid(self, pos: QPointF) -> bool:
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                distance = QLineF(pos, item.scenePos()).length()
                if distance < GraphConfig.MIN_DISTANCE:
                    return False
        return True

    def get_nodes_list(self):
        lst = []
        nodes = [item for item in self.scene.items() if isinstance(item, NodeItem)]
        for u in nodes:
            h = []
            h.append(u.name)
            s = ''
            for edge in u.edges:
                if edge.source == u:
                    s += edge.dest.name
                else:
                    s += edge.source.name
            h.append(s)
            lst.append(h)
        return lst

    @property
    def format_for_solving_graph(self):
        data = self.get_nodes_list()
        for i in range(len(data)):
            data[i][0] = data[i][0].upper()
            data[i][1] = ''.join(sorted([c.upper() for c in data[i][1] if c.isalpha()]))
        data.sort(key=lambda lst: lst[0])
        print(data)
        s = ''
        for i in data:
            s += ''.join(i) + ' '
        s = s[: -1]
        return s


# ==========================================
# 4_5. Matrix Widget (Таблица весов)
# ==========================================
class WeightMatrixWidget(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(0)
        self.setRowCount(0)
        self.setWindowTitle("Матрица весов")

        # Стилизация таблицы под темную тему
        self.setStyleSheet(f"""
            QTableWidget {{
                background-color: {GraphConfig.TABLE_BG.name()};
                color: {GraphConfig.TABLE_TEXT.name()};
                gridline-color: #666;
            }}
            QHeaderView::section {{
                background-color: #333;
                color: white;
                padding: 4px;
                border: 1px solid #666;
            }}
            QLineEdit {{ color: white; background-color: #444; }}
        """)

        # Обработка изменений для симметрии
        self.itemChanged.connect(self.on_item_changed)

        # 1. Задаем фиксированную ширину столбцов (например, 40 пикселей)
        self.horizontalHeader().setDefaultSectionSize(40)

        # 2. (Опционально) Задаем высоту строк, чтобы ячейки были квадратными
        # self.verticalHeader().setDefaultSectionSize(40)

        # 3. (Опционально) Запрещаем пользователю менять ширину мышкой, чтобы верстка не "поехала"
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)

    @property
    def format_for_solving_table(self):
        matrix = self.get_data()
        col_set = "123456789"[:len(matrix[0])]
        print(matrix)
        c = ''
        for i in range(len(matrix[0])):
            c += col_set[i]
            for j in range(len(matrix[0])):
                c += (matrix[i][j] != '') * col_set[j]
            c += ' '
        c = c[:-1]
        return c

    def update_size(self, node_count: int):
        """Обновляет размер таблицы при добавлении/удалении узлов графа"""
        current_rows = self.rowCount()

        self.setRowCount(node_count)
        self.setColumnCount(node_count)

        headers = [str(i + 1) for i in range(node_count)]
        self.setHorizontalHeaderLabels(headers)
        self.setVerticalHeaderLabels(headers)

        # Блокировка сигналов во время перестройки, чтобы не триггерить on_item_changed
        self.blockSignals(True)

        # Настройка ячеек (диагональ и пустые)
        for r in range(node_count):
            for c in range(node_count):
                item = self.item(r, c)
                if not item:
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.setItem(r, c, item)

                # Диагональ
                if r == c:
                    item.setFlags(Qt.ItemIsEnabled)  # Только чтение
                    item.setBackground(QBrush(GraphConfig.TABLE_DIAGONAL))
                else:
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                    item.setBackground(QBrush(GraphConfig.TABLE_BG))

        self.blockSignals(False)

    def on_item_changed(self, item):
        """Обеспечивает симметричность матрицы"""
        row = item.row()
        col = item.column()

        if row == col: return

        text = item.text()

        # Блокируем сигналы, чтобы не уйти в бесконечную рекурсию
        self.blockSignals(True)

        symmetric_item = self.item(col, row)
        if symmetric_item:
            symmetric_item.setText(text)

        self.blockSignals(False)

    def get_data(self) -> List[List[str]]:
        rows = self.rowCount()
        data = []
        for r in range(rows):
            row_data = []
            for c in range(rows):
                item = self.item(r, c)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        return data

    def set_data(self, data: List[List[str]]):
        size = len(data)
        self.update_size(size)
        self.blockSignals(True)
        for r in range(size):
            for c in range(size):
                if r < len(data) and c < len(data[r]):
                    val = data[r][c]
                    item = self.item(r, c)
                    if item:
                        item.setText(val)
        self.blockSignals(False)


# ==========================================
# 5. Graph Scene & View
# ==========================================
class GraphScene(QGraphicsScene):
    def __init__(self, manager: GraphManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.chain_builder = ChainBuilder()
        self.setBackgroundBrush(QBrush(GraphConfig.COLOR_BG))
        self.setSceneRect(0, 0, 800, 600)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            self.chain_builder.reset()
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        pos = event.scenePos()
        item = self.itemAt(pos, self.views()[0].transform())

        if event.button() == Qt.LeftButton:
            if event.modifiers() & Qt.ShiftModifier:
                if isinstance(item, NodeItem):
                    prev_node = self.chain_builder.start_or_continue(item)
                    if prev_node:
                        self.manager.create_edge(prev_node, item)
                    event.accept()
                    return
                else:
                    self.chain_builder.reset()
            else:
                self.chain_builder.reset()

            if item is None:
                if self.manager.is_position_valid(pos):
                    self.manager.create_node(pos)
                event.accept()
                return

            super().mousePressEvent(event)

        elif event.button() == Qt.RightButton:
            self.chain_builder.reset()
            if item:
                self.manager.delete_item(item)
                event.accept()


# ==========================================
# 6. Main Application Window
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Тренажер: Граф и Матрица весов (ЕГЭ Информатика)")
        self.resize(1200, 700)

        # 1. Сцена и Менеджер
        self.scene = QGraphicsScene()  # Placeholder initialization
        self.graph_manager = GraphManager(self.scene)
        self.scene = GraphScene(self.graph_manager, self)  # Override with custom scene
        self.graph_manager.scene = self.scene  # Re-link

        # 2. Виджеты
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)

        self.matrix_widget = WeightMatrixWidget()

        # 3. Связь Граф -> Таблица
        self.graph_manager.node_count_changed.connect(self.matrix_widget.update_size)

        # 4_5. Лейаут
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)

        # Новая кнопка для решения задачи
        self.solve_button = QPushButton("Решить задачу")
        self.solve_button.clicked.connect(self.solve)

        # Левая часть (Матрица)
        left_layout = QVBoxLayout()
        left_label = QLabel("Матрица весов (Симметричная)")
        left_layout.addWidget(left_label)
        left_layout.addWidget(self.matrix_widget)
        left_layout.addWidget(self.solve_button)

        # Правая часть (Граф)
        right_layout = QVBoxLayout()
        right_label = QLabel("Редактор графа (ЛКМ - узел, Shift+ЛКМ - ребро, ПКМ - удалить)")
        right_layout.addWidget(right_label)
        right_layout.addWidget(self.view)

        main_layout.addLayout(left_layout, 1)  # stretch factor 1
        main_layout.addLayout(right_layout, 2)  # stretch factor 2 (граф шире)

        self.setCentralWidget(central_widget)

        # 5. Меню
        self.create_menu()

    def solve(self):
        matrix_data = self.matrix_widget.format_for_solving_table
        graph_data = self.graph_manager.format_for_solving_graph
        res = solve_first_task(graph_data, matrix_data, len(matrix_data.split()))
        print(res)

        headers = [i for i in res]
        self.matrix_widget.setHorizontalHeaderLabels(headers)
        self.matrix_widget.setVerticalHeaderLabels(headers)

    def create_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("Файл")

        save_action = QAction("Сохранить упражнение...", self)
        save_action.triggered.connect(self.save_exercise)
        file_menu.addAction(save_action)

        load_action = QAction("Загрузить упражнение...", self)
        load_action.triggered.connect(self.load_exercise)
        file_menu.addAction(load_action)

        clear_action = QAction("Очистить всё", self)
        clear_action.triggered.connect(self.clear_all)
        file_menu.addAction(clear_action)

    def clear_all(self):
        self.graph_manager.reset()
        self.matrix_widget.update_size(0)

    def save_exercise(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", "", "JSON Files (*.json)")
        if not file_path:
            return

        # Сбор данных графа
        nodes_data = []
        node_id_map = {}  # Object -> ID

        # Находим все узлы
        items = [i for i in self.scene.items() if isinstance(i, NodeItem)]
        # Сортируем по имени, чтобы порядок был детерминированным (опционально)
        # Но нам важнее просто назначить ID
        for idx, node in enumerate(items):
            node_id_map[node] = idx
            nodes_data.append({
                "id": idx,
                "name": node.name,
                "x": node.pos().x(),
                "y": node.pos().y()
            })

        edges_data = []
        visited_edges = set()
        for node in items:
            for edge in node.edges:
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    u_id = node_id_map.get(edge.source)
                    v_id = node_id_map.get(edge.dest)
                    if u_id is not None and v_id is not None:
                        edges_data.append({"u": u_id, "v": v_id})

        # Сбор данных матрицы
        matrix_data = self.matrix_widget.get_data()

        data = {
            "graph": {
                "nodes": nodes_data,
                "edges": edges_data,
                "node_counter": self.graph_manager.node_counter
            },
            "matrix": matrix_data
        }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Успех", "Упражнение сохранено!")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {e}")

    def load_exercise(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть файл", "", "JSON Files (*.json)")
        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 1. Очистка
            self.clear_all()

            # 2. Восстановление графа
            graph_data = data.get("graph", {})
            nodes_list = graph_data.get("nodes", [])
            edges_list = graph_data.get("edges", [])

            # Восстанавливаем счетчик имен
            self.graph_manager.node_counter = graph_data.get("node_counter", 0)

            # Создаем узлы и мапим ID -> NodeItem
            id_to_node = {}
            for n_data in nodes_list:
                pos = QPointF(n_data["x"], n_data["y"])
                name = n_data["name"]
                node = self.graph_manager.create_node(pos, name)
                id_to_node[n_data["id"]] = node

            # Создаем ребра
            for e_data in edges_list:
                u = id_to_node.get(e_data["u"])
                v = id_to_node.get(e_data["v"])
                if u and v:
                    self.graph_manager.create_edge(u, v)

            # 3. Восстановление матрицы
            matrix_data = data.get("matrix", [])
            self.matrix_widget.set_data(matrix_data)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {e}")

def solve_first_task(s, z, table_length):
    # s = 'ADEF BDF CFG DABE EADG FABC GCE'
    #d = {c:set(v) for c,*v in s.split()}

    # z = '123 2145 316 427 5267 6357 7456'
    for x in permutations(set(s)-{' '}):
      t = z
      for a,b in zip(''.join(str(i + 1) for i in range(table_length)), x):
        t = t.replace(a,b)


      #g = {c:set(v) for c,*v in t.split()}
      g = ' '.join(c+''.join(sorted(v)) for c,*v in sorted(t.split()))
      if g==s:
        return x

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Установка темной темы для всего приложения
    app.setStyle("Fusion")
    palette = app.palette()
    palette.setColor(palette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.WindowText, Qt.white)
    palette.setColor(palette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(palette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ToolTipBase, Qt.white)
    palette.setColor(palette.ColorRole.ToolTipText, Qt.white)
    palette.setColor(palette.ColorRole.Text, Qt.white)
    palette.setColor(palette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(palette.ColorRole.ButtonText, Qt.white)
    palette.setColor(palette.ColorRole.BrightText, Qt.red)
    palette.setColor(palette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(palette.ColorRole.HighlightedText, Qt.black)
    app.setPalette(palette)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())