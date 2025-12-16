"""
Солвер для логических формул на числовой прямой.
Определяет ограничения на искомое множество и находит оптимальное решение.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Tuple, Optional, Set
import math

from formula_parser import (
    ASTNode, MembershipNode, NotNode, BinaryNode,
    parse_formula, get_sets_from_ast
)


class Constraint(Enum):
    """Ограничение на интервал"""
    MUST_INCLUDE = auto()  # Интервал обязан входить в A
    MUST_EXCLUDE = auto()  # Интервал обязан НЕ входить в A
    FREE = auto()  # Интервал может входить или не входить
    IMPOSSIBLE = auto()  # Нет решения для этого интервала


@dataclass
class Interval:
    """Интервал на числовой прямой"""
    left: float
    right: float
    left_closed: bool = True
    right_closed: bool = False

    @property
    def length(self) -> float:
        return self.right - self.left

    def __repr__(self):
        l_bracket = '[' if self.left_closed else '('
        r_bracket = ']' if self.right_closed else ')'
        return f"{l_bracket}{self.left}, {self.right}{r_bracket}"


@dataclass
class ConstrainedInterval:
    """Интервал с ограничением"""
    interval: Interval
    constraint: Constraint

    def __repr__(self):
        return f"{self.interval}: {self.constraint.name}"


@dataclass
class SolverResult:
    """Результат работы солвера"""
    success: bool
    intervals: List[Interval] = field(default_factory=list)
    total_length: float = 0.0
    message: str = ""

    @property
    def is_infinite(self) -> bool:
        return any(math.isinf(i.left) or math.isinf(i.right) for i in self.intervals)


class FormulaEvaluator:
    """Вычислитель формул для конкретных значений предикатов"""

    @staticmethod
    def evaluate(node: ASTNode, values: Dict[str, bool]) -> bool:
        """
        Вычисляет значение формулы при заданных значениях предикатов.

        Args:
            node: Узел AST
            values: Словарь {имя_множества: принадлежит_ли_x}

        Returns:
            Логическое значение формулы
        """
        if isinstance(node, MembershipNode):
            return values.get(node.set_name, False)

        elif isinstance(node, NotNode):
            return not FormulaEvaluator.evaluate(node.operand, values)

        elif isinstance(node, BinaryNode):
            left = FormulaEvaluator.evaluate(node.left, values)
            right = FormulaEvaluator.evaluate(node.right, values)

            if node.op == 'AND':
                return left and right
            elif node.op == 'OR':
                return left or right
            elif node.op == 'IMPLIES':
                return (not left) or right
            elif node.op == 'EQUIV':
                return left == right
            elif node.op == 'XOR':
                return left != right

        raise ValueError(f"Неизвестный тип узла: {type(node)}")


class LogicSolver:
    """
    Главный класс солвера.
    Находит оптимальное множество A, удовлетворяющее формуле.
    """

    def __init__(
            self,
            formula: str,
            known_sets: Dict[str, Tuple[float, float]],
            target_set: str,
            maximize: bool = True,
            formula_true: bool = True
    ):
        """
        Args:
            formula: Логическая формула в текстовом виде
            known_sets: Известные отрезки {имя: (левая, правая)}
            target_set: Имя искомого множества
            maximize: True = максимизировать длину, False = минимизировать
            formula_true: True = формула должна быть истинной, False = ложной
        """
        self.formula_str = formula
        self.ast = parse_formula(formula)
        self.known_sets = known_sets
        self.target_set = target_set
        self.maximize = maximize
        self.formula_true = formula_true

        self._validate()

    def _validate(self):
        """Проверяет корректность входных данных"""
        all_sets = get_sets_from_ast(self.ast)

        if self.target_set not in all_sets:
            raise ValueError(f"Искомое множество '{self.target_set}' не найдено в формуле")

        for set_name in all_sets:
            if set_name != self.target_set and set_name not in self.known_sets:
                raise ValueError(f"Множество '{set_name}' не определено")

    def _get_critical_points(self) -> List[float]:
        """Возвращает отсортированный список критических точек"""
        points = set()
        for left, right in self.known_sets.values():
            points.add(left)
            points.add(right)
        return sorted(points)

    def _build_intervals(self, points: List[float]) -> List[Interval]:
        """Строит интервалы по критическим точкам"""
        if not points:
            return [Interval(-math.inf, math.inf)]

        intervals = []

        # Левый бесконечный интервал
        intervals.append(Interval(-math.inf, points[0], False, False))

        # Конечные интервалы между точками
        for i in range(len(points) - 1):
            intervals.append(Interval(points[i], points[i + 1], True, False))

        # Последняя точка как отдельный интервал для корректности
        # Правый бесконечный интервал
        intervals.append(Interval(points[-1], math.inf, True, False))

        return intervals

    def _point_in_set(self, x: float, set_name: str) -> bool:
        """Проверяет принадлежность точки известному множеству"""
        if set_name not in self.known_sets:
            return False
        left, right = self.known_sets[set_name]
        return left <= x <= right

    def _get_constraint_for_interval(self, interval: Interval) -> Constraint:
        """
        Определяет ограничение для интервала.
        Берёт произвольную внутреннюю точку интервала.
        """
        # Выбираем представительную точку
        if math.isinf(interval.left):
            if math.isinf(interval.right):
                test_point = 0.0
            else:
                test_point = interval.right - 1.0
        elif math.isinf(interval.right):
            test_point = interval.left + 1.0
        else:
            test_point = (interval.left + interval.right) / 2

        # Вычисляем значения известных предикатов
        base_values = {}
        for set_name in self.known_sets:
            base_values[set_name] = self._point_in_set(test_point, set_name)

        # Вычисляем формулу при A=0 и A=1
        values_a0 = {**base_values, self.target_set: False}
        values_a1 = {**base_values, self.target_set: True}

        result_a0 = FormulaEvaluator.evaluate(self.ast, values_a0)
        result_a1 = FormulaEvaluator.evaluate(self.ast, values_a1)

        # Инвертируем если нужна ложная формула
        target_value = self.formula_true

        satisfies_a0 = (result_a0 == target_value)
        satisfies_a1 = (result_a1 == target_value)

        if satisfies_a0 and satisfies_a1:
            return Constraint.FREE
        elif satisfies_a0 and not satisfies_a1:
            return Constraint.MUST_EXCLUDE
        elif not satisfies_a0 and satisfies_a1:
            return Constraint.MUST_INCLUDE
        else:
            return Constraint.IMPOSSIBLE

    def _analyze_intervals(self) -> List[ConstrainedInterval]:
        """Анализирует все интервалы и определяет ограничения"""
        points = self._get_critical_points()
        intervals = self._build_intervals(points)

        constrained = []
        for interval in intervals:
            constraint = self._get_constraint_for_interval(interval)
            constrained.append(ConstrainedInterval(interval, constraint))

        return constrained

    def _optimize(self, constrained: List[ConstrainedInterval]) -> SolverResult:
        """
        Находит оптимальное множество A.

        Для максимизации: включаем все MUST_INCLUDE и FREE интервалы
        Для минимизации: включаем только MUST_INCLUDE интервалы
        """
        # Проверяем наличие IMPOSSIBLE
        for ci in constrained:
            if ci.constraint == Constraint.IMPOSSIBLE:
                return SolverResult(
                    success=False,
                    message=f"Нет решения: невозможное ограничение на интервале {ci.interval}"
                )

        # Собираем интервалы для включения в A
        result_intervals = []

        for ci in constrained:
            should_include = False

            if ci.constraint == Constraint.MUST_INCLUDE:
                should_include = True
            elif ci.constraint == Constraint.FREE:
                should_include = self.maximize  # Включаем только при максимизации

            if should_include:
                result_intervals.append(ci.interval)

        # Объединяем смежные интервалы
        merged = self._merge_intervals(result_intervals)

        # Вычисляем суммарную длину (только конечные части)
        total_length = sum(
            i.length for i in merged
            if not math.isinf(i.left) and not math.isinf(i.right)
        )

        if not merged:
            return SolverResult(
                success=True,
                intervals=[],
                total_length=0,
                message="Решение: A = ∅ (пустое множество)"
            )

        return SolverResult(
            success=True,
            intervals=merged,
            total_length=total_length,
            message=self._format_result(merged, total_length)
        )

    def _merge_intervals(self, intervals: List[Interval]) -> List[Interval]:
        """Объединяет смежные и пересекающиеся интервалы"""
        if not intervals:
            return []

        # Сортируем по левой границе
        sorted_intervals = sorted(intervals, key=lambda i: i.left)
        merged = [sorted_intervals[0]]

        for current in sorted_intervals[1:]:
            last = merged[-1]

            # Проверяем смежность или пересечение
            if current.left <= last.right:
                # Объединяем
                merged[-1] = Interval(
                    last.left,
                    max(last.right, current.right),
                    last.left_closed,
                    current.right_closed if current.right > last.right else last.right_closed
                )
            else:
                merged.append(current)

        return merged

    def _format_result(self, intervals: List[Interval], length: float) -> str:
        """Форматирует результат в читаемую строку"""
        if not intervals:
            return f"{self.target_set} = ∅"
        self.parts_max = -1
        self.parts_min = 1000000
        parts = []
        for interval in intervals:
            if math.isinf(interval.left) and math.isinf(interval.right):
                parts.append("(-∞, +∞)")
            elif math.isinf(interval.left):
                parts.append(f"(-∞, {interval.right}]")
            elif math.isinf(interval.right):
                parts.append(f"[{interval.left}, +∞)")
            else:
                parts.append(f"[{interval.left}, {interval.right}]")
                l = int(interval.left)
                r = int(interval.right)
                self.parts_max = max(r - l, self.parts_max) if self.parts_max != '?' else r - l
                self.parts_min = min(r - l, self.parts_min) if self.parts_max != '?' else r - l

        result = f"{self.target_set} = " + " ∪ ".join(parts) + f"  max: {self.parts_max} min: {self.parts_min}"

        if not any(math.isinf(i.left) or math.isinf(i.right) for i in intervals):
            result += f", суммарная длина = {length}"
        else:
            result += " (бесконечное решение)"

        return result

    def solve(self) -> SolverResult:
        """Главный метод решения"""
        constrained = self._analyze_intervals()
        return self._optimize(constrained)

    def get_analysis(self) -> List[ConstrainedInterval]:
        """Возвращает анализ интервалов (для отладки и визуализации)"""
        return self._analyze_intervals()


# ===================== Тестирование =====================

if __name__ == "__main__":
    # Тестовый пример из условия
    formula = "((x ∈ P) ≡ (x ∈ Q)) → ¬(x ∈ A)"
    known_sets = {
        'P': (5, 30),
        'Q': (14, 23)
    }

    print("=" * 60)
    print("Тест 1: Максимизация A при истинной формуле")
    print("=" * 60)
    print(f"Формула: {formula}")
    print(f"P = [5, 30], Q = [14, 23]")
    print()

    solver = LogicSolver(
        formula=formula,
        known_sets=known_sets,
        target_set='A',
        maximize=True,
        formula_true=True
    )

    print("Анализ интервалов:")
    for ci in solver.get_analysis():
        print(f"  {ci}")

    print()
    result = solver.solve()
    print(f"Результат: {result.message}")
    print()

    # Тест 2: Минимизация
    print("=" * 60)
    print("Тест 2: Минимизация A при истинной формуле")
    print("=" * 60)

    solver2 = LogicSolver(
        formula=formula,
        known_sets=known_sets,
        target_set='A',
        maximize=False,
        formula_true=True
    )

    result2 = solver2.solve()
    print(f"Результат: {result2.message}")