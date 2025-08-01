import os, json, pytest, ast
from prompts import PROMPT_KEYS, TEST_CASES
from scoring import run_tests_for, analyze_syntax_diversity

SCORES_JSON= os.path.join(os.path.dirname(__file__), "..", "scores.json")
RESP_DIR   = os.path.join(os.path.dirname(__file__), "..", "responses")

@pytest.mark.parametrize("model_file", os.listdir(RESP_DIR))
def test_robustness_and_syntax(model_file):
    if not model_file.endswith(".json"):
        pytest.skip()
    model = model_file[:-5]
    resp   = json.load(open(os.path.join(RESP_DIR, model_file), encoding="utf-8"))
    scores = json.load(open(SCORES_JSON, encoding="utf-8"))[model]

    for key in PROMPT_KEYS:
        code = resp.get(key)
        if not code:
            pytest.skip(f"{model}.{key}: missing code")
        # compile & func
        ns = {}
        exec(code, {}, ns)
        func = ns.get(key)
        if not callable(func):
            pytest.skip(f"{model}.{key}: no function")
        # robustness: edge tests
        edge_key = f"{key}_edge"
        if edge_key in TEST_CASES:
            passed, total = run_tests_for(edge_key, func)
            if total > 0:
                expected = round((passed/total)*5,1)
                actual   = scores[key]["advanced"]["robustness"]
                assert actual == expected, f"{model}.{key} robustness {expected}≠{actual}"
        # syntax_diversity
        sd = analyze_syntax_diversity(code)
        actual_sd = scores[key]["advanced"]["syntax_diversity"]
        assert isinstance(actual_sd, int) and actual_sd == sd
