#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Einmaliges Bereinigungsskript: Dopplungen in Modul-/Namespace-Guides.

Kanonische Orte:
  - Diagramme leben im Modul-Guide (bekommen dort stabile Anker-IDs);
    Namespace-Guides verweisen stattdessen.
  - Geteilte Erklärtexte leben beim übergeordneten Namespace;
    Unter-/Schwester-Namespaces verweisen stattdessen.
Arbeitet ausschließlich auf den Quellfragmenten unter _src/content/ai/
(libxml2/lxml, keine Textersetzung). Danach: generate.py + validate.py.
"""
import os
import re
from lxml import html as LH
import lxml.html

AI = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                  'content', 'ai') + os.sep

def norm(t):
    return re.sub(r'\s+', ' ', t).strip()

def load(rel):
    raw = open(AI + rel, encoding='utf-8').read()
    return raw, LH.fragment_fromstring(raw)

def save(rel, raw, el):
    new = lxml.html.tostring(el, encoding='unicode')
    if raw.endswith('\n') and not new.endswith('\n'):
        new += '\n'
    open(AI + rel, 'w', encoding='utf-8').write(new)
    print('geschrieben:', rel)

def find_diagram_by_note(el, keyword):
    """(div.diagram, p.diagram-note) dessen Note das Schlüsselwort enthält."""
    for d in el:
        cls = (d.get('class') or '').split()
        if d.tag == 'div' and ('diagram' in cls or 'umlwrap' in cls):
            nxt = d.getnext()
            if nxt is not None and nxt.tag == 'p' and 'diagram-note' in (nxt.get('class') or ''):
                if keyword in norm(nxt.text_content()):
                    return d, nxt
    raise SystemExit(f'Diagramm nicht gefunden: {keyword!r}')

def para_after_h4(el, heading, keyword):
    on = False
    for n in el:
        if n.tag == 'h4':
            on = (norm(n.text_content()) == heading)
            continue
        if on and n.tag == 'p' and keyword in norm(n.text_content()):
            return n
    raise SystemExit(f'Absatz nicht gefunden: {heading!r} / {keyword!r}')

def replace_with(el, victims, replacement_html):
    """Ersetzt die Elementfolge victims durch die Fragmente aus replacement_html."""
    parent = victims[0].getparent()
    assert parent is el or parent is not None
    pos = list(parent).index(victims[0])
    tail = victims[-1].tail
    for v in victims:
        parent.remove(v)
    frags = lxml.html.fragments_fromstring(replacement_html)
    frags = [f for f in frags if not isinstance(f, str)]
    for i, f in enumerate(frags):
        f.tail = '\n' if i < len(frags) - 1 else tail
        parent.insert(pos + i, f)

# ---------------------------------------------------------------- 1. Anker-IDs
def add_ids():
    # Modul com: Diagrammstrecke
    raw, el = load('modules/com/main_01.html')
    for kw, did in [
        ('Ein modelliertes Service Interface erzeugt', 'diag-service-rollen'),
        ('Discovery liefert Handles', 'diag-discovery-proxy'),
        ('Das Subscribe-Ergebnis ist asynchron', 'diag-subscribe-sequenz'),
        ('Auf der Proxy-Seite signalisiert kSubscriptionPending', 'diag-subscription-zustaende'),
        ('Ein Field kombiniert', 'diag-field-sequenz'),
        ('Der beim Skeleton gewählte Modus', 'diag-skeleton-modi'),
        ('Der E2E-Check wird dem Sample-Status', 'diag-e2e-check'),
        ('FVM liefert bzw. prüft Freshness-Werte', 'diag-secoc-fvm'),
        ('InstanceSpecifier wird gegen das Manifest', 'diag-instanzaufloesung'),
    ]:
        d, _ = find_diagram_by_note(el, kw)
        d.set('id', did)
    save('modules/com/main_01.html', raw, el)

    # Modul per
    raw, el = load('modules/per/main_01.html')
    for kw, did in [
        ('Öffnen setzt eine konfigurierte', 'diag-oeffnen-vor-nutzung'),
        ('Update, Finalisierung und Rollback', 'diag-update-rollback'),
    ]:
        d, _ = find_diagram_by_note(el, kw)
        d.set('id', did)
    save('modules/per/main_01.html', raw, el)

    # Modul crypto
    raw, el = load('modules/crypto/main_01.html')
    d, _ = find_diagram_by_note(el, 'Ein modellierter Zugang führt zu einem Slot')
    d.set('id', 'diag-zugangswege')
    save('modules/crypto/main_01.html', raw, el)

    # Namespace ara::sm — Abschnittsanker
    raw, el = load('namespaces/ns_sm_ara_sm_0efb8d/main_01.html')
    for h in el:
        if h.tag == 'h4' and norm(h.text_content()) == 'Anwendungskontext':
            h.set('id', 'guide-anwendungskontext')
    save('namespaces/ns_sm_ara_sm_0efb8d/main_01.html', raw, el)

    # Namespace ara::crypto — Abschnittsanker
    raw, el = load('namespaces/ns_crypto_ara_crypto_aacf86/main_01.html')
    ids = {'Rolle im Crypto Stack': 'guide-rolle-crypto-stack',
           'Providerzugänge': 'guide-providerzugaenge',
           'Gemeinsame Sicherheitsregeln': 'guide-sicherheitsregeln'}
    for h in el:
        if h.tag == 'h4' and norm(h.text_content()) in ids:
            h.set('id', ids[norm(h.text_content())])
    save('namespaces/ns_crypto_ara_crypto_aacf86/main_01.html', raw, el)

# ------------------------------------------- 2. Diagramm-Dopplungen → Verweise
COM = '../modules/com.html'

def fix_diagram_dupes():
    # ns ara::com: 5 kopierte Diagramme → Linkliste auf den Modul-Guide
    raw, el = load('namespaces/ns_com_ara_com_4a3210/main_01.html')
    victims = []
    for kw in ['Ein modelliertes Service Interface erzeugt',
               'Das Subscribe-Ergebnis ist asynchron',
               'Ein Field kombiniert',
               'Der beim Skeleton gewählte Modus',
               'Auf der Proxy-Seite signalisiert kSubscriptionPending']:
        d, n = find_diagram_by_note(el, kw)
        victims += [d, n]
    victims.sort(key=lambda x: list(el).index(x))
    replace_with(el, victims, f'''<p>Die zugehörigen Abläufe sind im Guide des Moduls <a href="{COM}">ara::com — Communication Management</a>, Abschnitt „Instanzbezug und Bindungsabstraktion“, als Diagramme dokumentiert:</p>
<ul>
<li><a href="{COM}#diag-service-rollen">Kollaborationsdiagramm „Service Interface, Proxy, Skeleton und Bindung“</a></li>
<li><a href="{COM}#diag-subscribe-sequenz">Sequenzdiagramm „Asynchrones Subscribe und Sample-Entnahme“</a></li>
<li><a href="{COM}#diag-field-sequenz">Sequenzdiagramm „Field: Lesen, Schreiben und Update-Benachrichtigung“</a></li>
<li><a href="{COM}#diag-skeleton-modi">Zustandsdiagramm „Verarbeitungsmodi des Skeleton“</a></li>
<li><a href="{COM}#diag-subscription-zustaende">Zustandsdiagramm „Subscription-Zustände auf Proxy-Seite“</a></li>
</ul>''')
    save('namespaces/ns_com_ara_com_4a3210/main_01.html', raw, el)

    # ns ara::com::runtime
    raw, el = load('namespaces/ns_com_ara_com_runtime_ac29a8/main_01.html')
    d, n = find_diagram_by_note(el, 'InstanceSpecifier wird gegen das Manifest')
    replace_with(el, [d, n], f'<p>Der Ablauf ist im Guide des Moduls als Aktivitätsdiagramm dokumentiert: <a href="{COM}#diag-instanzaufloesung">ara::com — Communication Management, Aktivitätsdiagramm „Auflösung des <code>InstanceSpecifier</code> gegen das Manifest“</a>.</p>')
    save('namespaces/ns_com_ara_com_runtime_ac29a8/main_01.html', raw, el)

    # ns apext::com::secoc
    raw, el = load('namespaces/ns_com_apext_com_secoc_eb0f3c/main_01.html')
    d, n = find_diagram_by_note(el, 'FVM liefert bzw. prüft Freshness-Werte')
    replace_with(el, [d, n], f'<p>Das Zusammenspiel von SecOC-Binding und FVM ist im Guide des Moduls als Kollaborationsdiagramm dokumentiert: <a href="{COM}#diag-secoc-fvm">ara::com — Communication Management, Kollaborationsdiagramm „Freshness-Value-Management bei SecOC“</a>.</p>')
    save('namespaces/ns_com_apext_com_secoc_eb0f3c/main_01.html', raw, el)

    # ns ara::com::e2e
    raw, el = load('namespaces/ns_com_ara_com_e2e_f19464/main_01.html')
    d, n = find_diagram_by_note(el, 'Der E2E-Check wird dem Sample-Status')
    replace_with(el, [d, n], f'<p>Der Ablauf beim Empfänger ist im Guide des Moduls als Aktivitätsdiagramm dokumentiert: <a href="{COM}#diag-e2e-check">ara::com — Communication Management, Aktivitätsdiagramm „E2E-geschütztes Event beim Empfänger“</a>.</p>')
    save('namespaces/ns_com_ara_com_e2e_f19464/main_01.html', raw, el)

    # ns ara::per: 2 kopierte Diagramme → ein Verweisabsatz
    raw, el = load('namespaces/ns_per_ara_per_d9a3e9/main_01.html')
    d1, n1 = find_diagram_by_note(el, 'Öffnen setzt eine konfigurierte')
    d2, n2 = find_diagram_by_note(el, 'Update, Finalisierung und Rollback')
    replace_with(el, [d1, n1, d2, n2], '<p>Beide Abläufe sind im Guide des Moduls <a href="../modules/per.html">ara::per — Persistency</a> als Diagramme dokumentiert: <a href="../modules/per.html#diag-oeffnen-vor-nutzung">Sequenzdiagramm „Storage öffnen und nutzen“</a> und <a href="../modules/per.html#diag-update-rollback">Aktivitätsdiagramm „Aktualisierung persistenter Daten“</a>.</p>')
    save('namespaces/ns_per_ara_per_d9a3e9/main_01.html', raw, el)

    # ns ara::crypto: 1 kopiertes Diagramm → Verweis
    raw, el = load('namespaces/ns_crypto_ara_crypto_aacf86/main_01.html')
    d, n = find_diagram_by_note(el, 'Ein modellierter Zugang führt zu einem Slot')
    replace_with(el, [d, n], '<p>Das Zusammenspiel der Zugangswege ist im Guide des Moduls als Diagramm dokumentiert: <a href="../modules/crypto.html#diag-zugangswege">ara::crypto — Cryptography, Diagramm „Zusammenspiel im Crypto Stack“</a>.</p>')
    save('namespaces/ns_crypto_ara_crypto_aacf86/main_01.html', raw, el)

# ----------------------------------------------- 3. Text-Dopplungen → Verweise
def fix_text_dupes():
    # ara::crypto::cryp — drei vom Eltern-Namespace kopierte Abschnitte
    P = 'ns_crypto_ara_crypto_aacf86.html'
    rel = 'namespaces/ns_crypto_ara_crypto_cryp_39bdc3/main_01.html'
    raw, el = load(rel)
    p = para_after_h4(el, 'Rolle im Crypto Stack', 'bündelt den öffentlichen Zugriff')
    replace_with(el, [p], f'<p><code>ara::crypto::cryp</code> enthält die allgemeinen Kryptographie-Schnittstellen des Crypto Stack: den <code>CryptoProvider</code> als Fabrik sowie die Kontext- und Schlüsselschnittstellen für kryptographische Primitive. <a class="docref" href="https://www.autosar.org/fileadmin/standards/R25-11/AP/AUTOSAR_AP_SWS_Cryptography.pdf#page=48">SWS Cryptography §7.3 „Crypto Provider“</a>. Die Einordnung des gesamten Crypto Stack beschreibt der Guide des übergeordneten Namespace: <a href="{P}#guide-rolle-crypto-stack">ara::crypto § „Rolle im Crypto Stack“</a>.</p>')
    p = para_after_h4(el, 'Providerzugänge', 'LoadCryptoProvider() adressiert')
    replace_with(el, [p], f'<p>Die modellierten Zugänge (<code>LoadCryptoProvider()</code>, <code>LoadKeySlot()</code>, <code>LoadWriteableKeySlot()</code>) sind im Guide des übergeordneten Namespace beschrieben: <a href="{P}#guide-providerzugaenge">ara::crypto § „Providerzugänge“</a>.</p>')
    p = para_after_h4(el, 'Gemeinsame Sicherheitsregeln', 'Providergrenzen, Slotrechte')
    replace_with(el, [p], f'<p>Es gelten die gemeinsamen Sicherheitsregeln des Crypto Stack (Providergrenzen, Slotrechte, <code>AllowedUsageFlags</code>, Functional-Cluster-Lebenszyklus); sie sind im Guide des übergeordneten Namespace beschrieben: <a href="{P}#guide-sicherheitsregeln">ara::crypto § „Gemeinsame Sicherheitsregeln“</a>.</p>')
    save(rel, raw, el)

    # ara::sm-Geschwister — gemeinsamer „Anwendungskontext“
    SM = 'ns_sm_ara_sm_0efb8d.html'
    for rel in ['namespaces/ns_sm_apext_sm_a5dc2b/main_01.html',
                'namespaces/ns_sm_ara_sm_s2r_b2e85c/main_01.html']:
        raw, el = load(rel)
        p = para_after_h4(el, 'Anwendungskontext', 'manifest- und integrationsabhängigen Zustandskoordination')
        replace_with(el, [p], f'<p>Es gilt der gemeinsame Anwendungskontext des State Management (manifest- und integrationsabhängige Zustandskoordination, Bewertung von Rückgabewerten und Fehlern in der aufrufenden Rolle); er ist im Guide des Namespace <a href="{SM}#guide-anwendungskontext">ara::sm § „Anwendungskontext“</a> beschrieben.</p>')
        save(rel, raw, el)

    # idsm/nm — wortgleiche generische Interpretation je Namespace spezialisieren
    rel = 'namespaces/ns_idsm_ara_idsm_c9e8a2/main_01.html'
    raw, el = load(rel)
    p = para_after_h4(el, 'Namespace-Grenze', 'Der Namespace bündelt Zugriffsobjekte')
    replace_with(el, [p], '<p class="interp"><strong>Interpretation:</strong> Der Namespace bündelt die Ereignis-, Provider- und Empfänger-Zugriffsobjekte samt Datentypen und Fehlerdarstellung; ihre konkrete Kopplung an Port-Prototypen wird über das Modell und den <code>ara::core::InstanceSpecifier</code> bestimmt.</p>')
    save(rel, raw, el)

    rel = 'namespaces/ns_nm_ara_nm_a7c4d1/main_01.html'
    raw, el = load(rel)
    p = para_after_h4(el, 'Namespace-Grenze', 'Der Namespace bündelt Zugriffsobjekte')
    replace_with(el, [p], '<p class="interp"><strong>Interpretation:</strong> Der Namespace bündelt das handle-basierte Steuerobjekt samt Datentypen und Fehlerdarstellung; die Zuordnung eines <code>NetworkHandle</code> zu konkreten (partiellen) Netzwerken wird über das Modell und den <code>ara::core::InstanceSpecifier</code> bestimmt.</p>')
    save(rel, raw, el)

add_ids()
fix_diagram_dupes()
fix_text_dupes()
print('fertig.')
