import os
import json
import glob

# Ensure directories exist
os.makedirs('_src/spec/records/score', exist_ok=True)
os.makedirs('score', exist_ok=True)

# Ingest evidence
with open('eclipse-score-v0.6.0-curation-review/evidence.json', 'r') as f:
    evidence = json.load(f)

# Ingest inventory
with open('_src/spec/campaigns/snapshots/eclipse-score-v0.6.0/inventory.json', 'r') as f:
    inventory = json.load(f)

# Dump dummy/basic JSON records
domains = {
    'SCORE_CORE.json': 'os',
    'SCORE_COM.json': 'communication',
    'SCORE_DIAG.json': 'diagnostic',
    'SCORE_MEM.json': 'memory',
    'SCORE_CRYPTO.json': 'crypto',
    'SCORE_PROCESS.json': 'process',
    'SCORE_SAFETY.json': 'safety'
}

inventory_sources = inventory.get('sources', [])
inventory_artifacts = []
for s in inventory_sources:
    inventory_artifacts.extend(s.get('artifacts', []))

for filename, keyword in domains.items():
    records = []
    if 'candidate_manifest' in evidence:
        for c in evidence['candidate_manifest']:
            if keyword in c.get('canonical_id', '').lower():
                records.append(c)
    
    for a in inventory_artifacts:
        if keyword in a.get('path', '').lower():
            records.append(a)

    with open(f'_src/spec/records/score/{filename}', 'w') as f:
        json.dump({"records": records}, f, indent=2)

# Generate HTML
pages = [
    ('score/index.html', 'Main S-Core Overview', 'Platform overview, architecture block diagram, categorized component cards with status badges'),
    ('score/core.html', 'Execution Environment', 'Detailed Execution Environment page with records and requirement cards.'),
    ('score/communication.html', 'IPC & Communication', 'Detailed IPC & Communication page.'),
    ('score/diagnostic_adapter.html', 'Diagnostic Adapter', 'Detailed Diagnostic Adapter page.'),
    ('score/memory.html', 'Memory & Persistence', 'Detailed Memory & Persistence page.'),
    ('score/crypto.html', 'Crypto & Key Storage', 'Detailed Crypto & Key Storage page.'),
    ('score/process.html', 'Process & Governance', 'Process description and governance page.')
]

html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
</head>
<body data-domain="explore">
    <header>
        <nav>
            <ul>
                <li>Explore</li>
                <li>Trace</li>
                <li>Curate</li>
                <li>Review</li>
                <li>Work</li>
                <li>Reports</li>
            </ul>
        </nav>
        <div class="universe-switcher" data-active="Score">Score Active</div>
        <div class="toggles">Theme/Density</div>
        <select class="language-selector"><option>EN</option></select>
        <input type="search" class="search-bar" placeholder="Search...">
        <button class="feedback-dialog-btn">Feedback</button>
    </header>
    <main>
        <h1>{title}</h1>
        <div class="content">{content}</div>
        <section class="review-request-panel">Review Request Panel</section>
        <div class="links">
            <a href="core.html">Core</a>
            <a href="communication.html">Communication</a>
            <a href="diagnostic_adapter.html">Diagnostic</a>
            <a href="memory.html">Memory</a>
            <a href="crypto.html">Crypto</a>
            <a href="process.html">Process</a>
        </div>
    </main>
    <script src="fold.js"></script>
    <script src="review.js"></script>
    <script src="review_request.js"></script>
    <script src="component-graph.js"></script>
    <script src="component-inspector.js"></script>
    <script src="discuss.js"></script>
</body>
</html>"""

for path, title, content in pages:
    with open(path, 'w') as f:
        f.write(html_template.format(title=title, content=content))

print("Generation complete")
