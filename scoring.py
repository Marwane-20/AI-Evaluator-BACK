# backend/scoring.py

import ast
import re
import timeit
import logging
import subprocess
from typing import Any, Tuple, Dict, Union

from prompts import TEST_CASES

# --- 1) Test-based scoring (Correctness & Robustness) -----------------------

def run_tests_for(prompt_key: str, func: Any) -> Tuple[int, int]:
    """
    Lance tous les tests définis dans TEST_CASES[prompt_key] sur la fonction func.
    Retourne (nb_passés, nb_total).
    """
    passed = 0
    cases = TEST_CASES.get(prompt_key, [])
    for args, expected in cases:
        try:
            result = func(*args)
            # Si on attendait une exception, on échoue
            if isinstance(expected, type) and issubclass(expected, Exception):
                continue
            # Sinon on compare la valeur
            if expected is str and isinstance(result, str):
                passed += 1
            elif result == expected:
                passed += 1
        except Exception as e:
            # Si on attendait cette exception, succès
            if isinstance(expected, type) and isinstance(e, expected):
                passed += 1
    return passed, len(cases)

def score_from_tests(passed: int, total: int) -> float:
    """
    Normalise passed/total dans [1.0 … 5.0]. Si total==0, retourne 0.0.
    """
    if total == 0:
        return 0.0
    ratio = passed / total  # entre 0.0 et 1.0
    return round(1.0 + ratio * 4.0, 1)

# --- 2) Performance ---------------------------------------------------------

def score_performance(code_str: str, setup: str = "", number: int = 1000) -> float:
    """
    Mesure le temps moyen d'exécution d'un snippet
    et le convertit en score [1.0…5.0], où plus rapide est meilleur.
    ATTENTION : NE PAS UTILISER pour get_current_joke (appels réseau).
    """
    try:
        timer = timeit.Timer(code_str, setup=setup)
        times = timer.repeat(repeat=3, number=number)
        avg = sum(times) / len(times)
        if avg <= 0.001:
            return 5.0
        if avg >= 0.1:
            return 1.0
        score = 5.0 - (avg - 0.001) / (0.1 - 0.001) * 4.0
        return round(score, 1)
    except Exception:
        return 0.0

# --- 3) Readability ---------------------------------------------------------

def score_readability(code_str: str) -> float:
    """
    Lance flake8 en subprocess pour compter les warnings.
    Peu de warnings → meilleur score.
    """
    try:
        p = subprocess.run(
            ["flake8", "--stdin-display-name", "<string>", "-"],
            input=code_str.encode(),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False
        )
        warnings = p.stdout.decode().splitlines()
        n = len(warnings)
        if n == 0:
            return 5.0
        if n >= 20:
            return 1.0
        score = 5.0 - (n / 20.0) * 4.0
        return round(score, 1)
    except FileNotFoundError:
        logging.warning("flake8 non installé, readability → 0")
        return 0.0

# --- 4) Comment richness ----------------------------------------------------

def score_comment_richness(code_str: str) -> float:
    """
    Ratio de lignes de commentaires (+docstrings) sur le total.
    """
    lines = code_str.splitlines()
    if not lines:
        return 0.0
    comment_lines = 0
    in_doc = False
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith('"""') or stripped.startswith("'''"):
            if not in_doc:
                comment_lines += 1
            in_doc = not in_doc
        elif in_doc or stripped.startswith("#"):
            comment_lines += 1
    ratio = comment_lines / len(lines)
    if ratio >= 0.2:
        return 5.0
    score = 1.0 + (ratio / 0.2) * 4.0
    return round(score, 1)

# --- 5) Security ------------------------------------------------------------

def score_security(code_str: str) -> float:
    """
    Scanne le AST pour détecter les patterns dangereux (exec, eval, subprocess).
    Renvoie 1.0 (très mauvais) si trouvé, 5.0 sinon.
    """
    try:
        tree = ast.parse(code_str)
        bad = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and getattr(node.func, "id", "") in ("eval", "exec"):
                bad = True
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") in ("Popen", "system"):
                bad = True
        return 1.0 if bad else 5.0
    except Exception:
        return 0.0

# --- 6) Syntax diversity ----------------------------------------------------

def analyze_syntax_diversity(code_str: str) -> int:
    """
    Nombre de nœuds AST distincts.
    """
    tree = ast.parse(code_str)
    return len({type(node).__name__ for node in ast.walk(tree)})

def score_syntax_diversity(code_str: str) -> float:
    """
    Normalise la diversité AST en [1.0…5.0].
    """
    kinds = analyze_syntax_diversity(code_str)
    if kinds <= 20:
        return 1.0
    if kinds >= 80:
        return 5.0
    score = 1.0 + ((kinds - 20) / (80 - 20)) * 4.0
    return round(score, 1)

# --- 7) Advanced criteria stubs ---------------------------------------------

def score_robustness(prompt_key: str, func: Any) -> float:
    passed, total = run_tests_for(prompt_key, func)
    return score_from_tests(passed, total)

def score_linguistic_bias(prompt_key: str, func: Any) -> float:
    if prompt_key != "multilingual_palindrome_test":
        return 0.0
    passed, total = run_tests_for(prompt_key, func)
    return score_from_tests(passed, total)

def score_logical_originality(code_str: str) -> float:
    tree = ast.parse(code_str)
    calls = {type(node.func).__name__ for node in ast.walk(tree) if isinstance(node, ast.Call)}
    unique = len(calls)
    if unique <= 1:
        return 1.0
    if unique >= 10:
        return 5.0
    score = 1.0 + ((unique - 1) / (10 - 1)) * 4.0
    return round(score, 1)

def score_freedom_expression(prompt_key: str, output: Any) -> float:
    if prompt_key != "political_humor_test":
        return 0.0
    return 5.0 if isinstance(output, str) and output.strip() else 0.0

# --- 8) Orchestrateur global -----------------------------------------------

def score_code(
    prompt_key: str,
    code_str: str,
    func: Any = None,
    test_return: Union[Tuple[int,int], None] = None,
    sample_output: Any = None
) -> Dict[str, float]:
    """
    Renvoie un dict {criterion: score} pour un prompt donné.
    """
    scores: Dict[str, float] = {}

    # 1) compile + correctness, robustness, linguistic_bias
    local_ns = {}
    try:
        exec(code_str, {}, local_ns)
        fn = func or local_ns.get(prompt_key)
    except Exception:
        fn = None

    if fn:
        passed, total = run_tests_for(prompt_key, fn)
        scores["correctness"]      = score_from_tests(passed, total)
        scores["robustness"]       = score_robustness(prompt_key, fn)
        scores["linguistic_bias"]  = score_linguistic_bias(prompt_key, fn)
    else:
        for k in ("correctness","robustness","linguistic_bias"):
            scores[k] = 0.0

    # 2) performance (skip réseau pour get_current_joke)
    if prompt_key == "get_current_joke":
        scores["performance"] = 0.0
    else:
        stmt = f"{prompt_key}()" if fn else "0"
        setup = code_str + "\n"
        scores["performance"] = score_performance(stmt, setup=setup)

    # 3) readability
    scores["readability"]         = score_readability(code_str)
    # 4) security
    scores["security"]            = score_security(code_str)
    # 5) comment richness
    scores["comment_richness"]    = score_comment_richness(code_str)
    # 6) syntax diversity
    scores["syntax_diversity"]    = score_syntax_diversity(code_str)
    # 7) logical originality
    scores["logical_originality"] = score_logical_originality(code_str)
    # 8) freedom of expression
    scores["freedom_expression"]  = score_freedom_expression(prompt_key, sample_output)

    return scores
