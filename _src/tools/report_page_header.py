"""Shared, generated explanatory header for the report landscape (0043-05)."""
import re
from datetime import datetime, timezone
from html import escape


HEADER_MARKER = 'data-report-header="0043-05"'

# Brief names (--bg-card, --border-subtle, --text-primary, --text-secondary)
# are not yet defined in tokens.css; fall back to the live token aliases so
# light/dark and compact density inherit from the design system.
BG_CARD = "var(--bg-card, var(--bg-surface))"
BG_SUBTLE = "var(--bg-subtle)"
BORDER = "var(--border-subtle, var(--border-default))"
TEXT = "var(--text-primary, var(--color-ink))"
TEXT_MUTED = "var(--text-secondary, var(--color-ink-muted))"

REPORT_DENSITY_CSS = (
    "[data-density=\"compact\"] .report-context,"
    "[data-density=\"compact\"] .tr-head,"
    "[data-density=\"compact\"] .cr-head,"
    "[data-density=\"compact\"] .br-head,"
    "[data-density=\"compact\"] .or-head"
    "{padding:var(--space-3) var(--space-4)}"
    "[data-density=\"compact\"] .tr-table th,"
    "[data-density=\"compact\"] .tr-table td,"
    "[data-density=\"compact\"] .cr-table th,"
    "[data-density=\"compact\"] .cr-table td,"
    "[data-density=\"compact\"] .br-table th,"
    "[data-density=\"compact\"] .br-table td,"
    "[data-density=\"compact\"] .or-table th,"
    "[data-density=\"compact\"] .or-table td"
    "{padding:var(--space-1) var(--space-2);font-size:var(--font-size-nav)}"
    "[data-density=\"compact\"] .tr-grid article,"
    "[data-density=\"compact\"] .cr-grid article,"
    "[data-density=\"compact\"] .br-grid article"
    "{padding:var(--space-3)}"
    "[data-density=\"compact\"] .tr-meta span,"
    "[data-density=\"compact\"] .cr-meta span,"
    "[data-density=\"compact\"] .br-meta span,"
    "[data-density=\"compact\"] .or-stats span,"
    "[data-density=\"compact\"] .report-context-meta span"
    "{padding:var(--space-1) var(--space-2);font-size:var(--font-size-nav)}"
)

# Longer literals first so gradient/compound rules are not partially rewritten.
_HEX_TO_TOKEN = (
    ("linear-gradient(135deg,#f7f8ff,#eef5ff)", BG_CARD),
    ("linear-gradient(135deg,#f8faff,#eef4ff)", BG_CARD),
    ("linear-gradient(135deg,#fff7f0,#fff1e8)", BG_CARD),
    ("linear-gradient(180deg,#fff,#f8fbff)", BG_CARD),
    ("linear-gradient(180deg,#fff,#f7fbf5)", BG_CARD),
    ("box-shadow:0 5px 18px rgba(20,40,80,.07)", "box-shadow:none"),
    ("box-shadow:0 3px 14px rgba(20,40,80,.06)", "box-shadow:none"),
    ("box-shadow:0 2px 8px rgba(20,40,80,.06)", "box-shadow:none"),
    ("border:1px solid #d9dce3", "border:1px solid " + BORDER),
    ("border:1px solid #d7dcea", "border:1px solid " + BORDER),
    ("border:1px solid #e4e7ec", "border:1px solid " + BORDER),
    ("border:1px dashed #d0d5e0", "border:1px dashed " + BORDER),
    ("border:1px solid #d6dbe8", "border:1px solid " + BORDER),
    ("border:1px solid #cfe0ff", "border:1px solid " + BORDER),
    ("border:1px solid #eceef2", "border:1px solid " + BORDER),
    ("border:1px solid #ecd9c8", "border:1px solid " + BORDER),
    ("border-bottom:1px solid #e4e7ec", "border-bottom:1px solid " + BORDER),
    ("border-color:#cdead2", "border-color:var(--status-approved)"),
    ("background:#ffffff", "background:" + BG_CARD),
    ("background:#fff", "background:" + BG_CARD),
    ("background:#f7f8fa", "background:" + BG_SUBTLE),
    ("background:#fafbfc", "background:" + BG_SUBTLE),
    ("background:#eef1f6", "background:" + BG_SUBTLE),
    ("background:#e7ecf6", "background:" + BG_SUBTLE),
    ("background:#eef5ff", "background:" + BG_SUBTLE),
    ("background:#eef6ff", "background:" + BG_SUBTLE),
    ("background:#eef8ef", "background:" + BG_SUBTLE),
    ("background:#fdfdff", "background:" + BG_SUBTLE),
    ("background:#dff3e2", "background:" + BG_SUBTLE),
    ("background:#ffedd5", "background:" + BG_SUBTLE),
    ("background:#dbeafe", "background:" + BG_SUBTLE),
    ("background:#dcfce7", "background:" + BG_SUBTLE),
    ("background:#f3e8ff", "background:" + BG_SUBTLE),
    ("background:#fee2e2", "background:" + BG_SUBTLE),
    ("background:#f3f4f6", "background:" + BG_SUBTLE),
    ("background:#fef3c7", "background:" + BG_SUBTLE),
    ("color:#596274", "color:" + TEXT_MUTED),
    ("color:#6b7280", "color:" + TEXT_MUTED),
    ("color:#24344d", "color:" + TEXT),
    ("color:#425064", "color:" + TEXT_MUTED),
    ("color:#1f6b34", "color:var(--status-approved)"),
    ("color:#166534", "color:var(--status-approved)"),
    ("color:#9a3412", "color:var(--status-candidate)"),
    ("color:#92400e", "color:var(--status-candidate)"),
    ("color:#1e40af", "color:var(--status-trace)"),
    ("color:#7e22ce", "color:var(--status-trace)"),
    ("color:#991b1b", "color:var(--status-rejected)"),
    ("color:#4b5563", "color:" + TEXT_MUTED),
)

ROOT_UNIVERSES = (
    '<div class="universes">'
    '<a class="cur" href="adaptive/index.html" data-universe="autosar-adaptive" title="AUTOSAR Adaptive Platform R25-11">Adaptive</a>'
    '<a href="classic/index.html" data-universe="classic" title="AUTOSAR Classic Platform R20-11">Classic</a>'
    '<a href="score/index.html" data-universe="eclipse-score" title="Eclipse S-Core v0.6.0">S-Core</a>'
    '<a href="eclipse-score-v0.6.0-curation-review/de/index.html" class="universe-review" title="Eclipse S-Core Curation Review Portal">Review</a>'
    "</div>"
)

ROOT_LANGS = (
    '<div class="langs">'
    '<a class="cur" href="index.html" title="Deutsch" hreflang="de"><img src="flags/de.svg" alt="DE"></a>'
    '<a href="en/index.html" title="English" hreflang="en"><img src="flags/gb.svg" alt="EN"></a>'
    '<a href="es/index.html" title="Español" hreflang="es"><img src="flags/es.svg" alt="ES"></a>'
    '<a href="pt/index.html" title="Português" hreflang="pt"><img src="flags/pt.svg" alt="PT"></a>'
    '<a href="fr/index.html" title="Français" hreflang="fr"><img src="flags/fr.svg" alt="FR"></a>'
    '<a href="ru/index.html" title="Русский" hreflang="ru"><img src="flags/ru.svg" alt="RU"></a>'
    '<a href="ar/index.html" title="العربية" hreflang="ar"><img src="flags/sa.svg" alt="AR"></a>'
    '<a href="hi/index.html" title="हिन्दी" hreflang="hi"><img src="flags/in.svg" alt="HI"></a>'
    '<a href="ko/index.html" title="한국어" hreflang="ko"><img src="flags/kr.svg" alt="KO"></a>'
    '<a href="zh/index.html" title="中文" hreflang="zh"><img src="flags/cn.svg" alt="ZH"></a>'
    '<a href="nl/index.html" title="Nederlands" hreflang="nl"><img src="flags/nl.svg" alt="NL"></a>'
    "</div>"
)


def rewrite_hex_report_css(text):
    """Replace hardcoded report-landscape hex colors with design-token variables."""
    rewritten = text
    for old, new in _HEX_TO_TOKEN:
        rewritten = rewritten.replace(old, new)
    return rewritten


def ensure_report_density_css(text):
    """Append compact-density rules once, without touching report body data."""
    if "[data-density=\"compact\"] .report-context" in text:
        return text
    idx = text.rfind("</style>")
    if idx < 0:
        return text
    return text[:idx] + REPORT_DENSITY_CSS + text[idx:]


def tokenize_report_markup(text):
    """Tokenize embedded report CSS and attach compact-density rules."""
    return ensure_report_density_css(rewrite_hex_report_css(text))


def active_report_domain(page_file, html=None):
    """Return the domain key that should be current for a report page."""
    if page_file == "extraction-reports.html":
        if html and 'data-domain="extract"' in html:
            return "extract"
        if html and 'data-domain="reports"' in html:
            return "reports"
        return "extract"
    if page_file == "build-reports.html":
        if html and 'data-domain="build"' in html:
            return "build"
        if html and 'data-domain="reports"' in html:
            return "reports"
        return "build"
    if page_file == "curation-report.html":
        return "curate"
    if page_file == "open-reviews.html":
        return "review"
    if page_file in ("traceability-report.html", "mutation-ledger.html"):
        return "trace"
    return "build" if not html or 'data-domain="build"' in html else "reports"


def wrap_legacy_report_shell(html, donor_html, page_file):
    """Replace pre-shell chrome with the current domain header; keep body data."""
    if 'class="shell"' in html:
        return mark_report_shell_chrome(html, page_file)
    title_m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = title_m.group(1) if title_m else page_file
    crumbs_idx = html.find('<nav class="crumbs">')
    main_idx = html.find("<main")
    rest_idx = crumbs_idx if crumbs_idx >= 0 else main_idx
    if rest_idx < 0:
        raise ValueError("legacy report has no crumbs/main: %s" % page_file)
    rest = html[rest_idx:].replace("<main>", '<main id="main">', 1)
    donor_cut = donor_html.find('<nav class="crumbs">')
    if donor_cut < 0:
        raise ValueError("donor report has no crumbs")
    prefix = re.sub(
        r"<title>.*?</title>",
        "<title>%s</title>" % title,
        donor_html[:donor_cut],
        count=1,
        flags=re.S,
    )
    if "data-review-open" in html[:rest_idx] and "data-review-open" not in prefix:
        bar_m = re.search(r'<div class="reviewbar".*?</div>', html[:rest_idx], re.S)
        if bar_m:
            prefix = prefix.replace("</div></header>", bar_m.group(0) + "</div></header>", 1)
    return mark_report_shell_chrome(prefix + rest, page_file)


def mark_report_shell_chrome(html, page_file):
    """Fill nolang gaps: universe switcher, language switcher, current domain."""
    if 'class="universes"' not in html:
        marker = 'data-universe="eclipse-score"'
        idx = html.find(marker)
        if idx >= 0:
            close = html.find("</nav>", idx)
            if close >= 0:
                html = html[:close] + ROOT_UNIVERSES + html[close:]
    if 'class="langs"' not in html:
        marker = '<details class="shell-dropdown shell-prefs"'
        if marker in html:
            html = html.replace(marker, ROOT_LANGS + "\n" + marker, 1)
        elif '<button type="button" class="shell-toggle" data-theme-toggle' in html:
            html = html.replace(
                '<button type="button" class="shell-toggle" data-theme-toggle',
                ROOT_LANGS + "\n"
                '<button type="button" class="shell-toggle" data-theme-toggle',
                1,
            )
    domain = active_report_domain(page_file, html)
    needle = 'data-domain="%s"' % domain
    if needle in html and 'aria-current="page"' not in html:
        html = html.replace(needle, needle + ' aria-current="page"', 1)
    return html


def report_page_header(*, generator, data_source, purpose, generated_at=None):
    """Return the uniform report header; timestamps are UTC and regeneration-owned."""
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return '''<style>
.report-context{padding:var(--space-4) var(--space-5);border:1px solid var(--border-subtle, var(--border-default));border-radius:12px;background:var(--bg-card, var(--bg-surface));color:var(--text-primary, var(--color-ink));margin:1rem 0 1.4rem}
.report-context p{margin:.35rem 0}.report-context-meta{display:flex;gap:var(--space-2);flex-wrap:wrap;margin:.65rem 0 0}
.report-context-meta span{background:var(--bg-subtle);border:1px solid var(--border-subtle, var(--border-default));color:var(--text-secondary, var(--color-ink-muted));border-radius:999px;padding:.28rem .66rem;font-size:.88rem}
%s
</style><section class="report-context" data-report-header="0043-05"><p>%s</p><p>Die Kampagnen-Evidenz für Eclipse S-Core ist als <code>0019-06</code> im Arbeitsbestand nachverfolgbar und wird in dieser Berichtslandschaft ausdrücklich mitgeführt.</p><p class="report-context-meta"><span>Erzeugt: <strong>%s</strong></span><span>Werkzeug: <code>%s</code></span><span>Datenquelle: <code>%s</code></span></p></section>''' % (
        REPORT_DENSITY_CSS,
        escape(purpose),
        escape(timestamp),
        escape(generator),
        escape(data_source),
    )


def upsert_report_page_header(page, *, generator, data_source, purpose, generated_at=None):
    """Insert or replace the generated header without rebuilding report data."""
    blocks = page.get("main")
    if not isinstance(blocks, list):
        raise ValueError("report page has no main block list")
    header = report_page_header(
        generator=generator,
        data_source=data_source,
        purpose=purpose,
        generated_at=generated_at,
    )
    for block in blocks:
        body = block.get("html") if isinstance(block, dict) else None
        if not isinstance(body, str):
            continue
        marker = body.find(HEADER_MARKER)
        if marker >= 0:
            start = body.rfind("<style>", 0, marker)
            end = body.find("</section>", marker)
            if start < 0 or end < 0:
                raise ValueError("malformed generated report header")
            block["html"] = body[:start] + header + body[end + len("</section>"):]
        else:
            block["html"] = header + "\n" + body
        return page
    raise ValueError("report page has no HTML main block")
