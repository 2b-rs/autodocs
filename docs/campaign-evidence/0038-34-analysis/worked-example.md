# `0038-34` — worked example of conforming completion evidence

- **Author:** `Tom-Sisko-20260825T091500Z`
- **Status:** draft, illustrative. Reconstructed from the real record of `0038-33`.
- **Source:** `review-0038-33-data-geordi-20260822T203512Z:docs/campaign-evidence/review-0038-33-20260822-data-geordi/report.md`;
  candidate branch `0038-33`, substantive commit `0607d15b76f8b179db7e898252680983c9d187a1`,
  tip `305f83fbad5391e550e3e3746c224216e16f350f`.

`0038-33` is used because the node already cites it as the positive counter-example and
because its negative cases were named in advance by `DEC-0038-002` — which is exactly the
mechanism the drafted requirement asks implementers to follow.

---

## 1. The change and the contract claim it makes

`0038-33` replaced a blanket `AUTO010` prohibition in the aggregate control with an exactly
closed allow-set binding five findings by **line, symbol and full evidence hash**, with
asserted equality.

**Contract claim:** *exactly these five identities are permitted; any sixth, moved, renamed
or byte-changed `AUTO010`, and any `AUTO001`/`AUTO002`/`AUTO009` at all, still fails.*

That claim is what the negative cases are derived from. It touches **gate behaviour** and
**identity** — two of the four covered change kinds — so the requirement applies.

## 2. The negative cases, named before the fix

`DEC-0038-002` named four cases that must go red. The implementer did not invent them; the
decision record specified them as a binding boundary:

| Case | Derived from | Expected |
|---|---|---|
| N1 — a **sixth** `AUTO010` | "exactly five" | red |
| N2 — a **moved** `AUTO010` (same symbol, different line) | line participates in identity | red |
| N3 — a **renamed** symbol | symbol participates in identity | red |
| N4 — **byte-changed** evidence, hash recomputed to match | full hash participates in identity | red |

Plus the unconditional prohibitions retained from the pre-existing control: `AUTO001`,
`AUTO002`, `AUTO009` each red.

## 3. Criterion (1) — red-first, with real command and output

Each case is run as its own single-test process, so that one failure cannot be masked by
another. This is what the reviewer independently reproduced:

```
$ python3 -m unittest _src.tests.test_automation_safety.<TestCase>.test_rejects_a_sixth_auto010 -v
...
OK   (1 test)
```

and the assertion itself, invoked directly without the `assertRaises` wrapper, so that the
red is observed rather than inferred from a passing negative test:

```
$ python3 -c "…; assert_runner_transaction_control(findings_plus_sixth)"
Traceback (most recent call last):
  …
AssertionError: unexpected AUTO010 identity …
```

**Why the direct invocation matters, and why it belongs in the requirement.** A test named
`test_rejects_a_sixth_auto010` that wraps the call in `assertRaises` is green both when the
guard works and when the test is wrong about what it is calling. Calling the assertion
directly and showing the real `AssertionError` is the red. The reviewer did exactly this,
and the record lists all seven direct invocations.

The strongest form present in this record goes one step further: the reviewer **mutated
real source text and rescanned it with the real `automation_safety.scan_text`** before
calling the aggregate helper — so the finding fed to the guard was produced by the actual
scanner, not hand-constructed. Where that is available, it is the evidence to produce.

## 4. Criterion (2) — named adjacent cases and their results

Adjacent to "an exactly closed allow-set on five identities" are:

| Adjacent case | Result |
|---|---|
| A1 — the five baseline identities still pass unchanged | **fine** — green, as required |
| A2 — `AUTO001`, `AUTO002`, `AUTO009` injected separately | **fine** — each red, blanket prohibition preserved |
| A3 — protected blobs unchanged by the substantive commit | **fine** — `runner_transaction.py`, `automation_safety.py`, `automation_safety_policy.json`, `validate.py` byte-identical before and after (blob hashes recorded) |

All three turned out fine. Under the drafted criterion (2) **that is a pass** — the
obligation is to name where you looked, not to find something. A3 in particular is the
adjacent case that matters most for a gate change: it establishes that the scope of the
change is the test module only and that no policy, scanner or runtime was quietly widened.

## 5. Criterion (3) — property test

**Not applicable here, and stated as such.** `0038-33` asserts an invariant over a fixed
five-element allow-set, not over an open set produced by deduplication, merging, closure
or ordering. Enumerating all four negative directions is complete for a closed set of that
size, so a property test would add generated cases without adding coverage.

The contrasting case is `0038-31`, where the change asserted a multiset-union invariant
over an open set of findings — there hand-enumeration provably ran out (ten tests missed
the line-collision case) and the property test with **10,000 cases** was what closed it.

Stating "not applicable, because the invariant is over a closed enumerated set" **is**
conforming evidence. Silence is not.

## 6. What this example does not show

Surfaced deliberately rather than left implicit:

- The recorded verdict on `0038-33` is **`inconclusive`**, not `accepted` — on an
  authority/package boundary (a 30-item prerequisite closure outside the assignment), with
  no technical nonconformity found. This example demonstrates conforming *evidence*, not a
  completed acceptance.
- Criteria (1) and (2) here are reconstructed in the drafted format from a record that
  predates the requirement. The commands and results are real and are taken from the
  review record; the tabular presentation is this draft's proposal.
