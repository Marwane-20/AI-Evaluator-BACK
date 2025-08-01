import os, json, pytest
from prompts import PROMPT_KEYS

SCORES_JSON = os.path.join(os.path.dirname(__file__), "..", "scores.json")

def test_scores_schema_and_types():
    data = json.load(open(SCORES_JSON, encoding="utf-8"))
    for model, prompts in data.items():
        assert set(prompts.keys()) == set(PROMPT_KEYS)
        for key, ent in prompts.items():
            # champs de base
            assert isinstance(ent["present"], bool)
            assert isinstance(ent["passed"], int)
            assert isinstance(ent["total"], int)
            # standard
            std = ent["standard"]
            assert set(std.keys()) == {
                "technical_quality",
                "readability",
                "security",
                "performance",
                "error_handling",
            }
            # tq est float ou null
            tq = std["technical_quality"]
            assert (tq is None) or (isinstance(tq, (int,float)) and 0 <= tq <= 5)
            # les 4 autres sont None
            for c in ["readability","security","performance","error_handling"]:
                assert std[c] is None
            # advanced
            adv = ent["advanced"]
            assert set(adv.keys()) == {
                "robustness",
                "linguistic_bias",
                "syntax_diversity",
                "logical_originality",
                "comment_richness",
                "freedom_expression",
            }
            # syntax_diversity int >0, robustness None|[0..5], les autres None
            assert isinstance(adv["syntax_diversity"], int) and adv["syntax_diversity"] > 0
            rb = adv["robustness"]
            assert (rb is None) or (isinstance(rb,(int,float)) and 0 <= rb <= 5)
            for c in ["linguistic_bias","logical_originality","comment_richness","freedom_expression"]:
                assert adv[c] is None
            # pas d’erreur inattendue
            assert isinstance(ent["error"], (type(None), str))
