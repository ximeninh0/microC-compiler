from __future__ import annotations

import dataclasses
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))

from Lexer import Lexer, LexerError, Token, TokenKind  # noqa: E402


EXPECTED_CODES = {
    "EOF": -1,
    "IDENTIFIER": 1,
    "INT_LITERAL": 2,
    "STRING_LITERAL": 3,
    "KW_INT": 10,
    "KW_BOOL": 11,
    "KW_VOID": 12,
    "KW_TRUE": 13,
    "KW_FALSE": 14,
    "KW_IF": 15,
    "KW_ELSE": 16,
    "KW_WHILE": 17,
    "KW_RETURN": 18,
    "KW_PRINT": 19,
    "PLUS": 20,
    "MINUS": 21,
    "STAR": 22,
    "SLASH": 23,
    "PERCENT": 24,
    "LESS": 25,
    "LESS_EQUAL": 26,
    "GREATER": 27,
    "GREATER_EQUAL": 28,
    "EQUAL_EQUAL": 29,
    "NOT_EQUAL": 30,
    "LOGICAL_AND": 31,
    "LOGICAL_OR": 32,
    "LOGICAL_NOT": 33,
    "ASSIGN": 34,
    "LEFT_PAREN": 40,
    "RIGHT_PAREN": 41,
    "LEFT_BRACE": 42,
    "RIGHT_BRACE": 43,
    "COMMA": 44,
    "SEMICOLON": 45,
}


def test_contrato_publico_do_enum():
    assert {kind.name: kind.value for kind in TokenKind} == EXPECTED_CODES


def test_programa_integrado():
    tokens = Lexer('int main() { bool ok = true; print("ok\\n", 42); return 0; }').scan()
    assert [token.kind.name for token in tokens] == [
        "KW_INT", "IDENTIFIER", "LEFT_PAREN", "RIGHT_PAREN", "LEFT_BRACE",
        "KW_BOOL", "IDENTIFIER", "ASSIGN", "KW_TRUE", "SEMICOLON",
        "KW_PRINT", "LEFT_PAREN", "STRING_LITERAL", "COMMA", "INT_LITERAL",
        "RIGHT_PAREN", "SEMICOLON", "KW_RETURN", "INT_LITERAL", "SEMICOLON",
        "RIGHT_BRACE", "EOF",
    ]


def test_palavras_reservadas_limites_e_maiusculas():
    tokens = Lexer(
        "int bool void true false if else while return print intx true1 While _int"
    ).scan()
    assert [token.kind.name for token in tokens] == [
        "KW_INT", "KW_BOOL", "KW_VOID", "KW_TRUE", "KW_FALSE", "KW_IF",
        "KW_ELSE", "KW_WHILE", "KW_RETURN", "KW_PRINT", "IDENTIFIER",
        "IDENTIFIER", "IDENTIFIER", "IDENTIFIER", "EOF",
    ]
    assert tokens[3].value is True
    assert tokens[4].value is False
    assert [token.value for token in tokens[10:14]] == ["intx", "true1", "While", "_int"]


def test_identificadores_inteiros_e_menos_sao_tokens_distintos():
    tokens = Lexer("_x x2 0042 -10 1abc 0xff").scan()
    assert [(token.kind.name, token.lexeme, token.value) for token in tokens] == [
        ("IDENTIFIER", "_x", "_x"),
        ("IDENTIFIER", "x2", "x2"),
        ("INT_LITERAL", "0042", 42),
        ("MINUS", "-", None),
        ("INT_LITERAL", "10", 10),
        ("INT_LITERAL", "1", 1),
        ("IDENTIFIER", "abc", "abc"),
        ("INT_LITERAL", "0", 0),
        ("IDENTIFIER", "xff", "xff"),
        ("EOF", "", None),
    ]


def test_operadores_usam_o_maior_casamento():
    tokens = Lexer("a<=b!=c&&true||!false;x=y+2*3/4%5>=0").scan()
    assert [token.kind.name for token in tokens] == [
        "IDENTIFIER", "LESS_EQUAL", "IDENTIFIER", "NOT_EQUAL", "IDENTIFIER",
        "LOGICAL_AND", "KW_TRUE", "LOGICAL_OR", "LOGICAL_NOT", "KW_FALSE",
        "SEMICOLON", "IDENTIFIER", "ASSIGN", "IDENTIFIER", "PLUS",
        "INT_LITERAL", "STAR", "INT_LITERAL", "SLASH", "INT_LITERAL",
        "PERCENT", "INT_LITERAL", "GREATER_EQUAL", "INT_LITERAL", "EOF",
    ]


def test_comentarios_e_espacos_atualizam_posicoes():
    tokens = Lexer(" \t// comentario ASCII\n/*x\n y*/bool x").scan()
    assert [(token.kind, token.line, token.column) for token in tokens] == [
        (TokenKind.KW_BOOL, 3, 5),
        (TokenKind.IDENTIFIER, 3, 10),
        (TokenKind.EOF, 3, 11),
    ]


def test_comentario_de_linha_pode_terminar_no_eof():
    tokens = Lexer("int// fim").scan()
    assert [(token.kind, token.lexeme) for token in tokens] == [
        (TokenKind.KW_INT, "int"),
        (TokenKind.EOF, ""),
    ]


def test_strings_preservam_lexema_e_decodificam_escapes():
    tokens = Lexer(r'"" "a\n\t\"\\b" "// nao e comentario"').scan()
    assert [(token.lexeme, token.value) for token in tokens[:-1]] == [
        ('""', ""),
        (r'"a\n\t\"\\b"', "a\n\t\"\\b"),
        ('"// nao e comentario"', "// nao e comentario"),
    ]


def test_strings_adjacentes_continuam_separadas():
    tokens = Lexer('"resultado "/* separador */"final"').scan()
    assert [(token.kind, token.value) for token in tokens] == [
        (TokenKind.STRING_LITERAL, "resultado "),
        (TokenKind.STRING_LITERAL, "final"),
        (TokenKind.EOF, None),
    ]


@pytest.mark.parametrize(
    ("source", "line", "column"),
    [
        ("@", 1, 1),
        ("&", 1, 1),
        ("|", 1, 1),
        ('"\\q"', 1, 2),
        ('"abc\n', 1, 5),
        ('"abc', 1, 1),
        ("/* sem fim", 1, 1),
        ("é", 1, 1),
    ],
)
def test_erros_lexicos_informam_posicao(source: str, line: int, column: int):
    with pytest.raises(LexerError) as caught:
        Lexer(source).scan()
    assert (caught.value.line, caught.value.column) == (line, column)


@pytest.mark.parametrize(
    ("source", "position"),
    [("", (1, 1)), ("x", (1, 2)), ("x\n", (2, 1)), ("/* ok */", (1, 9))],
)
def test_existe_um_unico_eof_na_posicao_final(source: str, position: tuple[int, int]):
    tokens = Lexer(source).scan()
    assert sum(token.kind is TokenKind.EOF for token in tokens) == 1
    assert tokens[-1].kind is TokenKind.EOF
    assert (tokens[-1].line, tokens[-1].column) == position


def test_token_e_imutavel_e_tem_saida_canonica():
    token = Token(TokenKind.STRING_LITERAL, '"a\\n"', "a\n", 2, 3)
    assert str(token) == '<3, STRING_LITERAL, \'"a\\\\n"\', \'a\\n\', 2, 3>'
    with pytest.raises(dataclasses.FrozenInstanceError):
        token.line = 9  # type: ignore[misc]


def test_runner_imprime_exatamente_um_token_por_linha(tmp_path: Path):
    source = tmp_path / "simples.microc"
    source.write_text("int x = 42;\n", encoding="ascii")
    runner = Path(__file__).parents[1] / "runner.py"
    result = subprocess.run(
        [sys.executable, str(runner), str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stderr == ""
    assert result.stdout.splitlines() == [
        "<10, KW_INT, 'int', None, 1, 1>",
        "<1, IDENTIFIER, 'x', 'x', 1, 5>",
        "<34, ASSIGN, '=', None, 1, 7>",
        "<2, INT_LITERAL, '42', 42, 1, 9>",
        "<45, SEMICOLON, ';', None, 1, 11>",
        "<-1, EOF, '', None, 2, 1>",
    ]


def test_runner_nao_imprime_prefixo_quando_ha_erro(tmp_path: Path):
    source = tmp_path / "erro.microc"
    source.write_text("int x; @", encoding="ascii")
    runner = Path(__file__).parents[1] / "runner.py"
    result = subprocess.run(
        [sys.executable, str(runner), str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout == ""
    assert "erro léxico em 1:8" in result.stderr
