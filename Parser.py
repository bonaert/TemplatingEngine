from Exception import *
from Constants import *
import Node


def ensure(expr):
    if not expr:
        raise Exception("An error occurred during parsing.")


_statement_keywords = ['for', 'if']
_compare_operators = frozenset(['eq', 'ne', 'lt', 'lteq', 'gt', 'gteq'])


class NodeVisitor(object):
    def get_visitor(self, node):
        method = 'visit_' + node.__class__.__name__
        return getattr(self, method, None)

    def visit(self, node, *args, **kwargs):
        f = self.get_visitor(node)
        if f and callable(f):
            return f(node, *args, **kwargs)
        return self.generic_visit(node, *args, **kwargs)

    def generic_visit(self, node, *args, **kwargs):
        for node in node.iter_child_nodes():
            self.visit(node, *args, **kwargs)


class Parser(NodeVisitor):
    def __init__(self, lexer, source):
        self.source = source
        self.stream = lexer.tokenize(source)
        self._end_token_stack = []

    def parse(self):
        return Node.Template(self.subparse())

    def subparse(self, end_tokens=None):
        body = []

        while self.stream:
            token = self.stream.current

            if token.token_type == TOKEN_DATA:
                next(self.stream)
                if token.value:
                    body.append(Node.Value(token.value))
            elif token.token_type == TOKEN_VARIABLE_START:
                next(self.stream)
                body.append(self.parse_tuple(with_conditional_expression=True))
                self.stream.expect(TOKEN_VARIABLE_END)
            elif token.token_type == TOKEN_BLOCK_START:
                # parses the entire block. ex:  ->{% if True%} 10 {%endif%}{{item}} changes to ->{{item}}
                # (-> represents the current token)

                next(self.stream)
                if end_tokens is not None and self.stream.current.test_any(*end_tokens):
                    return body

                result = self.parse_statement()
                self.add_result_to_body(result, body)
            else:
                raise TemplateParsingException('Internal parsing error: %s.' % token)

        return body

    def add_result_to_body(self, result, body):
        if isinstance(result, list):
            body.extend(result)
        else:
            body.append(result)

    def parse_statement(self):
        token = self.stream.current
        if not token.test('name'):
            raise TemplateSyntaxException('Unknown token %s' % token.value)

        if token.value in _statement_keywords:
            parse_method = getattr(self, 'parse_' + token.value)
            return parse_method()
        else:
            raise Exception("%s is not a keyword" % token.value)

    def parse_tuple(self, explicit_parentheses=False, with_conditional_expression=True, extra_end_rules=None):
        items = []
        is_tuple = False

        if with_conditional_expression:
            parse = self.parse_expression
        else:
            parse = lambda: self.parse_expression(with_conditional_expression=False)

        while True:
            if items:
                self.stream.expect('comma')
            if self.has_reached_tuple_end(extra_end_rules):
                break
            items.append(parse())
            if self.stream.current.token_type == 'comma':
                is_tuple = True
            else:
                break

        if not is_tuple:
            if items:
                return items[0]
            if not explicit_parentheses:
                raise TemplateSyntaxException('Cannot allow empty element')

        return Node.Tuple(items)

    def has_reached_tuple_end(self, extra_end_rules):
        if self.stream.current.token_type in ('variable_end', 'block_end', 'rparen'):
            return True
        elif extra_end_rules is not None:
            return self.stream.current.test_any(extra_end_rules)
        else:
            return False

    def parse_expression(self, with_conditional_expression=True):
        if with_conditional_expression:
            return self.parse_conditional_expression()
        return self.parse_or()

    def parse_conditional_expression(self):
        expr = self.parse_or()
        while self.stream.skip_if('name:if'):
            condition = self.parse_or()
            if self.stream.skip_if('name:else'):
                else_expr = self.parse_expression()
            else:
                else_expr = None
            expr = Node.Cond(condition, expr, else_expr)
        return expr

    def parse_or(self):
        left = self.parse_and()
        while self.stream.skip_if('name:or'):
            right = self.parse_and()
            left = Node.Or(left, right)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.stream.skip_if('name:and'):
            right = self.parse_not()
            left = Node.And(left, right)
        return left

    def parse_not(self):
        if self.stream.skip_if('name:not'):
            return Node.Not(self.parse_not())
        return self.parse_compare()

    def parse_compare(self):
        left = self.parse_add()
        ops = []
        while True:
            token_type = self.stream.current.token_type
            if token_type in _compare_operators:
                next(self.stream)
                ops.append(Node.Operand(token_type, self.parse_and()))
            elif self.stream.skip_if('name:in'):
                ops.append(Node.Operand('in', self.parse_add()))
            elif self.stream.current.test('name:not') and self.stream.look().test('name:in'):
                self.stream.skip(2)
                ops.append(Node.Operand('notin', self.parse_add()))
            else:
                break
        if not ops:
            return left
        return Node.Compare(left, ops)

    def parse_add(self):
        left = self.parse_sub()
        while self.stream.current.token_type == 'add':
            next(self.stream)
            right = self.parse_sub()
            left = Node.Add(left, right)
        return left

    def parse_sub(self):
        left = self.parse_mul()
        while self.stream.current.token_type == 'sub':
            next(self.stream)
            right = self.parse_mul()
            left = Node.Sub(left, right)
        return left

    def parse_mul(self):
        left = self.parse_div()
        while self.stream.current.token_type == 'mul':
            next(self.stream)
            right = self.parse_div()
            left = Node.Mul(left, right)
        return left

    def parse_div(self):
        left = self.parse_floor_div()
        while self.stream.current.token_type == 'div':
            next(self.stream)
            right = self.parse_floor_div()
            left = Node.Div(left, right)
        return left

    def parse_floor_div(self):
        left = self.parse_mod()
        while self.stream.current.token_type == 'floordiv':
            next(self.stream)
            right = self.parse_mod()
            left = Node.FloorDiv(left, right)
        return left

    def parse_mod(self):
        left = self.parse_pow()
        while self.stream.current.token_type == 'mod':
            next(self.stream)
            right = self.parse_pow()
            left = Node.Mod(left, right)
        return left

    def parse_pow(self):
        left = self.parse_unary()
        while self.stream.current.token_type == 'pow':
            next(self.stream)
            right = self.parse_unary()
            left = Node.Pow(left, right)
        return left

    def parse_unary(self):
        token_type = self.stream.current.token_type
        if token_type == 'sub':
            next(self.stream)
            node = Node.Neg(self.parse_unary())
        elif token_type == 'add':
            next(self.stream)
            node = Node.Pos(self.parse_unary())
        else:
            node = self.parse_primary()

        return self.parse_postfix(node)

    def parse_primary(self):
        token_type = self.stream.current.token_type
        token_value = self.stream.current.value
        if token_type == 'name':
            return self.parse_name(token_value)
        elif token_type == 'string':
            return self.parse_string(token_value)
        elif token_type in ('float', 'integer'):
            next(self.stream)
            return Node.Value(token_value)
        elif token_type == 'lparen':
            return self.parse_explicit_tuple()
        elif token_type == 'lbracket':
            return self.parse_list()
        elif token_type == 'lbrace':
            return self.parse_dict()
        else:
            raise TemplateSyntaxException('Unknown token %s' % self.stream.current)

    def parse_name(self, token_value):
        try:
            if token_value in ('True', 'False', 'true', 'false'):
                return Node.Value(token_value in ('True', 'true'))
            elif token_value in ('None', 'none'):
                return Node.Value(None)
            else:
                return Node.Variable(token_value)
        finally:
            next(self.stream)


    def parse_string(self, token_value):
        buffer = [token_value]
        next(self.stream)
        while self.stream.current.token_type == 'string':
            buffer.append(self.stream.current.value)
            next(self.stream)
        return Node.Value(''.join(buffer))

    def parse_explicit_tuple(self):
        self.stream.expect('lparen')
        parsed_tuple = self.parse_tuple()
        self.stream.expect('rparen')
        return parsed_tuple

    def parse_list(self):
        self.stream.expect('lbracket')

        items = []
        while self.stream.current.token_type != 'rbracket':
            if items:
                self.stream.expect('comma')
            items.append(self.parse_expression())

        self.stream.expect('rbracket')

        return Node.List(items)

    def parse_dict(self):
        self.stream.expect('lbrace')

        items = []
        while self.stream.current.token_type != 'rbrace':
            if items:
                self.stream.expect('comma')

            key = self.parse_expression()
            self.stream.expect('colon')
            value = self.parse_expression()

            items.append(Node.Pair(key, value))

        self.stream.expect('rbrace')

        return Node.Dict(items)

    def parse_postfix(self, node):
        while True:
            token_type = self.stream.current.token_type
            if token_type == 'dot' or token_type == 'lbracket':
                node = self.parse_subscript(node)
            elif token_type == 'lparen':
                node = self.parse_call(node)
            else:
                break
        return node

    def parse_subscript(self, node):
        token = self.stream.current
        next(self.stream)
        if token.token_type == 'dot':
            return self.parse_dot_subscript(node)
        elif token.token_type == 'lbracket':
            return self.parse_bracket_subscript(node)

        raise TemplateSyntaxException('Parsing error: cannot parse subscript')

    def parse_dot_subscript(self, node):
        """  foo.->bar ... into foo.bar->... """
        token = self.stream.current
        if token.token_type in ('name', 'integer'):
            next(self.stream)
            return Node.GetAttr(node, token.value, 'load')

    def parse_bracket_subscript(self, node):
        args = []
        while not self.stream.current.test('rbracket'):
            if args:
                self.stream.expect('comma')
            args.append(self.parse_subscribed())
        self.stream.expect('rbracket')

        if len(args) == 1:
            arg = args[0]
        else:
            arg = Node.Tuple(args)

        return Node.GetItem(node, arg, 'load')

    def parse_subscribed(self):
        if self.stream.current.token_type != 'colon':
            expr = self.parse_expression()
            if self.stream.current.token_type != 'colon':
                return expr
            return self.parse_remaining_slice(expr)
        else:
            return self.parse_remaining_slice()


    def parse_remaining_slice(self, first_arg=None):
        # for list[2:3:4], args will be [2]
        args = [first_arg]
        self.stream.expect('colon')

        token_type = self.stream.current.token_type
        # Stop argument
        # [2:->:-1] or [2:->]
        if token_type in ('colon', 'rbracket'):
            args.append(None)
        # [2:->7:1]
        elif token_type not in ('rbracket', 'comma'):
            args.append(self.parse_expression())

        # Step argument
        if self.stream.current.token_type == 'colon':
            next(self.stream)
            # [1:7->]
            if self.stream.current.token_type == 'rbracket':
                args.append(None)
            # [1:15:->3]
            else:
                args.append(self.parse_expression())
        else:
            # [1:->]
            args.append(None)

        return Node.Slice(*args)

    def parse_call(self, node):
        args = []             # f(2, 3)
        kwargs = []           # f(line=3), f(item=[2,3,4], number=7)
        dyn_args = None         # f(*iterable), f(*args)
        dyn_kwargs = None       # f(**dict), f(**kwargs)
        # Complete function could be f(3, 'a', line=7, *iterable, **dict)

        require_comma = False
        self.stream.expect('lparen')
        while not self.stream.current.test('rparen'):
            if require_comma:
                self.stream.expect('comma')

            # passing *args (python syntax requires it to be the last arg
            if self.stream.current.test('mul'):
                # There cannot be various dyn_args and dyn_args always comes before dyn_kwargs
                ensure(dyn_args is None and dyn_kwargs is None)
                next(self.stream)
                dyn_args = self.parse_expression()

            # passing **kwargs (python syntax requires it to be the last kwarg)
            elif self.stream.current.test('pow'):
                ensure(dyn_kwargs is None)
                next(self.stream)
                dyn_kwargs = self.parse_expression()
            else:
                arg = self.parse_expression()
                # kwarg
                if self.stream.current.test('equal'):
                    ensure(dyn_args is None and dyn_kwargs is None)
                    next(self.stream)
                    kwargs.append(Node.KeyWordArgument(arg, self.parse_expression()))
                # arg
                else:
                    args.append(arg)

            require_comma = True

        self.stream.expect('rparen')
        return Node.Call(node, args, kwargs, dyn_args, dyn_kwargs)

    def parse_if(self):
        self.stream.expect('name:if')
        first_node = node = Node.If()
        while True:

            node.test = self.parse_tuple(with_conditional_expression=False)
            self.stream.expect(TOKEN_BLOCK_END)
            node.body = self.parse_statements(['name:elif', 'name:else', 'name:endif'])

            if self.stream.skip_if('name:elif'):
                # {% elif ->... %} ...
                new_node = Node.If()
                node.else_body = [new_node]
                node = new_node
                continue
            elif self.stream.skip_if('name:else'):
                # {% else ->%} ... {% endif %}
                self.stream.expect(TOKEN_BLOCK_END)
                node.else_body = self.parse_statements(['name:endif'])
                self.stream.expect('name:endif')
                self.stream.expect(TOKEN_BLOCK_END)
                break
            elif self.stream.skip_if('name:endif'):
                # ... {% endif ->%}
                self.stream.expect(TOKEN_BLOCK_END)
                node.else_body = []
                break

        return first_node

    def parse_for(self):
        self.stream.expect('name:for')
        target = Node.Value(self.stream.expect('name').value)
        self.stream.expect('name:in')
        items = self.parse_tuple(with_conditional_expression=False)
        self.stream.expect(TOKEN_BLOCK_END)

        body = self.parse_statements(['name:endfor'])
        self.stream.expect('name:endfor')
        self.stream.expect(TOKEN_BLOCK_END)

        return Node.For(target, items, body)

    def parse_statements(self, end_tokens, remove_end_token=False):
        result = self.subparse(end_tokens)

        if remove_end_token:
            next(self.stream)

        return result