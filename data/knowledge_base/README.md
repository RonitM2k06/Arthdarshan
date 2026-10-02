# Knowledge base

`concepts.json` — the concept graph (built from `concepts_src.py`).
`docs/*.md` — short educational notes used for retrieval (RAG).

**Provenance, stated honestly:** every note in `docs/` is **project-authored general education** written for ARTHDARSHAN
(`source_type: project_authored`, `verified_official: false`). They are *not* official publications of SEBI, NSDL, RBI or any
other body, and the product never presents them as such. Numbers in them are illustrative.

To add **official** material (for example a regulator's investor-education PDF that you have downloaded yourself), place the file
in `data/raw/` with a sidecar `<name>.meta.json` (`title`, `source`, `date`, `url`, `verified_official: true`) and run
`python scripts/ingest_knowledge.py`. Retrieval returns the source, title, date and chunk for every answer.
If nothing relevant is retrieved the system answers: "I don't have enough verified information to establish that."
