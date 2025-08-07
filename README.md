# 🧠 AI Code Evaluation Backend

## 📂 Structure

```
backend/
├── .env                  # your API keys and URLs (not checked in)
├── prompts.py            # list of prompt keys and test cases
├── scoring.py            # functions to compute all criterion scores
├── evaluate_models.py    # loads responses/*.json → produces scores.json
├── main.py               # (optional) command-line runner for single model
├── responses/            # model response JSONs (one per AI service)
├── requirements.txt      # liste of dependencies to download
├── tests/                # unit tests for the responses and scores file
├── api.py                # api exposure of our scores file
└── scores.json           # output report of all models (generated)
```

## 🔧 Prerequisites

- Python 3.10+

Create & activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate     # Linux / macOS
.\.venv\Scripts\Activate      # Windows PowerShell
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy `example.env` → `.env` and fill your API keys if you plan to regenerate `responses/` via actual API calls:

```ini
OPENAI_API_KEY=…
MISTRAL_API_KEY=…
GEMINI_API_KEY=…
DEEPSEEK_API_KEY=…
```

## 🚀 Usage

### 1. Evaluate All Models in Bulk

This script reads every `<model>.json` in `responses/`, runs all tests & scoring pipelines, and writes a combined report to `scores.json`:

```bash
python evaluate_models.py
```

Upon success you’ll see:

```
✅ Written /path/to/backend/scores.json
```

### 2. Inspect or Serve Scores

- Static JSON: open `scores.json` in your editor or serve it via your preferred web server.
- On-demand (optional): you can call `evaluate_models.py` to evaluate a single model:

```bash
python evaluate_models.py --model gemini
```

(Add argument parsing as needed.)

## 📑 Response / Output Format

The generated `scores.json` has this structure:

```jsonc
{
  "<model_name>": {
    "<prompt_key>": {
      "present": true,
      "error": null,
      "test_counts": {
        "passed": 2,
        "total": 3
      },
      "overall_score": 4.3,
      "breakdown": {
        "correctness":        5.0,
        "robustness":         4.5,
        "linguistic_bias":    4.0,
        "performance":        4.2,
        "readability":        4.7,
        "security":           3.8,
        "comment_richness":   3.5,
        "syntax_diversity":   4.1,
        "logical_originality":3.9,
        "freedom_expression": 4.6
      }
    },
    ...
  },
  ...
}
```

- `correctness` & `robustness` come from your unit-test suite (`prompts.py → TEST_CASES`).
- Other criteria are computed automatically via AST analysis, timing, linting, etc., in `scoring.py`.
- `overall_score` is a 1–5 aggregate (you may customize its formula).

## 🛠️ Customization

- Add or refine test cases in `prompts.py:TEST_CASES`.
- Extend scoring functions in `scoring.py` (e.g., new criteria).
- Integrate real-time API calls to re-generate `responses/<model>.json` if needed (see `main.py`).
- Hook up to a web framework (FastAPI, Flask) to serve `/api/evaluate`.

## 📝 Notes

- Ensure `responses/` contains one `.json` per model, with keys matching `PROMPT_KEYS`.
- If you only want to re-score (no API calls), you can skip providing any keys in `.env`.
- `scores.json` is overwritten on each run of `evaluate_models.py`.

## 🤝 License & Contribution

Feel free to fork and extend! This backend is released under the MIT license. Any improvements—better test coverage, additional criteria, CI integration—are very welcome.
