import os
import json
import pytest

from scoring import run_tests_for, score_from_tests
from prompts import PROMPT_KEYS, TEST_CASES

# noms des fichiers JSON (sans .json)
MODELS = ["openai_gpt4", "gemini", "mistralai", "deepseek"]

RESPONSES_DIR = os.path.join(
    os.path.dirname(__file__), os.pardir, "responses"
)

@pytest.mark.parametrize("model", MODELS)
@pytest.mark.parametrize("prompt_key", PROMPT_KEYS)
def test_all_prompts(model: str, prompt_key: str):
    # 1) charge le JSON
    path = os.path.join(RESPONSES_DIR, f"{model}.json")
    assert os.path.isfile(path), f"Missing responses/{model}.json"
    data = json.load(open(path, encoding="utf-8"))

    # 2) code_str présent et non vide
    code_str = data.get(prompt_key)
    assert code_str and code_str.strip(), f"{model}.{prompt_key}: code vide"

    # 3) compilation et extraction de la fonction
    local_ns: dict = {}
    try:
        exec(code_str, {}, local_ns)
    except Exception as e:
        pytest.fail(f"{model}.{prompt_key}: code invalide ({e!r})")
    func = local_ns.get(prompt_key)
    assert callable(func), f"{model}.{prompt_key}: pas de fonction {prompt_key}()"

    # 4) s’il y a des cas de test, on les exécute et on exige 100% de réussite
    cases = TEST_CASES.get(prompt_key, [])
    if cases:
        passed, total = run_tests_for(prompt_key, func)
        assert total > 0, f"Aucun cas défini pour {prompt_key}"
        assert passed == total, f"{model}.{prompt_key}: {passed}/{total} tests passés"
    # sinon, on s'arrête ici (on a déjà validé la présence et la compile)
