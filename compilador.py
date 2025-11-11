#!/usr/bin/env python3
"""
Compilador para expresiones matemáticas
Genera código assembly ASUA compatible
Versión parcial: solo operadores + y -
"""

import re
import sys
from typing import List, Tuple, Dict


class Compilador:
    def __init__(self):
        self.lines_count = 0
        self.memory_accesses = 0
        self.registers = ['R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']
        self.next_register = 0
        self.assembly_code = []
        self.variables = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        
    def reset(self):
        """Reinicia los contadores para una nueva compilación"""
        self.lines_count = 0
        self.memory_accesses = 0
        self.next_register = 0
        self.assembly_code = []
    
    def get_register(self) -> str:
        """Obtiene el siguiente registro disponible"""
        if self.next_register >= len(self.registers):
            raise Exception("No hay más registros disponibles")
        reg = self.registers[self.next_register]
        self.next_register += 1
        return reg
    
    def add_instruction(self, instruction: str):
        """Agrega una instrucción al código assembly"""
        self.assembly_code.append(instruction)
        self.lines_count += 1
    
    def load_variable(self, var: str, reg: str):
        """Carga una variable desde memoria a un registro"""
        self.add_instruction(f"MOV {reg}, ({var})")
        self.memory_accesses += 1
    
    def store_variable(self, var: str, reg: str):
        """Almacena un registro en una variable de memoria"""
        self.add_instruction(f"MOV ({var}), {reg}")
        self.memory_accesses += 1
    
    def add_operation(self, reg1: str, reg2: str, op: str):
        """Realiza una operación entre dos registros"""
        if op == '+':
            self.add_instruction(f"ADD {reg1}, {reg2}")
        elif op == '-':
            self.add_instruction(f"SUB {reg1}, {reg2}")
        else:
            raise Exception(f"Operador no soportado en versión parcial: {op}")
    
    def parse_expression(self, expression: str) -> List:
        """Parsea una expresión matemática en tokens"""
        # Limpiar espacios
        expression = expression.replace(' ', '')
        
        # Tokenizar: números, variables, operadores, paréntesis
        tokens = []
        i = 0
        while i < len(expression):
            if expression[i] in '+-*/%()':
                tokens.append(expression[i])
                i += 1
            elif expression[i].isalpha():
                # Variable o función
                var = ''
                while i < len(expression) and expression[i].isalnum():
                    var += expression[i]
                    i += 1
                tokens.append(var)
            elif expression[i].isdigit() or expression[i] == '-':
                # Número (puede ser negativo)
                num = expression[i]
                i += 1
                while i < len(expression) and expression[i].isdigit():
                    num += expression[i]
                    i += 1
                tokens.append(num)
            else:
                i += 1
        
        return tokens
    
    def shunting_yard(self, tokens: List) -> List:
        """Convierte expresión infija a postfija usando algoritmo Shunting Yard"""
        output = []
        operators = []
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2}
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token in self.variables or (token.isdigit() or (token.startswith('-') and token[1:].isdigit())):
                # Operando
                output.append(token)
            elif token in precedence:
                # Operador
                while (operators and operators[-1] != '(' and 
                       precedence.get(operators[-1], 0) >= precedence[token]):
                    output.append(operators.pop())
                operators.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                if operators and operators[-1] == '(':
                    operators.pop()
            
            i += 1
        
        while operators:
            output.append(operators.pop())
        
        return output
    
    def compile_postfix(self, postfix: List) -> str:
        """Compila una expresión en notación postfija a assembly"""
        stack = []
        
        for token in postfix:
            if token in self.variables:
                # Cargar variable
                reg = self.get_register()
                self.load_variable(token, reg)
                stack.append(reg)
            elif token.isdigit() or (token.startswith('-') and token[1:].isdigit()):
                # Constante
                reg = self.get_register()
                self.add_instruction(f"MOV {reg}, {token}")
                stack.append(reg)
            elif token in ['+', '-']:
                # Operación binaria
                if len(stack) < 2:
                    raise Exception("Expresión inválida: faltan operandos")
                reg2 = stack.pop()
                reg1 = stack.pop()
                self.add_operation(reg1, reg2, token)
                # Liberar reg2 si no es necesario
                stack.append(reg1)
        
        if len(stack) != 1:
            raise Exception("Expresión inválida: resultado no único")
        
        return stack[0]
    
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
        
        # Parsear y compilar
        tokens = self.parse_expression(expr_part)
        postfix = self.shunting_yard(tokens)
        result_reg = self.compile_postfix(postfix)
        
        # Almacenar resultado
        self.store_variable('result', result_reg)
        
        # Generar código completo con DATA section
        code = "; Valores iniciales (cambiar por los valores reales al ejecutar)\n"
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

