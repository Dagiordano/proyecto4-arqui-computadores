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
    
    def tokenize_expression(self, expression: str) -> List[str]:
        """Convierte una expresión en una lista de tokens"""
        tokens = []
        i = 0
        while i < len(expression):
            c = expression[i]
            if c in '+-()':
                tokens.append(c)
                i += 1
            elif c in 'abcdefg':
                tokens.append(c)
                i += 1
            elif c.isspace():
                # Ignorar espacios
                i += 1
            else:
                raise Exception(f"Carácter no válido en la expresión: {c}")
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
        
        # Tokenizar y convertir a términos con signo
        tokens = self.tokenize_expression(expr_part)
        terms = self.convert_to_signed_terms(tokens)
        
        # Separar términos positivos y negativos
        positives = [var for var, sign in terms if sign == 1]
        negatives = [var for var, sign in terms if sign == -1]
        
        # Generar código optimizado usando solo registros A y B
        if positives:
            # Cargar el primer término positivo en A
            first_var = positives[0]
            self.add_instruction(f"MOV A, (v_{first_var})")
            self.memory_accesses += 1
            
            # Sumar los términos positivos restantes
            for var in positives[1:]:
                self.add_instruction(f"ADD A, (v_{var})")
                self.memory_accesses += 1
            
            # Restar los términos negativos
            for var in negatives:
                self.add_instruction(f"SUB A, (v_{var})")
                self.memory_accesses += 1
        else:
            # No hay términos positivos, empezar con 0
            self.add_instruction("MOV A, 0")
            
            # Restar todos los términos negativos
            for var in negatives:
                self.add_instruction(f"SUB A, (v_{var})")
                self.memory_accesses += 1
        
        # Almacenar el resultado
        self.add_instruction("MOV (v_result), A")
        self.memory_accesses += 1
        
        
        # Generar código completo con secciones DATA y CODE
        full_assembly = "; Valores iniciales (cambiar por los valores reales)\n"
        full_assembly += "DATA:\n"
        for var in self.variables:
            full_assembly += f"v_{var} 0\n"
        full_assembly += "v_error 0\n"
        full_assembly += "v_result 0\n"
        full_assembly += "\nCODE:\n"
        full_assembly += "\n".join(self.assembly_code)
        
        return full_assembly, self.lines_count, self.memory_accesses


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python compilador.py <expresión>")
        print("Ejemplo: python compilador.py 'result = a + b - c'")
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