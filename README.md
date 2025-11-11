# Compilador de Expresiones Matemáticas

Compilador que genera código assembly ASUA compatible a partir de expresiones matemáticas.

## Versión Parcial (Entrega Parcial)

Esta versión soporta:
- ✅ Operadores: `+`, `-`
- ✅ Paréntesis para priorizar operaciones
- ✅ Variables: `a`, `b`, `c`, `d`, `e`, `f`, `g`
- ✅ Generación de código assembly optimizado
- ✅ Conteo de líneas generadas y accesos a memoria

**No incluye (para versión completa):**
- ❌ Operadores: `*`, `/`, `%`
- ❌ Funciones: `max`, `min`, `abs`
- ❌ Detección de errores (overflow, división por cero)

## Uso

### Compilar una expresión

```bash
python compilador.py "result = a + b"
```

### Ejemplos

```bash
# Expresión simple
python compilador.py "result = a + b"

# Con múltiples operaciones
python compilador.py "result = a + b - c"

# Con paréntesis
python compilador.py "result = a + (b - c)"

# Expresión compleja
python compilador.py "result = a + b - c + (d - e) + f"
```

### Ejecutar pruebas

```bash
python test_compilador.py
```

## Formato de Salida

El compilador genera código assembly con:

1. **Sección DATA**: Define todas las variables necesarias
2. **Sección CODE**: Contiene las instrucciones generadas
3. **Estadísticas**: Número de líneas generadas y accesos a memoria

### Ejemplo de salida

```
DATA:
a 0
b 0
c 0
d 0
e 0
f 0
g 0
error 0
result 0

CODE:
LOAD R0, a
LOAD R1, b
ADD R0, R1
STORE result, R0

; Líneas generadas: 4
; Accesos a memoria: 3
```

## Instrucciones Assembly Generadas

El compilador utiliza las siguientes instrucciones ASUA:

- `LOAD reg, var`: Carga una variable desde memoria a un registro
- `LOADI reg, valor`: Carga un valor inmediato a un registro
- `ADD reg1, reg2`: Suma reg2 a reg1 (reg1 = reg1 + reg2)
- `SUB reg1, reg2`: Resta reg2 de reg1 (reg1 = reg1 - reg2)
- `STORE var, reg`: Almacena un registro en una variable de memoria

## Estructura del Código

- `compilador.py`: Compilador principal
- `test_compilador.py`: Script de pruebas
- `README.md`: Esta documentación

## Algoritmo

El compilador utiliza:

1. **Parser**: Tokeniza la expresión matemática
2. **Shunting Yard**: Convierte la expresión infija a notación postfija
3. **Generación de código**: Evalúa la expresión postfija generando instrucciones assembly

## Requisitos

- Python 3.6 o superior

