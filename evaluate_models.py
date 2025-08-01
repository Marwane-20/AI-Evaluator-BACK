# backend/evaluate_models.py

import os
import json
import ast
import logging
from typing import Any, Dict

from prompts import PROMPT_KEYS
from scoring import (
    run_tests_for,
    score_from_tests,
    score_code,
    analyze_syntax_diversity,
)

RESP_DIR = os.path.join(os.path.dirname(__file__), "responses")
OUT_FILE = os.path.join(os.path.dirname(__file__), "scores.json")


def load_responses(model_name: str) -> Dict[str, str]:
    """
    Charge le JSON de réponses générées par le modèle.
    """
    path = os.path.join(RESP_DIR, f"{model_name}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_model(model_name: str) -> Dict[str, Dict[str, Any]]:
    """
    Pour chaque prompt, compile et score le code généré par `model_name`.
    Renvoie un dict {
      prompt_key: {
        present: bool,
        error: str|null,
        test_counts: { passed, total },
        overall_score: float,
        breakdown: { criterion: score, ... }
      }
    }
    """
    responses = load_responses(model_name)
    report: Dict[str, Dict[str, Any]] = {}

    for key in PROMPT_KEYS:
        code_str = responses.get(key)
        entry: Dict[str, Any] = {
            "present": bool(code_str),
            "error": None,
            "test_counts": {"passed": 0, "total": 0},
            "overall_score": 0.0,
            "breakdown": {}
        }

        if not code_str:
            entry["error"] = "missing code"
            report[key] = entry
            continue

        # --- 1) Tentative de compilation & extraction de la fonction ----
        namespace: Dict[str, Any] = {}
        try:
            exec(code_str, {}, namespace)
        except Exception as e:
            entry["error"] = f"compile error: {e!r}"
            report[key] = entry
            continue

        func = namespace.get(key)
        if not callable(func):
            entry["error"] = "function not found"
            report[key] = entry
            continue

        # --- 2) Exécution des tests unitaires de base -------------------
        passed, total = run_tests_for(key, func)
        entry["test_counts"] = {"passed": passed, "total": total}

        # --- 3) Scoring complet ------------------------------------------
        # score_code renvoie toutes les métriques (dict criterion → score)
        scores = score_code(key, code_str, func=func)

        # calcul de la moyenne globale
        all_scores = [v for v in scores.values() if isinstance(v, (int, float))]
        overall = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0.0

        entry["overall_score"] = overall
        entry["breakdown"] = scores

        report[key] = entry

    return report


def main():
    full_report: Dict[str, Any] = {}
    for fname in os.listdir(RESP_DIR):
        if not fname.endswith(".json"):
            continue
        model = fname[:-5]
        logging.info(f"Evaluating model {model}...")
        full_report[model] = evaluate_model(model)

    # Écriture JSON indenté, UTF-8
    with open(OUT_FILE, "w", encoding="utf-8") as out:
        json.dump(full_report, out, indent=2, ensure_ascii=False)

    print(f"✅ Scores written to {OUT_FILE}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
