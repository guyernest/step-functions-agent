from jinja2.ext import Extension

import re

def to_snake_case(value):
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', value).lower()

class FunctionNamesExtension(Extension):
    def __init__(self, environment):
        super(FunctionNamesExtension, self).__init__(environment)
        environment.filters['to_snake_case'] = to_snake_case