"""Shared, generated explanatory header for the report landscape (0043-05)."""
from datetime import datetime, timezone
from html import escape


def report_page_header(*, generator, data_source, purpose, generated_at=None):
    """Return the uniform report header; timestamps are UTC and regeneration-owned."""
    timestamp = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return '''<style>
.report-context{padding:1.15rem 1.35rem;border:1px solid #d9dce3;border-radius:14px;background:linear-gradient(135deg,#f7f8ff,#eef5ff);margin:1rem 0 1.4rem}
.report-context p{margin:.35rem 0}.report-context-meta{display:flex;gap:.5rem;flex-wrap:wrap;margin:.65rem 0 0}
.report-context-meta span{background:#fff;border:1px solid #d7dcea;border-radius:999px;padding:.28rem .66rem;font-size:.88rem}
</style><section class="report-context" data-report-header="0043-05"><p>%s</p><p>Die Kampagnen-Evidenz für Eclipse S-Core ist als <code>0019-06</code> im Arbeitsbestand nachverfolgbar und wird in dieser Berichtslandschaft ausdrücklich mitgeführt.</p><p class="report-context-meta"><span>Erzeugt: <strong>%s</strong></span><span>Werkzeug: <code>%s</code></span><span>Datenquelle: <code>%s</code></span></p></section>''' % (escape(purpose), escape(timestamp), escape(generator), escape(data_source))
