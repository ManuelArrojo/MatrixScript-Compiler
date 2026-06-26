import re
import sys

# ==========================================
# FASE 1: ANÁLISIS LÉXICO (TOKENIZACIÓN)
# ==========================================
TOKENS_REGEX = [
    ('COMMENT_BLOCK', r'/\*.*?\*/'),      # Comentarios de bloque
    ('COMMENT_LINE',  r'//.*'),           # Comentarios de línea única
    ('LBRACKET',      r'\['),             # Apertura de matriz/fila
    ('RBRACKET',      r'\]'),             # Cierre de matriz/fila
    ('LPAREN',        r'\('),             # Paréntesis izquierdo para funciones
    ('RPAREN',        r'\)'),             # Paréntesis derecho para funciones
    ('COMMA',         r','),              # Separador de elementos/filas
    ('ASSIGN',        r'='),              # Operador de asignación
    ('SEMI',          r';'),              # Delimitador de instrucción
    
    # Palabras reservadas obligatorias de MatrixScript
    ('KW_MATRIZ',     r'\bmatriz\b'),
    ('KW_TRANSPONER', r'\btransponer\b'),
    ('KW_DET',        r'\bdet\b'),
    ('KW_MULT',       r'\bmult\b'),
    ('KW_SUMA',       r'\bsuma\b'),
    ('KW_IMPRIMIR',   r'\bimprimir\b'),
    
    # Identificadores y literales
    ('ID',            r'[a-zA-Z_][a-zA-Z0-9_]*'),
    ('NUMERAL',       r'-?[0-9]+(\.[0-9]+)?'),    # Soporta enteros, reales y negativos
    ('WHITESPACE',    r'[ \t\r\n]+'),             # Espacios y saltos
    ('MISMATCH',      r'.')                       # Cualquier otro carácter erróneo
]

class Token:
    def __init__(self, type, value, line, column):
        self.type = type
        self.value = value
        self.line = line
        self.column = column

class Lexer:
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.tokenize()

    def tokenize(self):
        line_num = 1
        line_start = 0
        pos = 0
        while pos < len(self.code):
            match = None
            for token_type, regex in TOKENS_REGEX:
                pattern = re.compile(regex, re.DOTALL if token_type == 'COMMENT_BLOCK' else 0)
                match = pattern.match(self.code, pos)
                if match:
                    value = match.group(0)
                    column = pos - line_start + 1
                    
                    if token_type == 'MISMATCH':
                        print(f"Error léxico [línea {line_num}, columna {column}]: carácter inesperado '{value}'")
                    elif token_type not in ['WHITESPACE', 'COMMENT_BLOCK', 'COMMENT_LINE']:
                        self.tokens.append(Token(token_type, value, line_num, column))
                    
                    line_breaks = value.count('\n')
                    if line_breaks > 0:
                        line_num += line_breaks
                        line_start = pos + len(value) - value.rfind('\n') - 1
                    
                    pos = match.end()
                    break
        self.tokens.append(Token('EOF', '', line_num, pos - line_start + 1))


# ==========================================
# FASE 2: ANÁLISIS SINTÁCTICO Y AST
# ==========================================
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = 0

    def current(self):
        return self.tokens[self.pos]

    def consume(self, expected_type):
        if self.current().type == expected_type:
            tok = self.current()
            self.pos += 1
            return tok
        else:
            tok = self.current()
            print(f"Error sintáctico [línea {tok.line}, columna {tok.column}]: se esperaba '{expected_type}' y se encontró '{tok.value}'")
            self.errors += 1
            self.panic_mode_sync()
            return None

    def panic_mode_sync(self):
        # Sincronización en puntos clave del lenguaje
        sync_tokens = ['SEMI', 'KW_MATRIZ', 'KW_IMPRIMIR', 'EOF']
        while self.current().type not in sync_tokens:
            self.pos += 1
        if self.current().type == 'SEMI':
            self.pos += 1

    def parse_program(self):
        ast = []
        while self.current().type != 'EOF':
            if self.current().type == 'KW_MATRIZ':
                ast.append(self.parse_declaracion())
            elif self.current().type == 'KW_IMPRIMIR':
                ast.append(self.parse_impresion())
            else:
                # Omitir tokens inesperados fuera de lugar para evitar bucles
                self.pos += 1 
        return ast

    def parse_declaracion(self):
        self.consume('KW_MATRIZ')
        id_node = self.consume('ID')
        self.consume('ASSIGN')
        expr = self.parse_expression()
        self.consume('SEMI')
        return {
            'tipo': 'declaracion', 
            'id': id_node.value if id_node else '?', 
            'expr': expr,
            'line': id_node.line if id_node else 0
        }

    def parse_impresion(self):
        self.consume('KW_IMPRIMIR')
        expr = self.parse_expression()
        self.consume('SEMI')
        return {'tipo': 'imprimir', 'expr': expr}

    def parse_expression(self):
        curr = self.current()
        if curr.type == 'LBRACKET':
            return self.parse_literal_matriz()
        elif curr.type == 'ID':
            self.pos += 1
            return {'tipo': 'variable', 'id': curr.value, 'line': curr.line}
        elif curr.type in ['KW_TRANSPONER', 'KW_DET']:
            func_type = curr.value
            self.pos += 1
            self.consume('LPAREN')
            arg = self.parse_expression()
            self.consume('RPAREN')
            return {'tipo': 'unario', 'operacion': func_type, 'argumento': arg, 'line': curr.line}
        elif curr.type in ['KW_MULT', 'KW_SUMA']:
            func_type = curr.value
            self.pos += 1
            self.consume('LPAREN')
            arg1 = self.parse_expression()
            self.consume('COMMA')
            arg2 = self.parse_expression()
            self.consume('RPAREN')
            return {'tipo': 'binario', 'operacion': func_type, 'arg1': arg1, 'arg2': arg2, 'line': curr.line}
        else:
            print(f"Error sintáctico [línea {curr.line}, columna {curr.column}]: expresión inválida '{curr.value}'")
            self.errors += 1
            return {'tipo': 'error'}

    def parse_literal_matriz(self):
        # Estructura: [[1, 2], [3, 4]]
        line = self.current().line
        self.consume('LBRACKET')
        filas = []
        
        # Leer primera fila obligatoria o vacía
        if self.current().type == 'LBRACKET':
            filas.append(self.parse_fila())
            while self.current().type == 'COMMA':
                self.consume('COMMA')
                filas.append(self.parse_fila())
                
        self.consume('RBRACKET')
        return {'tipo': 'literal_matriz', 'valores': filas, 'line': line}

    def parse_fila(self):
        self.consume('LBRACKET')
        elementos = []
        if self.current().type == 'NUMERAL':
            elementos.append(float(self.current().value))
            self.pos += 1
            while self.current().type == 'COMMA':
                self.consume('COMMA')
                if self.current().type == 'NUMERAL':
                    elementos.append(float(self.current().value))
                    self.pos += 1
        self.consume('RBRACKET')
        return elementos


# ==========================================
# FASE 3: ANÁLISIS SEMÁNTICO
# ==========================================
class SemanticAnalyzer:
    def __init__(self, ast):
        self.ast = ast
        self.errors = 0
        self.tabla_simbolos = {} # Guarda pares: id -> ('matriz', (filas, columnas))

    def analyze(self):
        for node in self.ast:
            if not node:
                continue
            if node['tipo'] == 'declaracion':
                self.analyze_declaracion(node)
            elif node['tipo'] == 'imprimir':
                self.evaluate_expr_type(node['expr'])

    def analyze_declaracion(self, node):
        var_id = node['id']
        expr_info = self.evaluate_expr_type(node['expr'])
        
        if expr_info:
            tipo_retorno, dims = expr_info
            if tipo_retorno == 'numero':
                print(f"Error semántico [línea {node['line']}]: No se puede asignar un resultado de tipo 'numero' (escalar) a la variable de tipo matriz '{var_id}'.")
                self.errors += 1
            else:
                self.tabla_simbolos[var_id] = ('matriz', dims)

    def evaluate_expr_type(self, expr):
        if expr['tipo'] == 'error':
            return None
            
        if expr['tipo'] == 'literal_matriz':
            filas = expr['valores']
            if not filas:
                return ('matriz', (0, 0))
            
            # Regla Semántica: Matrices rectangulares bien formadas
            longitud_esperada = len(filas[0])
            for idx, fila in enumerate(filas):
                if len(fila) != longitud_esperada:
                    print(f"Error semántico [línea {expr['line']}]: Matriz mal formada. La fila {idx + 1} tiene longitud {len(fila)} pero se esperaba {longitud_esperada}.")
                    self.errors += 1
                    return None
            return ('matriz', (len(filas), longitud_esperada))

        elif expr['tipo'] == 'variable':
            var_id = expr['id']
            if var_id not in self.tabla_simbolos:
                print(f"Error semántico [línea {expr['line']}]: La variable '{var_id}' no ha sido declarada.")
                self.errors += 1
                return None
            return self.tabla_simbolos[var_id]

        elif expr['tipo'] == 'unario':
            op = expr['operacion']
            arg_info = self.evaluate_expr_type(expr['argumento'])
            if not arg_info:
                return None
            
            tipo, dims = arg_info
            if tipo != 'matriz':
                print(f"Error semántico [línea {expr['line']}]: Operación '{op}' requiere un argumento de tipo 'matriz'.")
                self.errors += 1
                return None
                
            if op == 'transponer':
                return ('matriz', (dims[1], dims[0]))
                
            elif op == 'det':
                # Regla Semántica: Determinante solo en matrices cuadradas
                if dims[0] != dims[1]:
                    print(f"Error semántico [línea {expr['line']}]: No se puede calcular el determinante de '{op}'; la matriz no es cuadrada (dimensiones: {dims[0]}x{dims[1]}).")
                    self.errors += 1
                    return None
                return ('numero', None) # Devuelve un escalar

        elif expr['tipo'] == 'binario':
            op = expr['operacion']
            inf1 = self.evaluate_expr_type(expr['arg1'])
            inf2 = self.evaluate_expr_type(expr['arg2'])
            if not inf1 or not inf2:
                return None
                
            t1, d1 = inf1
            t2, d2 = inf2
            
            if t1 != 'matriz' or t2 != 'matriz':
                print(f"Error semántico [línea {expr['line']}]: La operación '{op}' requiere que ambos operandos sean matrices.")
                self.errors += 1
                return None

            if op == 'suma':
                if d1 != d2:
                    print(f"Error semántico [línea {expr['line']}]: Dimensiones incompatibles para la suma: {d1[0]}x{d1[1]} y {d2[0]}x{d2[1]}.")
                    self.errors += 1
                    return None
                return ('matriz', d1)
                
            elif op == 'mult':
                # Regla Semántica: Columnas de A == Filas de B
                if d1[1] != d2[0]:
                    print(f"Error semántico [línea {expr['line']}]: No se pueden multiplicar una matriz {d1[0]}x{d1[1]} con una {d2[0]}x{d2[1]}: dimensiones incompatibles.")
                    self.errors += 1
                    return None
                return ('matriz', (d1[0], d2[1]))

        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            source = f.read()
        print("--- Fase 1: Lexer ---")
        lexer = Lexer(source)
        print("--- Fase 2: Parser ---")
        parser = Parser(lexer.tokens)
        ast = parser.parse_program()
        if parser.errors == 0:
            print("--- Fase 3: Semántica ---")
            semantic = SemanticAnalyzer(ast)
            semantic.analyze()
            if semantic.errors == 0:
                print("Compilación Exitosa")
    else:
        print("Uso: python MatrixScript.py <archivo_de_prueba.mat>")