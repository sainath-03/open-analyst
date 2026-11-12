"""Execution-accuracy eval: run `python -m tests.eval`. Compares result sets of generated vs gold SQL."""
import json
import time
from decimal import Decimal
from pathlib import Path

from app.db import run_query
from app.graph import ask


def _v(x):
    return round(float(x), 2) if isinstance(x, (int, float, Decimal)) and not isinstance(x, bool) else x


def _cols(res):
    keys = list(res["rows"][0].keys()) if res["rows"] else []
    return [[_v(r[k]) for r in res["rows"]] for k in keys]


def matches(gen, gold) -> bool:
    """Every gold column must appear in the generated result (extra columns are fine).
    Same row count: compare as multisets. Generated has more rows: compare the first
    len(gold) rows, so top-k answers that omit/extend LIMIT still pass."""
    g, e = _cols(gen), _cols(gold)
    n = len(gold["rows"])
    if not e or len(gen["rows"]) < n:
        return not e and not gen["rows"]
    same = len(gen["rows"]) == n
    for col in e:
        ok = False
        for cand in g:
            head = cand if same else cand[:n]
            ok = sorted(map(str, head)) == sorted(map(str, col)) if same else head == col
            if ok:
                break
        if not ok:
            return False
    return True


def main():
    cases = json.loads((Path(__file__).parent / "eval_set.json").read_text())
    ok = 0
    for c in cases:
        t = time.time()
        st = ask(c["q"])
        good = False
        if st.get("result"):
            good = matches(st["result"], run_query(c["gold"], max_rows=10000))
        ok += good
        print(f"{'PASS' if good else 'FAIL'} ({time.time()-t:.0f}s, retries={st.get('attempts',0)}) {c['q']}")
        if not good:
            print("   sql:", st.get("sql"), "| error:", st.get("error"))
    print(f"\nExecution accuracy: {ok}/{len(cases)} = {ok/len(cases):.0%}")


if __name__ == "__main__":
    main()
