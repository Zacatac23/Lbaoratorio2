def check_balance(line):
    stack = []
    steps = []
    balanced = True
    i = 0
    n = len(line)
    
    while i < n and balanced:
        char = line[i]
        
        # Manejar caracteres escapados
        if char == '\\':
            i += 2  # Saltar el carácter escapado
            continue
            
        # Verificar símbolos de apertura
        if char in '([{':
            stack.append(char)
            steps.append(f"Push '{char}': Stack = {stack}")
            i += 1
            
        # Verificar símbolos de cierre
        elif char in ')]}':
            if not stack:
                balanced = False
                steps.append(f"Error: '{char}' sin símbolo de apertura")
            else:
                top = stack.pop()
                if (char == ')' and top == '(') or \
                   (char == ']' and top == '[') or \
                   (char == '}' and top == '{'):
                    steps.append(f"Pop '{char}': Stack = {stack}")
                    i += 1
                else:
                    balanced = False
                    steps.append(f"Error: '{char}' no coincide con '{top}'")
                    
        # Ignorar otros caracteres
        else:
            i += 1
    
    # Verificar si quedan símbolos sin cerrar
    if balanced and stack:
        balanced = False
        steps.append(f"Error: Símbolos sin cerrar: {stack}")
    
    return balanced, steps

def main():
    import sys
    filename = sys.argv[1] if len(sys.argv) > 1 else "input.txt"
    
    try:
        with open(filename, 'r') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                print(f"\n--- Línea {line_num}: {line} ---")
                balanced, steps = check_balance(line)
                
                for step in steps:
                    print(step)
                
                print(f"Balanceado: {'Sí' if balanced else 'No'}")
                
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{filename}'")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")

if __name__ == "__main__":
    main()