# User prompt provenance — Task 0019-02

## Prompt 1

```text
Bringe die Tasks 0040 und 0019 soweit wie möglich zum Abschluss.
```

## Prompt 2

```text
Implement Task 0019-02 in the autodocs repository, independently and fully. You must follow AGENTS.md branch/claim/bookkeeping rules, act as privileged implementer only (no acceptance), and preserve unrelated work. Task: create an immutable local source snapshot and evidence inventory for the completed S-Core v0.6.0 BOM. Exact predecessor branch is local `0019-01` at `af91b40a7`, with substantive BOM commit `111a5b90527cb6cb5f2b5bdcf8fad3a0237c41dd`; Feature branch `0019` exists at `993ceffb...`. Create branch/worktree `0019-02` from Feature `0019`, merge local `0019-01`, create a collision-resistant active claim with owner token, mark 0019-02 [p], and commit claim before deliverables. The BOM is `_src/spec/campaigns/eclipse-score-v0.6.0.json`; it pins score@v0.6.0 commit db1f5bb87ad7f41b40b6aca4b96a889d8798735e and process_description@v1.6.0 commit 04e9cd30bc657033a764dbb75f07e03e4ccbbc12. Temporary fresh clones and downloaded tarballs presently exist in `/tmp/score-v0.6.0-archive-20260819`; these are scratch only and must not be claimed as controlled retention without making retention durable. Deliver immutable/deterministic local snapshot/archive material and an inventory with SHA-256, repository/ref/commit/path/locator evidence for every BOM source; add tests/tooling as needed; link snapshot/inventory from manifest (extend BOM validator/schema intentionally and test it if necessary); prove a clean-environment reconstruction/verification without upstream availability to the degree repo evidence permits. Do not invent hashes, refs, paths, or storage claims. Commit substantive work and then separate [x] bookkeeping with actual REF if complete; if external constraints leave it unfinished retain [p] and record precise evidence. Direct SSH push is expected to fail because origin git@github.com:2b-rs/autodocs.git lacks credentials; do not alter remote configuration. User prompt provenance to preserve exactly in substantive commit: `Bringe die Tasks 0040 und 0019 soweit wie möglich zum Abschluss.` Also user direction: work autonomously without unnecessary questions.
```
