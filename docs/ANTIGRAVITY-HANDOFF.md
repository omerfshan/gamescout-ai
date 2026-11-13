# GameScout devralma kaydı

```json
{
  "date": "2026-11-14",
  "status": "model_pipeline_rewritten_pending_live8b_eval",
  "roles": "Runtime application LLM extracts needs and invents concepts; development agents only implement code. User now requests Antigravity handoff due credits.",
  "implemented": [
    "Original evidence preserved; fake keyword translation removed",
    "False Apple -> Google/Reddit source labels removed; Google unavailable",
    "Community request/discussion JSON/RSS candidate sources",
    "Two inference stages: raw evidence -> player needs -> concept hypotheses",
    "No fixed blueprint or heuristic concept fallback",
    "Strict nested report and evidence ref validation Python/PHP/TS",
    "UI honest demo/no-data/unavailable status; needs/prototype/raw quotes displayed",
    "Paid providers disabled unless server opts in; no internal Ollama URL to browser"
  ],
  "tests": {
    "ai_service": 35,
    "backend_tests": 20,
    "backend_assertions": 82,
    "frontend": "tsc passed;5 runtime parser checks passed"
  },
  "live_eval": {
    "qwen2.5:3b": "2 synthetic cases generated valid schema but poor semantic results; exact no-change case now regression guarded",
    "qwen3:8b": "5.2GB pull started; not completed or evaluated at handoff; check tags and download state before resuming"
  },
  "training_performed": false,
  "remaining": [
    "Finish qwen3:8b download, inspect metadata/digest and run synthetic eval; no production quality claim yet",
    "Verify real source access/rights; registry currently limited AppStore/Reddit, not all internet; Google unavailable",
    "Check current runtime .env model selection (do not reveal credentials), not just .env.example",
    "Browser and live API/model E2E validation",
    "Later: persistent asynchronous jobs; current HTTP Python bridge remains synchronous"
  ],
  "paths": {
    "root": "/Users/omerfaruksahan/Projects/gamescout-ai",
    "evaluation_cases": "GameScout-AI-AI-Service/evaluation/player-needs-v1.json",
    "evaluation_runner": "scripts/evaluate_scout_model.py",
    "model_plan": "docs/ai-model-plan.md",
    "previous_3b_results": ".orchestra/reports/model-evaluation-qwen25-3b.json"
  },
  "git": "Remain main; preserve existing uncommitted user changes; no commit or push this turn."
}
```

## Sonraki doğrulama

```bash
.orchestra/tools/bin/ollama list
python3 scripts/evaluate_scout_model.py --live --model qwen3:8b --limit 3
python3 -m unittest discover -s GameScout-AI-AI-Service/tests -v
.orchestra/tools/bin/php GameScout-AI-Backend/vendor/bin/phpunit --configuration GameScout-AI-Backend/phpunit.xml --do-not-cache-result
.orchestra/tools/node/bin/node GameScout-AI-Fronted/node_modules/typescript/bin/tsc --noEmit -p GameScout-AI-Fronted/tsconfig.json
```

Ağsız testlerde model sahteleştirilir. Canlı değerlendirmede yalnızca sentetik test girdileri yerel modele gönderilir; sonuçlar insan incelemesi ister. Eğitim veya gerçek pazar doğruluğu anlamına gelmez.
