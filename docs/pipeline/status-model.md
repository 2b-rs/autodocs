# Statusmodell

Quelle: `_src/SPEC_BUILD_PROCESS.md`, Abschnitt "Statusmodell", ergänzt um
tatsächlich beobachtete Werte in den Records.

Jeder Record trägt genau einen `status.state` und einen `status.reason`.

| `state` | Bedeutung | Darf generiert/publiziert werden? |
|---|---|---|
| `invalid/obsolete` | Vor dem Import entwertet, noch nicht neu bewertet | Nein |
| `valid/auto-approved` | Beide Backends und DB identisch | Ja |
| `valid/corrected` | Beide Backends einig, DB wich ab, DB korrigiert | Ja |
| `invalid/to-be-confirmed` | Backends uneinig, Entscheidung offen | Nein |
| `valid/ai-decided` | Strittiger Fall durch KI entschieden, Rationale vorhanden | Ja |
| `valid/curator-decided` | Strittiger Fall durch Kurator entschieden | Ja |
| `invalid/hypothesized` | Neu vorgeschlagenes Element aus informeller Evidenz | Nein |

## Regeln

1. Nur `valid/*` fließt in Seiten, Indizes und Diagramme.
2. Jeder Statuswechsel erzeugt einen Eintrag in `history[]`.
3. Jeder `valid/*`-Wert braucht Traceability nach `SPEC_TRACEABILITY.md`.
4. `hypothesized/unconfirmed` ist sichtbar in Reports, nie in der
   Publikation.

## History-Eintrag — Pflichtfelder

```json
"history": [
  {
    "campaign": "2026-08-spec-update-after-tool-improvement",
    "date": "2026-08-10",
    "from": "valid/auto-approved",
    "to": "invalid/obsolete",
    "reason": "spec update after tool improvement",
    "actor": "tool"
  }
]
```

Pflichtfelder: `campaign`, `date`, `from`, `to`, `reason`, `actor`
(`tool`|`ai`|`curator`). History wird **nur angehängt, nie umgeschrieben**.

## In den Records tatsächlich beobachtete Zusatzwerte

Diese wurden in `SWS_LOG`-Records gefunden, sind aber im
Prozessdokument nicht explizit aufgeführt — vermutlich Erweiterungen des
Schemas oder ältere/parallele Konventionen:

| Feld | Beobachteter Wert | Interpretation |
|---|---|---|
| `requirement_meta.review_status` | `"pending"` | Wartet auf menschliche/KI-Review, analog zu `invalid/to-be-confirmed`, aber auf Requirement-Text-Ebene statt Feld-Ebene |
| `requirement_meta.review_reason` | `"legacy-desc-import"` | Grund für `pending`-Status: Beschreibung stammt aus älterem Importpfad |
| `requirement_meta.trace[0].review.status` | `accepted`\|`rejected` | Von `review_flags.build_instruction()` als Zielfeld für KI-Agenten vorgeschrieben |

## Beziehung zu Feld-Level-Triage (Phase 2)

Das oben beschriebene `status.state` ist der **Record**-Status. Auf
**Feld**-Ebene (siehe `processes.md` Phase 2) gilt eine eigene, engere
Zustandsmenge je Feld: `valid/auto-approved`, `valid/corrected`,
`invalid/to-be-confirmed` — mit dem Record-Status als Minimum aller
Feld-Zustände (strittig > korrigiert > unverändert).
