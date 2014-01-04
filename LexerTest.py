import unittest
from Lexer import Lexer
from Constants import *


class LexerTest(unittest.TestCase):
    def setUp(self):
        self.lexer = Lexer()

    def assert_tokens_are_correct(self, tokens, source):
        self.assertListEqual(tokens, self.get_tokens(source))

    def get_tokens(self, source):
        return [token.items() for token in self.lexer.tokenize(source)]

    def test_empty_text_return_no_tokens(self):
        self.assert_tokens_are_correct([], '')

    def test_can_parse_raw_text(self):
        source = 'raw_text'
        tokens = [(TOKEN_DATA, source)]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_start_block(self):
        source = '{%'
        tokens = [(TOKEN_BLOCK_START, source)]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_end_block(self):
        source = '{{'
        tokens = [(TOKEN_VARIABLE_START, source)]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_entire_block(self):
        source = '{% bla bla %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'bla'),
            (TOKEN_NAME, 'bla'),
            (TOKEN_BLOCK_END, '%}')
        ]

        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_entire_variable(self):
        source = '{{ bla }}'
        tokens = [
            (TOKEN_VARIABLE_START, '{{'),
            (TOKEN_NAME, 'bla'),
            (TOKEN_VARIABLE_END, '}}')
        ]

        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_start_block_and_end_block(self):
        source = '{% bla %}hello{% end %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'bla'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_DATA, 'hello'),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'end'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_nested_block(self):
        source = '{%foo%}{%bar%}  {{hello}} {%end%}{%end%}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'foo'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'bar'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_DATA, '  '),
            (TOKEN_VARIABLE_START, '{{'),
            (TOKEN_NAME, 'hello'),
            (TOKEN_VARIABLE_END, '}}'),
            (TOKEN_DATA, ' '),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'end'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'end'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def can_parse_consecutive_blocks(self):
        source = '{%foo%}{%end%}{{baz}}{%bar%}{%end%}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'foo'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'end'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_VARIABLE_START, '{{'),
            (TOKEN_NAME, 'baz'),
            (TOKEN_VARIABLE_END, '}}'),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'bar'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'end'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_integers(self):
        source = "{%2%}"
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_INTEGER, 2),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_floats(self):
        source = '{%1.23%}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_FLOAT, 1.23),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_string(self):
        source = '{% "hello" %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_STRING, 'hello'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_lists(self):
        source = '{% [1,2.2,"hello"] %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_LBRACKET, '['),
            (TOKEN_INTEGER, 1),
            (TOKEN_COMMA, ','),
            (TOKEN_FLOAT, 2.2),
            (TOKEN_COMMA, ','),
            (TOKEN_STRING, 'hello'),
            (TOKEN_RBRACKET, ']'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_sets(self):
        source = '{% {1,2.2,"hello"} %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_LBRACE, '{'),
            (TOKEN_INTEGER, 1),
            (TOKEN_COMMA, ','),
            (TOKEN_FLOAT, 2.2),
            (TOKEN_COMMA, ','),
            (TOKEN_STRING, 'hello'),
            (TOKEN_RBRACE, '}'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_tuples(self):
        source = '{% (1,2.2,"hello") %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_LPAREN, '('),
            (TOKEN_INTEGER, 1),
            (TOKEN_COMMA, ','),
            (TOKEN_FLOAT, 2.2),
            (TOKEN_COMMA, ','),
            (TOKEN_STRING, 'hello'),
            (TOKEN_RPAREN, ')'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_dictionaries(self):
        source = '{% {"a":3, "b": "hello"} %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_LBRACE, '{'),
            (TOKEN_STRING, 'a'),
            (TOKEN_COLON, ":"),
            (TOKEN_INTEGER, 3),
            (TOKEN_COMMA, ','),
            (TOKEN_STRING, 'b'),
            (TOKEN_COLON, ':'),
            (TOKEN_STRING, 'hello'),
            (TOKEN_RBRACE, '}'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_call_function(self):
        source = '{% todo.items() %}{%end%}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'todo'),
            (TOKEN_DOT, '.'),
            (TOKEN_NAME, 'items'),
            (TOKEN_LPAREN, '('),
            (TOKEN_RPAREN, ')'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'end'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_do_assignements(self):
        source = '{%a=3%}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'a'),
            (TOKEN_ASSIGN, '='),
            (TOKEN_INTEGER, 3),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_operators_work(self):
        source = '{% 2 + 3 - 4 * 5 / 6 // 7 % 8 ** -9 %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_INTEGER, 2),
            (TOKEN_ADD, '+'),
            (TOKEN_INTEGER, 3),
            (TOKEN_SUB, '-'),
            (TOKEN_INTEGER, 4),
            (TOKEN_MUL, '*'),
            (TOKEN_INTEGER, 5),
            (TOKEN_DIV, '/'),
            (TOKEN_INTEGER, 6),
            (TOKEN_FLOORDIV, '//'),
            (TOKEN_INTEGER, 7),
            (TOKEN_MOD, '%'),
            (TOKEN_INTEGER, 8),
            (TOKEN_POW, '**'),
            (TOKEN_SUB, '-'),
            (TOKEN_INTEGER, 9),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_for_loops(self):
        source = '{% for item in items %}{{item}}{% endfor %}'
        tokens = [
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'for'),
            (TOKEN_NAME, 'item'),
            (TOKEN_NAME, 'in'),
            (TOKEN_NAME, 'items'),
            (TOKEN_BLOCK_END, '%}'),
            (TOKEN_VARIABLE_START, '{{'),
            (TOKEN_NAME, 'item'),
            (TOKEN_VARIABLE_END, '}}'),
            (TOKEN_BLOCK_START, '{%'),
            (TOKEN_NAME, 'endfor'),
            (TOKEN_BLOCK_END, '%}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_parse_calls(self):
        source = '{{ list.todo.text() }}'
        tokens = [
            (TOKEN_VARIABLE_START, '{{'),
            (TOKEN_NAME, 'list'),
            (TOKEN_DOT, '.'),
            (TOKEN_NAME, 'todo'),
            (TOKEN_DOT, '.'),
            (TOKEN_NAME, 'text'),
            (TOKEN_LPAREN, '('),
            (TOKEN_RPAREN, ')'),
            (TOKEN_VARIABLE_END, '}}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_process_unicode(self):
        source = '{{ èéáàìíóòúùüïoäë }}'
        tokens = [
            (TOKEN_VARIABLE_START, '{{'),
            (TOKEN_NAME, 'èéáàìíóòúùüïoäë'),
            (TOKEN_VARIABLE_END, '}}')
        ]
        self.assert_tokens_are_correct(tokens, source)

    def test_can_use_look(self):
        source = '{{ foo }}'
        stream = self.lexer.tokenize(source)

        current_token = stream.current
        next_token = stream.look()
        self.assertEqual(current_token, stream.current)

        next(stream)
        self.assertEqual(stream.current, next_token)

        next(stream)
        stream.expect(TOKEN_VARIABLE_END)


class TokenStream(unittest.TestCase):
    def setUp(self):
        self.lexer = Lexer()

    def assert_token_stream_has_not_ended(self, token_stream):
        assert bool(token_stream)
        assert not token_stream.has_ended()

    def assert_token_type_correspond(self, token, token_type):
        self.assertTrue(token.test(token_type))

    def test_can_iterate_over_token_stream(self):
        source = '{{ name }}'
        token_stream = self.lexer.tokenize(source)

        self.assert_token_type_correspond(token_stream.current, TOKEN_VARIABLE_START)
        self.assert_token_stream_has_not_ended(token_stream)
        next(token_stream)
        self.assert_token_type_correspond(token_stream.current, TOKEN_NAME + ':' + 'name')
        self.assert_token_stream_has_not_ended(token_stream)
        next(token_stream)
        self.assert_token_type_correspond(token_stream.current, TOKEN_VARIABLE_END)
        self.assert_token_stream_has_not_ended(token_stream)
        next(token_stream)
        self.assert_token_type_correspond(token_stream.current, TOKEN_EOF)
        assert not bool(token_stream)
        assert token_stream.has_ended()

    def test_token_stream_has_right_types(self):
        token_types = [TOKEN_VARIABLE_START, TOKEN_NAME, TOKEN_VARIABLE_END,
                       TOKEN_DATA, TOKEN_BLOCK_START, TOKEN_NAME, TOKEN_BLOCK_END]
        source = '{{ data }}hello{%foo%}'
        self.assertListEqual(token_types, [token.token_type for token in self.lexer.tokenize(source)])

    def test_stops_iteration_when_stream_ends(self):
        source = 'hello {{name}} {%foo%}{{bar}}baz{%end%}'
        stream = self.lexer.tokenize(source)
        while stream:
            next(stream)
        assert stream.has_ended()
        assert not bool(stream)
        assert not stream


if __name__ == '__main__':
    unittest.main()