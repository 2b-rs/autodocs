"""Shared, generated explanatory header for the report landscape (0043-05)."""
from datetime import datetime, timezone
from html import escape


HEADER_MARKER = 'data-report-header="0043-05"'


def report_page_header(*, generator, data_source, purpose, generated_at=None):
    """Return the uniform report header; timestamps are UTC and regeneration-owned."""
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return '''<style>
.report-context{padding:1.15rem 1.35rem;border:1px solid #d9dce3;border-radius:14px;background:linear-gradient(135deg,#f7f8ff,#eef5ff);margin:1rem 0 1.4rem}
.report-context p{margin:.35rem 0}.report-context-meta{display:flex;gap:.5rem;flex-wrap:wrap;margin:.65rem 0 0}
.report-context-meta span{background:#fff;border:1px solid #d7dcea;border-radius:999px;padding:.28rem .66rem;font-size:.88rem}
</style><section class="report-context" data-report-header="0043-05"><p>%s</p><p>Die Kampagnen-Evidenz für Eclipse S-Core ist als <code>0019-06</code> im Arbeitsbestand nachverfolgbar und wird in dieser Berichtslandschaft ausdrücklich mitgeführt.</p><p class="report-context-meta"><span>Erzeugt: <strong>%s</strong></span><span>Werkzeug: <code>%s</code></span><span>Datenquelle: <code>%s</code></span></p></section>''' % (escape(purpose), escape(timestamp), escape(generator), escape(data_source))


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
