"""Build data/knowledge_base/concepts.json from concepts_src.py and sanity-check the graph."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "data" / "knowledge_base"
sys.path.insert(0, str(KB))
sys.path.insert(0, str(ROOT))


def main() -> int:
    from concepts_src import CONCEPTS
    from ai.misconception.taxonomy import MISCONCEPTION_IDS

    ids = {c["id"] for c in CONCEPTS}
    problems = []
    for c in CONCEPTS:
        for r in c["related"]:
            if r not in ids:
                problems.append(f"{c['id']}: unknown related concept {r}")
        for m in c["misconceptions"]:
            if m not in MISCONCEPTION_IDS:
                problems.append(f"{c['id']}: unknown misconception {m}")
        for q in c["quiz"]:
            if not 0 <= q["correct_index"] < len(q["options"]):
                problems.append(f"{q['id']}: bad correct_index")
            for o in q["options"]:
                if o["misconception_id"] and o["misconception_id"] not in MISCONCEPTION_IDS:
                    problems.append(f"{q['id']}: unknown misconception {o['misconception_id']}")
    if problems:
        print("\n".join(problems))
        return 1
    (KB / "concepts.json").write_text(json.dumps(CONCEPTS, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[ok] {len(CONCEPTS)} concepts, {sum(len(c['quiz']) for c in CONCEPTS)} quiz questions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
