import re

# =====================================================================
# PARTE 1: Analizador Sintáctico con Procesamiento Descendente Recursivo
# =====================================================================

class Atributos:
    """
    Clase equivalente a 'NoTerminal' mencionada en el documento.
    Maneja el valor numérico, el valor lógico y el indicador 'relacional'.
    """
    def __init__(self, valor=0.0, valorLogico=False, relacional=False):
        self.valor = valor
        self.valorLogico = valorLogico
        self.relacional = relacional # Controla si es resultado de una expresión relacional

    def __str__(self):
        if self.relacional:
            return str(self.valorLogico)
        return str(self.valor)

class AnalizadorRecursivo:
    def __init__(self, expr):
        # FIX: Se actualizó la expresión regular para capturar '==' correctamente y el '!' unario.
        patron = r'\d+\.\d+|\d+|==|!=|<=|>=|<|>|&|\||\+|-|\*|/|\^|\(|\)|!'
        self.tokens = re.findall(patron, expr.replace(" ", ""))
        self.pos = 0

    def actual(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else '$'

    def avanzar(self):
        self.pos += 1

    def match(self, esperado):
        if self.actual() == esperado:
            self.avanzar()
        else:
            raise Exception(f"Error Sintáctico: Se esperaba '{esperado}', se encontró '{self.actual()}'")

    # 1. <S> -> <ELO>
    def S(self):
        s = self.ELO()
        if self.actual() != '$':
            raise Exception(f"Error Sintáctico: Tokens inesperados al final: {self.actual()}")
        return s

    # 2. <ELO> -> <EL2> <ELO_L>
    def ELO(self):
        s2 = self.EL2()
        return self.ELO_L(s2)

    # 3 y 4. <ELO_L> -> | <EL2> {procOR} <ELO_L> | e
    def ELO_L(self, i1):
        if self.actual() == '|':
            self.match('|')
            s2 = self.EL2()
            
            # {procOR} - Control semántico: Validar que ambos operandos sean relacionales
            if not i1.relacional or not s2.relacional:
                raise Exception("Error Semántico: Los operandos de OR (|) deben ser expresiones relacionales (Ej: 5>3).")
            
            s_new = Atributos(valorLogico=(i1.valorLogico or s2.valorLogico), relacional=True)
            return self.ELO_L(s_new)
        return i1

    # 5. <EL2> -> <ER> <EL2_L>
    def EL2(self):
        s2 = self.ER()
        return self.EL2_L(s2)

    # 6 y 7. <EL2_L> -> & <ER> {procAND} <EL2_L> | e
    def EL2_L(self, i1):
        if self.actual() == '&':
            self.match('&')
            s2 = self.ER()
            
            # {procAND} - Control semántico: Validar que ambos operandos sean relacionales
            if not i1.relacional or not s2.relacional:
                raise Exception("Error Semántico: Los operandos de AND (&) deben ser expresiones relacionales (Ej: 5>3). La expresión '5&6' no es válida.")
            
            s_new = Atributos(valorLogico=(i1.valorLogico and s2.valorLogico), relacional=True)
            return self.EL2_L(s_new)
        return i1

    # 8. <ER> -> <E> <ER_L>
    def ER(self):
        s2 = self.E()
        return self.ER_L(s2)

    # 9 y 10. <ER_L> -> <OR> <E> {pComparar} | e
    def ER_L(self, i1):
        # FIX: Se incluye '==' en la validación en lugar de '='
        if self.actual() in ['<', '<=', '>', '>=', '==', '!=']:
            op = self.OR()
            s2 = self.E()
            
            # {pComparar} - Control semántico: Operandos deben ser aritméticos
            if i1.relacional or s2.relacional:
                raise Exception("Error Semántico: No se pueden usar operadores relacionales sobre valores booleanos consecutivos (Ej: 6>10>50 no es válido).")
            
            val1, val2 = i1.valor, s2.valor
            res = False
            if op == '<': res = (val1 < val2)
            elif op == '<=': res = (val1 <= val2)
            elif op == '>': res = (val1 > val2)
            elif op == '>=': res = (val1 >= val2)
            elif op == '==': res = (val1 == val2)
            elif op == '!=': res = (val1 != val2)
            
            return Atributos(valorLogico=res, relacional=True)
        return i1

    # 11 - 20. <OR> (Operadores relacionales)
    def OR(self):
        op = self.actual()
        if op in ['<', '<=', '>', '>=', '==', '!=']: # FIX: == corregido
            self.avanzar()
            return op
        raise Exception("Error Sintáctico: Operador relacional esperado.")

    # 21. <E> -> <T> <E_L>
    def E(self):
        s2 = self.T()
        return self.E_L(s2)

    # 22, 23 y 24. <E_L> -> + <T> {suma} <E_L> | - <T> {resta} <E_L> | e
    def E_L(self, i1):
        if self.actual() == '+':
            self.match('+')
            s2 = self.T()
            if i1.relacional or s2.relacional: raise Exception("Error Semántico: Aritmética con booleanos.")
            s_new = Atributos(valor=(i1.valor + s2.valor), relacional=False)
            return self.E_L(s_new)
        elif self.actual() == '-':
            self.match('-')
            s2 = self.T()
            if i1.relacional or s2.relacional: raise Exception("Error Semántico: Aritmética con booleanos.")
            s_new = Atributos(valor=(i1.valor - s2.valor), relacional=False)
            return self.E_L(s_new)
        return i1

    # 25. <T> -> <P> <T_L>
    def T(self):
        s2 = self.P()
        return self.T_L(s2)

    # 26, 27 y 28. <T_L> -> * <P> {mul} <T_L> | / <P> {div} <T_L> | e
    def T_L(self, i1):
        if self.actual() == '*':
            self.match('*')
            s2 = self.P()
            if i1.relacional or s2.relacional: raise Exception("Error Semántico: Aritmética con booleanos.")
            s_new = Atributos(valor=(i1.valor * s2.valor), relacional=False)
            return self.T_L(s_new)
        elif self.actual() == '/':
            self.match('/')
            s2 = self.P()
            if i1.relacional or s2.relacional: raise Exception("Error Semántico: Aritmética con booleanos.")
            s_new = Atributos(valor=(i1.valor / s2.valor), relacional=False)
            return self.T_L(s_new)
        return i1

    # 29. <P> -> <F> <P_L>
    def P(self):
        s2 = self.F()
        return self.P_L(s2)

    # 30 y 31. <P_L> -> ^ <F> {exp} <P_L> | e
    def P_L(self, i1):
        if self.actual() == '^':
            self.match('^')
            s2 = self.F()
            if i1.relacional or s2.relacional: raise Exception("Error Semántico: Aritmética con booleanos.")
            s_new = Atributos(valor=(i1.valor ** s2.valor), relacional=False)
            return self.P_L(s_new)
        return i1

    # 32, 33 y Adicional. <F> -> ( <ELO> ) | i | ! ( <ELO> )
    def F(self):
        c = self.actual()
        
        # FIX: Integración del operador lógico NOT exigido por la práctica.
        if c == '!':
            self.match('!')
            if self.actual() == '(':
                self.match('(')
                s = self.ELO()
                self.match(')')
                # Control semántico: NOT solo puede negar resultados lógicos/relacionales
                if not s.relacional:
                    raise Exception("Error Semántico: El operador NOT (!) solo se aplica a expresiones lógicas o relacionales.")
                
                # Invertir el valor lógico
                s.valorLogico = not s.valorLogico
                s.relacional = True
                return s
            else:
                raise Exception("Error Sintáctico: Se esperaba '(' después de '!' para negar una expresión.")
                
        elif c == '(':
            self.match('(')
            s = self.ELO()
            self.match(')')
            return s
            
        elif re.match(r'^\d+(\.\d+)?$', c):
            val = float(c)
            self.avanzar()
            return Atributos(valor=val, relacional=False)
            
        else:
            raise Exception(f"Error Sintáctico: Número, '!' o paréntesis esperado, se encontró '{c}'")


# =====================================================================
# PARTE 2: Analizador Sintáctico con Procesamiento Descendente No Recursivo (Pila)
# =====================================================================

class AnalizadorPila:
    # Tabla de análisis LL(1) para la gramática aritmética pura
    LL1_TABLE = {
        'S':   {'(': ['E', '{Respuesta}'], 'i': ['E', '{Respuesta}']},
        'E':   {'(': ['T', 'E_L'],         'i': ['T', 'E_L']},
        'E_L': {'+': ['+', 'T', '{suma}', 'E_L'], '-': ['-', 'T', '{resta}', 'E_L'], ')': [], '$': []},
        'T':   {'(': ['P', 'T_L'],         'i': ['P', 'T_L']},
        'T_L': {'*': ['*', 'P', '{mul}', 'T_L'],  '/': ['/', 'P', '{div}', 'T_L'],   '+': [], '-': [], ')': [], '$': []},
        'P':   {'(': ['F', 'P_L'],         'i': ['F', 'P_L']},
        'P_L': {'^': ['^', 'F', '{exp}', 'P_L'],  '*': [], '/': [], '+': [], '-': [], ')': [], '$': []},
        'F':   {'(': ['(', 'E', ')'],      'i': ['i']}
    }

    def __init__(self, expr):
        raw_tokens = re.findall(r'\d+\.\d+|\d+|\+|-|\*|/|\^|\(|\)', expr.replace(" ", ""))
        self.tokens = []
        for t in raw_tokens:
            if re.match(r'^\d+(\.\d+)?$', t):
                self.tokens.append(('i', float(t)))
            else:
                self.tokens.append((t, t))
        self.tokens.append(('$', '$'))
        self.pos = 0
        self.resultado = None

    def parse(self):
        stack = ['$', 'S']
        sem_stack = [] # Pila semántica para calcular atributos sintetizados

        while len(stack) > 0:
            top = stack.pop()
            curr_type, curr_val = self.tokens[self.pos]

            if top in self.LL1_TABLE: # Es un No Terminal
                if curr_type in self.LL1_TABLE[top]:
                    produccion = self.LL1_TABLE[top][curr_type]
                    # Insertar en la pila en orden inverso
                    for symbol in reversed(produccion):
                        stack.append(symbol)
                else:
                    raise Exception(f"Error Sintáctico en token '{curr_type}' al evaluar '{top}'.")
            
            elif top.startswith('{') and top.endswith('}'): # Es una Acción Semántica
                self.ejecutar_accion(top, sem_stack)
            
            else: # Es un Terminal
                if top == curr_type:
                    if top == 'i':
                        # Para los terminales tipo "i", se suben a la pila semántica como nodos hoja
                        v_str = str(curr_val)
                        if v_str.endswith(".0"): v_str = v_str[:-2] # Limpiar enteros formateados
                        sem_stack.append({
                            'val': curr_val,
                            'inf': v_str,
                            'pos': v_str,
                            'pre': v_str
                        })
                    self.pos += 1
                else:
                    raise Exception(f"Error Sintáctico: Esperaba terminal '{top}', encontró '{curr_type}'")

    def ejecutar_accion(self, accion, sem_stack):
        if accion == '{Respuesta}':
            self.resultado = sem_stack.pop()
            return

        # Para operaciones binarias, sacar lado derecho e izquierdo de la pila semántica
        derecho = sem_stack.pop()
        izquierdo = sem_stack.pop()

        v_izq, v_der = izquierdo['val'], derecho['val']
        inf_izq, inf_der = izquierdo['inf'], derecho['inf']
        pos_izq, pos_der = izquierdo['pos'], derecho['pos']
        pre_izq, pre_der = izquierdo['pre'], derecho['pre']

        op_str = ''
        if accion == '{suma}':
            val = v_izq + v_der
            op_str = '+'
        elif accion == '{resta}':
            val = v_izq - v_der
            op_str = '-'
        elif accion == '{mul}':
            val = v_izq * v_der
            op_str = '*'
        elif accion == '{div}':
            if v_der == 0: raise Exception("Error de División por cero.")
            val = v_izq / v_der
            op_str = '/'
        elif accion == '{exp}':
            val = v_izq ** v_der
            op_str = '^'

        # Subir los nuevos atributos computados de regreso a la pila semántica
        sem_stack.append({
            'val': round(val, 4), # Redondear para estética
            'inf': f"({inf_izq}{op_str}{inf_der})",
            'pos': f"{pos_izq} {pos_der} {op_str}",
            'pre': f"{op_str} {pre_izq} {pre_der}"
        })


# =====================================================================
# BLOQUE DE PRUEBAS PARA VALIDAR CON LOS CASOS DEL DOCUMENTO
# =====================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("   PRÁCTICA NO. 1 - LENGUAJES FORMALES Y AUTÓMATAS")
    print("=" * 60)

    print("\n[PARTE 1] Analizador Descendente Recursivo")
    print("-" * 60)
    
    # Casos descritos en la práctica PDF + Pruebas para NOT y ==
    casos_parte1 = [
        "(25.5+30.2)+50",                   # Matemático puro (Debe dar 105.7)
        "((5.5/3)+10)>20 & 20.5<10",        # PDF Relacional (Debe dar False)
        "5>3 & 3<8",                        # Expresión Correcta (True)
        "5==5 | 3!=4",                      # Prueba de corrección del '==' y '!=' (Debe dar True)
        "!(5==5)",                          # Prueba del operador NOT '!' (Debe dar False)
        "5&6",                              # NO debe permitirse (Error Semántico)
        "6>10>50"                           # NO debe permitirse (Error Semántico consecutivo)
    ]

    for expr in casos_parte1:
        print(f"Evaluando : {expr}")
        try:
            parser1 = AnalizadorRecursivo(expr)
            resultado = parser1.S()
            print(f"Resultado : {resultado}")
        except Exception as e:
            print(f"Detectado : {e}")
        print()

    print("\n[PARTE 2] Analizador Descendente No Recursivo (Automata de Pila)")
    print("-" * 60)
    
    # Casos matemáticos para validar todas las notaciones
    casos_parte2 = [
        "(25.5+30.2)+50",
        "3+5*2-8/4^2"  # Prioridades: 4^2=16 -> 8/16=0.5 -> 5*2=10 -> 3+10=13 -> 13-0.5 = 12.5
    ]

    for expr in casos_parte2:
        print(f"Evaluando : {expr}")
        try:
            parser2 = AnalizadorPila(expr)
            parser2.parse()
            res = parser2.resultado
            print(f" Valor    : {res['val']}")
            print(f" Infija   : {res['inf']}")
            print(f" Postfija : {res['pos']}")
            print(f" Prefija  : {res['pre']}")
        except Exception as e:
            print(f"Detectado: {e}")
        print()