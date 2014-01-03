from Lexer import Lexer
from Parser import Parser


class Template(object):
    def __init__(self, source):
        lexer = Lexer()
        parser = Parser(lexer, source)
        self.root = parser.parse()

    def render(self, **kwargs):
        return self.root.render(kwargs)