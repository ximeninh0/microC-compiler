from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Iterator


class TokenKind(enum.Enum):
    """Classe já implementada: nomes e números não devem ser alterados."""

    EOF = -1

    IDENTIFIER = 1
    INT_LITERAL = 2
    STRING_LITERAL = 3

    KW_INT = 10
    KW_BOOL = 11
    KW_VOID = 12
    KW_TRUE = 13
    KW_FALSE = 14
    KW_IF = 15
    KW_ELSE = 16
    KW_WHILE = 17
    KW_RETURN = 18
    KW_PRINT = 19

    PLUS = 20
    MINUS = 21
    STAR = 22
    SLASH = 23
    PERCENT = 24
    LESS = 25
    LESS_EQUAL = 26
    GREATER = 27
    GREATER_EQUAL = 28
    EQUAL_EQUAL = 29
    NOT_EQUAL = 30
    LOGICAL_AND = 31
    LOGICAL_OR = 32
    LOGICAL_NOT = 33
    ASSIGN = 34

    LEFT_PAREN = 40
    RIGHT_PAREN = 41
    LEFT_BRACE = 42
    RIGHT_BRACE = 43
    COMMA = 44
    SEMICOLON = 45


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    lexeme: str
    value: int | str | bool | None
    line: int
    column: int

    def __str__(self) -> str:
        return (
            f"<{self.kind.value}, {self.kind.name}, {self.lexeme!r}, "
            f"{self.value!r}, {self.line}, {self.column}>"
        )


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        return f"erro léxico em {self.line}:{self.column}: {self.message}"


class State(enum.Enum):
    START = 0
    IN_IDENTIFIER = 1
    IN_INT = 2
    IN_STRING = 3
    IN_STRING_ESCAPE = 4
    IN_STRING_END = 5
    
    IN_ASSIGN = 6          # =
    IN_EQUAL_EQUAL = 7     # ==
    IN_EXCLAMATION = 8     # !
    IN_NOT_EQUAL = 9       # !=
    IN_LESS = 10           # <
    IN_LESS_EQUAL = 11     # <=
    IN_GREATER = 12        # >
    IN_GREATER_EQUAL = 13  # >=
    IN_AMPERSAND = 14      # &
    IN_LOGICAL_AND = 15    # &&
    IN_PIPE = 16           # |
    IN_LOGICAL_OR = 17     # ||
    
    IN_PLUS = 18
    IN_MINUS = 19
    IN_STAR = 20
    IN_PERCENT = 21
    IN_LEFT_PAREN = 22
    IN_RIGHT_PAREN = 23
    IN_LEFT_BRACE = 24
    IN_RIGHT_BRACE = 25
    IN_COMMA = 26
    IN_SEMICOLON = 27

    ERROR = -1
    


class CharClass(enum.Enum):
    LETTER = 0
    DIGIT = 1
    EQUAL = 2
    LESS = 3
    GREATER = 4
    NOT = 5
    SPACE = 6
    PLUS = 7
    MINUS = 8
    STAR = 9
    SLASH = 10
    QUOTE = 11
    OPEN_PAREN = 12
    OPEN_BRACE = 13
    CLOSE_PAREN = 14
    CLOSE_BRACE = 15
    INV_SLASH = 16
    AMPERSAND = 17
    PIPE = 18
    PERCENT = 19

CHAR_CLASS = {
    "=": CharClass.EQUAL,
    "<": CharClass.LESS,
    ">": CharClass.GREATER,
    "!": CharClass.NOT,
    "+": CharClass.PLUS,
    "-": CharClass.MINUS,
    "*": CharClass.STAR,
    "/": CharClass.SLASH,
    "%": CharClass.PERCENT,
    '"': CharClass.QUOTE,
    "(": CharClass.OPEN_PAREN,
    "{": CharClass.OPEN_BRACE,
    ")": CharClass.CLOSE_PAREN,
    "}": CharClass.CLOSE_BRACE,
    " ": CharClass.SPACE,
    "\\":CharClass.INV_SLASH,
    "&": CharClass.AMPERSAND,
    "|": CharClass.PIPE,
    ",": CharClass.COMMA,
    ";": CharClass.SEMICOLON
}

KEYWORDS: dict[str, TokenKind] = {
    "int": TokenKind.KW_INT,
    "bool": TokenKind.KW_BOOL,
    "void": TokenKind.KW_VOID,
    "true": TokenKind.KW_TRUE,
    "false": TokenKind.KW_FALSE,
    "if": TokenKind.KW_IF,
    "else": TokenKind.KW_ELSE,
    "while": TokenKind.KW_WHILE,
    "return": TokenKind.KW_RETURN,
    "print": TokenKind.KW_PRINT
}

class Lexer:
    """Converte texto-fonte MicroC em uma sequência de tokens."""
    state = None
    last_final = None
    position = 0

    delta: dict[State, dict[CharClass, State]] = {
        State.START: {
            CharClass.LETTER: State.IN_IDENTIFIER,
            CharClass.DIGIT: State.IN_INT,
            CharClass.QUOTE: State.IN_STRING,
            CharClass.EQUAL: State.IN_ASSIGN,
            CharClass.NOT: State.IN_EXCLAMATION,
            CharClass.LESS: State.IN_LESS,
            CharClass.GREATER: State.IN_GREATER,
            CharClass.AMPERSAND: State.IN_AMPERSAND,
            CharClass.PIPE: State.IN_PIPE,
            CharClass.PLUS: State.IN_PLUS,
            CharClass.MINUS: State.IN_MINUS,
            CharClass.STAR: State.IN_STAR,
            CharClass.PERCENT: State.IN_PERCENT,
            CharClass.OPEN_PAREN: State.IN_LEFT_PAREN,
            CharClass.CLOSE_PAREN: State.IN_RIGHT_PAREN,
            CharClass.OPEN_BRACE: State.IN_LEFT_BRACE,
            CharClass.CLOSE_BRACE: State.IN_RIGHT_BRACE,
            CharClass.COMMA: State.IN_COMMA,
            CharClass.SEMICOLON: State.IN_SEMICOLON
        },

        # Identificadores e Inteiros (loops de continuação)
        State.IN_IDENTIFIER: {
            CharClass.LETTER: State.IN_IDENTIFIER,
            CharClass.DIGIT: State.IN_IDENTIFIER
        },
        State.IN_INT: {
            CharClass.DIGIT: State.IN_INT
        },

        # Strings e Escapes
        State.IN_STRING: {
            CharClass.LETTER: State.IN_STRING,
            CharClass.DIGIT: State.IN_STRING,
            CharClass.EQUAL: State.IN_STRING,
            CharClass.LESS: State.IN_STRING,
            CharClass.GREATER: State.IN_STRING,
            CharClass.NOT: State.IN_STRING,
            CharClass.SPACE: State.IN_STRING,
            CharClass.PLUS: State.IN_STRING,
            CharClass.MINUS: State.IN_STRING,
            CharClass.STAR: State.IN_STRING,
            CharClass.SLASH: State.IN_STRING,
            CharClass.PERCENT: State.IN_STRING,
            CharClass.OPEN_PAREN: State.IN_STRING,
            CharClass.CLOSE_PAREN: State.IN_STRING,
            CharClass.OPEN_BRACE: State.IN_STRING,
            CharClass.CLOSE_BRACE: State.IN_STRING,
            CharClass.AMPERSAND: State.IN_STRING,
            CharClass.PIPE: State.IN_STRING,
            CharClass.COMMA: State.IN_STRING,
            CharClass.SEMICOLON: State.IN_STRING,
            CharClass.INV_SLASH: State.IN_STRING_ESCAPE,  # Transita ao ler \
            CharClass.QUOTE: State.IN_STRING_END        # Transita ao ler o " final
        },
        State.IN_STRING_ESCAPE: {
            # Qualquer caractere de escape válido devolve o estado para IN_STRING
            CharClass.LETTER: State.IN_STRING,
            CharClass.INV_SLASH: State.IN_STRING,
            CharClass.QUOTE: State.IN_STRING
        },

        # Operadores simples que viram compostos se encontrarem o segundo caractere
        State.IN_ASSIGN: {
            CharClass.EQUAL: State.IN_EQUAL_EQUAL       # = seguido de = vira ==
        },
        State.IN_EXCLAMATION: {
            CharClass.EQUAL: State.IN_NOT_EQUAL         # ! seguido de = vira !=
        },
        State.IN_LESS: {
            CharClass.EQUAL: State.IN_LESS_EQUAL        # < seguido de = vira <=
        },
        State.IN_GREATER: {
            CharClass.EQUAL: State.IN_GREATER_EQUAL     # > seguido de = vira >=
        },
        State.IN_AMPERSAND: {
            CharClass.AMPERSAND: State.IN_LOGICAL_AND   # & seguido de & vira &&
        },
        State.IN_PIPE: {
            CharClass.PIPE: State.IN_LOGICAL_OR         # | seguido de | vira ||
        },
    }

    final_states = {
        State.IN_IDENTIFIER, State.IN_INT, State.IN_STRING_END,
        State.IN_ASSIGN, State.IN_EQUAL_EQUAL, State.IN_EXCLAMATION,
        State.IN_NOT_EQUAL, State.IN_LESS, State.IN_LESS_EQUAL,
        State.IN_GREATER, State.IN_GREATER_EQUAL, State.IN_LOGICAL_AND,
        State.IN_LOGICAL_OR, State.IN_PLUS, State.IN_MINUS, State.IN_STAR,
        State.IN_PERCENT, State.IN_LEFT_PAREN, State.IN_RIGHT_PAREN,
        State.IN_LEFT_BRACE, State.IN_RIGHT_BRACE, State.IN_COMMA,
        State.IN_SEMICOLON
    }

    def get_next_state(self, current_state: State, char_class: CharClass) -> State:
        return self.delta.get(current_state, {}).get(char_class, State.ERROR)
    
    def __init__(self, source: str):
        self.source = source
        self.state = State.START
        self.position = 0

    

    def tokens(self) -> Iterator[Token]:
        """Produza todos os tokens significativos e um único EOF ao final."""
        while self.position < len(self.source):
            # if whitespace or comment skip
            # ?

            start_position = self.position
            start_line = self.line
            start_column = self.column

            state = State.START
            last_final = None

            while self.position < len(self.source):
                char = self.source[self.position]
                char_class = self.classify(char)
                next_state = self.get_next_state(self.state, char_class)

                if next_state == State.ERROR:
                    break

                self.state = next_state
                self.position += 1

                if self.state in self.final_states:
                    last_final = (state, self.position, self.line, self.column)

            if last_final is not None:
                # volta para o ultimo estado de aceitação
                rollback_to(last_final.input_position)
                return TokenKind[last_final.state]
            else:
                raise LexerError(f"caractere inesperado: {self.source[self.position]!r}", self.line, self.column)
            
        yield Token(TokenKind.EOF, "", None, self.line, self.column) # mantém este método como gerador durante o desenvolvimento

    def scan(self) -> list[Token]:
        return list(self.tokens())

    def classify(char: str) -> CharClass:
        if char.isalpha(): return CharClass.LETTER
        if char.isdigit(): return CharClass.DIGIT
        return CHAR_CLASS[char]