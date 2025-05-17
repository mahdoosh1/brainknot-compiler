from dataclasses import dataclass
import re

@dataclass
class Token:
    name: str  # Type of token, e.g., 'STACK_DECLARE'
    value: list  # Token's lexeme split into parts
    expression: bool  # Whether this token is part of an expression
    line: int # for logging

def tokenize(code: str) -> list:
    """
    Converts input code into a list of Token objects based on predefined syntax rules.
    """
    # Define token specifications in order of priority
    token_specs = [
        # Format: (type_name, regex_pattern, is_expression)
        ('WHITESPACE', r'[ \t]+', False),
        ('NEWLINE', r'(\r\n|\r|\n)', False),
        ('PRINTLN', r'println', False),
        ('PRINT', r'print', False),
        ('STRING_LITERAL', r'\"([^\\\"]|\\.)*\"', True),
        ('STACK_DECLARE', r'stack\s+', False),
        ('BINARY_DECLARE', r'binary\s+', False),
        ('FUNC_DECLARE', r'func', False),
        ('IF', r'if', False),
        ('ELSE', r'else', False),
        ('WHILE', r'while', False),
        ('POP', r'\.pop\(\)', True),
        ('PUSH', r'\.push', False),
        ('BREAK', r'break', False),
        ('ASSIGN', r'=', False),
        ('SEMICOLON', r';', False),
        ('LPAREN', r'\(', True),   # Fixed: Matches '('
        ('RPAREN', r'\)', True),   # Fixed: Matches ')'
        ('LBRACE', r'\{', False),
        ('RBRACE', r'\}', False),
        ('BOOLEAN_LITERAL', r'true|false|True|False|TRUE|FALSE|1|0', True),
        ('OPERATOR_NOT', r'not', True),
        ('INPUT_CALL', r'input\(\)', True),
        ('OUTPUT_CALL', r'output', False),
        ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*', True),
    ]

    # Build a master regex pattern that matches all tokens
    master_regex = '|'.join(
        f'(?P<{name}>{regex})' for name, regex, _ in token_specs
    )
    token_re = re.compile(master_regex)

    tokens = []
    pos = 0
    line = 1

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
        if matched_type == 'NEWLINE':
            line += 1
        elif matched_type != 'WHITESPACE':
            # Add new token
            tokens.append(
                Token(name=matched_type, value=matched_val, expression=matched_expr, line=line)
            )
        pos = match.end()

    return tokens