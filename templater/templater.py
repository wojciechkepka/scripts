from typing import Optional, Any, List, Dict
from enum import Enum


class TextReader(object):
    def __init__(self, text: str):
        self.text = text
        self.length = len(text)
        self.idx = 0

    def current(self) -> Optional[str]:
        if self.text:
            return self.text[self.idx]
        else:
            return None

    def peek(self) -> Optional[str]:
        if self.idx + 1 >= self.length:
            return None
        else:
            return self.text[self.idx + 1]

    def next(self) -> Optional[str]:
        if self.peek() != None:
            self.idx += 1
            return self.current()
        else:
            return None

    def is_last(self) -> bool:
        return self.idx == (self.length - 1)


class TokenType(Enum):
    NORMAL = 1
    VARIABLE = 2


class Token(object):
    def __init__(self, text: str, type_: TokenType, variable=""):
        self.text = text
        self.type = type_

        if type_ == TokenType.VARIABLE:
            self.variable = variable

    def __eq__(self, other):
        if isinstance(other, Token):
            return self.text == other.text and self.type == other.type
        else:
            return False


class Lexer(object):
    def __init__(self, text: str):
        self.reader = TextReader(text)

    def parse_variable_token(self) -> Optional[Any]:
        text = self.reader.current()  # add first '{'
        variable = ""
        if self.reader.current() != "{" or self.reader.peek() != "{":
            return Token(text, TokenType.NORMAL)

        text += self.reader.next()  # add second '{'

        while self.reader.peek() != "}":
            _next = self.reader.next()
            if _next == None:
                return Token(text, TokenType.NORMAL)

            if _next.isalpha() or _next == "." or _next == "_":
                text += _next
                variable += _next
            elif _next == " ":
                text += _next
            else:
                return Token(text, TokenType.NORMAL)

        text += self.reader.next()  # add first '}'
        if self.reader.peek() != "}":
            return Token(text, TokenType.NORMAL)
        text += self.reader.next()  # add second '}'
        self.reader.next()

        return Token(text, TokenType.VARIABLE, variable=variable)

    def lex(self) -> List[Token]:
        tokens = []

        text = ""
        while True:
            if self.reader.current() == "{" and self.reader.peek() == "{":
                token = self.parse_variable_token()
                if token.type == TokenType.NORMAL:
                    text += token.text
                    self.reader.next()
                else:
                    if text:
                        tokens.append(Token(text, TokenType.NORMAL))
                        text = ""
                    tokens.append(token)

                # early exit because "}" is already parsed and if it breaks out
                # it will get added as an extra token
                if self.reader.is_last():
                    break
            elif self.reader.current() == None:
                break
            else:
                text += self.reader.current()
                self.reader.next()

            if self.reader.is_last():
                if self.reader.current() != None:
                    text += self.reader.current()
                break

        if text:
            tokens.append(Token(text, TokenType.NORMAL))

        return tokens


class Templater(object):
    def __init__(self, text: str, variables: Dict[str, Any]):
        self.tokens = Lexer(text).lex()
        self.variables = variables

    def render(self) -> str:
        s = ""
        for token in self.tokens:
            if token.type == TokenType.NORMAL:
                s += token.text
            elif token.type == TokenType.VARIABLE:
                if token.variable in self.variables.keys():
                    s += str(self.variables[token.variable])
                else:
                    s += f"`MISSING VARIABLE {token.variable}`"

        return s
