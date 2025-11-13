from typing import Tuple, Optional, List, Dict
import graphviz

try:
    from automata.fa.nfa import NFA
    from automata.fa.dfa import DFA
except ImportError:
    NFA = None
    DFA = None

def regex_to_dfa(pattern: str) -> Tuple[Optional[dict], Optional[str]]:
    if not pattern or not pattern.strip():
        return None, "La expresión regular está vacía."
    if NFA is None or DFA is None:
        return None, "automata-lib no está instalada. Instálala con: pip install automata-lib"
    try:
        nfa = NFA.from_regex(pattern)
        dfa = DFA.from_nfa(nfa)
    except Exception as e:
        return None, f"No se pudo construir el DFA desde la expresión regular: {e}"

    transitions: Dict[str, Dict[str, str]] = {}
    for state, trans in dfa.transitions.items():
        o = str(state)
        transitions[o] = {}
        for symbol, dest in trans.items():
            transitions[o][str(symbol)] = str(dest)

    dfa_dict = {
        "states": [str(s) for s in dfa.states],
        "input_symbols": [str(a) for a in dfa.input_symbols],
        "initial_state": str(dfa.initial_state),
        "final_states": [str(s) for s in dfa.final_states],
        "transitions": transitions,
    }
    return dfa_dict, None

def dfa_to_regular_grammar(dfa_dict: dict) -> List[str]:
    finals = set(dfa_dict.get("final_states", []))
    start = dfa_dict.get("initial_state")
    trans: Dict[str, Dict[str, str]] = dfa_dict.get("transitions", {})
    reglas: List[str] = []
    for origen, movs in trans.items():
        for simbolo, destino in movs.items():
            reglas.append(f"{origen} → {simbolo}{destino}")
            if destino in finals:
                reglas.append(f"{origen} → {simbolo}")
    if start in finals:
        reglas.append(f"{start} → ε")
    return reglas

def regex_to_dfa_and_grammar(pattern: str):
    dfa, err = regex_to_dfa(pattern)
    if err:
        return None, None, err
    reglas = dfa_to_regular_grammar(dfa)
    return dfa, reglas, None

def render_dfa_graphviz(dfa_dict: dict, filename: str = "dfa") -> str:
    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir="LR")
    finals = set(str(s) for s in dfa_dict.get("final_states", []))
    start = str(dfa_dict.get("initial_state", ""))
    dot.node("ini", shape="point")
    for s in dfa_dict.get("states", []):
        s = str(s)
        dot.node(s, shape=("doublecircle" if s in finals else "circle"))
    if start:
        dot.edge("ini", start)
    for origen, movs in dfa_dict.get("transitions", {}).items():
        for simb, dest in movs.items():
            dot.edge(str(origen), str(dest), label=str(simb))
    dot.render(filename, cleanup=True)
    return filename + ".png"

def _leer_glc(texto: str) -> Dict[str, List[str]]:
    gr: Dict[str, List[str]] = {}
    for linea in texto.strip().split("\n"):
        linea = linea.strip()
        if not linea or ("->" not in linea and "→" not in linea):
            continue
        if "->" in linea:
            izq, der = linea.split("->", 1)
        else:
            izq, der = linea.split("→", 1)
        A = izq.strip()
        alternativas = [p.strip() for p in der.split("|")]
        gr.setdefault(A, []).extend(alternativas)
    return gr

def glc_to_pda(texto: str):
    if not texto or not texto.strip():
        return None, "La gramática está vacía."
    gr = _leer_glc(texto)
    if not gr:
        return None, "No se pudieron leer producciones válidas."

    start_symbol = next(iter(gr.keys()))
    states = ["q"]
    input_symbols: set = set()
    stack_symbols: set = {start_symbol}
    transitions: Dict[str, Dict[str, List[dict]]] = {"q": {}}

    for A, prods in gr.items():
        stack_symbols.add(A)
        for prod in prods:
            if prod in ("ε", ""):
                transitions["q"].setdefault("", []).append({"pop": A, "push": ""})
                continue
            rhs_tokens = prod.split()
            if len(rhs_tokens) == 1:
                rhs_tokens = list(rhs_tokens[0])
            for x in rhs_tokens:
                if x.isupper():
                    stack_symbols.add(x)
                else:
                    input_symbols.add(x)
            push_str = "".join(reversed(rhs_tokens))
            transitions["q"].setdefault("", []).append({"pop": A, "push": push_str})

    for a in sorted(input_symbols):
        transitions["q"].setdefault(a, []).append({"pop": a, "push": ""})
        stack_symbols.add(a)

    pda = {
        "type": "PDA",
        "states": states,
        "input_symbols": sorted(list(input_symbols)),
        "stack_symbols": sorted(list(stack_symbols)),
        "initial_state": "q",
        "initial_stack_symbol": start_symbol,
        "transitions": transitions,
    }
    return pda, None

def render_pda_graphviz(pda_dict: dict, filename: str = "pda") -> str:
    dot = graphviz.Digraph(format="png")
    dot.attr(rankdir="LR")
    states = [str(s) for s in pda_dict.get("states", [])]
    initial = str(pda_dict.get("initial_state", states[0] if states else "q"))
    finals = set(str(s) for s in pda_dict.get("final_states", []))
    dot.node("ini", shape="point")
    for s in states:
        dot.node(s, shape=("doublecircle" if s in finals else "circle"))
    if states:
        dot.edge("ini", initial)
    transitions = pda_dict.get("transitions", {})
    for origen, movs in transitions.items():
        for leer, lst in movs.items():
            for t in lst:
                to = str(t.get("to", origen))
                pop = t.get("pop", "")
                push = t.get("push", "")
                lbl = f"{leer if leer else 'ε'}, {pop or 'ε'}→{push or 'ε'}"
                dot.edge(str(origen), to, label=lbl)
    dot.render(filename, cleanup=True)
    return filename + ".png"

def pda_to_transition_rows(pda_dict: dict) -> List[dict]:
    rows: List[dict] = []
    transitions = pda_dict.get("transitions", {})
    for origen, movs in transitions.items():
        for leer, lst in movs.items():
            for t in lst:
                rows.append({
                    "Desde": str(origen),
                    "Leer": leer if leer != "" else "ε",
                    "Pop": t.get("pop", "") or "ε",
                    "Push": t.get("push", "") or "ε",
                    "Hacia": str(t.get("to", origen)),
                })
    return rows
