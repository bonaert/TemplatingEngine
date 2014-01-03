class TokenException(Exception):
    pass


class TemplateContextException(TokenException):
    def __init__(self, variable, context):
        self.context_variable = variable
        self.context = context

    def __str__(self):
        return "Cannot resolve the variable '%s' in \ncontext: %s" % (self.context_variable, self.context)


class TemplateSyntaxException(TokenException):
    def __init__(self, syntax_error_text):
        self.syntax_error_text = syntax_error_text

    def __str__(self):
        return self.syntax_error_text


class TemplateNestingException(TokenException):
    def __str__(self):
        return "Template has nesting issues"


class TemplateParsingException(TokenException):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message