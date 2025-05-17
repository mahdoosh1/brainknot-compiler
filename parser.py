from dataclasses import dataclass
from typing import Any, Sequence, MutableSequence
from lexer import Token
from ast import literal_eval


@dataclass
class ASTNode:
    type: str
    fields: dict[str, Any]
    line: int

class TokenSyntaxError(SyntaxError):
    def __init__(self, token: Token | None, arg1: Any, *args: Sequence[Any]):
        if token is not None:
            args = (f"At line {token.line}: ",arg1)+args
        else:
            args = (arg1,)+args
        super().__init__(args)

class ASTNodeError(SyntaxError):
    def __init__(self, node: ASTNode, arg1: Any, *args: Sequence[Any]):
        args = (f"At line {node.line}: ",arg1) + args
        super().__init__(args)


class Parser:
    def __init__(self, tokens: Sequence[Token]):
        self.tokens = tokens
        self.pos = 0
        self.defined_identifiers: dict[str,list[bool]] = dict({"current":[True, True, False]}) # {key = name, value = index [0] for binary, [1] for stack, [2] for function}

    def add_identifier(self, token: Token, name: str, index: int) -> None:
        if self.defined_identifiers.get(name):
            if self.defined_identifiers[name][index]:
                raise TokenSyntaxError(token, "Cannot use name {name}, it is already taken")
            self.defined_identifiers[name][index] = True
        else:
            self.defined_identifiers[name] = [i == index for i in range(3)]

    def check_identifier(self, token: Token, name: str, index: int) -> None:
        if not self.defined_identifiers.get(name):
            raise TokenSyntaxError(token, f"Name {name} is not declared/defined")
        if not self.defined_identifiers[name][index]:
            raise TokenSyntaxError(token, f"Name {name} is not declared/defined")

    def peek(self, amount: int=0) -> Token:
        if self.pos + amount < len(self.tokens):
            return self.tokens[self.pos + amount]
        raise EOFError(f"Unexpected End of file in position: {self.pos}")

    def consume(self) -> Token:
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        raise EOFError(f"Unexpected End of file in position: {self.pos}")

    def expect(self, token_name: str) -> Token:
        token = self.peek()
        if token:
            if token.name == token_name:
                return self.consume()
            raise TokenSyntaxError(token, f"Expected token '{token_name}', got '{token.name}'")
        raise TokenSyntaxError(token, f"Expected token '{token_name}', got 'EOF' in line UNKNOWN")

    def parse_program(self) -> list:
        # __init__
        statements = []
        self.pos = 0
        self.defined_identifiers: dict[str,list[bool]] = dict({"current":[True, True, False]}) # {key = name, value = index [0] for binary, [1] for stack, [2] for function}
        while self.pos < len(self.tokens):
            statements.append(self.parse_statement())
        return statements

    def parse_statement(self) -> ASTNode:
        token = self.peek()
        if token.expression and token.name != "IDENTIFIER":
            raise TokenSyntaxError(token, f"Expression {token.name} with value {token.value} is not implemented")
        if token.name == 'BREAK':
            self.consume()
            self.expect('SEMICOLON')
            return ASTNode(type='BreakLoop', fields={}, line=token.line)
        if token.name in ('PRINT', 'PRINTLN'):
            self.consume()
            self.expect('LPAREN')
            text = repr(literal_eval(self.expect('STRING_LITERAL').value[0]))[1:-1].replace("{","\\{").replace("}", "\\}")
            self.expect('RPAREN')
            self.expect('SEMICOLON')
            if token.name == 'PRINTLN':
                text += "\\n"
            return ASTNode(type='PrintStatement',fields={'text': text}, line=token.line)
        if token.name == 'STACK_DECLARE':
            self.consume()
            name = self.expect('IDENTIFIER').value[0]
            self.add_identifier(token, name, 1)
            self.expect('SEMICOLON')
            return ASTNode(type='StackDeclaration', fields={'name': name}, line=token.line)

        if token.name == 'BINARY_DECLARE':
            self.consume()
            name = self.expect('IDENTIFIER').value[0]
            self.add_identifier(token, name, 0)
            if self.peek() and self.peek().name == 'ASSIGN':
                self.consume() # ASSIGN
                expr = self.parse_expression()
                self.expect('SEMICOLON')
                return ASTNode(type='BinaryDeclaration', fields={'name': name, 'value': expr}, line=token.line)
            self.expect('SEMICOLON')
            return ASTNode(type='BinaryDeclaration',
                           fields={'name': name, 'value': ASTNode(type='Identifier', fields={'name': 'current'}, line=token.line)}, line=token.line)

        if token.name == 'FUNC_DECLARE':
            self.consume()
            name = self.expect('IDENTIFIER').value[0]
            self.add_identifier(token, name, 2)
            if self.peek() and self.peek().name == 'LPAREN':
                self.consume()
                self.expect('RPAREN')
                body = self.parse_block()
                return ASTNode(type='FunctionDefinitionAndCall', fields={'name': name, 'body': body}, line=token.line)
            body = self.parse_block()
            self.expect('SEMICOLON')
            return ASTNode(type='FunctionDefinition', fields={'name': name, 'body': body}, line=token.line)

        if token.name == 'IF':
            self.consume()
            self.expect('LPAREN')
            condition = self.parse_expression()
            self.expect('RPAREN')
            then_block = self.parse_block()
            else_block = []
            if self.peek() and self.peek().name == 'ELSE':
                self.consume()
                else_block = self.parse_block()
            self.expect('SEMICOLON')
            return ASTNode(type='IfStatement',
                           fields={'condition': condition, 'then_block': then_block, 'else_block': else_block}, line=token.line)

        if token.name == 'WHILE':
            self.consume()
            self.expect('LPAREN')
            condition = self.parse_expression()
            self.expect('RPAREN')
            body = self.parse_block()
            return ASTNode(type='WhileLoop', fields={'condition': condition, 'body': body}, line=token.line)

        if token.name == 'OUTPUT_CALL':
            self.consume()
            self.expect('LPAREN')
            expr = self.parse_expression()
            self.expect('RPAREN')
            self.expect('SEMICOLON')
            return ASTNode(type='Output', fields={'arguments': expr}, line=token.line)

        if token.name == 'IDENTIFIER':
            if self.pos + 1 < len(self.tokens):
                next_token = self.tokens[self.pos + 1]
                if next_token.name == 'PUSH':
                    name = self.expect('IDENTIFIER').value[0]
                    self.check_identifier(token, name, 1)
                    self.expect('PUSH')
                    self.expect('LPAREN')
                    value = self.parse_expression()
                    self.expect('RPAREN')
                    self.expect('SEMICOLON')
                    return ASTNode(type='PushOperation', fields={'stack_name': name, 'value': value}, line=token.line)
                if next_token.name == 'ASSIGN':
                    return self.parse_assignment()
                if next_token.name == 'LPAREN':
                    return self.parse_function_call()
                raise TokenSyntaxError(token, f"Unexpected identifier {next_token.name}")
            raise TokenSyntaxError(token, f"no token found after position {self.pos}")

        raise TokenSyntaxError(token, f"Uncaught statement {token.name}")

    def parse_block(self) -> list:
        self.expect('LBRACE')
        statements = []
        while self.peek() and self.peek().name != 'RBRACE':
            statements.append(self.parse_statement())
        self.expect('RBRACE')
        return statements

    def parse_assignment(self) -> ASTNode:
        token = self.expect('IDENTIFIER')
        name = token.value[0]
        self.check_identifier(self.peek(), name, 0)
        self.expect('ASSIGN')
        expr = self.parse_expression()
        self.expect('SEMICOLON')
        return ASTNode(type='Assignment', fields={'target': name, 'expression': expr}, line=token.line)

    def parse_function_call(self) -> ASTNode:
        token = self.expect('IDENTIFIER')
        name = token.value[0]
        self.check_identifier(self.peek(), name, 2)
        self.expect('LPAREN')
        self.expect('RPAREN')
        self.expect('SEMICOLON')
        return ASTNode(type='FunctionCall', fields={'name': name}, line=token.line)

    def parse_expression(self) -> ASTNode:
        if (token := self.peek()) and self.peek().name == 'OPERATOR_NOT':
            self.consume()
            operand = self.parse_primary()
            return ASTNode(type='NotOp', fields={'operand': operand}, line=token.line)
        return self.parse_primary()

    def parse_primary(self) -> ASTNode:
        token = self.peek()
        if token.name == 'INPUT_CALL':
            self.consume()
            return ASTNode(type='Input', fields={}, line=token.line)
        if token.name == 'BOOLEAN_LITERAL':
            value = token.value[0] in ('True', 'true', '1')
            self.consume()
            return ASTNode(type='BooleanLiteral', fields={'value': value}, line=token.line)
        if token.name == 'IDENTIFIER':
            name = self.consume().value[0]
            if self.peek() and self.peek().name == 'POP':
                self.consume()
                self.check_identifier(token, name, 1)
                return ASTNode(type='PopOperation', fields={'stack_name': name}, line=token.line)
            self.check_identifier(token, name, 0)
            return ASTNode(type='Identifier', fields={'name': name}, line=token.line)
        if token.name == 'LPAREN':
            self.consume()
            expr = self.parse_expression()
            self.expect('RPAREN')
            return expr
        raise TokenSyntaxError(token, f"Unexpected token in expression: {token.name}")