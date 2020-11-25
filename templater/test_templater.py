#!/usr/bin/env python

import unittest
from templater import Lexer, TokenType, Token, Templater


class TestLexer(unittest.TestCase):
    def test_empty_string(self):
        inp = """"""
        got = Lexer(inp).lex()
        want = []

        self.assertEqual(got, want)

    def test_parses_unfinished_token(self):
        inp = """{{  """
        got = Lexer(inp).lex()
        want = [Token("{{  ", TokenType.NORMAL)]

        self.assertEqual(got, want)

    def test_doesnt_parse_comma_in_variable(self):
        inp = """{{  xx,y }}"""
        got = Lexer(inp).lex()
        want = [Token("{{  xx,y }}", TokenType.NORMAL)]

        self.assertEqual(got, want)

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

    def test_parses_comma_separated_variable(self):
        inp = """{{ category.subcategory.variable }}"""
        got = Lexer(inp).lex()
        want = [
            Token("{{ category.subcategory.variable }}", TokenType.VARIABLE, variable="category.subcategory.variable")
        ]

        self.assertEqual(got, want)

    def test_parses_underscore_separated_variable(self):
        inp = """{{ some_long_name }}"""
        got = Lexer(inp).lex()
        want = [Token("{{ some_long_name }}", TokenType.VARIABLE, variable="some_long_name")]

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

    def test_doesnt_parse_variable_with_whitespace(self):
        inp = """{{ some variable }}"""
        got = Lexer(inp).lex()
        want = [
            Token("{{ some variable }}", TokenType.NORMAL),
        ]

        self.assertEqual(got, want)

    def test_parses_variable_with_multiple_spaces(self):
        inp = """{{  some.long.variable      }}"""
        got = Lexer(inp).lex()
        want = [
            Token("{{  some.long.variable      }}", TokenType.VARIABLE, variable="some.long.variable"),
        ]

        self.assertEqual(got, want)

    def test_parses_variable_with_digits(self):
        inp = """{{ gtk2.theme.name1 }}"""

        got = Lexer(inp).lex()
        want = [
            Token("{{ gtk2.theme.name1 }}", TokenType.VARIABLE, variable="gtk2.theme.name1"),
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
