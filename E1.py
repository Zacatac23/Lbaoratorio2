import re
import sys
import os
import subprocess
import tempfile

class ASTNode:
    def __init__(self, value, left=None, right=None, node_type="operand"):
        self.value = value
        self.left = left
        self.right = right
        self.node_type = node_type
        self.id = None

class GuaranteedPNGRegexToAST:
    def __init__(self):
        self.precedence = {
            '*': 4, '+': 4, '?': 4,
            '.': 3,
            '|': 2,
            '(': 1
        }
        self.node_counter = 0
        
        # Verificar múltiples métodos para generar PNG
        self.png_methods = []
        self._test_png_methods()

    def _test_png_methods(self):
        """Prueba diferentes métodos para generar PNG"""
        print("🔍 PROBANDO MÉTODOS PARA GENERAR PNG...")
        
        # Método 1: Graphviz Python module
        try:
            import graphviz
            
            # Test básico
            test_dot = graphviz.Digraph()
            test_dot.node('A', 'Test')
            
            # Probar renderizado
            try:
                test_file = tempfile.mktemp()
                test_dot.render(test_file, format='png', cleanup=False)
                if os.path.exists(f'{test_file}.png'):
                    os.remove(f'{test_file}.png')
                    self.png_methods.append('graphviz_module')
                    print("✅ Método 1: Módulo graphviz Python")
            except:
                pass
                
        except ImportError:
            pass
        
        # Método 2: Subprocess directo con dot
        try:
            result = subprocess.run(
                ['dot', '-Tpng'], 
                input='digraph test { A -> B; }',
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                self.png_methods.append('subprocess_direct')
                print("✅ Método 2: Subprocess directo")
        except:
            pass
        
        # Método 3: Archivo temporal + dot
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.dot', delete=False) as f:
                f.write('digraph test { A -> B; }')
                temp_dot = f.name
            
            temp_png = temp_dot.replace('.dot', '.png')
            result = subprocess.run(['dot', '-Tpng', temp_dot, '-o', temp_png], 
                                  capture_output=True, timeout=5)
            
            if result.returncode == 0 and os.path.exists(temp_png):
                self.png_methods.append('temp_file')
                print("✅ Método 3: Archivo temporal")
                os.remove(temp_png)
            
            os.remove(temp_dot)
        except:
            pass
        
        if not self.png_methods:
            print("❌ No se encontraron métodos válidos para PNG")
        else:
            print(f"🎯 {len(self.png_methods)} métodos disponibles para PNG")

    def expand_extensions(self, regex):
        """Expande + y ? correctamente"""
        print(f"\n{'='*60}")
        print("🔄 EXPANDIENDO EXTENSIONES")
        print(f"{'='*60}")
        print(f"Original: {regex}")
        
        expanded = regex
        changes = []
        
        # Expandir a? → (a|ε) primero
        i = 0
        while i < len(expanded):
            if i > 0 and expanded[i] == '?':
                if expanded[i-1] == ')':
                    # Encontrar paréntesis correspondiente
                    paren_count = 1
                    j = i - 2
                    while j >= 0 and paren_count > 0:
                        if expanded[j] == ')':
                            paren_count += 1
                        elif expanded[j] == '(':
                            paren_count -= 1
                        j -= 1
                    j += 1
                    operand = expanded[j:i]
                    new_expanded = expanded[:j] + f"({operand}|ε)" + expanded[i+1:]
                    changes.append(f"  {operand}? → ({operand}|ε)")
                    expanded = new_expanded
                    i = j + len(f"({operand}|ε)") - 1
                else:
                    operand = expanded[i-1]
                    new_expanded = expanded[:i-1] + f"({operand}|ε)" + expanded[i+1:]
                    changes.append(f"  {operand}? → ({operand}|ε)")
                    expanded = new_expanded
                    i = i - 1 + len(f"({operand}|ε)") - 1
            i += 1
        
        # Expandir a+ → aa*
        i = 0
        while i < len(expanded):
            if i > 0 and expanded[i] == '+':
                if expanded[i-1] == ')':
                    paren_count = 1
                    j = i - 2
                    while j >= 0 and paren_count > 0:
                        if expanded[j] == ')':
                            paren_count += 1
                        elif expanded[j] == '(':
                            paren_count -= 1
                        j -= 1
                    j += 1
                    operand = expanded[j:i]
                    new_expanded = expanded[:j] + f"{operand}{operand}*" + expanded[i+1:]
                    changes.append(f"  {operand}+ → {operand}{operand}*")
                    expanded = new_expanded
                    i = j + len(f"{operand}{operand}*") - 1
                else:
                    operand = expanded[i-1]
                    new_expanded = expanded[:i-1] + f"{operand}{operand}*" + expanded[i+1:]
                    changes.append(f"  {operand}+ → {operand}{operand}*")
                    expanded = new_expanded
                    i = i - 1 + len(f"{operand}{operand}*") - 1
            i += 1
        
        if changes:
            print("Cambios realizados:")
            for change in changes:
                print(change)
        else:
            print("No hay extensiones que expandir")
        
        print(f"Expandida: {expanded}")
        return expanded

    def tokenize(self, regex):
        """Tokeniza la expresión"""
        tokens = []
        i = 0
        
        while i < len(regex):
            char = regex[i]
            if char == '\\' and i + 1 < len(regex):
                tokens.append(regex[i:i+2])
                i += 2
            elif char == '[':
                j = i
                while j < len(regex) and regex[j] != ']':
                    j += 1
                tokens.append(regex[i:j+1])
                i = j + 1
            else:
                tokens.append(char)
                i += 1
        
        return tokens

    def insert_concatenation(self, tokens):
        """Inserta concatenación explícita"""
        new_tokens = []
        
        for i in range(len(tokens)):
            if i > 0:
                prev, curr = tokens[i-1], tokens[i]
                
                if (prev not in ['|', '('] and 
                    curr not in ['|', '*', '+', '?', ')']):
                    new_tokens.append('.')
                elif (prev in [')', '*', '+', '?'] and 
                      curr not in ['|', ')', '*', '+', '?']):
                    new_tokens.append('.')
            
            new_tokens.append(tokens[i])
        
        return new_tokens

    def to_postfix(self, regex):
        """Convierte a postfix usando Shunting Yard"""
        expanded = self.expand_extensions(regex)
        tokens = self.tokenize(expanded)
        tokens = self.insert_concatenation(tokens)
        
        print(f"\n🔄 CONVERSIÓN A POSTFIX")
        print(f"Tokens finales: {tokens}")
        
        output = []
        stack = []
        
        for token in tokens:
            if token not in self.precedence and token != ')':
                output.append(token)
            elif token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                if stack:
                    stack.pop()
            else:
                while (stack and stack[-1] != '(' and
                       self.precedence.get(stack[-1], 0) >= 
                       self.precedence.get(token, 0)):
                    output.append(stack.pop())
                stack.append(token)
        
        while stack:
            output.append(stack.pop())
        
        postfix = ' '.join(output)
        print(f"Postfix: {postfix}")
        return output

    def postfix_to_ast(self, tokens):
        """Construye AST desde postfix"""
        print(f"\n🌳 CONSTRUYENDO AST")
        
        stack = []
        self.node_counter = 0
        
        for token in tokens:
            self.node_counter += 1
            
            if token in ['*', '+', '?']:
                if not stack:
                    raise ValueError(f"Operador unario {token} sin operando")
                child = stack.pop()
                node = ASTNode(token, left=child, node_type="unary_op")
                node.id = self.node_counter
                stack.append(node)
                
            elif token in ['|', '.']:
                if len(stack) < 2:
                    raise ValueError(f"Operador binario {token} necesita 2 operandos")
                right = stack.pop()
                left = stack.pop()
                node = ASTNode(token, left=left, right=right, node_type="binary_op")
                node.id = self.node_counter
                stack.append(node)
                
            else:
                node = ASTNode(token, node_type="operand")
                node.id = self.node_counter
                stack.append(node)
        
        if len(stack) != 1:
            raise ValueError("Error en construcción del AST")
        
        print("✅ AST construido exitosamente")
        return stack[0]

    def generate_dot_code(self, root):
        """Genera código DOT para Graphviz"""
        dot_code = ['digraph AST {']
        dot_code.append('  rankdir=TB;')
        dot_code.append('  size="10,8";')
        dot_code.append('  dpi=150;')
        dot_code.append('  node [shape=circle, style=filled, fontname="Arial", fontsize=14];')
        
        # Colores
        colors = {
            'operand': '"#E3F2FD"',      # Azul claro
            'unary_op': '"#E8F5E8"',     # Verde claro
            'binary_op': '"#FFEBEE"'     # Rojo claro
        }
        
        def add_node(node):
            if not node:
                return
            
            # Formatear etiqueta
            label = node.value
            if label == '.':
                label = 'CONCAT'
            elif label == '|':
                label = 'OR'
            elif label == 'ε':
                label = 'ε'
            
            color = colors.get(node.node_type, '"white"')
            dot_code.append(f'  {node.id} [label="{label}", fillcolor={color}];')
            
            if node.left:
                dot_code.append(f'  {node.id} -> {node.left.id};')
                add_node(node.left)
            
            if node.right:
                dot_code.append(f'  {node.id} -> {node.right.id};')
                add_node(node.right)
        
        add_node(root)
        dot_code.append('}')
        return '\n'.join(dot_code)

    def create_png_guaranteed(self, root, filename):
        """Crea PNG usando el mejor método disponible"""
        print(f"\n🖼️ GENERANDO PNG: {filename}")
        
        if not self.png_methods:
            print(".")
            return False
        
        dot_code = self.generate_dot_code(root)
        
        # Intentar métodos en orden de preferencia
        for method in self.png_methods:
            try:
                success = False
                
                if method == 'graphviz_module':
                    import graphviz
                    dot = graphviz.Source(dot_code)
                    dot.render(filename, format='png', cleanup=True)
                    success = os.path.exists(f'{filename}.png')
                
                elif method == 'subprocess_direct':
                    result = subprocess.run(
                        ['dot', '-Tpng'],
                        input=dot_code,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        with open(f'{filename}.png', 'wb') as f:
                            f.write(result.stdout.encode('latin1'))
                        success = True
                
                elif method == 'temp_file':
                    # Crear archivo DOT temporal
                    dot_file = f'{filename}.dot'
                    with open(dot_file, 'w') as f:
                        f.write(dot_code)
                    
                    # Convertir a PNG
                    result = subprocess.run(
                        ['dot', '-Tpng', dot_file, '-o', f'{filename}.png'],
                        capture_output=True,
                        timeout=10
                    )
                    
                    success = result.returncode == 0 and os.path.exists(f'{filename}.png')
                    
                    # Limpiar archivo DOT
                    if os.path.exists(dot_file):
                        os.remove(dot_file)
                
                if success:
                    print(f"✅ PNG creado exitosamente con método: {method}")
                    print(f"📁 Archivo: {filename}.png")
                    return True
                    
            except Exception as e:
                print(f"⚠️ Método {method} falló: {e}")
                continue
        
        # Si todos los métodos fallan, guardar código DOT
        try:
            with open(f'{filename}.dot', 'w') as f:
                f.write(dot_code)
            print(f"💾 Código DOT guardado: {filename}.dot")
            print("   Puedes convertir manualmente: dot -Tpng {filename}.dot -o {filename}.png")
        except Exception as e:
            print(f"❌ Error guardando DOT: {e}")
        
        return False

    def create_ascii_tree(self, root):
        """Visualización ASCII"""
        print(f"\n🎨 VISUALIZACIÓN ASCII")
        print("═" * 50)
        
        def print_tree(node, prefix="", is_last=True, is_root=True):
            if not node:
                return
            
            symbols = {
                'operand': '🔵',
                'unary_op': '🟢', 
                'binary_op': '🔴'
            }
            
            display = node.value
            if display == '.':
                display = 'CONCAT'
            elif display == '|':
                display = 'OR'
            elif display == 'ε':
                display = 'EPSILON'
            
            symbol = symbols.get(node.node_type, '⚪')
            
            if is_root:
                print(f"🌳 Root: {symbol} {display}")
                child_prefix = ""
            else:
                connector = "└── " if is_last else "├── "
                print(f"{prefix}{connector}{symbol} {display}")
                child_prefix = prefix + ("    " if is_last else "│   ")
            
            children = []
            if node.left:
                children.append(node.left)
            if node.right:
                children.append(node.right)
            
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                print_tree(child, child_prefix, is_last_child, False)
        
        print_tree(root)

    def process_expression(self, regex, expr_num):
        """Procesa una expresión completa"""
       
        print(f"EXPRESIÓN {expr_num}: {regex}")
      

        
        try:
            # Convertir a postfix
        
            postfix_tokens = self.to_postfix(regex)
            
            # Construir AST
            ast_root = self.postfix_to_ast(postfix_tokens)
            
            # Generar PNG
            png_success = self.create_png_guaranteed(ast_root, f"ast_expr_{expr_num}")
            
            # Mostrar ASCII siempre
            self.create_ascii_tree(ast_root)
            
            return ast_root, png_success
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None, False

    def run_demo(self):
        """Ejecuta la demostración completa"""
        expressions = [
            "(a*|b*)+",
            "((ε|a)|b*)*",
            "(a|b)*abb(a|b)*",
            "0?(1?)?0*"
        ]
        
        
        results = []
        png_count = 0
        
        for i, expr in enumerate(expressions, 1):
            ast, png_success = self.process_expression(expr, i)
            results.append((expr, ast is not None, png_success))
            if png_success:
                png_count += 1
            
            if i < len(expressions):
                input(f"\n⏸️  Presiona Enter para continuar...")
        
        # Resumen final
        print(f"\n🎉 RESUMEN FINAL")
        print("=" * 50)
        successful = sum(1 for _, success, _ in results if success)
        print(f"✅ Expresiones procesadas: {successful}/{len(expressions)}")
    
        
        print(f"\n📁 ARCHIVOS GENERADOS:")
        for i in range(1, len(expressions) + 1):
            png_file = f"ast_expr_{i}.png"
            dot_file = f"ast_expr_{i}.dot"
            
            if os.path.exists(png_file):
                size = os.path.getsize(png_file)
                print(f"🖼️ {png_file} ({size} bytes)")
            elif os.path.exists(dot_file):
                print(f"💾 {dot_file} (convertir con: dot -Tpng {dot_file} -o {png_file})")

def main():
    converter = GuaranteedPNGRegexToAST()
    if converter.png_methods:
        print(f"🚀 Listo para generar PNG con {len(converter.png_methods)} métodos")
    else:
        print("⚠️ PNG no disponible, pero continuaremos con ASCII")
    
    converter.run_demo()

if __name__ == "__main__":
    main()