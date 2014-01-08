import random
import operator

_binary_operator_to_function = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '//': operator.floordiv,
    '%': operator.mod,
    '**': operator.pow
}

_unary_operator_to_function = {
    '+': operator.pos,
    '-': operator.neg,
    'not': operator.not_
}

_compare_operator_to_function = {
    'eq': operator.eq,
    'ne': operator.ne,
    'gt': operator.gt,
    'gteq': operator.ge,
    'lt': operator.lt,
    'lteq': operator.le,
    'in': lambda a, b: a in b,
    'notin': lambda a, b: a not in b
}


def resolve_in_context(name, scope_stack):
    for scope in reversed(scope_stack):
        if name in scope:
            return scope[name]
    raise Exception('Variable %s was not found' % name)


def with_metaclass(meta, *bases):
    # This requires a bit of explanation: the basic idea is to make a
    # dummy metaclass for one level of class instanciation that replaces
    # itself with the actual metaclass.  Because of internal type checks
    # we also need to make sure that we downgrade the custom metaclass
    # for one level to something closer to type (that's why __call__ and
    # __init__ comes back from type etc.).
    #
    # This has the advantage over six.with_metaclass in that it does not
    # introduce dummy classes into the final MRO.
    class Metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return Metaclass('temporary_class', None, {})


class NodeType(type):
    def __new__(cls, name, bases, dct):
        assert len(bases) == 1, 'Multiple inheritance is not allowed!'

        for attr in ['fields', 'attributes']:
            storage = []
            storage.extend(getattr(bases[0], attr, ()))
            storage.extend(dct.get(attr, ()))
            assert len(storage) == len(set(storage))
            dct[attr] = tuple(storage)
        dct.setdefault('abstract', False)
        return type.__new__(cls, name, bases, dct)


class Node(with_metaclass(NodeType, object)):
    fields = ()
    attributes = ('environment', )
    abstract = True

    def __init__(self, *fields, **attributes):
        if self.abstract:
            raise TypeError('Abstract nodes cannot be instanciated.')

        if fields:
            self._check_fields(fields)
            for name, arg in zip(self.fields, fields):
                setattr(self, name, arg)

        for attr in self.attributes:
            setattr(self, attr, attributes.pop(attr, None))

        if attributes:
            raise TypeError('Unknown attribute %r' % next(iter(attributes)))

    def _check_fields(self, fields):
        if len(fields) == len(self.fields):
            return

        if not self.fields:
            raise TypeError('%r takes 0 arguments' % self.__class__.__name__)
        else:
            raise TypeError('%r takes 0 or %d argument%s' % (
                self.__class__.__name__,
                len(self.fields),
                len(self.fields) != 1 and 's' or ''
            ))

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % (arg, getattr(self, arg, None)) for
                      arg in self.fields)
        )

    def render_as_string(self, context=None):
        return str(self.render(context))


class Template(Node):
    fields = ('body', )

    def render(self, context=None):
        context = self._build_context(context)
        return ''.join(item.render_as_string(context) for item in self.body)

    def _build_context(self, context):
        builtin_functions = {'abs': abs,
                             'any': any,
                             'all': all,
                             'capitalize': str.capitalize,
                             'float': float,
                             'format': format,
                             'int': int,
                             'length': len,
                             'lower': str.lower,
                             'random': random.random,
                             'randint': random.randint,
                             'range': range,
                             'round': round,
                             'reversed': reversed,
                             'sorted': sorted,
                             'string': str,
                             'title': str.title,
                             'upper': str.upper,
                             'even': lambda x: x % 2 == 0,
                             'odd': lambda x: x % 2 != 0,
                             'type': type
        }
        if context is not None:
            return [builtin_functions, context]
        else:
            return [builtin_functions]

###########################################################################
#                                                                         #
#                            Basic Nodes                                  #
#                                                                         #
###########################################################################


class Value(Node):
    fields = ('value', )

    def render(self, context=None):
        return self.value


class Variable(Node):
    fields = ('name', )

    def render(self, context=None):
        return resolve_in_context(self.name, context)

###########################################################################
#                                                                         #
#                         Data structures                                 #
#                                                                         #
###########################################################################

class List(Node):
    fields = ('items', )

    def render(self, context=None):
        return [item.render(context) for item in self.items]


class Slice(Node):
    fields = ('start', 'stop', 'step')

    def render(self, context=None):
        def const(item):
            return item.render(context) if item else None

        return slice(const(self.start), const(self.stop), const(self.step))


class Tuple(Node):
    fields = ('items', )

    def render(self, context=None):
        return tuple(item.render(context) for item in self.items)


class Dict(Node):
    fields = ('items', )

    def render(self, context=None):
        return dict(item.render(context) for item in self.items)


class Pair(Node):
    fields = ('key', 'value')

    def render(self, context=None):
        return self.key.render(context), self.value.render(context)


class KeyWordArgument(Node):
    fields = ('key', 'value')

    def render(self, context=None):
        return self.key, self.value.render(context)

###########################################################################
#                                                                         #
#                         Control flow                                    #
#                                                                         #
###########################################################################


class If(Node):
    """ Renders
    * if-statement:
        if True:
            return 10

    * if-else:
        if todo:
            return todo.text()
        else:
            return ''

    """
    fields = ('test', 'body', 'else_body')

    def render(self, context=None):

        if self.test.render(context):
            return ''.join(item.render_as_string(context) for item in self.body)

        if self.else_body:
            return ''.join(item.render_as_string(context) for item in self.else_body)
        else:
            return ''


class Cond(Node):
    """ Render a if-else statement:
    * 5 if True else 10
    * todo.item() if todo else ''
    It differs from an IF node because it requires an else-clause.
    """
    fields = ('test', 'if_expr', 'else_expr')

    def render(self, context=None):

        if self.test.render(context):
            return self.if_expr.render_as_string(context)

        if not self.else_expr:
            raise Exception()

        return self.else_expr.render_as_string(context)


class For(Node):
    fields = ('target', 'items', 'body')

    def render(self, context=None):
        result = []
        for item in self.items.render(context):
            context.append({self.target.render(context): item})
            result.extend(expr.render_as_string(context) for expr in self.body)
            context.pop()

        return ''.join(result)


###########################################################################
#                                                                         #
#                   Binary and unary expressions                          #
#                                                                         #
###########################################################################


class BinaryExpr(Node):
    fields = ('left', 'right')
    operator = None
    abstract = True

    def render(self, context=None):
        operator_function = _binary_operator_to_function[self.operator]
        return operator_function(self.left.render(context), self.right.render(context))


class And(BinaryExpr):
    operator = 'and'

    def render(self, context=None):
        return self.left.render(context) and self.right.render(context)


class Or(BinaryExpr):
    operator = 'or'

    def render(self, context=None):
        return self.left.render(context) or self.right.render(context)


class Add(BinaryExpr):
    operator = '+'


class Sub(BinaryExpr):
    operator = '-'


class Mul(BinaryExpr):
    operator = '*'


class Div(BinaryExpr):
    operator = '/'


class FloorDiv(BinaryExpr):
    operator = '//'


class Mod(BinaryExpr):
    operator = '%'


class Pow(BinaryExpr):
    operator = '**'


class UnaryExpr(Node):
    fields = ('node', )
    operator = None
    abstract = True

    def render(self, context=None):
        unary_function = _unary_operator_to_function[self.operator]
        return unary_function(self.node.render(context))


class Not(UnaryExpr):
    operator = 'not'


class Neg(UnaryExpr):
    operator = '-'


class Pos(UnaryExpr):
    operator = '+'

###########################################################################
#                                                                         #
#                            Comparison                                   #
#                                                                         #
###########################################################################


class Compare(Node):
    """ Renders a 5 > 3 > 2 > 0 < 2 expression (should be True)"""
    fields = ('expr', 'ops')

    def render(self, context=None):

        left_value = self.expr.render(context)

        for op in self.ops:
            right_value = op.expr.render(context)
            compare_function = _compare_operator_to_function[op.operator]

            if not compare_function(left_value, right_value):
                return False

            left_value = right_value

        return True


class Operand(Node):
    fields = ('operator', 'expr')


###########################################################################
#                                                                         #
#                      Attributes and items                               #
#                                                                         #
###########################################################################

class GetAttr(Node):
    fields = ('node', 'attr', 'purpose')

    def render(self, context=None):
        node = self.node.render(context)
        return getattr(node, self.attr)


class GetItem(Node):
    fields = ('node', 'name', 'purpose')

    def render(self, context=None):
        node = self.node.render(context)
        return node.__getitem__(self.name.render(context))


class Call(Node):
    fields = ('node', 'args', 'kwargs', 'dyn_args', 'dyn_kwargs')

    def render(self, context=None):
        node = self.node.render(context)

        args = [arg.render(context) for arg in self.args]
        kwargs = dict(kwarg.render(context) for kwarg in self.kwargs)

        if self.dyn_args is not None:
            args.extend(self.dyn_args.render(context))

        if self.dyn_kwargs is not None:
            kwargs.update(self.dyn_kwargs.render(context))

        return node(*args, **kwargs)