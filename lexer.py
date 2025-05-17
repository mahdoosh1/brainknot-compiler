from dataclasses import dataclass
import re

@dataclass
class Token:
    name: str  # Type of token, e.g., 'STACK_DECLARE'
    value: list  # Token's lexeme split into parts
    expression: bool  # Whether this token is part of an expression

def tokenize(code):
    """
    Converts input code into a list of Token objects based on predefined syntax rules.
    """
    # Define token specifications in order of priority
    token_specs = [
        # Format: (type_name, regex_pattern, is_expression)
        ('WHITESPACE', r'\s+', False),
        ('STACK_DECLARE', r'stack\s+', False),
        ('BINARY_DECLARE', r'binary\s+', False),
        ('FUNC_DECLARE', r'func', False),
        ('IF', r'if', False),
        ('ELSE', r'else', False),
        ('WHILE', r'while', False),
        ('POP', r'\.pop\(\)', True),
        ('PUSH', r'\.push', False),
        ('ASSIGN', r'=', False),
        ('SEMICOLON', r';', False),
        ('LPAREN', r'\(', True),   # Fixed: Matches '('
        ('RPAREN', r'\)', True),   # Fixed: Matches ')'
        ('LBRACE', r'\{', False),
        ('RBRACE', r'\}', False),
        ('BOOLEAN_LITERAL', r'true|false|True|False|TRUE|FALSE|1|0', True),
        ('OPERATOR_NOT', r'not', True),
        ('INPUT_CALL', r'input\(\)', True),
        ('OUTPUT_CALL', r'output', True),
        ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*', True),
    ]

    # Build a master regex pattern that matches all tokens
    master_regex = '|'.join(
        f'(?P<{name}>{regex})' for name, regex, _ in token_specs
    )
    token_re = re.compile(master_regex)

    tokens = []
    pos = 0

    while pos < len(code):
        match = token_re.match(code, pos)
        if not match:
            # No valid token found
            raise SyntaxError(f"Invalid token at position {pos}: {code[pos:pos+10]}")

        # Find the token type that matched
        matched_type = ""
        matched_expr = False
        matched_val = []

        # Iterate through token specs to determine which pattern matched
        for name, _, expr in token_specs:
            val = match.group(name)
            if val:
                matched_type = name
                matched_expr = expr
                matched_val = [val]
                break

        if matched_type != 'WHITESPACE':
            # Add new token
            tokens.append(
                Token(name=matched_type, value=matched_val, expression=matched_expr)
            )
        pos = match.end()

    return tokens
# Example usage:
# -----------------
# code = """stack my_stack;
# binary my_binary = input();
# binary new_binary;
# new_binary = my_binary;
# my_stack.push(not my_binary);
# my_binary = my_stack.pop();
# if (my_binary) {
#     new_binary = True;
# } else {
#     my_stack.push(false);
# };
# func my_func {
#     my_binary = my_stack.pop();
#     my_stack.push(my_binary);
# };
# func main() {
#     output(new_binary);
#     new_binary = input();
#     my_func();
#     output(my_stack.pop());
#     if (my_stack.pop()) {
#         if (not new_binary) {
#             output(not my_binary);
#         };
#     };
# };"""
# -----------------
# stack [name];    # statement
# binary [name];    #statement
# binary [name] = expression;    # statement
# [stack_name].push(expression)    # expression
# [stack_name].pop()    # expression
# if (expression) {code1} else {code2}    # expression
# while (expression) {code}    # expression
# output(expression)    # expression
# input()    # expression
# func [name] {code}    # statement
# func [name]() {code}    # expression
# [func_name]()    # expression
# not [expression]    # expression
# statements end in semicolon
# for token in tokenize(code):
#     print(token)