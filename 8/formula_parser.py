"""
Парсер логических формул с поддержкой Unicode и ASCII синтаксиса.
Использует рекурсивный спуск с учётом приоритетов операций.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Union
import re


class TokenType(Enum):
    LPAREN = auto()
    RPAREN = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    IMPLIES = auto()
    EQUIV = auto()
    XOR = auto()
    IN = auto()
    IDENTIFIER = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    position: int


# ===================== AST Nodes =====================

@dataclass
class ASTNode:
    """Базовый класс для узлов AST"""
    pass


@dataclass
class MembershipNode(ASTNode):
    """Узел принадлежности: x ∈ P"""
    var: str
    set_name: str

    def __repr__(self):
        return f"({self.var} ∈ {self.set_name})"


@dataclass
class NotNode(ASTNode):
    """Узел отрицания: ¬A"""
    operand: ASTNode

    def __repr__(self):
        return f"¬{self.operand}"


@dataclass
class BinaryNode(ASTNode):
    """Узел бинарной операции"""
    op: str  # 'AND', 'OR', 'IMPLIES', 'EQUIV', 'XOR'
    left: ASTNode
    right: ASTNode

    def __repr__(self):
        op_symbols = {
            'AND': '∧', 'OR': '∨', 'IMPLIES': '→',
            'EQUIV': '≡', 'XOR': '⊕'
        }
        return f"({self.left} {op_symbols.get(self.op, self.op)} {self.right})"


# ===================== Lexer =====================

class Lexer:
    """Лексический анализатор для логических формул"""

    # Паттерны токенов (порядок важен!)
    TOKEN_PATTERNS = [
        (r'\s+', None),  # Пропускаем пробелы
        (r'\(', TokenType.LPAREN),
        (r'\)', TokenType.RPAREN),
        (r'¬|!|NOT\b', TokenType.NOT),
        (r'∧|&|AND\b', TokenType.AND),
        (r'∨|\|(?!\|)|OR\b', TokenType.OR),
        (r'→|->|IMPLIES\b', TokenType.IMPLIES),
        (r'≡|<->|<=>|==|EQUIV\b', TokenType.EQUIV),
        (r'⊕|\^|XOR\b', TokenType.XOR),
        (r'∈|in\b', TokenType.IN),
        (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
    ]

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.tokens: List[Token] = []
        self._tokenize()

    def _tokenize(self):
        """Разбивает текст на токены"""
        while self.pos < len(self.text):
            match_found = False

            for pattern, token_type in self.TOKEN_PATTERNS:
                regex = re.compile(pattern, re.IGNORECASE)
                match = regex.match(self.text, self.pos)

                if match:
                    value = match.group()
                    if token_type is not None:
                        self.tokens.append(Token(token_type, value, self.pos))
                    self.pos = match.end()
                    match_found = True
                    break

            if not match_found:
                raise SyntaxError(
                    f"Неизвестный символ '{self.text[self.pos]}' на позиции {self.pos}"
                )

        self.tokens.append(Token(TokenType.EOF, '', self.pos))


# ===================== Parser =====================

class Parser:
    """
    Парсер логических формул.

    Приоритет операций (от низшего к высшему):
    1. ≡ (EQUIV) - эквиваленция
    2. → (IMPLIES) - импликация
    3. ⊕ (XOR) - исключающее ИЛИ
    4. ∨ (OR) - дизъюнкция
    5. ∧ (AND) - конъюнкция
    6. ¬ (NOT) - отрицание
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> ASTNode:
        """Главный метод парсинга"""
        result = self._parse_equiv()
        if self.current.type != TokenType.EOF:
            raise SyntaxError(
                f"Неожиданный токен '{self.current.value}' на позиции {self.current.position}"
            )
        return result

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self):
        self.pos += 1

    def _expect(self, token_type: TokenType) -> Token:
        if self.current.type != token_type:
            raise SyntaxError(
                f"Ожидался {token_type.name}, получен {self.current.type.name} "
                f"на позиции {self.current.position}"
            )
        token = self.current
        self._advance()
        return token

    def _parse_equiv(self) -> ASTNode:
        """equiv := implies (EQUIV implies)*"""
        left = self._parse_implies()
        while self.current.type == TokenType.EQUIV:
            self._advance()
            right = self._parse_implies()
            left = BinaryNode('EQUIV', left, right)
        return left

    def _parse_implies(self) -> ASTNode:
        """implies := xor (IMPLIES xor)*"""
        left = self._parse_xor()
        while self.current.type == TokenType.IMPLIES:
            self._advance()
            right = self._parse_xor()
            left = BinaryNode('IMPLIES', left, right)
        return left

    def _parse_xor(self) -> ASTNode:
        """xor := or (XOR or)*"""
        left = self._parse_or()
        while self.current.type == TokenType.XOR:
            self._advance()
            right = self._parse_or()
            left = BinaryNode('XOR', left, right)
        return left

    def _parse_or(self) -> ASTNode:
        """or := and (OR and)*"""
        left = self._parse_and()
        while self.current.type == TokenType.OR:
            self._advance()
            right = self._parse_and()
            left = BinaryNode('OR', left, right)
        return left

    def _parse_and(self) -> ASTNode:
        """and := not (AND not)*"""
        left = self._parse_not()
        while self.current.type == TokenType.AND:
            self._advance()
            right = self._parse_not()
            left = BinaryNode('AND', left, right)
        return left

    def _parse_not(self) -> ASTNode:
        """not := NOT not | atom"""
        if self.current.type == TokenType.NOT:
            self._advance()
            operand = self._parse_not()
            return NotNode(operand)
        return self._parse_atom()

    def _parse_atom(self) -> ASTNode:
        """atom := '(' expr ')' | membership"""
        if self.current.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_equiv()
            self._expect(TokenType.RPAREN)
            return expr
        return self._parse_membership()

    def _parse_membership(self) -> ASTNode:
        """membership := IDENTIFIER IN IDENTIFIER"""
        var_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.IN)
        set_token = self._expect(TokenType.IDENTIFIER)
        return MembershipNode(var_token.value, set_token.value)


# ===================== Public API =====================

def parse_formula(formula: str) -> ASTNode:
    """
    Парсит логическую формулу и возвращает AST.

    Args:
        formula: Строка с формулой, например "((x ∈ P) ≡ (x ∈ Q)) → ¬(x ∈ A)"

    Returns:
        Корневой узел AST

    Raises:
        SyntaxError: При ошибках синтаксиса
    """
    lexer = Lexer(formula)
    parser = Parser(lexer.tokens)
    return parser.parse()


def get_sets_from_ast(node: ASTNode) -> set:
    """Извлекает все имена множеств из AST"""
    if isinstance(node, MembershipNode):
        return {node.set_name}
    elif isinstance(node, NotNode):
        return get_sets_from_ast(node.operand)
    elif isinstance(node, BinaryNode):
        return get_sets_from_ast(node.left) | get_sets_from_ast(node.right)
    return set()


# Тестирование
if __name__ == "__main__":
    test_formulas = [
        "((x ∈ P) ≡ (x ∈ Q)) → ¬(x ∈ A)",
        "(x in P) AND (x in Q) -> (x in A)",
        "!(x ∈ P) | (x ∈ A)",
        "((x ∈ P) XOR (x ∈ Q)) <-> (x ∈ A)",
    ]

    for formula in test_formulas:
        print(f"\nФормула: {formula}")
        try:
            ast = parse_formula(formula)
            print(f"AST: {ast}")
            print(f"Множества: {get_sets_from_ast(ast)}")
        except SyntaxError as e:
            print(f"Ошибка: {e}")