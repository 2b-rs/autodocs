from pathlib import Path
import shutil, sys
sys.path.insert(0, str(Path('_src').resolve()))
import lib_docmodel as dm
root=Path.cwd()
tmpl=(root/'_src/templates/page.html.tmpl').read_text(encoding='utf-8')
page={'title':'Review Request Bisect','file':'tests/review-request.html','body_class':'','nav_html':'','main_lead':'','footer':'default','main':[{'t':'rec','attrs':[['class','rec'],['id','AUTOSAR/AP/record/TSyncUserGuide']],'status':{'state':'valid/curator-decided','reason':'confirmed'},'review_request':{'canonical_id':'AUTOSAR/AP/record/TSyncUserGuide','release':'R25-11','content_text':'Time sync description','source_url':'https://example.invalid/spec.pdf','title':'TSync User Guide'},'blocks':[{'t':'html','html':'<p>Content</p>'}]}]}
html=dm.render_page(page, {'default':''}, tmpl)
for base in (root/'_review_request_bisect_tmp', root/'output/_review_request_bisect_tmp'):
    shutil.rmtree(base, ignore_errors=True)
    (base/'tests').mkdir(parents=True)
    for name in ('review.js','review_request.js','fold.js','style.css'):
        shutil.copy2(root/name, base/name)
    for name in ('cytoscape.min.js','component-graph.js'):
        (base/name).write_text('', encoding='utf-8')
    target=base/'tests/review-request.html'
    target.write_text(html, encoding='utf-8')
    print(target)
