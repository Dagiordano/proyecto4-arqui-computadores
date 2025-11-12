#!/usr/bin/env python3
"""
Compilador para expresiones matemáticas
Genera código assembly ASUA compatible
Versión parcial: solo operadores + y -
"""

import sys
from typing import List, Tuple


class Compilador:
    def __init__(self):
        self.lines_count = 0
        self.memory_accesses = 0
        self.assembly_code = []
        self.variables = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        
    def reset(self):
        """Reinicia los contadores para una nueva compilación"""
        self.lines_count = 0
        self.memory_accesses = 0
        self.assembly_code = []
    
    def add_instruction(self, instruction: str):
        """Agrega una instrucción al código assembly"""
        self.assembly_code.append(instruction)
        self.lines_count += 1
    
    def parse_expression(self, expression: str) -> List:
        """Parsea una expresión matemática en tokens"""
        # Limpiar espacios
        expression = expression.replace(' ', '')
        
        # Tokenizar: variables, operadores, paréntesis
        tokens = []
        i = 0
        while i < len(expression):
            if expression[i] in '+-()':
                tokens.append(expression[i])
                i += 1
            elif expression[i] in 'abcdefg':
                # Variable válida (a-g)
                tokens.append(expression[i])
                i += 1
            else:
                raise Exception(f"Carácter no válido en la expresión: {expression[i]}")
        
        return tokens
    
    def convert_to_signed_terms(self, tokens: List[str]) -> List[Tuple[str, int]]:
        """Convierte tokens en una lista de términos con signo"""
        terms = []
        sign_stack = [1]  # Pila de signos
        current_sign = 1   # Signo actual antes de una variable
        
        for token in tokens:
            if token in self.variables:
                # Calcular el signo total para esta variable
                total_sign = current_sign * sign_stack[-1]
                terms.append((token, total_sign))
                current_sign = 1  # Resetear signo después de una variable
            elif token == '+':
                current_sign = 1
            elif token == '-':
                current_sign = -1
            elif token == '(':
                # Al encontrar '(', actualizamos la pila
                new_sign = current_sign * sign_stack[-1]
                sign_stack.append(new_sign)
                current_sign = 1  # Resetear signo después de '('
            elif token == ')':
                sign_stack.pop()
                # No resetear current_sign después de ')'
        
        return terms
    
    def compile(self, expression: str) -> Tuple[str, int, int]:
        """
        Compila una expresión matemática a código assembly
        
        Args:
            expression: Expresión en formato "result = ..."
        
        Returns:
            Tupla con (código assembly, líneas generadas, accesos a memoria)
        """
        self.reset()
        
        # Extraer la expresión del lado derecho
        if '=' not in expression:
            raise Exception("Expresión debe tener formato: result = ...")
        
        expr_part = expression.split('=', 1)[1].strip()
        
        # Parsear y convertir a términos con signo
        tokens = self.parse_expression(expr_part)
        terms = self.convert_to_signed_terms(tokens)
        
        if not terms:
            raise Exception("No hay términos en la expresión")
        
        # Generar código assembly optimizado
        first_term, first_sign = terms[0]
        
        # Cargar el primer término en A
        self.add_instruction(f"MOV A, ({first_term})")
        self.memory_accesses += 1
        
        # Si el primer término es negativo, necesitamos negarlo
        if first_sign == -1:
            self.add_instruction("MOV B, A")
            self.add_instruction("MOV A, 0")
            self.add_instruction("SUB A, B")
        
        # Procesar los términos restantes
        for term, sign in terms[1:]:
            if sign == 1:
                self.add_instruction(f"ADD A, ({term})")
                self.memory_accesses += 1
            else:
                self.add_instruction(f"SUB A, ({term})")
                self.memory_accesses += 1
        
        # Almacenar resultado
        self.add_instruction("MOV (result), A")
        self.memory_accesses += 1
        
        # Generar código completo
        code = "; Compilado automáticamente\n"
        code += "DATA:\n"
        for var in self.variables:
            code += f"{var} 0\n"
        code += "error 0\n"
        code += "result 0\n"
        code += "\nCODE:\n"
        code += "\n".join(self.assembly_code)
        
        return code, self.lines_count, self.memory_accesses


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python compilador.py <expresión>")
        print("Ejemplo: python compilador.py 'result = a + b - c + (d - e) + f'")
        sys.exit(1)
    
    expression = sys.argv[1]
    
    try:
        compilador = Compilador()
        assembly, lines, memory = compilador.compile(expression)
        
        print(assembly)
        print(f"\n; Estadísticas:")
        print(f"; Líneas generadas: {lines}")
        print(f"; Accesos a memoria: {memory}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()