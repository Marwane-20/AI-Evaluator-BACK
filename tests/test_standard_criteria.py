import os, json, pytest
from prompts import PROMPT_KEYS
from scoring import run_tests_for

RESP_DIR   = os.path.join(os.path.dirname(__file__), "..", "responses")
SCORES_JSON= os.path.join(os.path.dirname(__file__), "..", "scores.json")

@pytest.mark.parametrize("model_file", os.listdir(RESP_DIR))
def test_technical_quality_matches(model_file):
    if not model_file.endswith(".json"):
        pytest.skip()
    model = model_file[:-5]
    resp = json.load(open(os.path.join(RESP_DIR, model_file), encoding="utf-8"))
    scores = json.load(open(SCORES_JSON, encoding="utf-8"))[model]

    for key in PROMPT_KEYS:
        code = resp.get(key)
        if not code:
            pytest.skip(f"{model}.{key}: no code to test")
        # Compile & extract
        local_ns = {}
        exec(code, {}, local_ns)
        func = local_ns.get(key)
        if not callable(func):
            pytest.skip(f"{model}.{key}: no function")
        passed, total = run_tests_for(key, func)
        if total == 0:
            pytest.skip(f"{key}: no test cases defined")
        # expected technical_quality = round((passed/total)*5, 1)
        expected = round((passed/total)*5, 1)
        actual   = scores[key]["standard"]["technical_quality"]
        assert actual == expected, f"{model}.{key}: expected {expected} got {actual}"
