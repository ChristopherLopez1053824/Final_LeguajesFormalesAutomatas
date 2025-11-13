import streamlit as st
import pandas as pd
import random, secrets
from Equivalencias import comparar_gramaticas

def _gen_type3_regular(rnd: random.Random) -> str:
    NT = ["S","A","B","C"]
    T  = rnd.sample(["a","b","c"], k=2)  
    n_rules = rnd.randint(5,8)
    rules = set()

    if rnd.random() < .6: rules.add("S -> ε")
    for _ in range(rnd.randint(1,3)):
        rules.add(f"S -> {rnd.choice(T)}")
        rules.add(f"S -> {rnd.choice(T)}{rnd.choice(NT)}")

    for A in ["A","B","C"]:
        if rnd.random() < .8:
            rules.add(f"{A} -> {rnd.choice(T)}{A}")
        if rnd.random() < .8:
            rules.add(f"{A} -> {rnd.choice(T)}{rnd.choice(NT)}")
        if rnd.random() < .7:
            rules.add(f"{A} -> {rnd.choice(T)}")
        if rnd.random() < .3:
            rules.add(f"{A} -> ε")

    rules = list(rules)
    rnd.shuffle(rules)
    return "\n".join(rules[:n_rules]) or "S -> a | ε"

def _gen_type2_cfg(rnd: random.Random) -> str:

    T = rnd.sample(["a","b","c"], k=2)
    a, b = T[0], T[1]
    cand = []
    cand.append(f"S -> {a} S {b} | ε")
    cand.append(f"S -> {a} S {a} | {b} S {b} | {a} | {b} | ε")
    cand.append(f"S -> {a} S {b} | A\nA -> {a} A | {b} | ε")
    cand.append(f"S -> {a} S {b} | S S | ε")

    rules = rnd.choice(cand)
    return rules

def _gen_type1_cs(rnd: random.Random) -> str:
    T = rnd.sample(["a","b","c"], k=2)
    a, b = T[0], T[1]
    base = [
        f"S -> {a} S B | {a} B",
        "A B -> B A",            
        f"B {a} -> {a} B",       
        "A -> " + a,
        "B -> " + b,
    ]
    if rnd.random() < .5: base.append("S A -> A S")
    if rnd.random() < .5: base.append("B B -> B B")
    return "\n".join(base)

def _gen_type0_unrestricted(rnd: random.Random) -> str:
    T = rnd.sample(["a","b","c"], k=2)
    a, b = T[0], T[1]
    base = [
        "S -> A B | " + a,
        "A B -> A",                 
        f"A -> {a} A | {a}",
        f"B -> {b} B | {b}",
    ]
    if rnd.random() < .6:
        base.append("S A -> ε")
    if rnd.random() < .4:
        base.append("B A -> B")
    return "\n".join(base)

def generar_gramatica_por_tipo(tipo: int, rnd: random.Random = None) -> str:
    rnd = rnd or random
    if tipo == 3: return _gen_type3_regular(rnd)
    if tipo == 2: return _gen_type2_cfg(rnd)
    if tipo == 1: return _gen_type1_cs(rnd)
    if tipo == 0: return _gen_type0_unrestricted(rnd)
    return _gen_type2_cfg(rnd)

from chomsky_classifier import (
    leer_gramatica,
    tipo_de_gramatica,
    clasificar_con_explicacion,
    construir_automata_regular,
    generar_grafo_automata,
    generar_arbol_derivacion,
    generar_grafo,
    clasificar_automata,
    generar_grafo_automata_desde_json,
)

from model_converters import (
    regex_to_dfa_and_grammar,
    glc_to_pda,
    render_dfa_graphviz,
    render_pda_graphviz,
    pda_to_transition_rows,
)

from tutor import (
    init_state,
    ensure_question,
    get_current_question,
    check_answer,
    next_random_question,
    progress,
    LABELS,
)

st.set_page_config(page_title="Chomsky Classifier AI", page_icon="", layout="wide")

page_style = """
<style>
/* General App Style */
[data-testid="stAppViewContainer"] {
    background-color: #F0F2F6; /* Light Gray */
}

[data-testid="stHeader"] {
    background-color: #FFFFFF;
    border-bottom: 2px solid #4A90E2;
}

/* Main Title */
h1 {
    color: #2C5A99; /* Darker, more professional blue */
    text-align: center;
    font-family: 'Segoe UI', sans-serif;
}

/* Sub-headers */
h2, h3 {
    color: #2C5A99;
    font-family: 'Segoe UI', sans-serif;
    border-bottom: 1px solid #D1D5DB;
    padding-bottom: 5px;
}

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 8px; /* Reduce gap slightly */
    border-bottom: 2px solid #D1D5DB; /* Add a bottom line to the whole tab list */
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    padding: 12px 16px;
    white-space: nowrap; /* Prevent wrapping */
    background-color: transparent; /* Make non-selected tabs transparent */
    border: none;
    border-bottom: 2px solid transparent; /* Placeholder for active indicator */
    border-radius: 4px 4px 0 0;
    color: #555555;
    transition: all 0.2s ease-in-out;
    margin-bottom: -2px; /* Align with the tab list border */
    height: auto; /* Remove fixed height */
}

[data-testid="stTabs"] [data-baseweb="tab"]:hover {
    background-color: #E9EFF8;
    color: #2C5A99;
}

[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {
    background-color: transparent;
    color: #4A90E2;
    font-weight: bold;
    border-color: #4A90E2; /* This creates the active indicator line */
}

/* Buttons */
[data-testid="stButton"] > button {
    border: 2px solid #4A90E2;
    border-radius: 25px;
    background-color: transparent;
    color: #4A90E2;
    padding: 8px 18px;
    font-weight: bold;
    transition: all 0.3s ease-in-out;
}

[data-testid="stButton"] > button:hover {
    background-color: #4A90E2;
    color: #FFFFFF;
}

[data-testid="stButton"] > button:focus {
    box-shadow: 0 0 0 0.2rem rgba(74, 144, 226, 0.5) !important;
    border-color: #4A90E2 !important;
}

/* Text Input / Text Area */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
    background-color: #FFFFFF;
    color: #333333;
    border: 1px solid #D1D5DB;
    border-radius: 5px;
    font-family: 'monospace';
}

[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
    border-color: #4A90E2;
    box-shadow: 0 0 0 1px #4A90E2;
}


/* Selectbox */
[data-testid="stSelectbox"] {
    border-radius: 5px;
}

/* Markdown/Info boxes */
[data-testid="stMarkdownContainer"] {
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    line-height: 1.6;
    color: #333333;
}

[data-testid="stInfo"] {
    background-color: #E9EFF8; /* Light blue background */
    border-left: 5px solid #4A90E2;
    border-radius: 5px;
    padding: 15px;
    color: #2C5A99;
}

/* Code blocks */
[data-testid="stCodeBlock"] {
    border: 1px solid #D1D5DB;
    border-radius: 5px;
}

/* Subtitle color */
p[style*='text-align: center'] {
    color: #555555 !important;
}

</style>
"""
st.markdown(page_style, unsafe_allow_html=True)

st.title("Chomsky IA")
st.markdown("<p style='text-align: center; font-size: 1.1rem;'>Herramienta de IA para el Análisis de Lenguajes Formales y Autómatas</p>", unsafe_allow_html=True)


st.markdown(
    """
Esta herramienta te permite:

- Clasificar **gramáticas** (Tipos 0, 1, 2, 3) con explicación paso a paso.
- Generar **autómatas equivalentes** cuando aplica.
- Construir **árboles de derivación** para ciertas gramáticas.
- Clasificar **autómatas** (AFD/AFN, PDA, MT) según la jerarquía.
- Convertir entre modelos:
  - Regex ⇨ AFD ⇨ Gramática Regular
  - GLC ⇨ Autómata con Pila (PDA)
- Practicar con un **Tutor/Quiz** interactivo.
"""
)
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Gramática", "Autómata", "Conversión", "Tutor", "Equivalencia"])
with tab1:
        def _gen_type3_regular(rnd: random.Random) -> str:
            NT = ["S","A","B","C"]
            T  = rnd.sample(["a","b","c"], k=2)
            n_rules = rnd.randint(5,8)
            rules = set()

            if rnd.random() < .6:
                rules.add("S -> ε")
            for _ in range(rnd.randint(1,3)):
                rules.add(f"S -> {rnd.choice(T)}")
                rules.add(f"S -> {rnd.choice(T)}{rnd.choice(NT)}")

            for A in ["A","B","C"]:
                if rnd.random() < .8:
                    rules.add(f"{A} -> {rnd.choice(T)}{A}")
                if rnd.random() < .8:
                    rules.add(f"{A} -> {rnd.choice(T)}{rnd.choice(NT)}")
                if rnd.random() < .7:
                    rules.add(f"{A} -> {rnd.choice(T)}")
                if rnd.random() < .3:
                    rules.add(f"{A} -> ε")

            rules = list(rules)
            rnd.shuffle(rules)
            return "\n".join(rules[:n_rules]) or "S -> a | ε"

        def _gen_type2_cfg(rnd: random.Random) -> str:
            T = rnd.sample(["a","b","c"], k=2)
            a, b = T
            cand = [
                f"S -> {a} S {b} | ε",
                f"S -> {a} S {a} | {b} S {b} | {a} | {b} | ε",
                f"S -> {a} S {b} | A\nA -> {a} A | {b} | ε",
                f"S -> {a} S {b} | S S | ε",
            ]
            return rnd.choice(cand)

        def _gen_type1_cs(rnd: random.Random) -> str:
            T = rnd.sample(["a","b","c"], k=2)
            a, b = T
            base = [
                f"S -> {a} S B | {a} B",
                "A B -> B A",
                f"B {a} -> {a} B",
                f"A -> {a}",
                f"B -> {b}",
            ]
            if rnd.random() < .5: base.append("S A -> A S")
            if rnd.random() < .5: base.append("B B -> B B")
            return "\n".join(base)

        def _gen_type0_unrestricted(rnd: random.Random) -> str:
            T = rnd.sample(["a","b","c"], k=2)
            a, b = T
            base = [
                f"S -> A B | {a}",
                "A B -> A",
                f"A -> {a} A | {a}",
                f"B -> {b} B | {b}",
            ]
            if rnd.random() < .6: base.append("S A -> ε")
            if rnd.random() < .4: base.append("B A -> B")
            return "\n".join(base)

        def generar_gramatica_por_tipo(tipo: int, rnd: random.Random = None) -> str:
            rnd = rnd or random.Random(secrets.randbits(64))  
            if tipo == 3: return _gen_type3_regular(rnd)
            if tipo == 2: return _gen_type2_cfg(rnd)
            if tipo == 1: return _gen_type1_cs(rnd)
            if tipo == 0: return _gen_type0_unrestricted(rnd)
            return _gen_type2_cfg(rnd)
        st.header("Clasificación de Gramáticas")

        st.subheader("Generador automático de ejemplos")
        colg1, colg2, colg3 = st.columns([2,1,1])
        with colg1:
            tipo_sel = st.selectbox(
                "Tipo de gramática a generar:",
                options=[3, 2, 1, 0],
                format_func=lambda t: {3:"3 (Regular)", 2:"2 (Libre de Contexto)", 1:"1 (Sensible al Contexto)", 0:"0 (No Restringida)"}[t],
                index=1,
                key="tipo_gen_gram"
            )
        with colg2:
            if st.button("Insertar ejemplo", key="btn_insertar_ejemplo"):
                st.session_state["gramatica_text"] = generar_gramatica_por_tipo(tipo_sel)
                st.rerun()
        with colg3:
            if st.button("Limpiar", key="btn_limpiar_ejemplo"):
                st.session_state["gramatica_text"] = ""
                st.rerun()
        texto = st.text_area(
            "Gramática (una producción por línea, usa → o -> y | para alternativas):",
            value=st.session_state.get("gramatica_text", "S -> a S b\nS -> ε"),
            height=220,
            key="gramatica_text"
        )

        modo_explicativo = st.checkbox("Activar modo explicativo paso a paso", value=True)

        cadena = st.text_input(
            "Cadena para árbol de derivación (opcional)",
            "",
            help="El árbol solo se genera si todas las producciones tienen un único no terminal en el lado izquierdo (A → α).",
            key="cadena_derivacion"
        )

        if st.button("Clasificar gramática", key="btn_clasificar_gramatica"):
            if modo_explicativo:
                tipo, explicacion, pasos = clasificar_con_explicacion(texto)
            else:
                tipo, explicacion = tipo_de_gramatica(texto)
                pasos = None

            gramatica = leer_gramatica(texto)

            st.subheader("Resultado del análisis de la gramática")
            st.markdown(f"**Tipo detectado:** `{tipo}`")
            st.info(explicacion)

            if pasos:
                st.subheader("Explicación paso a paso (producciones)")
                for p in pasos:
                    st.markdown(f"- {p}")
            try:
                generar_grafo(gramatica)
                st.subheader("Diagrama de la gramática")
                st.image("gramatica.png")
            except Exception as e:
                st.warning(f"No se pudo generar el grafo de la gramática: {e}")
            if tipo == 3:
                st.subheader("Autómata finito equivalente (Tipo 3)")
                automata = construir_automata_regular(texto)
                if automata:
                    st.markdown(f"**Estados:** {', '.join(map(str, automata['states']))}")
                    st.markdown(f"**Alfabeto:** {', '.join(map(str, automata['alphabet']))}")
                    st.markdown(f"**Estado inicial:** `{automata['start_state']}`")
                    st.markdown("**Estados de aceptación:** " + ", ".join(map(str, automata["final_states"])))

                    rows = []
                    for origen, trans in automata["transitions"].items():
                        for simbolo, destinos in trans.items():
                            for dest in destinos:
                                rows.append({"Desde": origen, "Símbolo": simbolo, "Hacia": dest})

                    if rows:
                        import pandas as pd
                        df = pd.DataFrame(rows)

with tab2:
    st.header("Clasificación de Autómatas")
    
    st.markdown(
        """
Pega la descripción de tu autómata en formato JSON.

El sistema:
- Intenta inferir si es **AFD/AFN**, **PDA**, **MT**, etc.
- Lo mapea al **tipo de lenguaje** (3, 2, 1, 0).
- Explica la decisión basada en su estructura.
"""
    )

    auto_text = st.text_area(
        "JSON del autómata:",
        height=260,
        help="Solo se usa lo que pegues aquí; tú eliges el formato mientras sea JSON válido.",
        key="automata_json"
    )

    if st.button("Clasificar autómata", key="clasificar_automata"):
        if not auto_text.strip():
            st.warning("Pega un JSON de autómata para analizarlo.")
        else:
            tipo, explicacion, data, pasos_auto = clasificar_automata(auto_text)

            st.subheader("Resultado del análisis del autómata")

            if tipo is None:
                st.warning(explicacion)
            else:
                st.markdown(f"**Tipo de lenguaje reconocido:** `{tipo}`")
                st.info(explicacion)

            if pasos_auto:
                st.subheader("Explicación paso a paso")
                for linea in pasos_auto:
                    st.markdown(f"- {linea}")

            if data and isinstance(data, dict) and all(
                k in data for k in ("states", "transitions", "initial_state")
            ):
                st.subheader("Transiciones del autómata")

                rows = []
                transitions = data.get("transitions", {})
                for origen, trans in transitions.items():
                    for simbolo, destino in trans.items():
                        if isinstance(destino, list):
                            for d in destino:
                                rows.append({"Desde": origen, "Símbolo": simbolo, "Hacia": d})
                        else:
                            rows.append({"Desde": origen, "Símbolo": simbolo, "Hacia": destino})

                if rows:
                    df = pd.DataFrame(rows)
                    st.dataframe(df, use_container_width=True)

                dot = generar_grafo_automata_desde_json(data)
                if dot:
                    try:
                        st.image("automata_input.png")
                    except Exception:
                        pass

with tab3:
    st.header("Conversión entre Modelos")
    
    st.markdown(
        """
Convierte entre modelos equivalentes:

- **Regex → AFD → Gramática Regular**
- **GLC → PDA**

Tú proporcionas la expresión o gramática, el sistema construye el modelo equivalente.
"""
    )

    subtab_regex, subtab_glc = st.tabs(["Regex → AFD + GR", "GLC → PDA"])
    with subtab_regex:
        st.subheader("Conversión: Expresión Regular → AFD + Gramática Regular")
        regex = st.text_input("Expresión regular:", key="regex_input")

        if st.button("Convertir Regex → AFD + Gramática Regular", key="convertir_regex"):
            if not regex.strip():
                st.warning("Escribe una expresión regular primero.")
            else:
                dfa, reglas, err = regex_to_dfa_and_grammar(regex)
                if err:
                    st.error(err)
                else:
                    try:
                        png = render_dfa_graphviz(dfa, filename="dfa_from_regex")
                        st.subheader("AFD equivalente (gráfico)")
                        st.image(png, caption="AFD generado desde la regex")
                    except Exception as e:
                        st.warning(f"No se pudo renderizar el grafo del AFD: {e}")
                    rows = []
                    for origen, trans in dfa["transitions"].items():
                        for simbolo, destino in trans.items():
                            rows.append({"Desde": origen, "Símbolo": simbolo, "Hacia": destino})
                    if rows:
                        df = pd.DataFrame(rows)
                        st.markdown("**Tabla de transiciones (δ):**")
                        st.dataframe(df, use_container_width=True)
                    st.subheader("📘 Gramática regular equivalente (A → aB | a)")
                    for r in reglas:
                        st.markdown(f"- `{r}`")
    with subtab_glc:
        st.subheader("Conversión: Gramática Libre de Contexto → PDA")
        glc_text = st.text_area(
            "Gramática Libre de Contexto:",
            height=200,
            help="Una producción por línea. Usa -> o → y | para alternativas.",
            key="glc_input"
        )

        if st.button("Convertir GLC → PDA", key="convertir_glc"):
            if not glc_text.strip():
                st.warning("Pega una GLC para convertirla.")
            else:
                pda, err = glc_to_pda(glc_text)
                if err:
                    st.error(err)
                else:
                    rows = pda_to_transition_rows(pda)
                    if rows:
                        df = pd.DataFrame(rows)
                        st.markdown("**Transiciones del PDA:**")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("No se encontraron transiciones para mostrar.")
                    try:
                        png = render_pda_graphviz(pda, filename="pda_equivalente")
                        st.image(png, caption="PDA equivalente")
                    except Exception as e:
                        st.warning(f"No se pudo renderizar el grafo del PDA: {e}")

with tab4:
    st.header("Tutor Interactivo")
    st.markdown("Pon a prueba lo que sabes de la **Jerarquía de Chomsky** con mini-ejercicios.")
    init_state(st.session_state)

    cols_top = st.columns([1, 1, 2])
    with cols_top[0]:
        if st.button("➕ Nueva pregunta de Gramática", key="nueva_gramatica"):
            from chomsky_classifier import clasificar_con_explicacion as _cc
            from tutor import new_grammar_question
            new_grammar_question(st.session_state, _cc)

    with cols_top[1]:
        if st.button("➕ Nueva pregunta de Autómata", key="nueva_automata"):
            from chomsky_classifier import clasificar_automata as _ca
            from tutor import new_automaton_question
            new_automaton_question(st.session_state, _ca)
    ensure_question(st.session_state, clasificar_con_explicacion, clasificar_automata)

    kind, qtext, truth, expl, auto_data = get_current_question(st.session_state)

    st.subheader("pregunta")
    if kind == "grammar":
        st.caption("Clasifica la gramática (Tipo 3 / 2 / 1 / 0):")
        st.code(qtext, language="text")
    else:
        st.caption("¿Qué tipo de lenguaje reconoce este autómata? (Tipo 3 / 2 / 1 / 0)")
        st.code(qtext, language="json")
        try:
            if auto_data and all(k in auto_data for k in ("states", "transitions", "initial_state")):
                dot = generar_grafo_automata_desde_json(auto_data)
                if dot:
                    st.image("automata_input.png", caption="Autómata de la pregunta")
        except Exception:
            pass

    st.markdown("**Elige tu respuesta:**")
    opt_map = {
        "3": LABELS["3"],
        "2": LABELS["2"],
        "1": LABELS["1"],
        "0": LABELS["0"],
    }
    sel = st.radio(
        "Tipo:",
        options=list(opt_map.keys()),
        format_func=lambda k: opt_map[k],
        horizontal=True,
        key="t_user_choice_radio",
    )

    cols_actions = st.columns([1, 1, 2])
    with cols_actions[0]:
        if st.button("Comprobar", key="comprobar_respuesta"):
            is_ok, truth_label = check_answer(st.session_state, sel)
            if is_ok:
                st.success(f"¡Correcto! {truth_label}")
            else:
                st.error(f"Incorrecto. Respuesta correcta: {truth_label}")
    st.markdown("**Explicación / Pistas:**")
    st.info(expl or "Sin explicación disponible para esta pregunta.")
    st.subheader("Progreso")
    prog = progress(st.session_state)
    c1, c2, c3 = st.columns(3)
    c1.metric("Preguntas", prog["total"])
    c2.metric("Aciertos", prog["aciertos"])
    c3.metric("Precisión", f"{prog['precision']}%" )

with tab5:
    st.header("Comparación de Gramáticas")

    st.markdown("Ingresa **dos gramáticas** para comparar si generan el mismo lenguaje.")

    g1 = st.text_area("Gramática 1:", height=180, key="eq_g1")
    g2 = st.text_area("Gramática 2:", height=180, key="eq_g2")

    max_len = st.slider("Longitud máxima de derivación:", 2, 10, 6)

    if st.button("Comparar", key="btn_comparar_gramaticas"):
        msg, L1, L2 = comparar_gramaticas(g1, g2, max_len)
        st.subheader("Resultado")
        st.info(msg)

        colA, colB = st.columns(2)
        with colA:
            st.markdown("### Lenguaje estimado G1")
            st.write(sorted(list(L1)))
        with colB:
            st.markdown("### Lenguaje estimado G2")
            st.write(sorted(list(L2)))