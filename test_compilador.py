#!/usr/bin/env python3
"""
Script de prueba para el compilador
"""

import subprocess
import sys


def test_compilador(expression, expected_lines_min=None, expected_memory_min=None):
    """Prueba el compilador con una expresión"""
    print(f"\n{'='*60}")
    print(f"Probando: {expression}")
    print('='*60)
    
    result = subprocess.run(
        [sys.executable, 'compilador.py', expression],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}")
        return False
    
    print(result.stdout)
    
    # Extraer estadísticas
    lines = None
    memory = None
    for line in result.stdout.split('\n'):
        if 'Líneas generadas:' in line:
            lines = int(line.split(':')[1].strip())
        if 'Accesos a memoria:' in line:
            memory = int(line.split(':')[1].strip())
    
    if expected_lines_min and lines and lines > expected_lines_min:
        print(f"ADVERTENCIA: Se generaron {lines} líneas, se esperaba máximo {expected_lines_min}")
    
    if expected_memory_min and memory and memory > expected_memory_min:
        print(f"ADVERTENCIA: Se realizaron {memory} accesos a memoria, se esperaba máximo {expected_memory_min}")
    
    return True


def main():
    """Ejecuta todas las pruebas"""
    print("Ejecutando pruebas del compilador...")
    
    tests = [
        ("result = a + b", 5, 3),
        ("result = a - b", 5, 3),
        ("result = a + b - c", 7, 4),
        ("result = a + b + c + d", 9, 5),
        ("result = (a + b) - c", 7, 4),
        ("result = a + (b - c)", 7, 4),
        ("result = a + b - c + (d - e)", 11, 6),
        ("result = a + b - c + (d - e) + f", 13, 7),
    ]
    
    passed = 0
    failed = 0
    
    for expr, max_lines, max_memory in tests:
        if test_compilador(expr, max_lines, max_memory):
            passed += 1
        else:
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"Resumen: {passed} pruebas pasadas, {failed} fallidas")
    print('='*60)


if __name__ == "__main__":
    main()

