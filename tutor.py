import random, json

GRAMMARS_BANK = [
    "S → aS | bS | ε",
    "S -> aA | b\nA -> a | b | ε",
    "S -> aS | a",
    "S -> a S b | ε",
    "S -> a S | b S | ε\n",
    "S -> a A | b\nA -> A a | a",
    "S A -> A S\nS -> a\nA -> b",
    "A B -> B A\nA -> a\nB -> b",
    "S -> a S B | a B\nB a -> a B",
    "AB -> A\nS -> AB | a",
    "S S -> S\nS -> a | b",
    "S A -> ε\nS -> SA | a",
]

AUTOMATA_BANK = [
    {"type":"DFA","states":["q0","q1"],"input_symbols":["a","b"],
     "initial_state":"q0","final_states":["q1"],
     "transitions":{"q0":{"a":"q1","b":"q0"},"q1":{"a":"q1","b":"q0"}}},
    {"type":"NFA","states":["s","t"],"input_symbols":["0","1"],
     "initial_state":"s","final_states":["t"],
     "transitions":{"s":{"0":"t","1":"s"},"t":{"0":"t","1":"s"}}},
    {"type":"PDA","states":["q"],"input_symbols":["a","b"],
     "stack_symbols":["S","A","a","b"],"initial_state":"q","initial_stack_symbol":"S",
     "transitions":{"q":{"":[{"pop":"S","push":"aSb"},{"pop":"S","push":""}],
                         "a":[{"pop":"a","push":""}],
                         "b":[{"pop":"b","push":""}]}}},
    {"type":"TM","states":["q0","q1"],"input_symbols":["0","1"],
     "tape_symbols":["0","1","_"],"blank_symbol":"_","initial_state":"q0"},
    {"type":"LBA","states":["p","q"],"input_symbols":["a","b"],
     "initial_state":"p","final_states":["q"],"transitions":{}},
]

LABELS = {
    "3": "3 (Regular)",
    "2": "2 (Libre de Contexto)",
    "1": "1 (Sensible al Contexto)",
    "0": "0 (No Restringida)"
}

def init_state(state):
    state.setdefault("t_score", 0)
    state.setdefault("t_total", 0)
    state.setdefault("t_kind", None)
    state.setdefault("t_qtext", "")
    state.setdefault("t_truth", None)
    state.setdefault("t_expl", "")
    state.setdefault("t_auto_data", None)
    state.setdefault("t_checked", False)

def new_grammar_question(state, clasificar_con_explicacion):
    g = random.choice(GRAMMARS_BANK)
    tipo, explicacion, _ = clasificar_con_explicacion(g)
    state.update({"t_kind":"grammar","t_qtext":g,"t_truth":tipo,
                  "t_expl":explicacion,"t_auto_data":None,"t_checked":False})

def new_automaton_question(state, clasificar_automata):
    data = random.choice(AUTOMATA_BANK)
    tipo, explicacion, parsed, pasos = clasificar_automata(json.dumps(data))
    state.update({"t_kind":"automaton",
                  "t_qtext":json.dumps(data, indent=2, ensure_ascii=False),
                  "t_truth":tipo,
                  "t_expl":explicacion + ("\n\n" + "\n".join(pasos) if pasos else ""),
                  "t_auto_data":data,
                  "t_checked":False})

def ensure_question(state, clasificar_con_explicacion, clasificar_automata):
    if not state.get("t_qtext"):
        (new_grammar_question if random.random()<0.5 else new_automaton_question)(
            state, clasificar_con_explicacion if random.random()<0.5 else clasificar_automata
        )

def get_current_question(state):
    return (state.get("t_kind"), state.get("t_qtext"), state.get("t_truth"),
            state.get("t_expl"), state.get("t_auto_data"))

def check_answer(state, user_choice_str):
    try:
        choice = int(user_choice_str)
    except Exception:
        choice = None
    correct = (choice == state.get("t_truth"))
    state["t_total"] += 1
    if correct: state["t_score"] += 1
    state["t_checked"] = True
    return correct, LABELS.get(str(state.get("t_truth")), str(state.get("t_truth")))

def next_random_question(state, clasificar_con_explicacion, clasificar_automata):
    (new_grammar_question if random.random()<0.5 else new_automaton_question)(
        state, clasificar_con_explicacion if random.random()<0.5 else clasificar_automata
    )

def progress(state):
    total = state.get("t_total", 0)
    aciertos = state.get("t_score", 0)
    precision = round(100.0 * aciertos / total, 2) if total else 0.0
    return {"total": total, "aciertos": aciertos, "precision": precision}
