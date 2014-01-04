import unittest
from Lexer import Lexer
from Parser import Parser


class ParserTest(unittest.TestCase):
    def make_environment(self):
        class Environment(object):
            def __init__(self):
                self.lexer = Lexer()

            def tokenize(self, source):
                return self.lexer.tokenize(source)

        return Environment()

    def make_object_with_attr(self, attr, value):
        return type('Dummy object', (object, ), {attr: value})

    def assert_source_parses_and_renders_correctly(self):
        environment = self.make_environment()
        parser = Parser(environment, self.source)
        parsed_source = parser.parse()
        rendered_source = parsed_source.render(self.items)
        print("Parsed source: ", parsed_source)

        if isinstance(self.result, list):
            self.assertIn(rendered_source, self.result)
        else:
            self.assertEqual(self.result, rendered_source)

    def test_can_do_data(self):
        self.source = 'hello world!'
        self.result = 'hello world!'
        self.items = {}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_variable_substitutions(self):
        self.source = '{{foo}} {{bar}}'
        self.result = 'hello world'
        self.items = {'foo': 'hello', 'bar': 'world'}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_if_statements(self):
        self.source = '{% if True %} 10 {% endif %}'
        self.result = ' 10 '
        self.items = {}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_if_else_statements(self):
        self.source = '{% if False %} 10 {% else %} 20 {% endif %}'
        self.result = ' 20 '
        self.items = {}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_if_statement_that_do_not_evaluate_to_true(self):
        self.source = '{% if False %} 10 {% endif %}'
        self.result = ''
        self.items = {}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_if_elif_statement(self):
        self.source = '{% if False %} 10 {% elif True %} 20 {% endif %}'
        self.result = ' 20 '
        self.items = {}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_if_elif_else_statement(self):
        self.source = '{% if False %} 10 {% elif False %} 20 {% else %} 30 {% endif %}'
        self.result = ' 30 '
        self.items = {}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_if_statements_with_variables(self):
        self.source = '{% if test %} 10 {% else %} 20 {% endif %}'

        self.result = ' 10 '
        self.items = {'test': True}
        self.assert_source_parses_and_renders_correctly()

        self.source = '{% if test %} 10 {% else %} 20 {% endif %}'
        self.result = ' 20 '
        self.items = {'test': False}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_for_loops(self):
        self.source = '{% for item in foo %}10{% endfor %}'
        self.result = '101010'
        self.items = {'foo': [1, 2, 3]}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_for_loop_and_use_item(self):
        self.source = '{% for item in foo %}{{item}}{% endfor %}'
        self.result = 'FooBarBaz'
        self.items = {'foo': ['Foo', 'Bar', 'Baz']}
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_for_loop_over_values(self):
        self.items = {}

        self.source = '{% for item in [2,3.2,"a"] %} {{item}} {% endfor %}'
        self.result = ' 2  3.2  a '
        self.assert_source_parses_and_renders_correctly()

        self.source = '{% for item in (2,3.2,"a") %} {{item}} {% endfor %}'
        self.result = ' 2  3.2  a '
        self.assert_source_parses_and_renders_correctly()

        self.source = '{% for item in {2:1,3.2:1,"a":1} %} {{item}} {% endfor %}'
        self.result = [' 2  3.2  a ', ' 2  a  3.2 ', ' a  3.2  2 ', ' a  2  3.2 ', ' 3.2  2  a ', ' 3.2  a  2 ']
        self.assert_source_parses_and_renders_correctly()

    def test_can_call_function_on_object(self):
        self.source = '{{foo.bar()}}'

        def bar():
            return 'hello world!'

        obj = self.make_object_with_attr('bar', bar)
        self.items = {'foo': obj}
        self.result = 'hello world!'
        self.assert_source_parses_and_renders_correctly()

    def test_can_call_function_on_object_with_args(self):
        self.source = '{{foo.add(4000,5000)}}'

        def add(a, b):
            return a + b

        obj = self.make_object_with_attr('add', add)
        self.items = {'foo': obj}
        self.result = '9000'
        self.assert_source_parses_and_renders_correctly()

    def test_can_get_item_of_list(self):
        self.source = '{{list[1]}}{{list[0]}}'
        self.items = {'list': ['Hello!', 'My dear Watson!']}
        self.result = 'My dear Watson!Hello!'
        self.assert_source_parses_and_renders_correctly()

    def test_can_use_slices(self):
        self.source = '{{list[8:2:-2]}}'
        self.items = {'list': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]}
        self.result = '[8, 6, 4]'
        self.assert_source_parses_and_renders_correctly()

    def test_can_use_methods_from_standard_library(self):
        self.items = {}

        self.source = '{% for i in reversed([1,2,3,4,5]) %}{{i}}{% endfor %}'
        self.result = '54321'
        self.assert_source_parses_and_renders_correctly()

        self.source = '{{ capitalize("hello!") }}'
        self.result = 'Hello!'
        self.assert_source_parses_and_renders_correctly()

        self.source = '{% for i in range(10) %}<{{i**2}}>{% endfor %}'
        self.result = '<0><1><4><9><16><25><36><49><64><81>'
        self.assert_source_parses_and_renders_correctly()

        self.source = '{% if even(10) %}{{ title("hello world!") }}{% endif %}'
        self.result = 'Hello World!'
        self.assert_source_parses_and_renders_correctly()

    def test_can_use_and_or_not(self):
        self.items = {'foo': True, 'bar': False, 'baz': 'hello world!'}
        self.source = '{% if foo and bar %}{{baz}}{% endif %}'
        self.result = ''
        self.assert_source_parses_and_renders_correctly()

        self.items = {'foo': True, 'bar': False, 'baz': 'hello world!'}
        self.source = '{% if foo or bar %}{{baz}}{% endif %}'
        self.result = 'hello world!'
        self.assert_source_parses_and_renders_correctly()

        self.items = {'foo': True, 'bar': False, 'baz': 'hello world!'}
        self.source = '{% if not foo %}{{baz}}{% endif %}'
        self.result = ''
        self.assert_source_parses_and_renders_correctly()

        self.items = {'foo': True, 'bar': False, 'baz': 'hello world!'}
        self.source = '{% if not bar %}{{baz}}{% endif %}'
        self.result = 'hello world!'
        self.assert_source_parses_and_renders_correctly()

    def test_can_use_comparisons(self):
        self.items = {}
        self.source = "{% if 5 > 4 %}a{% else %} {% endif %}" \
                      "{% if 5 >= 4 %}a{% else %} {% endif %}" \
                      "{% if 5 == 4 %}a{% else %} {% endif %}" \
                      "{% if 5 != 4 %}a{% else %} {% endif %}" \
                      "{% if 5 < 4 %}a{% else %} {% endif %}" \
                      "{% if 5 <= 4 %}a{% else %} {% endif %}"
        self.result = 'aa a  '
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_math(self):
        self.items = {}
        self.source = "{{ 7 + 4 }} " \
                      "{{ 7 - 4 }} " \
                      "{{ 7 * 4 }} " \
                      "{{ 7 / 4 }} " \
                      "{{ 7 // 4 }} " \
                      "{{ 7 % 4 }} " \
                      "{{ 7 ** 4 }} " \
                      "{{ +7 }} " \
                      "{{ -7 }} " \
                      "{{ 7 }}"
        self.result = '11 3 28 1.75 1 3 2401 7 -7 7'
        self.assert_source_parses_and_renders_correctly()

    def test_can_do_cond_expressions(self):
        self.items = {'bar': True}
        self.source = '{{ "Hello World!" if bar else "Goodbye World!" }}'
        self.result = 'Hello World!'
        self.assert_source_parses_and_renders_correctly()

        self.items = {'bar': False}
        self.source = '{{ "Hello World!" if bar else "Goodbye World!" }}'
        self.result = 'Goodbye World!'
        self.assert_source_parses_and_renders_correctly()

    def test_can_use_standard_methods_of_data_structures(self):
        self.items = {}
        self.source = '{% for i in {1:2, 3:4}.values() %}<{{i}}>{% endfor %}'
        self.result = '<2><4>'
        self.assert_source_parses_and_renders_correctly()

        self.items = {}
        self.source = '{{ [1,2,3].pop() }} {{ [1,2,3].pop(0) }}'
        self.result = '3 1'
        self.assert_source_parses_and_renders_correctly()

    def test_can_check_for_inclusion(self):
        self.items = {}
        self.source = '{% if 1 in [1,2,3,4,5] %}hi!{% endif %}'
        self.result = 'hi!'
        self.assert_source_parses_and_renders_correctly()

        self.items = {}
        self.source = '{% if 1 not in [1,2,3,4,5] %}hi!{% endif %}'
        self.result = ''
        self.assert_source_parses_and_renders_correctly()

    def test_can_use_unicode(self):
        self.items = {'äáéà' : 'hi', 'ííìì': [1,2,3]}
        self.source = '{{ äáéà }} {% for i in ííìì %}{{i}}{% endfor %}'
        self.result = 'hi 123'
        self.assert_source_parses_and_renders_correctly()




if __name__ == '__main__':
    unittest.main()