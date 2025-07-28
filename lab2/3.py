import re

class ShuntingYardRegex:
    def __init__(self):
        self.precedence = {
            '*': 4, '+': 4, '?': 4,  # Operadores unarios (máxima precedencia)
            '.': 3,                   # Concatenación implícita
            '|': 2,                   # Alternancia
            '(': 1                    # Paréntesis (mínima precedencia en pila)
        }
        self.escape_chars = {'(', ')', '[', ']', '{', '}', '*', '+', '?', '|', '.', '\\'}

    def tokenize(self, regex):
        """Divide la expresión en tokens, manejando escapes y clases de caracteres"""
        tokens = []
        i = 0
        n = len(regex)
        
        while i < n:
            # Manejar caracteres escapados
            if regex[i] == '\\':
                if i + 1 < n:
                    tokens.append(regex[i:i+2])
                    i += 2
                else:
                    tokens.append(regex[i])
                    i += 1
                continue
                
            # Manejar clases de caracteres [a-z]
            if regex[i] == '[':
                j = i + 1
                while j < n and regex[j] != ']':
                    if regex[j] == '\\':  # Escape dentro de clase
                        j += 1
                    j += 1
                if j < n:
                    tokens.append(regex[i:j+1])
                    i = j + 1
                else:
                    raise ValueError("Clase de caracteres no cerrada")
                continue
                
            # Manejar otros tokens
            if regex[i] in self.precedence or regex[i] in {')', '}'}:
                tokens.append(regex[i])
            else:
                tokens.append(regex[i])
            i += 1
            
        return tokens

    def insert_explicit_concatenation(self, tokens):
        """Inserta operadores de concatenación explícita (.) donde sea necesario"""
        new_tokens = []
        for i in range(len(tokens)):
            if i > 0:
                prev = tokens[i-1]
                curr = tokens[i]
                
                # Condiciones para insertar concatenación
                cond1 = (prev not in ['|', '('] and curr not in ['|', '*', '+', '?', ')', '}'])
                cond2 = (prev in [')', '*', '+', '?'] and curr not in ['|', ')', '}'])
                cond3 = (prev == '}' and curr not in ['|', ')', '}'])
                
                if cond1 or cond2 or cond3:
                    new_tokens.append('.')
            
            new_tokens.append(tokens[i])
        return new_tokens

    def to_postfix(self, regex):
        """Convierte expresión infix a postfix"""
        tokens = self.tokenize(regex)
        tokens = self.insert_explicit_concatenation(tokens)
        
        output = []
        operator_stack = []
        steps = []
        
        for token in tokens:
            step_info = {
                'token': token,
                'stack': list(operator_stack),
                'output': list(output)
            }
            
            # Caso 1: Operando (carácter literal, clase, escape)
            if (token not in self.precedence and 
                token not in [')', '}'] and
                not (len(token) == 1 and token in self.escape_chars)):
                output.append(token)
                
            # Caso 2: Paréntesis de apertura
            elif token == '(':
                operator_stack.append(token)
                
            # Caso 3: Paréntesis de cierre
            elif token == ')':
                while operator_stack and operator_stack[-1] != '(':
                    output.append(operator_stack.pop())
                if not operator_stack:
                    raise ValueError("Paréntesis no balanceados")
                operator_stack.pop()  # Eliminar '('
                
            # Caso 4: Operador
            else:
                while (operator_stack and 
                       operator_stack[-1] != '(' and
                       self.precedence.get(operator_stack[-1], 0) >= self.precedence.get(token, 0)):
                    output.append(operator_stack.pop())
                operator_stack.append(token)
            
            steps.append(step_info)
        
        # Paso final: vaciar la pila
        while operator_stack:
            if operator_stack[-1] == '(':
                raise ValueError("Paréntesis no balanceados")
            output.append(operator_stack.pop())
            steps.append({
                'token': '',
                'stack': list(operator_stack),
                'output': list(output)
            })
        
        return ' '.join(output), steps

    def process_file(self, filename):
        """Procesa un archivo con expresiones regulares"""
        try:
            with open(filename, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    print(f"\n--- Expresión {line_num}: {line} ---")
                    try:
                        postfix, steps = self.to_postfix(line)
                        
                        print("\nPasos de conversión:")
                        for i, step in enumerate(steps, 1):
                            print(f"Paso {i}: Token='{step['token']}'")
                            print(f"  Pila: {step['stack']}")
                            print(f"  Salida: {step['output']}")
                            print("-" * 40)
                            
                        print(f"\nResultado postfix: {postfix}")
                        
                    except ValueError as e:
                        print(f"Error: {str(e)}")
                    except Exception as e:
                        print(f"Error inesperado: {str(e)}")
                        
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo '{filename}'")
        except Exception as e:
            print(f"Error al procesar archivo: {str(e)}")

if __name__ == "__main__":
    import sys
    converter = ShuntingYardRegex()
    input_file = sys.argv[1] if len(sys.argv) > 1 else "expresiones.txt"
    converter.process_file(input_file)