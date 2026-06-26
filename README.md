# MatrixScript Compiler (Front-End)

## Descripción General
Este repositorio contiene la implementación completa de un **Analizador de Tres Fases (Compiler Front-End)** para el Lenguaje de Dominio Específico (DSL) denominado **MatrixScript**. El lenguaje ha sido diseñado con el propósito de declarar, validar y realizar operaciones algebraicas bidimensionales (matrices) garantizando la consistencia dimensional de manera estática.

El compilador está desarrollado enteramente en **Python puro (versión 3.8+)** utilizando exclusivamente la librería estándar del lenguaje, cumpliendo con las directrices académicas de la asignatura de **Compiladores** para el 3er año de la Licenciatura en Ciencias de la Computación.

---

## Arquitectura del Compilador

El sistema se compone de tres etapas modulares acopladas linealmente dentro de `MatrixScript.py`:

1. **Análisis Léxico (Lexer):** Tokeniza el flujo de entrada basándose en expresiones regulares y reporta errores posicionales con número de línea y columna.
2. **Análisis Sintáctico (Parser):** Construye un Árbol de Sintaxis Abstracta (AST) utilizando la técnica de *Descendencia Recurrente* e incorpora un sistema de recuperación de errores sintácticos mediante el **Modo Pánico** (sincronizando en delimitadores de instrucciones `;`).
3. **Análisis Semántico (Semantic Analyzer):** Administra la Tabla de Símbolos global y ejecuta la comprobación de tipos y el chequeo estricto de restricciones dimensionales algebraicas.

---

## Características y Reglas Semánticas del DSL

El compilador valida estáticamente las siguientes reglas propias del dominio de álgebra lineal:
* **Matrices Bien Formadas:** Cada fila de un literal matricial debe contener exactamente la misma cantidad de elementos numéricos que las demás.
* **Compatibilidad de Multiplicación:** La operación `mult(A, B)` requiere estrictamente que el número de columnas de la matriz izquierda (`A`) sea igual al número de filas de la matriz derecha (`B`).
* **Restricción de Determinante Cuadrado:** La función `det(A)` solo es válida si se invoca sobre una matriz cuadrada (donde el conteo de filas y columnas coincide).
* **Asignación de Tipos Primitivos:** Se impide la asignación de un escalar (tipo `numero`, retornado por el determinante) a un identificador inicializado como `matriz`.

---

## Estructura del Repositorio

```text
MatrixScript-Compiler/
│
├── MatrixScript.py              # Código fuente unificado del compilador
├── prueba_valida.mat            # Caso de prueba sin errores (Compilación Exitosa)
├── prueba_error_sintactico.mat  # Caso de prueba con fallos sintácticos (Modo Pánico)
├── prueba_error_semantico.mat   # Caso de prueba con violaciones algebraicas
└── README.md                    # Documentación del repositorio
