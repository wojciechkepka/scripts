#!/usr/bin/env python

import unittest
from templater import Lexer, TokenType, Token, Templater


class TestLexer(unittest.TestCase):
    def test_parses_normal_token(self):
        inp = """some simple text."""
        got = Lexer(inp).lex()
        want = [Token("some simple text.", TokenType.NORMAL)]

        self.assertEqual(got, want)

    def test_parses_variable_token(self):
        inp = """{{ x }}"""
        got = Lexer(inp).lex()
        want = [Token("{{ x }}", TokenType.VARIABLE, variable="x")]

        self.assertEqual(got, want)

    def test_parses_multiple_variables(self):
        inp = """some text {{ x }} {{ y }}"""
        got = Lexer(inp).lex()
        want = [
            Token("some text ", TokenType.NORMAL),
            Token("{{ x }}", TokenType.VARIABLE, variable="x"),
            Token(" ", TokenType.NORMAL),
            Token("{{ y }}", TokenType.VARIABLE, variable="y"),
        ]

        self.assertEqual(got, want)

    def test_parses_variables_different_whitespace(self):
        inp = """some text {{x }} {{ y}} {{z}} some text"""
        got = Lexer(inp).lex()
        want = [
            Token("some text ", TokenType.NORMAL),
            Token("{{x }}", TokenType.VARIABLE, variable="x"),
            Token(" ", TokenType.NORMAL),
            Token("{{ y}}", TokenType.VARIABLE, variable="y"),
            Token(" ", TokenType.NORMAL),
            Token("{{z}}", TokenType.VARIABLE, variable="z"),
            Token(" some text", TokenType.NORMAL),
        ]

        self.assertEqual(got, want)

    def test_doesnt_parse_invalid_variables(self):
        inp = """some text {x{ x }} { y } { {z} } { { a } } {{b}} some text"""
        got = Lexer(inp).lex()
        want = [
            Token("some text {x{ x }} { y } { {z} } { { a } } ", TokenType.NORMAL),
            Token("{{b}}", TokenType.VARIABLE, variable="b"),
            Token(" some text", TokenType.NORMAL),
        ]

        self.assertEqual(got, want)


class TestTemplater(unittest.TestCase):
    def test_replacing(self):
        inp = """# Example config
some.invalid.var1 = {{ x }
some.invalid.var2 = { y }
some.invalid.var3 = {{y } }
some.invalid.var4 = { { x } }
some.working.var1 = {{x}}
some.working.var2 = {{ x }}
some.working.var3 = {{y }}
some.working.var4 = {{ y}}
some.missing.var1 = {{ z }}
"""
        variables = {"x": 123, "y": '"example text"'}
        got = Templater(inp, variables).render()

        want = """# Example config
some.invalid.var1 = {{ x }
some.invalid.var2 = { y }
some.invalid.var3 = {{y } }
some.invalid.var4 = { { x } }
some.working.var1 = 123
some.working.var2 = 123
some.working.var3 = "example text"
some.working.var4 = "example text"
some.missing.var1 = `MISSING VARIABLE z`"""

        self.assertEqual(got, want)


if __name__ == "__main__":
    unittest.main()
