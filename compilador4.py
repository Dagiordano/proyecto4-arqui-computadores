#!/usr/bin/env python3
"""
Compilador para expresiones matemáticas
Genera código assembly ASUA compatible
Soporta operadores: +, -, *, /, %
Usa solo registros A y B
"""

import sys
from typing import List, Tuple


class Compilador:
    def __init__(self):
        self.lines_count = 0
        self.memory_accesses = 0
        self.assembly_code = []
        self.variables = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        self.temp_counter = 0  # Contador para variables temporales
        self.op_id_counter = 0  # Contador para IDs únicos de operaciones
        
    def reset(self):
        """Reinicia los contadores para una nueva compilación"""
        self.lines_count = 0
        self.memory_accesses = 0
        self.assembly_code = []
        self.temp_counter = 0
        self.op_id_counter = 0
        
    def add_instruction(self, instruction: str):
        """Agrega una instrucción al código assembly"""
        self.assembly_code.append(instruction)
        self.lines_count += 1
    
    def get_temp_var(self) -> str:
        """Obtiene el nombre de una variable temporal"""
        temp = f"v_temp{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def tokenize_expression(self, expression: str) -> List[str]:
        """Convierte una expresión en una lista de tokens con detección de errores"""
        tokens = []
        i = 0
        paren_count = 0
        
        while i < len(expression):
            c = expression[i]
            if c in '+-*/%()':
                if c == '(':
                    paren_count += 1
                elif c == ')':
                    paren_count -= 1
                    if paren_count < 0:
                        raise Exception(f"Error: Paréntesis de cierre sin apertura en posición {i}")
                tokens.append(c)
                i += 1
            elif c in 'abcdefg':
                tokens.append(c)
                i += 1
            elif c.isspace():
                # Ignorar espacios
                i += 1
            else:
                raise Exception(f"Error: Carácter no válido '{c}' en posición {i}")
        
        if paren_count != 0:
            raise Exception("Error: Paréntesis no balanceados")
        
        if not tokens:
            raise Exception("Error: Expresión vacía")
        
        # Validar que no haya operadores consecutivos (excepto signos unarios)
        for i in range(len(tokens) - 1):
            if tokens[i] in '*/%' and tokens[i+1] in '*/%+-':
                raise Exception(f"Error: Operadores consecutivos inválidos: '{tokens[i]}' seguido de '{tokens[i+1]}'")
            if tokens[i] in '+-*/%' and tokens[i+1] == ')':
                raise Exception(f"Error: Operador '{tokens[i]}' seguido de ')'")
            if tokens[i] == '(' and tokens[i+1] in '*/%':
                raise Exception(f"Error: '(' seguido de operador '{tokens[i+1]}'")
        
        return tokens
    
    def shunting_yard(self, tokens: List[str]) -> List[str]:
        """Convierte expresión infija a postfija usando algoritmo Shunting Yard"""
        output = []
        operators = []
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2}
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token in self.variables:
                output.append(token)
            elif token in precedence:
                # Manejar signos unarios (si es el primer token o después de '(' u operador)
                if token in '+-' and (i == 0 or tokens[i-1] == '(' or tokens[i-1] in '+-*/%'):
                    # Es un signo unario, lo tratamos como parte del siguiente operando
                    if i + 1 >= len(tokens):
                        raise Exception(f"Error: Operador '{token}' sin operando")
                    next_token = tokens[i + 1]
                    if next_token not in self.variables and next_token != '(':
                        raise Exception(f"Error: Signo unario '{token}' seguido de token inválido")
                    # Para signos unarios, agregamos un 0 antes
                    if token == '-':
                        output.append('0')
                        operators.append('-')
                    # Si es '+', simplemente lo ignoramos
                    i += 1
                    continue
                
                # Operador binario
                while (operators and operators[-1] != '(' and 
                       precedence.get(operators[-1], 0) >= precedence[token]):
                    output.append(operators.pop())
                operators.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    output.append(operators.pop())
                if not operators:
                    raise Exception("Error: Paréntesis de cierre sin apertura")
                operators.pop()  # Remover '('
            
            i += 1
        
        while operators:
            if operators[-1] == '(':
                raise Exception("Error: Paréntesis de apertura sin cierre")
            output.append(operators.pop())
        
        return output
    
    def generate_multiplication(self, var1: str, var2: str) -> List[str]:
        """Genera código assembly para multiplicación usando solo A y B"""
        # Multiplicación: resultado = 0; for i in range(var2): resultado += var1
        op_id = self.op_id_counter
        self.op_id_counter += 1
        temp_result = self.get_temp_var()
        temp_counter = self.get_temp_var()
        
        code = []
        # Inicializar resultado en 0
        code.append(f"MOV A, 0")
        code.append(f"MOV ({temp_result}), A")
        
        # Cargar var2 en B (contador)
        code.append(f"MOV B, (v_{var2})")
        code.append(f"MOV ({temp_counter}), B")
        
        # Etiqueta de inicio del loop
        loop_start = f"loop_mul_{op_id}"
        code.append(f"{loop_start}:")
        
        # Verificar si contador es 0
        code.append(f"MOV A, ({temp_counter})")
        code.append(f"CMP A, 0")
        code.append(f"JEQ end_mul_{op_id}")
        
        # Sumar var1 al resultado
        code.append(f"MOV A, ({temp_result})")
        code.append(f"ADD A, (v_{var1})")
        code.append(f"MOV ({temp_result}), A")
        
        # Decrementar contador
        code.append(f"MOV A, ({temp_counter})")
        code.append(f"SUB A, 1")
        code.append(f"MOV ({temp_counter}), A")
        
        # Saltar al inicio del loop
        code.append(f"JMP {loop_start}")
        code.append(f"end_mul_{op_id}:")
        
        # Cargar resultado en A
        code.append(f"MOV A, ({temp_result})")
        
        return code
    
    def generate_division(self, var1: str, var2: str) -> List[str]:
        """Genera código assembly para división usando solo A y B"""
        # División: resultado = 0; while var1 >= var2: var1 -= var2; resultado += 1
        op_id = self.op_id_counter
        self.op_id_counter += 1
        temp_dividend = self.get_temp_var()
        temp_result = self.get_temp_var()
        
        code = []
        
        # Verificar división por cero
        code.append(f"MOV A, (v_{var2})")
        code.append(f"CMP A, 0")
        code.append(f"JEQ div_error_{op_id}")
        
        # Inicializar resultado en 0
        code.append(f"MOV A, 0")
        code.append(f"MOV ({temp_result}), A")
        
        # Cargar var1 (dividendo) en variable temporal
        code.append(f"MOV A, (v_{var1})")
        code.append(f"MOV ({temp_dividend}), A")
        
        # Etiqueta de inicio del loop
        loop_start = f"loop_div_{op_id}"
        code.append(f"{loop_start}:")
        
        # Verificar si dividendo >= divisor
        code.append(f"MOV A, ({temp_dividend})")
        code.append(f"MOV B, (v_{var2})")
        code.append(f"CMP A, B")
        code.append(f"JLT end_div_{op_id}")
        
        # Restar divisor del dividendo
        code.append(f"SUB A, B")
        code.append(f"MOV ({temp_dividend}), A")
        
        # Incrementar resultado
        code.append(f"MOV A, ({temp_result})")
        code.append(f"ADD A, 1")
        code.append(f"MOV ({temp_result}), A")
        
        # Saltar al inicio del loop
        code.append(f"JMP {loop_start}")
        code.append(f"end_div_{op_id}:")
        
        # Cargar resultado en A
        code.append(f"MOV A, ({temp_result})")
        code.append(f"JMP div_end_{op_id}")
        
        # Manejo de error de división por cero
        code.append(f"div_error_{op_id}:")
        code.append(f"MOV A, 0")
        code.append(f"MOV (v_error), 1")  # Marcar error
        code.append(f"div_end_{op_id}:")
        
        return code
    
    def generate_modulo(self, var1: str, var2: str) -> List[str]:
        """Genera código assembly para módulo usando solo A y B"""
        # Módulo: while var1 >= var2: var1 -= var2; resultado = var1
        op_id = self.op_id_counter
        self.op_id_counter += 1
        temp_dividend = self.get_temp_var()
        
        code = []
        
        # Verificar división por cero
        code.append(f"MOV A, (v_{var2})")
        code.append(f"CMP A, 0")
        code.append(f"JEQ mod_error_{op_id}")
        
        # Cargar var1 (dividendo) en variable temporal
        code.append(f"MOV A, (v_{var1})")
        code.append(f"MOV ({temp_dividend}), A")
        
        # Etiqueta de inicio del loop
        loop_start = f"loop_mod_{op_id}"
        code.append(f"{loop_start}:")
        
        # Verificar si dividendo >= divisor
        code.append(f"MOV A, ({temp_dividend})")
        code.append(f"MOV B, (v_{var2})")
        code.append(f"CMP A, B")
        code.append(f"JLT end_mod_{op_id}")
        
        # Restar divisor del dividendo
        code.append(f"SUB A, B")
        code.append(f"MOV ({temp_dividend}), A")
        
        # Saltar al inicio del loop
        code.append(f"JMP {loop_start}")
        code.append(f"end_mod_{op_id}:")
        
        # Cargar resultado (resto) en A
        code.append(f"MOV A, ({temp_dividend})")
        code.append(f"JMP mod_end_{op_id}")
        
        # Manejo de error de división por cero
        code.append(f"mod_error_{op_id}:")
        code.append(f"MOV A, 0")
        code.append(f"MOV (v_error), 1")  # Marcar error
        code.append(f"mod_end_{op_id}:")
        
        return code
    
    def compile_postfix(self, postfix: List[str]) -> None:
        """Compila una expresión en notación postfija a assembly usando solo A y B"""
        stack = []
        
        for token in postfix:
            if token in self.variables:
                # Cargar variable en A
                self.add_instruction(f"MOV A, (v_{token})")
                self.memory_accesses += 1
                # Guardar en stack (usando variable temporal)
                temp = self.get_temp_var()
                self.add_instruction(f"MOV ({temp}), A")
                self.memory_accesses += 1
                stack.append(temp)
            elif token == '0':
                # Constante cero (para signos unarios)
                temp = self.get_temp_var()
                self.add_instruction(f"MOV A, 0")
                self.add_instruction(f"MOV ({temp}), A")
                self.memory_accesses += 1
                stack.append(temp)
            elif token == '+':
                if len(stack) < 2:
                    raise Exception("Error: Operador '+' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                # Cargar op1 en A
                self.add_instruction(f"MOV A, ({op1})")
                self.memory_accesses += 1
                # Sumar op2
                self.add_instruction(f"ADD A, ({op2})")
                self.memory_accesses += 1
                # Guardar resultado
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                stack.append(result_temp)
            elif token == '-':
                if len(stack) < 2:
                    raise Exception("Error: Operador '-' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                # Cargar op1 en A
                self.add_instruction(f"MOV A, ({op1})")
                self.memory_accesses += 1
                # Restar op2
                self.add_instruction(f"SUB A, ({op2})")
                self.memory_accesses += 1
                # Guardar resultado
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                stack.append(result_temp)
            elif token == '*':
                if len(stack) < 2:
                    raise Exception("Error: Operador '*' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                # Usar las variables directamente (ya tienen prefijo v_)
                # Extraer nombres sin prefijo para las funciones de generación
                var1 = op1.replace('v_', '') if op1.startswith('v_') else op1
                var2 = op2.replace('v_', '') if op2.startswith('v_') else op2
                
                # Generar código de multiplicación
                mul_code = self.generate_multiplication(var1, var2)
                for line in mul_code:
                    self.add_instruction(line)
                
                # Guardar resultado
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                stack.append(result_temp)
            elif token == '/':
                if len(stack) < 2:
                    raise Exception("Error: Operador '/' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                # Extraer nombres sin prefijo para las funciones de generación
                var1 = op1.replace('v_', '') if op1.startswith('v_') else op1
                var2 = op2.replace('v_', '') if op2.startswith('v_') else op2
                
                # Generar código de división
                div_code = self.generate_division(var1, var2)
                for line in div_code:
                    self.add_instruction(line)
                
                # Guardar resultado
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                stack.append(result_temp)
            elif token == '%':
                if len(stack) < 2:
                    raise Exception("Error: Operador '%' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                # Extraer nombres sin prefijo para las funciones de generación
                var1 = op1.replace('v_', '') if op1.startswith('v_') else op1
                var2 = op2.replace('v_', '') if op2.startswith('v_') else op2
                
                # Generar código de módulo
                mod_code = self.generate_modulo(var1, var2)
                for line in mod_code:
                    self.add_instruction(line)
                
                # Guardar resultado
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                stack.append(result_temp)
        
        if len(stack) != 1:
            raise Exception("Error: Expresión inválida - resultado no único")
        
        # El resultado final está en el stack, cargarlo en A
        result = stack[0]
        self.add_instruction(f"MOV A, ({result})")
        self.memory_accesses += 1
    
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
            raise Exception("Error: Expresión debe tener formato: result = ...")
        
        expr_part = expression.split('=', 1)[1].strip()
        
        if not expr_part:
            raise Exception("Error: Expresión vacía después del '='")
        
        # Tokenizar y convertir a postfija
        try:
            tokens = self.tokenize_expression(expr_part)
            postfix = self.shunting_yard(tokens)
            
            # Validar que hay al menos un operando
            if not postfix:
                raise Exception("Error: No hay operandos en la expresión")
            
            # Compilar postfija a assembly
            self.compile_postfix(postfix)
        except Exception as e:
            raise Exception(str(e))
        
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
        
        # Agregar variables temporales
        for i in range(self.temp_counter):
            full_assembly += f"v_temp{i} 0\n"
        
        full_assembly += "\nCODE:\n"
        full_assembly += "\n".join(self.assembly_code)
        
        return full_assembly, self.lines_count, self.memory_accesses


def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python compilador3.py <expresión>")
        print("Ejemplo: python compilador3.py 'result = a + b - c'")
        print("Ejemplo: python compilador3.py 'result = a * b'")
        print("Ejemplo: python compilador3.py 'result = a / b'")
        print("Ejemplo: python compilador3.py 'result = a % b'")
        print("Soporta operadores: +, -, *, /, %")
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