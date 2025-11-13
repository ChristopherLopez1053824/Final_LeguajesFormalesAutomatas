import graphviz
import json

try:
    from automata.fa.dfa import DFA
    from automata.fa.nfa import NFA
    from automata.pda.npda import NPDA
    from automata.tm.dtm import DTM
except ImportError:
    DFA = NFA = NPDA = DTM = None


class ClasificadorGramaticas:
    """
    - Clasifica gramáticas en la jerarquía de Chomsky (Tipos 0,1,2,3).
    - Modo explicativo paso a paso para gramáticas.
    - Construye autómata equivalente si la gramática es regular (Tipo 3).
    - Genera árbol de derivación para gramáticas con LHS = 1 no terminal.
    - Clasifica autómatas (AFD/AFN, PDA, TM, LBA) a partir de JSON:
        * Detecta el modelo por su estructura.
        * Asocia el modelo a Tipo 3,2,1,0.
        * Explica paso a paso la decisión.
    """
    def _is_nt(self, c: str) -> bool:
        return c.isupper()
    def _is_t(self, c: str) -> bool:
        return c.islower()
    def leer_gramatica(self, texto: str):
        """
        Lee una gramática desde texto.
        Formato: una producción por línea, usando -> o → y | para alternativas.
        Sin espacios en símbolos, para trabajar por caracteres.
        """
        gr = {}
        for linea in texto.strip().split("\n"):
            linea = linea.strip()
            if not linea or ("->" not in linea and "→" not in linea):
                continue

            if "->" in linea:
                izq, der = linea.split("->", 1)
            else:
                izq, der = linea.split("→", 1)

            izq = izq.replace(" ", "")
            prods = []
            for p in der.split("|"):
                p = p.strip()
                if p != "ε":
                    p = p.replace(" ", "")
                prods.append(p)
            gr.setdefault(izq, []).extend(prods)
        return gr
    def _es_regla_regular(self, izq: str, prod: str) -> bool:
        """
        Forma de gramática regular (flexible, derecha o izquierda):
        A → a
        A → aB
        A → Ba
        A → ε
        con A un solo no terminal.
        """
        if len(izq) != 1 or not self._is_nt(izq):
            return False

        if prod == "ε":
            return True

        if not all(ch.isalpha() for ch in prod):
            return False
        if len(prod) == 1 and self._is_t(prod[0]):
            return True

        if len(prod) == 2 and self._is_t(prod[0]) and self._is_nt(prod[1]):
            return True

        if len(prod) == 2 and self._is_nt(prod[0]) and self._is_t(prod[1]):
            return True

        return False

    def clasificar_con_explicacion(self, texto: str):
        """
        Analiza todas las producciones y determina el tipo más restrictivo posible.
        Devuelve:
          - tipo (0,1,2,3)
          - explicación general
          - lista de mensajes explicativos (por producción)
        """
        gr = self.leer_gramatica(texto)
        pasos = []

        all_regular = True
        all_lhs_single_nt = True
        no_reduce_length = True
        forces_type0 = False

        pasos.append("Inicio del análisis producción por producción:")

        for izq, prods in gr.items():
            for prod in prods:
                detalle = f"Regla: {izq} → {prod}"
                lhs_len = len(izq)
                rhs_len = 0 if prod == "ε" else len(prod)
                if lhs_len == 1 and self._is_nt(izq):
                    detalle += " | LHS un solo no terminal (compatible con Tipos 3 y 2)."
                else:
                    all_lhs_single_nt = False
                    detalle += " | LHS no es un solo no terminal (rompe Tipos 3 y 2)."

                if prod == "ε":
                    if lhs_len > 1:
                        no_reduce_length = False
                        forces_type0 = True
                        detalle += " | ε con LHS múltiple → reducción → fuerza Tipo 0."
                    else:
                        detalle += " | ε aceptable en ciertos contextos (Tipo 2/3)."
                else:
                    if rhs_len < lhs_len:
                        no_reduce_length = False
                        forces_type0 = True
                        detalle += " |RHS| < |LHS| → reducción → fuerza Tipo 0."
                    else:
                        detalle += " | Longitud OK (|RHS| ≥ |LHS|)."

                if self._es_regla_regular(izq, prod):
                    detalle += " | Forma compatible con Tipo 3."
                else:
                    all_regular = False
                    detalle += " | Forma no es estrictamente regular."

                pasos.append(detalle)

        if forces_type0:
            pasos.append("Reducciones de longitud o LHS complejos → Clasificación final: Tipo 0.")
            return 0, "Gramática No Restringida (Tipo 0): viola restricciones de los tipos 1, 2 o 3.", pasos

        if all_regular:
            pasos.append("Todas las producciones son regulares → Clasificación final: Tipo 3.")
            return 3, "Gramática Regular (Tipo 3): producciones de la forma A → a, A → aB, A → Ba o A → ε.", pasos

        if all_lhs_single_nt:
            pasos.append("Todos los LHS son un solo no terminal, pero no todas son regulares → Clasificación final: Tipo 2.")
            return 2, "Gramática Libre de Contexto (Tipo 2): producciones de la forma A → α.", pasos

        if no_reduce_length:
            pasos.append("No hay reducción de longitud, pero hay contexto en el LHS → Clasificación final: Tipo 1.")
            return 1, "Gramática Sensible al Contexto (Tipo 1): no reduce longitud y admite contexto.", pasos

        pasos.append("No encaja en 3, 2 o 1 → Clasificación final: Tipo 0.")
        return 0, "Gramática No Restringida (Tipo 0).", pasos

    def tipo_de_gramatica(self, texto: str):
        tipo, explicacion, _ = self.clasificar_con_explicacion(texto)
        return tipo, explicacion

    def clasificar_automata(self, descripcion: str):
        """
        Clasifica un autómata dado en JSON según su estructura
        y genera una explicación paso a paso.

        Inferencia automática:

        - Si tiene cinta (tape_symbols, blank_symbol, etc.) → Máquina de Turing → Tipo 0.
        - Si tiene pila (stack_symbols, initial_stack_symbol, etc.) → PDA → Tipo 2.
        - Si tiene estructura de AFD/AFN → Tipo 3.
        - Si indica LBA / context_sensitive → Tipo 1.
        - Si solo 'type' está presente, se usa como pista secundaria.

        Devuelve:
        - tipo (0,1,2,3 o None)
        - explicación general
        - data (dict con el JSON parseado)
        - pasos (lista de strings explicativos)
        """
        pasos = []

        try:
            data = json.loads(descripcion)
            pasos.append("JSON válido: se pudo parsear correctamente.")
        except json.JSONDecodeError:
            pasos.append("Error: el texto ingresado no es un JSON válido.")
            return None, "No se pudo interpretar el autómata como JSON. Revisa llaves, comas y comillas.", None, pasos

        claves = set(data.keys())
        pasos.append(f"Claves detectadas: {', '.join(sorted(claves)) or '(ninguna)'}")

        tipo_decl = str(data.get("type", "")).strip().lower()
        if tipo_decl:
            pasos.append(f"ℹCampo 'type' detectado: '{tipo_decl}' (solo como pista, no definitivo).")

        tiene_cinta = any(k in data for k in ("tape_symbols", "blank_symbol"))
        tiene_pila = any(k in data for k in ("stack_symbols", "initial_stack_symbol"))
        tiene_estados = "states" in data
        tiene_trans = "transitions" in data
        tiene_ini = "initial_state" in data
        tiene_fins = ("final_states" in data) or ("accepting_states" in data)
        tiene_alfabeto = "input_symbols" in data

        if tiene_cinta or "turing" in tipo_decl or tipo_decl == "tm":
            pasos.append("Se detectan campos de cinta o tipo TM/Turing → Máquina de Turing.")
            return 0, "Detectado como Máquina de Turing → Lenguaje de **Tipo 0** (recursivamente enumerable).", data, pasos

        if tiene_pila or "pushdown" in tipo_decl or tipo_decl == "pda":
            pasos.append("Se detectan campos de pila o tipo PDA → Autómata con Pila.")
            return 2, "Detectado como Autómata con Pila (PDA) → Lenguaje de **Tipo 2** (libre de contexto).", data, pasos
        
        if "lba" in tipo_decl or "context_sensitive" in tipo_decl:
            pasos.append("'type' indica LBA/context_sensitive → Modelo sensible al contexto.")
            return 1, "Detectado como modelo sensible al contexto (LBA) → Lenguaje de **Tipo 1**.", data, pasos

        if tiene_estados and tiene_trans and tiene_ini and tiene_fins and tiene_alfabeto:
            pasos.append("🧠 Estructura clásica de autómata finito detectada (states, input_symbols, transitions, initial_state, final_states).")
            return 3, "🧠 Detectado como Autómata Finito (DFA/NFA) → Lenguaje de **Tipo 3** (regular).", data, pasos

        if tipo_decl in ("dfa", "nfa"):
            pasos.append("ℹ'type' = DFA/NFA, aunque falten algunos campos → asumido autómata finito.")
            return 3, "Indicador 'type' = DFA/NFA → asumido Lenguaje de **Tipo 3** (regular).", data, pasos

        if tipo_decl == "pda":
            pasos.append("ℹ'type' = PDA sin estructura completa → asumido PDA.")
            return 2, "Indicador 'type' = PDA → asumido Lenguaje de **Tipo 2**.", data, pasos

        if tipo_decl in ("tm", "turing"):
            pasos.append("ℹ'type' = TM/Turing sin cinta explícita → asumida Máquina de Turing.")
            return 0, "Indicador 'type' = TM/Turing → asumido Lenguaje de **Tipo 0**.", data, pasos

        pasos.append("No hay suficiente información estructural para clasificar el autómata.")
        pasos.append(
            "Sugerencia: incluye al menos:\n"
            "- Para DFA/NFA: states, input_symbols, transitions, initial_state, final_states.\n"
            "- Para PDA: stack_symbols, initial_stack_symbol.\n"
            "- Para TM: tape_symbols, blank_symbol."
        )

        return None, (
            "No se pudo determinar automáticamente el tipo de autómata.\n"
            "Revisa la estructura o agrega más información."
        ), data, pasos

    def generar_grafo_automata_desde_json(self, data: dict):
        if not all(k in data for k in ("states", "transitions", "initial_state")):
            return None

        states = data["states"]
        transitions = data["transitions"]
        final_states = data.get("final_states", data.get("accepting_states", []))
        initial_state = data["initial_state"]

        dot = graphviz.Digraph(format="png")
        dot.attr(rankdir="LR")
        dot.node("ini", shape="point")

        for s in states:
            if s in final_states:
                dot.node(str(s), shape="doublecircle")
            else:
                dot.node(str(s), shape="circle")

        dot.edge("ini", str(initial_state))

        for origen, trans in transitions.items():
            for simbolo, destino in trans.items():
                if isinstance(destino, list):
                    for d in destino:
                        dot.edge(str(origen), str(d), label=str(simbolo))
                else:
                    dot.edge(str(origen), str(destino), label=str(simbolo))

        dot.render("automata_input", cleanup=True)
        return dot
    
    def construir_automata_regular(self, texto: str):
        tipo, _, _ = self.clasificar_con_explicacion(texto)
        if tipo != 3:
            return None

        gr = self.leer_gramatica(texto)
        start = next(iter(gr.keys()))
        transitions = {}
        final_states = set()
        sink_final = "F"

        for A, prods in gr.items():
            transitions.setdefault(A, {})
            for prod in prods:
                if prod == "ε":
                    final_states.add(A)
                elif len(prod) == 1 and self._is_t(prod[0]):
                    a = prod[0]
                    transitions[A].setdefault(a, set()).add(sink_final)
                    final_states.add(sink_final)
                elif len(prod) == 2 and self._is_t(prod[0]) and self._is_nt(prod[1]):
                    a, B = prod[0], prod[1]
                    transitions[A].setdefault(a, set()).add(B)

        states = set(transitions.keys()) | final_states
        alphabet = sorted({a for trans in transitions.values() for a in trans.keys()})
        trans_clean = {
            s: {a: sorted(list(dests)) for a, dests in trans.items()}
            for s, trans in transitions.items()
        }

        return {
            "states": sorted(states),
            "alphabet": alphabet,
            "start_state": start,
            "final_states": sorted(final_states),
            "transitions": trans_clean,
        }

    def generar_grafo_automata(self, automata: dict):
        dot = graphviz.Digraph(format="png")
        dot.attr(rankdir="LR")
        dot.node("ini", shape="point")

        for s in automata["states"]:
            if s in automata["final_states"]:
                dot.node(str(s), shape="doublecircle")
            else:
                dot.node(str(s), shape="circle")

        dot.edge("ini", str(automata["start_state"]))

        for origen, trans in automata["transitions"].items():
            for simbolo, destinos in trans.items():
                for dest in destinos:
                    dot.edge(str(origen), str(dest), label=str(simbolo))

        dot.render("automata", cleanup=True)
        return dot

    def generar_arbol_derivacion(self, texto: str, cadena: str):
        cadena = cadena.strip()
        if not cadena:
            return None, "Ingresa una cadena para construir el árbol."

        gr = self.leer_gramatica(texto)
        start = next(iter(gr.keys()))

        for izq in gr.keys():
            if len(izq) != 1 or not self._is_nt(izq):
                return None, "El árbol solo se genera para gramáticas con producciones A → α (LHS con un solo no terminal)."

        max_pasos = 40

        def dfs(sentential, pasos):
            if len(pasos) > max_pasos:
                return None

            if all(self._is_t(c) for c in sentential):
                if "".join(sentential) == cadena:
                    return pasos
                return None

            for i, c in enumerate(sentential):
                if self._is_nt(c):
                    A = c
                    for prod in gr.get(A, []):
                        nueva = (
                            sentential[:i]
                            + ([] if prod == "ε" else list(prod))
                            + sentential[i + 1:]
                        )
                        r = dfs(
                            nueva,
                            pasos + [( "".join(sentential), A, prod, "".join(nueva) )]
                        )
                        if r is not None:
                            return r
                    return None
            return None
        deriv = dfs([start], [])
        if deriv is None:
            return None, f"No se pudo derivar la cadena '{cadena}' con esta gramática."
        dot = graphviz.Digraph(format="png")
        dot.attr(rankdir="TB")
        dot.node("s0", start)

        for idx, (antes, A, prod, despues) in enumerate(deriv, start=0):
            src = f"s{idx}"
            dst = f"s{idx+1}"
            dot.node(dst, despues)
            dot.edge(src, dst, label=f"{A}→{prod}")

        dot.render("derivacion", cleanup=True)

        pasos_tabla = []
        for i, (antes, A, prod, despues) in enumerate(deriv, start=1):
            pasos_tabla.append({
                "Paso": i,
                "Sentencia antes": antes,
                "Regla aplicada": f"{A} → {prod}",
                "Sentencia después": despues,
            })

        return pasos_tabla, None

    def generar_grafo(self, gr):
        dot = graphviz.Digraph(format="png")
        for izq, prods in gr.items():
            for prod in prods:
                dot.edge(izq, prod)
        dot.render("gramatica", cleanup=True)
        return dot

clasificador = ClasificadorGramaticas()

def leer_gramatica(texto: str):
    return clasificador.leer_gramatica(texto)

def tipo_de_gramatica(texto: str):
    return clasificador.tipo_de_gramatica(texto)

def clasificar_con_explicacion(texto: str):
    return clasificador.clasificar_con_explicacion(texto)

def construir_automata_regular(texto: str):
    return clasificador.construir_automata_regular(texto)

def generar_grafo_automata(automata: dict):
    return clasificador.generar_grafo_automata(automata)

def generar_arbol_derivacion(texto: str, cadena: str):
    return clasificador.generar_arbol_derivacion(texto, cadena)

def generar_grafo(gramatica: dict):
    return clasificador.generar_grafo(gramatica)

def clasificar_automata(descripcion: str):
    return clasificador.clasificar_automata(descripcion)

def generar_grafo_automata_desde_json(data: dict):
    return clasificador.generar_grafo_automata_desde_json(data)
