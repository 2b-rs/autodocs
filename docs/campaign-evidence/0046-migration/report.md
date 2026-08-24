# Feature 0046 migration/compatibility candidate

Pinned baseline: `c55cca8786d99f91d400f720cbcec616e228a6df`

TODO digest: `sha256:97a124e4fef596616e6026acda128fcb90cff28a01b554974889137a208780d8`

Manifest digest: `sha256:d6bb99803472f207cab4805e6fc4ffdb6a37384eb606c94602a19c3bd016af34`

This is a dormant migration candidate, not activation, Acceptance, or a QA conclusion. Existing governance remains controlling for every deferred or bounded-compatible Feature.

## Result

Exact active-Feature population: **32**. Dispositions: migrated **0**, compatible-with-bounds **1**, deferred **31**.

| Feature | Branch baseline | Work units | Gates | Disposition |
|---|---|---:|---:|---|
| 0046 | `c94e81878eb43ae2bf8c399e6ccdd882447eaf03` | 7 | 3 | `compatible-with-bounds` |
| 0044 | `eeb759a51d24dc4454d72ae1d8c202086054809a` | 13 | 9 | `deferred` |
| 0043 | `6f9a11c119670d32575bd956bc83b7f731b2db70` | 7 | 2 | `deferred` |
| 0041 | `caa7cda9a2a915899d70c04a85936d580bee1a63` | 6 | 2 | `deferred` |
| 0039 | `1973b356b8fef0b9b0bbe4f5054957d12995cccd` | 5 | 0 | `deferred` |
| 0038 | `6491e5609f0a9c6d104518c5d0b2a82fee9a6b15` | 38 | 9 | `deferred` |
| 0037 | `74af28df766ab0e55c4c43dcaebd6631ce40aefb` | 107 | 5 | `deferred` |
| 0035 | `unavailable` | 4 | 0 | `deferred` |
| 0034 | `unavailable` | 4 | 0 | `deferred` |
| 0033 | `993ceffbcea4fa8f0cca16de07ac91cf88fae619` | 24 | 0 | `deferred` |
| 0020 | `unavailable` | 9 | 0 | `deferred` |
| 0027 | `unavailable` | 10 | 0 | `deferred` |
| 0022 | `unavailable` | 2 | 0 | `deferred` |
| 0028 | `unavailable` | 1 | 0 | `deferred` |
| 0029 | `unavailable` | 2 | 0 | `deferred` |
| 0030 | `unavailable` | 2 | 0 | `deferred` |
| 0031 | `unavailable` | 3 | 0 | `deferred` |
| 0032 | `unavailable` | 3 | 0 | `deferred` |
| 0023 | `unavailable` | 11 | 0 | `deferred` |
| 0024 | `unavailable` | 2 | 0 | `deferred` |
| 0025 | `unavailable` | 10 | 0 | `deferred` |
| 0026 | `unavailable` | 2 | 0 | `deferred` |
| 0011 | `unavailable` | 6 | 0 | `deferred` |
| 0012 | `unavailable` | 9 | 0 | `deferred` |
| 0013 | `unavailable` | 11 | 0 | `deferred` |
| 0014 | `unavailable` | 13 | 0 | `deferred` |
| 0015 | `unavailable` | 10 | 0 | `deferred` |
| 0016 | `unavailable` | 15 | 0 | `deferred` |
| 0017 | `unavailable` | 7 | 0 | `deferred` |
| 0018 | `unavailable` | 10 | 0 | `deferred` |
| 0019 | `58b35f1e54cff2b4e718febe2c666cf5e67ae3f5` | 11 | 0 | `deferred` |
| 0007 | `unavailable` | 4 | 0 | `deferred` |

## Interpretation

Feature `0046` is bounded-compatible only with its dormant candidate contracts and trial IP; it lacks a complete issued WTP instance and receives no activation or execution authority. Every other Feature is explicitly deferred because complete Feature-specific WTP/IP evidence and an independent migration decision are absent. Missing Feature branches are recorded as unavailable, never replaced by an invented ref.

## Reproduction

```sh
python3 docs/campaign-evidence/0046-migration/evidence/build_manifest.py --baseline c55cca8786d99f91d400f720cbcec616e228a6df
python3 docs/campaign-evidence/0046-migration/evidence/validate_manifest.py --manifest docs/campaign-evidence/0046-migration/manifest.json --inventory docs/campaign-evidence/0046-migration/evidence/inventory.json
```

A distinct QA participant must independently audit process conformance; this report intentionally contains no QA verdict.
