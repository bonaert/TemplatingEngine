from collections import deque
import re
from Exception import TemplateSyntaxException
from Constants import *

ROOT = 'root'

# bind operators to token types
operators = {
    '+': TOKEN_ADD,
    '-': TOKEN_SUB,
    '/': TOKEN_DIV,
    '//': TOKEN_FLOORDIV,
    '*': TOKEN_MUL,
    '%': TOKEN_MOD,
    '**': TOKEN_POW,
    '~': TOKEN_TILDE,
    '[': TOKEN_LBRACKET,
    ']': TOKEN_RBRACKET,
    '(': TOKEN_LPAREN,
    ')': TOKEN_RPAREN,
    '{': TOKEN_LBRACE,
    '}': TOKEN_RBRACE,
    '==': TOKEN_EQ,
    '!=': TOKEN_NE,
    '>': TOKEN_GT,
    '>=': TOKEN_GTEQ,
    '<': TOKEN_LT,
    '<=': TOKEN_LTEQ,
    '=': TOKEN_ASSIGN,
    '.': TOKEN_DOT,
    ':': TOKEN_COLON,
    '|': TOKEN_PIPE,
    ',': TOKEN_COMMA,
    ';': TOKEN_SEMICOLON
}

# static regular expressions
newline_re = re.compile(r'(\r\n|\r|\n)')
whitespace_re = re.compile(r'\s+', re.U)
float_re = re.compile(r'(?<!\.)\d+\.\d+')
integer_re = re.compile(r'\d+')
name_re = re.compile(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b')
string_re = re.compile(r"('([^'\\]*(?:\\.[^'\\]*)*)'"
                       r'|"([^"\\]*(?:\\.[^"\\]*)*)")', re.S)
operator_re = re.compile('(%s)' % '|'.join(re.escape(x) for x in
                                           sorted(operators, key=lambda x: -len(x))))


class Rule():
    def __init__(self, pattern, tokens_type, new_state):
        self._pattern = pattern
        self._tokens_type = tokens_type
        self._new_state = new_state
        self._regex = re.compile(pattern)

    def match(self, text):
        return self._regex.match(text)

    def items(self):
        return self._regex, self._tokens_type, self._new_state


class Token():
    def __init__(self, token_type, value):
        self.token_type = token_type
        self.value = value

    def test(self, expr):
        if self.token_type == expr:
            return True
        elif ':' in expr:
            return expr.split(':') == [self.token_type, self.value]
        else:
            return False

    def items(self):
        return (self.token_type, self.value)

    def test_any(self, *iterable):
        return any(self.test(expr) for expr in iterable)

    def __repr__(self):
        return "Token(type: %s, value: %s)" % (self.token_type, self.value)


class TokenStreamIterator(object):
    def __init__(self, token_stream):
        self.stream = token_stream

    def __iter__(self):
        return self

    def __next__(self):
        token = self.stream.current
        if token.token_type == TOKEN_EOF:
            self.stream.close()
            raise StopIteration()
        next(self.stream)
        return token


class TokenStream():
    def __init__(self, generator):
        self._iter = iter(generator)
        self.current = Token(TOKEN_INITIAL, '')
        # Used for look()
        self._pushed = deque()
        next(self)

    def __iter__(self):
        return TokenStreamIterator(self)

    def __bool__(self):
        return self.current.token_type is not TOKEN_EOF

    def has_ended(self):
        return self.current.token_type is TOKEN_EOF

    def push(self, token):
        self._pushed.append(token)

    def look(self):
        token = next(self)
        new_token = self.current
        self.push(new_token)
        self.current = token
        return new_token

    def expect(self, expr):
        if not self.current.test(expr):
            if self.current.token_type == TOKEN_EOF:
                raise TemplateSyntaxException('Reached unexpected end of file')
            else:
                raise TemplateSyntaxException('Expected %s but got %s' % (expr, self.current))
        try:
            return self.current
        finally:
            next(self)

    def skip(self, n=1):
        for _ in range(n):
            next(self)

    def next_if(self, expr):
        if self.current.test(expr):
            return next(self)

    def skip_if(self, expr):
        return self.next_if(expr) is not None

    def __next__(self):
        old = self.current
        if self._pushed:
            self.current = self._pushed.popleft()
        elif self.current.token_type is not TOKEN_EOF:
            try:
                self.current = next(self._iter)
            except StopIteration:
                self.close()
        return old

    def close(self):
        self.current = Token(TOKEN_EOF, '')
        self._iter = None


class Lexer():
    def __init__(self):
        self.tag_rules = [
            Rule(whitespace_re, TOKEN_WHITESPACE, None),
            Rule(float_re, TOKEN_FLOAT, None),
            Rule(integer_re, TOKEN_INTEGER, None),
            Rule(name_re, TOKEN_NAME, None),
            Rule(string_re, TOKEN_STRING, None),
            Rule(operator_re, TOKEN_OPERATOR, None)
        ]
        self.rules = self.compile_rules()
        self.line_number = 0
        self.position = 0
        self.current_match_result = None
        self.current_regex = None
        self.node_stack = []
        self.current_rules = None

    def compile_rules(self):
        return {ROOT: self.compile_root_rules(),
                TOKEN_BLOCK_START: self.compile_block_start_rules(),
                TOKEN_VARIABLE_START: self.compile_variable_start_rules()}

    def compile_root_rules(self):
        return [self.compile_block_rule(),
                self.compile_data_rule()]

    def compile_block_start_rules(self):
        pattern = BLOCK_END_STRING
        return [Rule(pattern, TOKEN_BLOCK_END, '#pop')] + self.tag_rules

    def compile_variable_start_rules(self):
        pattern = VARIABLE_END_STRING
        return [Rule(pattern, TOKEN_VARIABLE_END, '#pop')] + self.tag_rules

    def compile_block_rule(self):
        rules = [
            (len(BLOCK_START_STRING), 'block', BLOCK_START_STRING),
            (len(VARIABLE_START_STRING), 'variable', VARIABLE_START_STRING)
        ]

        # sorts rule by length => raw text will be last option (bit of a hack)
        rules = (x[1:] for x in sorted(rules, reverse=True))
        regexes = self.build_regex_patterns(rules)
        final_pattern = '(.*?)(?:%s)' % '|'.join(regexes)
        return Rule(final_pattern, (TOKEN_DATA, '#bygroup'), '#bygroup')

    def compile_data_rule(self):
        return Rule('.+', TOKEN_DATA, None)

    def build_regex_pattern(self, group_name, rule):
        return r'(?P<%s_start>%s)' % (group_name, rule)

    def build_regex_patterns(self, rules):
        return (self.build_regex_pattern(group, rule) for group, rule in rules)

    def tokenize(self, source):
        stream = self.tokenize_source(source)
        tokens = self.make_tokens(stream)
        return TokenStream(tokens)

    def make_tokens(self, stream):
        for token_type, value in stream:
            if token_type == TOKEN_WHITESPACE:
                continue
            elif token_type == TOKEN_INTEGER:
                value = int(value)
            elif token_type == TOKEN_FLOAT:
                value = float(value)
            elif token_type == TOKEN_NAME:
                value = str(value)
            elif token_type == TOKEN_STRING:
                value = str(value[1:-1])
            elif token_type == TOKEN_OPERATOR:
                token_type = operators[value]
            yield Token(token_type, value)

    def tokenize_source(self, source):
        source_length = len(source)
        self.node_stack = ['root']
        self.current_rules = self.rules[self.node_stack[-1]]
        while True:
            for regex, token_types, new_state in self.rules_items():
                #print(regex.pattern)
                self.current_match_result = regex.match(source, self.position)

                if self.current_match_result is None:
                    #print("No match for %s" % regex.pattern)
                    continue
                else:
                    #print("Match for %s" % regex.pattern)
                    #print("Token type: ", token_types)
                    #print(self.position, " ", self.current_match_result.end() + 1)
                    #print(source[self.position:])
                    #source_concerned = source[self.position:self.current_match_result.end() + 1]
                    #print("Pattern: ", regex.pattern, "\nSource:", source_concerned)
                    results = self.process_result(token_types)
                    if isinstance(results, list):
                        for result in results:
                            yield result
                    else:
                        yield results

                    self.update_state(new_state)
                    self.update_position()
                    #print()
                    break
            else:
                if self.position == source_length:
                    return
                raise TemplateSyntaxException(
                    'Unexpected char %r at position %d' % (source[self.position], self.position))

    def rules_items(self):
        for rule in self.current_rules:
            yield rule.items()

    def process_result(self, possible_token_types):
        if isinstance(possible_token_types, tuple):
            return self.process_result_from_group(possible_token_types)
        else:
            return possible_token_types, self.current_match_result.group()

    def process_result_from_group(self, possible_token_types):
        result = []
        for (index, possible_token_type) in enumerate(possible_token_types):
            if possible_token_type == '#bygroup':
                result.append(self.process_result_from_by_group())
                return result
            else:
                value = self.process_result_from_normal_group(possible_token_type, index)
                if value:
                    result.append(value)
        return result

    def process_result_from_by_group(self):
        for group_token_type, token_text in self.current_match_result.groupdict().items():
            if token_text is not None:
                return group_token_type, token_text

    def update_state(self, new_state):
        if new_state is not None:
            self.change_state(new_state)
            self.update_rules()

    def change_state(self, new_state):
        if new_state == '#pop':
            self.node_stack.pop()
        elif new_state == '#bygroup':
            self.add_appropriate_group_type_to_stack()
        else:
            self.node_stack.append(new_state)

    def add_appropriate_group_type_to_stack(self):
        for group_type, text in self.current_match_result.groupdict().items():
            if text is not None:
                self.node_stack.append(group_type)
                return

    def update_position(self):
        new_position = self.current_match_result.end()
        if self.position == new_position:
            raise TemplateSyntaxException(
                '%s yielded empty string without stack change' % self.current_match_result.group())
        self.position = new_position

    def update_rules(self):
        self.current_rules = self.rules[self.node_stack[-1]]

    def process_result_from_normal_group(self, possible_token_type, index):
        data = self.current_match_result.group(index + 1)
        if data:
            return possible_token_type, data
        self.line_number += data.count('\n')
