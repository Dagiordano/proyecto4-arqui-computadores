#!/usr/bin/env python3
"""
Compilador para expresiones matemáticas - Versión Completa y Funcional
Genera código assembly ASUA compatible
Soporta operadores: +, -, *, /, %
Con manejo correcto de números negativos y detección de overflow
"""

import sys
from typing import List, Tuple


class Compilador:
    def __init__(self):
        self.lines_count = 0
        self.memory_accesses = 0
        self.assembly_code = []
        self.variables = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        self.temp_counter = 0
        self.op_id_counter = 0
        
    def reset(self):
        self.lines_count = 0
        self.memory_accesses = 0
        self.assembly_code = []
        self.temp_counter = 0
        self.op_id_counter = 0
        
    def add_instruction(self, instruction: str):
        self.assembly_code.append(instruction)
        self.lines_count += 1
    
    def get_temp_var(self) -> str:
        temp = f"v_temp{self.temp_counter}"
        self.temp_counter += 1
        return temp
    
    def add_error_check(self):
        """Agrega verificación de error después de operaciones críticas"""
        self.add_instruction("MOV A, (v_error)")
        self.add_instruction("CMP A, 1")
        self.add_instruction("JEQ end_program")
        self.memory_accesses += 1
    
    def tokenize_expression(self, expression: str) -> List[str]:
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
                i += 1
            else:
                raise Exception(f"Error: Carácter no válido '{c}' en posición {i}")
        
        if paren_count != 0:
            raise Exception("Error: Paréntesis no balanceados")
        
        if not tokens:
            raise Exception("Error: Expresión vacía")
        
        return tokens
    
    def shunting_yard(self, tokens: List[str]) -> List[str]:
        output = []
        operators = []
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2}
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token in self.variables:
                output.append(token)
            elif token in precedence:
                if token in '+-' and (i == 0 or tokens[i-1] == '(' or tokens[i-1] in '+-*/%'):
                    if i + 1 >= len(tokens):
                        raise Exception(f"Error: Operador '{token}' sin operando")
                    next_token = tokens[i + 1]
                    if next_token not in self.variables and next_token != '(':
                        raise Exception(f"Error: Signo unario '{token}' seguido de token inválido")
                    if token == '-':
                        output.append('0')
                        operators.append('-')
                    i += 1
                    continue
                
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
                operators.pop()
            
            i += 1
        
        while operators:
            if operators[-1] == '(':
                raise Exception("Error: Paréntesis de apertura sin cierre")
            output.append(operators.pop())
        
        return output

    def generate_absolute_value(self, source: str, result: str) -> List[str]:
        """Genera código para calcular valor absoluto"""
        code = []
        op_id = self.op_id_counter
        self.op_id_counter += 1
        
        code.append(f"MOV A, ({source})")
        code.append(f"AND A, 128")
        code.append(f"CMP A, 128")
        code.append(f"JNE positive_{op_id}")
        
        code.append(f"MOV A, ({source})")
        code.append(f"XOR A, 255")
        code.append(f"ADD A, 1")
        code.append(f"MOV ({result}), A")
        code.append(f"JMP abs_end_{op_id}")
        
        code.append(f"positive_{op_id}:")
        code.append(f"MOV A, ({source})")
        code.append(f"MOV ({result}), A")
        
        code.append(f"abs_end_{op_id}:")
        return code

    def check_overflow_addition(self, op1: str, op2: str, result_temp: str) -> List[str]:
        """Verifica overflow en suma"""
        op_id = self.op_id_counter
        self.op_id_counter += 1
        
        code = []
        code.append(f"MOV A, ({op1})")
        code.append(f"MOV B, ({op2})")
        
        code.append(f"AND A, 128")
        code.append(f"AND B, 128")
        code.append(f"OR A, B")
        code.append(f"CMP A, 0")
        code.append(f"JEQ check_positive_overflow_{op_id}")
        
        code.append(f"MOV A, ({op1})")
        code.append(f"MOV B, ({op2})")
        code.append(f"AND A, 128")
        code.append(f"AND B, 128")
        code.append(f"CMP A, 128")
        code.append(f"JNE no_overflow_{op_id}")
        code.append(f"CMP B, 128")
        code.append(f"JNE no_overflow_{op_id}")
        
        code.append(f"MOV A, ({result_temp})")
        code.append(f"AND A, 128")
        code.append(f"CMP A, 0")
        code.append(f"JEQ overflow_detected_{op_id}")
        code.append(f"JMP no_overflow_{op_id}")
        
        code.append(f"check_positive_overflow_{op_id}:")
        code.append(f"MOV A, ({result_temp})")
        code.append(f"AND A, 128")
        code.append(f"CMP A, 128")
        code.append(f"JEQ overflow_detected_{op_id}")
        code.append(f"JMP no_overflow_{op_id}")
        
        code.append(f"overflow_detected_{op_id}:")
        code.append(f"MOV A, 1")
        code.append(f"MOV (v_error), A")
        code.append(f"MOV A, 0")
        code.append(f"MOV ({result_temp}), A")
        
        code.append(f"no_overflow_{op_id}:")
        return code

    def check_overflow_subtraction(self, op1: str, op2: str, result_temp: str) -> List[str]:
        """Verifica overflow en resta"""
        op_id = self.op_id_counter
        self.op_id_counter += 1
        
        code = []
        code.append(f"MOV A, ({op1})")
        code.append(f"MOV B, ({op2})")
        
        code.append(f"AND A, 128")
        code.append(f"AND B, 128")
        
        code.append(f"CMP A, 0")
        code.append(f"JNE check_neg_pos_{op_id}")
        code.append(f"CMP B, 128")
        code.append(f"JNE no_overflow_{op_id}")
        
        code.append(f"MOV A, ({result_temp})")
        code.append(f"AND A, 128")
        code.append(f"CMP A, 128")
        code.append(f"JEQ overflow_detected_{op_id}")
        code.append(f"JMP no_overflow_{op_id}")
        
        code.append(f"check_neg_pos_{op_id}:")
        code.append(f"CMP A, 128")
        code.append(f"JNE no_overflow_{op_id}")
        code.append(f"CMP B, 0")
        code.append(f"JNE no_overflow_{op_id}")
        
        code.append(f"MOV A, ({result_temp})")
        code.append(f"AND A, 128")
        code.append(f"CMP A, 0")
        code.append(f"JEQ overflow_detected_{op_id}")
        code.append(f"JMP no_overflow_{op_id}")
        
        code.append(f"overflow_detected_{op_id}:")
        code.append(f"MOV A, 1")
        code.append(f"MOV (v_error), A")
        code.append(f"MOV A, 0")
        code.append(f"MOV ({result_temp}), A")
        
        code.append(f"no_overflow_{op_id}:")
        return code

    def generate_multiplication_signed(self, var1: str, var2: str) -> List[str]:
        """Multiplicación con signo usando valores absolutos"""
        op_id = self.op_id_counter
        self.op_id_counter += 1
        
        code = []
        result_temp = self.get_temp_var()
        counter_temp = self.get_temp_var()
        sign_temp = self.get_temp_var()
        abs1_temp = self.get_temp_var()
        abs2_temp = self.get_temp_var()
        
        # Determinar signo del resultado
        code.append(f"MOV A, (v_{var1})")
        code.append(f"AND A, 128")
        code.append(f"MOV B, (v_{var2})")
        code.append(f"AND B, 128")
        code.append(f"XOR A, B")
        code.append(f"MOV ({sign_temp}), A")
        
        # Calcular valores absolutos
        abs_code1 = self.generate_absolute_value(f"v_{var1}", abs1_temp)
        code.extend(abs_code1)
        
        abs_code2 = self.generate_absolute_value(f"v_{var2}", abs2_temp)
        code.extend(abs_code2)
        
        # Multiplicación de valores absolutos
        code.append(f"MOV A, 0")
        code.append(f"MOV ({result_temp}), A")
        code.append(f"MOV A, ({abs2_temp})")
        code.append(f"MOV ({counter_temp}), A")
        
        code.append(f"loop_mul_{op_id}:")
        code.append(f"MOV A, ({counter_temp})")
        code.append(f"CMP A, 0")
        code.append(f"JEQ end_mul_{op_id}")
        
        code.append(f"MOV A, ({result_temp})")
        code.append(f"ADD A, ({abs1_temp})")
        
        # Verificar overflow
        code.append(f"AND A, 128")
        code.append(f"CMP A, 128")
        code.append(f"JEQ overflow_mul_{op_id}")
        
        code.append(f"MOV A, ({result_temp})")
        code.append(f"ADD A, ({abs1_temp})")
        code.append(f"MOV ({result_temp}), A")
        
        code.append(f"MOV A, ({counter_temp})")
        code.append(f"SUB A, 1")
        code.append(f"MOV ({counter_temp}), A")
        code.append(f"JMP loop_mul_{op_id}")
        
        code.append(f"overflow_mul_{op_id}:")
        code.append(f"MOV A, 1")
        code.append(f"MOV (v_error), A")
        code.append(f"MOV A, 0")
        code.append(f"MOV ({result_temp}), A")
        code.append(f"JMP end_mul_{op_id}")
        
        code.append(f"end_mul_{op_id}:")
        
        # Aplicar signo si no hay error
        code.append(f"MOV A, (v_error)")
        code.append(f"CMP A, 1")
        code.append(f"JEQ skip_sign_{op_id}")
        
        code.append(f"MOV A, ({sign_temp})")
        code.append(f"CMP A, 0")
        code.append(f"JEQ mul_positive_{op_id}")
        
        code.append(f"MOV A, ({result_temp})")
        code.append(f"XOR A, 255")
        code.append(f"ADD A, 1")
        code.append(f"MOV ({result_temp}), A")
        
        code.append(f"mul_positive_{op_id}:")
        code.append(f"MOV A, ({result_temp})")
        
        code.append(f"skip_sign_{op_id}:")
        return code

    def generate_division_signed(self, var1: str, var2: str) -> List[str]:
        """División con signo usando valores absolutos"""
        op_id = self.op_id_counter
        self.op_id_counter += 1
        
        code = []
        result_temp = self.get_temp_var()
        remainder_temp = self.get_temp_var()
        sign_temp = self.get_temp_var()
        abs1_temp = self.get_temp_var()
        abs2_temp = self.get_temp_var()
        
        # Verificar división por cero
        code.append(f"MOV A, (v_{var2})")
        code.append(f"CMP A, 0")
        code.append(f"JEQ div_error_{op_id}")
        
        # Determinar signo del resultado
        code.append(f"MOV A, (v_{var1})")
        code.append(f"AND A, 128")
        code.append(f"MOV B, (v_{var2})")
        code.append(f"AND B, 128")
        code.append(f"XOR A, B")
        code.append(f"MOV ({sign_temp}), A")
        
        # Calcular valores absolutos
        abs_code1 = self.generate_absolute_value(f"v_{var1}", abs1_temp)
        code.extend(abs_code1)
        
        abs_code2 = self.generate_absolute_value(f"v_{var2}", abs2_temp)
        code.extend(abs_code2)
        
        # División de valores absolutos
        code.append(f"MOV A, 0")
        code.append(f"MOV ({result_temp}), A")
        code.append(f"MOV A, ({abs1_temp})")
        code.append(f"MOV ({remainder_temp}), A")
        
        code.append(f"div_loop_{op_id}:")
        code.append(f"MOV A, ({remainder_temp})")
        code.append(f"MOV B, ({abs2_temp})")
        code.append(f"CMP A, B")
        code.append(f"JLT div_end_{op_id}")
        
        code.append(f"SUB A, B")
        code.append(f"MOV ({remainder_temp}), A")
        
        code.append(f"MOV A, ({result_temp})")
        code.append(f"ADD A, 1")
        code.append(f"MOV ({result_temp}), A")
        code.append(f"JMP div_loop_{op_id}")
        
        code.append(f"div_end_{op_id}:")
        
        # Aplicar signo si no hay error
        code.append(f"MOV A, (v_error)")
        code.append(f"CMP A, 1")
        code.append(f"JEQ div_done_{op_id}")
        
        code.append(f"MOV A, ({sign_temp})")
        code.append(f"CMP A, 0")
        code.append(f"JEQ div_positive_{op_id}")
        
        code.append(f"MOV A, ({result_temp})")
        code.append(f"XOR A, 255")
        code.append(f"ADD A, 1")
        code.append(f"MOV ({result_temp}), A")
        
        code.append(f"div_positive_{op_id}:")
        code.append(f"MOV A, ({result_temp})")
        code.append(f"JMP div_done_{op_id}")
        
        code.append(f"div_error_{op_id}:")
        code.append(f"MOV A, 1")
        code.append(f"MOV (v_error), A")
        code.append(f"MOV A, 0")
        code.append(f"MOV ({result_temp}), A")
        
        code.append(f"div_done_{op_id}:")
        return code

    def generate_modulo_signed(self, var1: str, var2: str) -> List[str]:
        """Módulo que siempre retorna valor positivo (comportamiento Python)"""
        op_id = self.op_id_counter
        self.op_id_counter += 1
        
        code = []
        result_temp = self.get_temp_var()
        abs2_temp = self.get_temp_var()
        
        # Verificar módulo por cero
        code.append(f"MOV A, (v_{var2})")
        code.append(f"CMP A, 0")
        code.append(f"JEQ mod_error_{op_id}")
        
        # Calcular valor absoluto del divisor
        abs_code = self.generate_absolute_value(f"v_{var2}", abs2_temp)
        code.extend(abs_code)
        
        # Calcular módulo
        code.append(f"MOV A, (v_{var1})")
        code.append(f"MOV ({result_temp}), A")
        
        # Si es negativo, hacerlo positivo sumando múltiplos del divisor
        code.append(f"mod_adjust_{op_id}:")
        code.append(f"MOV A, ({result_temp})")
        code.append(f"AND A, 128")
        code.append(f"CMP A, 128")
        code.append(f"JNE mod_calc_{op_id}")
        code.append(f"MOV A, ({result_temp})")
        code.append(f"ADD A, ({abs2_temp})")
        code.append(f"MOV ({result_temp}), A")
        code.append(f"JMP mod_adjust_{op_id}")
        
        # Calcular módulo por resta repetida
        code.append(f"mod_calc_{op_id}:")
        code.append(f"MOV A, ({result_temp})")
        code.append(f"MOV B, ({abs2_temp})")
        code.append(f"CMP A, B")
        code.append(f"JLT mod_done_{op_id}")
        
        code.append(f"SUB A, B")
        code.append(f"MOV ({result_temp}), A")
        code.append(f"JMP mod_calc_{op_id}")
        
        code.append(f"mod_done_{op_id}:")
        code.append(f"MOV A, ({result_temp})")
        code.append(f"JMP mod_end_{op_id}")
        
        code.append(f"mod_error_{op_id}:")
        code.append(f"MOV A, 1")
        code.append(f"MOV (v_error), A")
        code.append(f"MOV A, 0")
        code.append(f"MOV ({result_temp}), A")
        
        code.append(f"mod_end_{op_id}:")
        return code
    
    def compile_postfix(self, postfix: List[str]) -> None:
        stack = []
        
        for token in postfix:
            if token in self.variables:
                # Cargar variable
                self.add_instruction(f"MOV A, (v_{token})")
                self.memory_accesses += 1
                temp = self.get_temp_var()
                self.add_instruction(f"MOV ({temp}), A")
                self.memory_accesses += 1
                stack.append(temp)
                self.add_error_check()
                
            elif token == '0':
                # Constante cero
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
                
                # Realizar suma
                self.add_instruction(f"MOV A, ({op1})")
                self.memory_accesses += 1
                self.add_instruction(f"ADD A, ({op2})")
                self.memory_accesses += 1
                
                # Guardar resultado
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                
                # Verificar overflow
                overflow_check = self.check_overflow_addition(op1, op2, result_temp)
                for line in overflow_check:
                    self.add_instruction(line)
                
                stack.append(result_temp)
                self.add_error_check()
                
            elif token == '-':
                if len(stack) < 2:
                    raise Exception("Error: Operador '-' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                
                # Realizar resta
                self.add_instruction(f"MOV A, ({op1})")
                self.memory_accesses += 1
                self.add_instruction(f"SUB A, ({op2})")
                self.memory_accesses += 1
                
                # Guardar resultado
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                
                # Verificar overflow
                overflow_check = self.check_overflow_subtraction(op1, op2, result_temp)
                for line in overflow_check:
                    self.add_instruction(line)
                
                stack.append(result_temp)
                self.add_error_check()
                
            elif token == '*':
                if len(stack) < 2:
                    raise Exception("Error: Operador '*' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                
                var1 = op1.replace('v_', '') if op1.startswith('v_') else op1
                var2 = op2.replace('v_', '') if op2.startswith('v_') else op2
                
                # Generar multiplicación con signo
                mul_code = self.generate_multiplication_signed(var1, var2)
                for line in mul_code:
                    self.add_instruction(line)
                
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                stack.append(result_temp)
                self.add_error_check()
                
            elif token == '/':
                if len(stack) < 2:
                    raise Exception("Error: Operador '/' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                
                var1 = op1.replace('v_', '') if op1.startswith('v_') else op1
                var2 = op2.replace('v_', '') if op2.startswith('v_') else op2
                
                # Generar división con signo
                div_code = self.generate_division_signed(var1, var2)
                for line in div_code:
                    self.add_instruction(line)
                
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                stack.append(result_temp)
                self.add_error_check()
                
            elif token == '%':
                if len(stack) < 2:
                    raise Exception("Error: Operador '%' requiere dos operandos")
                op2 = stack.pop()
                op1 = stack.pop()
                
                var1 = op1.replace('v_', '') if op1.startswith('v_') else op1
                var2 = op2.replace('v_', '') if op2.startswith('v_') else op2
                
                # Generar módulo
                mod_code = self.generate_modulo_signed(var1, var2)
                for line in mod_code:
                    self.add_instruction(line)
                
                result_temp = self.get_temp_var()
                self.add_instruction(f"MOV ({result_temp}), A")
                self.memory_accesses += 1
                stack.append(result_temp)
                self.add_error_check()
        
        if len(stack) != 1:
            raise Exception("Error: Expresión inválida - resultado no único")
        
        # El resultado final está en el stack
        result = stack[0]
        self.add_instruction(f"MOV A, ({result})")
        self.memory_accesses += 1
    
    def compile(self, expression: str) -> Tuple[str, int, int]:
        self.reset()
        
        if '=' not in expression:
            raise Exception("Error: Expresión debe tener formato: result = ...")
        
        expr_part = expression.split('=', 1)[1].strip()
        
        if not expr_part:
            raise Exception("Error: Expresión vacía después del '='")
        
        try:
            tokens = self.tokenize_expression(expr_part)
            postfix = self.shunting_yard(tokens)
            
            if not postfix:
                raise Exception("Error: No hay operandos en la expresión")
            
            self.compile_postfix(postfix)
        except Exception as e:
            raise Exception(str(e))
        
        # Manejo final de resultado
        self.add_instruction("end_program:")
        self.add_instruction("MOV (v_result), A")
        self.memory_accesses += 1
        
        # Generar código completo
        full_assembly = "DATA:\n"
        for var in self.variables:
            full_assembly += f"v_{var} 0\n"
        full_assembly += "v_error 0\n"
        full_assembly += "v_result 0\n"
        
        for i in range(self.temp_counter):
            full_assembly += f"v_temp{i} 0\n"
        
        full_assembly += "\nCODE:\n"
        full_assembly += "\n".join(self.assembly_code)
        
        return full_assembly, self.lines_count, self.memory_accesses


def main():
    if len(sys.argv) < 2:
        print("Uso: python compilador_completo.py <expresión>")
        print("Ejemplo: python compilador_completo.py 'result = a + b * c - d / e + f % g'")
        print("Soporta operadores: +, -, *, /, % con manejo de signo y overflow")
        sys.exit(1)
    
    expression = sys.argv[1]
    
    try:
        compilador = Compilador()
        assembly, lines, memory = compilador.compile(expression)
        
        print(assembly)
        print(f"\nEstadísticas:")
        print(f"Líneas generadas: {lines}")
        print(f"Accesos a memoria: {memory}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()