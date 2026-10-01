# Requirements-Analyse: Worker-Isolation und vereinfachte Check-in-Semantik

**Status:** RE-Arbeitsprodukt. Informativ bis zur Umsetzung durch Feature `0041`.
**Erhoben:** 2026-08-18, Requirements-Engineer-Funktion nach `docs/pipeline/process-roles.md`.
**Anlass:** Die Entwicklungspipeline steht still.

## 1. Anforderung im Originalwortlaut (`RQ-SRC-02`)

> Ich habe im worktree aufgeräumt. FYI: Der Grunt hat die Wahrheit gesagt. Ich
> hatte unter /tmp/autodocs einen symlink .git ->
> /Users/tobias.anton/devel/autodocs/.git erstellt und in /tmp einen git restore
> ausgeführt. So ist der Worktree für den Grunt entstanden. Er hat darin dann
> seinen Substantial Commit gemacht und *danach* das [x] bei 0038-18 gesetzt,
> aber nur in seiner lokalen TODO. Sein Vorgehen kann unerwünschte Seiteneffekte
> haben. Schlimmer ist aber, das bei diesem Vorgehen immer unerwünschte Branches
> entstehen, die nicht der nötigen Namenskonvention entsprechen und die zudem
> die Sicht auf den Haupt-Worktree in devel beeinflussen. Ist die
> Namenskonvention fürs Branching eigentlich schon festgelegt? Ich habe jetzt
> folgende Dinge entschieden und bitte dich die Requirements aufzunehmen und
> direkt gemäß Prozess mithilfe geeigneter Sub-Agenten (Sonnet oder Haiku)
> umzusetzen: 1. Sekundäre Worktrees für Worker werden auf git clone/git push
> umgestellt, 2. der bookkeeping commit für die Transition von [p] auf [x] oder
> [w] soll entfallen. Stattdessen soll im check-in commit des substantial commit
> die Ticket-ID und eine base-ref referenziert werden, gegen die die änderung
> gemacht wurde. 3. Das REF-tagging wird in Zukunft Bestandteil des übergangs
> von [x] auf [✓], ist also als Review-Step nachgelagert und in vielen Fällen
> optional. Wir müssen jetzt dringend schauen, dass wir den Workflow zum Laufen
> kriegen, denn die Entwicklungspipeline steht momentan still. Der aktuelle
> runner-Workflow leider ist insofern unvollständig, als dass es keine
> Festlegung darüber gibt wer den worktree und den branch erstellen muss, in dem
> die grunts letztlich arbeiten. Es ist auch fraglich, ob sie das in ihrer
> Sandbox überhaupt könnten. In dem Tool, das den Workflow technisch umsetzt
> (perplexity-cpu-load.js + run-loop.sh) sind Funktionen zum Branching und
> Merging jedenfalls nicht vorgesehen. Was können wir tun?

## 2. Ist-Zustand, belegt

| Nr. | Beobachtung | Beleg |
|---|---|---|
| W1 | `/tmp/autodocs/.git` ist ein **Symlink** auf `devel/autodocs/.git`. Beide Bäume teilen damit Objektspeicher, Refs, **HEAD und Index**. Ein Commit im einen bewegt den `HEAD` des anderen; dessen Arbeitsbaum bleibt stehen. | `ls -la /tmp/autodocs/.git` |
| W2 | Genau daraus entstand der Eindruck, `0038-18` sei nie begonnen worden: `main` zeigte auf den Commit, `devel`s Arbeitsbaum hielt den Vorzustand. Der Grunt hatte korrekt gearbeitet und sein `[x]` in `/tmp/autodocs/TODO.md` gesetzt. | `git diff 356f2bff7` war leer |
| W3 | Der reguläre Provisioner nutzt `git worktree add` auf fest verdrahtetem Branch `tmp-work` — nicht die Item-ID-Konvention. Der Symlink-Aufbau umgeht ihn ganz und ist für `git worktree list` unsichtbar. | `_src/tools/provision_tmp_worktree.sh:19,58` |
| W4 | Keines der drei Workflow-Werkzeuge enthält **irgendeine** Branch-, Merge-, Clone- oder Push-Funktion. | 0 Treffer in 9527 Zeilen |
| W5 | Die Branch-Namenskonvention **ist** festgelegt (nackte Item-IDs, Task vom Feature-Branch). Es fehlt die Zuständigkeit und die technische Umsetzung, nicht die Konvention. | `docs/pipeline/branch-workflow.md` |
| W6 | Sandboxed Agenten dürfen Git **nicht** direkt ausführen. Sie können den Branch also nicht selbst anlegen. | `SANDBOX.md` |

## 3. Anforderungen mit stabilen IDs

### 3.1 Worker-Isolation (Kundenentscheidung 1)

| ID | Anforderung |
|---|---|
| `RQ-WT-01` | Sekundäre Arbeitsbäume für Worker entstehen durch `git clone`, nicht durch `git worktree` und nicht durch einen `.git`-Symlink. |
| `RQ-WT-02` | Der Klon hat eigenen Objektspeicher, eigene Refs, eigenen `HEAD` und eigenen Index. Arbeit im Klon verändert den Haupt-Arbeitsbaum in `devel` nicht. |
| `RQ-WT-03` | Ergebnisse gelangen ausschließlich per `git push` in das kanonische Repository. |
| `RQ-WT-04` | Der Klon wird auf dem Branch bereitgestellt, der der Item-ID der zugewiesenen Aufgabe entspricht, gemäß der bestehenden Konvention. |
| `RQ-WT-05` | Branch und Klon werden von der **privilegierten Wirtsseite** erzeugt, bevor der Grunt Arbeit erhält. Der Grunt legt weder Branch noch Klon an. |
| `RQ-WT-06` | Ein Push, der nicht auf den Branch der eigenen Item-ID zielt, wird abgewiesen. |

### 3.2 Check-in-Semantik (Kundenentscheidung 2)

| ID | Anforderung |
|---|---|
| `RQ-CI-01` | Der separate Bookkeeping-Commit für den Übergang `[p]` → `[x]`/`[w]` entfällt. |
| `RQ-CI-02` | Der substantielle Check-in-Commit nennt die **Ticket-ID** der Aufgabe. |
| `RQ-CI-03` | Er nennt die **Base-Ref**, gegen die die Änderung erfolgte. |
| `RQ-CI-04` | Ticket-ID und Base-Ref stehen maschinenlesbar an definierter Stelle der Commit-Nachricht. |
| `RQ-CI-05` | Der Markerstand ist aus Commit-Metadaten ableitbar; der Zweischritt mit Hash-Abhängigkeit entfällt ersatzlos. |

### 3.3 REF-Tagging (Kundenentscheidung 3)

| ID | Anforderung |
|---|---|
| `RQ-REF-01` | Das `REF`-Tagging ist nicht mehr Bedingung für `[x]`/`[w]`. |
| `RQ-REF-02` | Es wird Bestandteil des Übergangs `[x]` → `✓` und damit ein nachgelagerter Review-Schritt. |
| `RQ-REF-03` | In vielen Fällen ist es optional; wann es verpflichtend bleibt, ist ausdrücklich zu benennen. |

## 4. RE-Befunde

**Befund G — Die Symlink-Konstruktion war die Ursache, nicht ein Agentenfehler.**
Der zuvor erhobene Vorwurf einer Falschmeldung gegen die implementierende Session
ist gegenstandslos und hiermit zurückgenommen. `W1`/`W2` erklären den Befund
vollständig. Lehre für die Personas: Ein abweichender Arbeitsbaumzustand belegt
kein Fehlverhalten, solange die Baum-Topologie nicht geprüft ist.

**Befund H — `RQ-CI-05` beseitigt eine belegte Fehlerklasse.**
Der Zweischritt war strukturell fragil: der zweite Commit hängt vom Hash des
ersten ab, kann also erst danach geschrieben werden, und nichts erzwingt ihn.
Vier Tasks stehen heute in diesem Zustand (`0007-01`, `0037-37`, `0038-02`,
`0038-18`). Die Entscheidung entfernt die Ursache, statt sie zu überwachen.

**Befund I — `RQ-WT-05` ist die einzige tragfähige Antwort auf die Zuständigkeitsfrage.**
Grunts dürfen Git nicht ausführen (`W6`), und die Werkzeuge können es nicht
(`W4`). Damit bleibt allein die privilegierte Wirtsseite. Das ist keine
Ermessensentscheidung, sondern die einzige Option, die die Fähigkeitsklassen
nicht verletzt.

**Befund J — Zielkonflikt mit der bisherigen Begründung des Provisioners.**
Dessen Kommentar nennt als Vorteil, dass ein Commit im Worktree „instantly
durable" im gemeinsamen Objektspeicher ist. Genau diese Kopplung ist die
Ursache von `W2`. Der Klon gibt sie bewusst auf: Dauerhaftigkeit entsteht erst
beim Push. Das ist der Preis der Isolation und ausdrücklich gewollt.

**Befund K — `RQ-REF-01/02` berührt die Marker-Semantik im `TODO.md`-Header.**
Dort ist `[x]` heute als „real substantive `REF` committed" definiert. Die
Änderung muss dort, in `AGENTS.md` und in `task-acceptance.md` konsistent
nachgezogen werden, sonst entsteht genau der Widerspruch zwischen Prozessdoku
und Instruktion, der als `T8` aktenkundig ist.

## 5. Offener Punkt

`RQ-WT-06` (Push-Ziel-Prüfung) setzt voraus, dass die Wirtsseite die Item-ID der
laufenden Zuweisung kennt. Ob `perplexity-cpu-loop.js` diese Information heute
führt, ist im Rahmen der Umsetzung zu klären; falls nicht, ist sie ein neuer
Eingabewert des Provisioners.
