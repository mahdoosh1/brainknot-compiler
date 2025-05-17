from parser import Parser, ASTNode, ASTNodeError
from typing import Container, Iterable


"""
stack my_stack;                      tgt= | src | opr  | tgt | indent+symbol
binary my_binary = input();               | >   |      | 0+  |
binary new_binary;                        |     | [*]  | 1+  |
new_binary = my_binary;              1-   | 0-+ |      | 1+  |
my_stack.push(not my_binary);             | 0-+ | *    | 99+ |
my_binary = my_stack.pop();          0-   | 99- |      | 0+  |
if (my_binary) {                          | 0-+ |      |     | [
    new_binary = True;               1-   |     | [,*] | 1+  |
} else {                                  |     |      |     | ,
    my_stack.push(false);                 |     | [*]  | 99+ |
};                                        |     |      |     | ]
if (not my_binary) {                      | 0-+ | *    |     | [
    new_binary = my_stack.pop();     1-   | 99- |      | 1+  |
};                                        |     |      |     | ]
func my_func {                            |     |      |     | my_func:[
    my_binary = my_stack.pop();      0-   | 99- |      | 0+  |
    my_stack.push(my_binary);             | 0-+ |      | 99+ |
};                                        |     |      |     | ]
func main() {                             |     |      |     | main:(
    output(new_binary);                   | 1-+ |      | <   |
    new_binary = input();            1-   | >   |      | 1+  |
    my_func();                            |     |      |     |   my_func
    output(my_stack.pop());               | 99- |      | <   |
    if (my_stack.pop()) {                 | 90- |      |     |   [
        if (not new_binary) {             | 1-+ | *    |     |     [
            output(not my_binary);        | 0-+ | *    | <   |
        };                                |     |      |     |     ]
    };                                    |     |      |     |   ]
}                                         |     |      |     | )
"""
def translate_expression(expression: ASTNode, stack_translate: dict[str, int], binary_translate: dict[str, int]):
    type_ = expression.type
    fields = expression.fields
    if type_ == "NotOp":
        argument = fields['operand']
        return translate_expression(argument, stack_translate, binary_translate)+"*"
    if type_ == "Identifier":
        name = fields['name']
        if name == 'current':
            return ''
        if name not in binary_translate:
            raise ASTNodeError(expression,f"name {name} is not declared")
        number = binary_translate[name]
        return f'{number}-+'
    if type_ == "PopOperation":
        stack_name = fields['stack_name']
        if stack_name not in stack_translate:
            raise ASTNodeError(expression,f"stack name {stack_name} is not declared")
        if stack_name == 'current':
            return '-'
        number = stack_translate[stack_name]
        return f'{number}-'
    if type_ == "BooleanLiteral":
        value = fields['value']
        if value:
            return '[,*]'
        return '[*]'
    if type_ == "Input":
        return ">"
    return ""
def translate(parser: Parser, function_names: list[str] | None = None):
    # 1 stack per binary
    # 4 operand
    # optimization = hard
    statements = parser.parse_program()
    declared_variables = parser.defined_identifiers
    stack_translate = {key: index for index, (key, value) in enumerate(declared_variables.items()) if (value[1] and key != 'current')}
    binary_translate = {key: index for index, (key, value) in enumerate(declared_variables.items()) if (value[0] and key != 'current')}
    if function_names is None:
        return_funcs = False
        function_names = []
    else:
        return_funcs = True
    output = []
    for statement in statements:
        fields = statement.fields
        type_ = statement.type
        instruction = ""
        if type_ == "BinaryDeclaration":
            target = binary_translate[fields['name']]
            source = fields['value']
            if source == 'current':
                source = ''
            elif type(source) == ASTNode:
                source = translate_expression(source, stack_translate, binary_translate)
            else:
                raise ASTNodeError(statement,f"Unknown source {source}")
            instruction = f"{source}{target}+"
        if type_ == "Output":
            source = fields['arguments']
            source = translate_expression(source, stack_translate, binary_translate)
            instruction = f"{source}<"
        if type_ == "PushOperation":
            source = fields['value']
            target = fields['stack_name']
            if target == 'current':
                target = ''
            elif target not in stack_translate:
                raise ASTNodeError(statement, f"stack {target} is not declared")
            else:
                target = stack_translate[target]
            source = translate_expression(source, stack_translate, binary_translate)
            instruction = f"{source}{target}+"
        if type_ == "Assignment":
            source = fields['expression']
            source = translate_expression(source, stack_translate, binary_translate)
            target = fields['target']
            if target == 'current':
                instruction = f"{source}"
            elif target not in binary_translate:
                raise ASTNodeError(statement, f"assignment target {target} is not declared")
            else:
                target = binary_translate[target]
                instruction = f"{target}-{source}{target}+"
        if type_ == "FunctionCall":
            name = fields['name']
            if name not in function_names:
                raise ASTNodeError(statement, f"function {name} is not defined")
            instruction = f"{name} "
        if type_ == "FunctionDefinition":
            name = fields['name']
            if name == 'current':
                raise ASTNodeError(statement, f"name {name} is preserved and cannot be redefined")
            body = fields['body']
            body, function_names = translate(body, declared_variables, function_names)
            instruction = f"{name}:[{body}]"
            function_names.append(name)
        if type_ == "FunctionDefinitionAndCall":
            name = fields['name']
            if name == 'current':
                raise ASTNodeError(statement, f"name {name} is preserved and cannot be redefined")
            body = fields['body']
            body, function_names = translate(body, declared_variables, function_names)
            instruction = f"{name}:({body})"
            function_names.append(name)
        if type_ == "IfStatement":
            condition = fields['condition']
            then_block = fields['then_block']
            else_block = fields['else_block']
            condition = translate_expression(condition, stack_translate, binary_translate)
            then_block, function_names  = translate(then_block, declared_variables, function_names)
            else_block, function_names  = translate(else_block, declared_variables, function_names)
            instruction = f"{condition}[{then_block},{else_block}]"
        if type_ == "WhileLoop":
            condition = fields['condition']
            body = fields['body']
            condition = translate_expression(condition, stack_translate, binary_translate)
            body, function_names = translate(body, declared_variables, function_names)
            instruction = f"{condition}({body})"
        if type_ == "BreakLoop":
            instruction = "."
        if type_ == "PrintStatement":
            text = repr(fields['text'])[1:-1]
            instruction = "{"+text+"}"
        output.append(instruction)
    translated = ''.join(output)
    if return_funcs:
        return translated, function_names
    return translated