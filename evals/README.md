# Offline evaluation

`evals/run_eval.py` checks observable artifacts in an already completed session. The checked-in cases are platform-neutral and contain no live repository URLs or credentials.

```bash
python evals/run_eval.py --session /path/to/session --eval-id 1
```

Use `python -m unittest discover -s tests -v` for deterministic script behavior, HTTP mocks, identity and integrity failures, knowledge filtering, and dry-run payload tests. Live GitHub writes are deliberately excluded.
