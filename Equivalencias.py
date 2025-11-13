from typing import Dict, List, Set
from itertools import product

def leer_gramatica(texto: str) -> Dict[str, List[str]]:
    gr = {}
    for linea in texto.strip().split("\n"):
        linea = linea.strip()
        if not linea or ("->" not in linea and "→" not in linea):
            continue

        if "->" in linea:
            izq, der = linea.split("->", 1)
        else:
            izq, der = linea.split("→", 1)

        izq = izq.strip()
        alternativas = [p.strip() for p in der.split("|")]
        gr.setdefault(izq, []).extend(alternativas)
    return gr

def generar_cadenas(glc: Dict[str, List[str]], max_len: int = 6) -> Set[str]:
    """
    Genera cadenas derivables hasta longitud <= max_len.
    No garantiza exhaustividad, pero sirve para comparación.
    """
    start = next(iter(glc.keys()))
    resultados = set()

    agenda = [start]
    visitados = set()

    while agenda:
        actual = agenda.pop()
        if actual in visitados:
            continue
        visitados.add(actual)
        if all(c.islower() for c in actual):
            if len(actual) <= max_len:
                resultados.add(actual)
            continue
        if len(actual) > max_len:
            continue

        for i, c in enumerate(actual):
            if c.isupper():  
                for prod in glc.get(c, []):
                    nueva = actual[:i] + ("" if prod == "ε" else prod) + actual[i+1:]
                    if len(nueva) <= max_len + 2:
                        agenda.append(nueva)

    return resultados

def comparar_gramaticas(txt1: str, txt2: str, max_len: int = 6):
    g1 = leer_gramatica(txt1)
    g2 = leer_gramatica(txt2)

    L1 = generar_cadenas(g1, max_len)
    L2 = generar_cadenas(g2, max_len)

    inter = L1 & L2
    union = L1 | L2

    if not L1 and not L2:
        return "No se pudo generar ninguna cadena con ambas gramáticas.", L1, L2

    if L1 == L2:
        return "Las gramáticas parecen equivalentes (misma muestra generada).", L1, L2
    sim = len(inter) / len(union)

    if sim > 0.70:
        return f"Posible equivalencia (similitud {sim*100:.1f}%).", L1, L2
    elif sim > 0.30:
        return f"Coincidencia parcial (similitud {sim*100:.1f}%).", L1, L2
    else:
        return f"Las gramáticas NO parecen equivalentes (similitud {sim*100:.1f}%).", L1, L2
