import sys
from lexer import tokenize
from parser import Parser
from translator import translate

def main():
    print("Brainknot Interactive Compiler")
    print("How to use:")
    print(" - Enter Brainknot code line by line.")
    print(" - Press Enter on an empty line to compile and run the code you entered so far.")
    print(" - Type 'exit' to quit the interactive compiler.\n")
    buffer = []
    prompt = ""
    while True:
        try:
            line = input(prompt)
            if line.strip().lower() == 'exit':
                print("Exiting.")
                break
            if line.strip() == "":
                if buffer:
                    source = "\n".join(buffer)
                    buffer.clear()

                    # Lexical analysis
                    tokens = tokenize(source)
                    print("Tokens:", tokens)

                    # Parsing
                    parser = Parser(tokens)
                    ast = parser.parse_program()
                    print("AST:", ast)

                    # Translation
                    output = translate(parser=parser)
                    print("Output:", output)
                    print("Brainknot Interactive Compiler")
                    print("How to use:")
                    print(" - Enter Brainknot code line by line.")
                    print(" - Press Enter on an empty line to compile and run the code you entered so far.")
                    print(" - Type 'exit' to quit the interactive compiler.\n")
                prompt = ""
            else:
                buffer.append(line)
                prompt = ""
        except Exception as e:
            print("Error:", e, file=sys.stderr)
            buffer.clear()
            prompt = ""

if __name__ == "__main__":
    main()