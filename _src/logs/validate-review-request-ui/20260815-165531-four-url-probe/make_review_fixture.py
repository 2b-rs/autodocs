from pathlib import Path
import shutil, sys
root=Path.cwd(); out=Path(sys.argv[1])
sys.path.insert(0, str((root/'_src').resolve()))
import lib_docmodel as dm
tmpl=(root/'_src/templates/page.html.tmpl').read_text(encoding='utf-8')
page={'title':'Review Request Navigation Probe','file':'tests/review-request.html','body_class':'','nav_html':'','main_lead':'','footer':'default','main':[{'t':'rec','attrs':[['class','rec'],['id','AUTOSAR/AP/record/TSyncUserGuide']],'status':{'state':'valid/curator-decided','reason':'confirmed'},'review_request':{'canonical_id':'AUTOSAR/AP/record/TSyncUserGuide','release':'R25-11','content_text':'Time sync description','source_url':'https://example.invalid/spec.pdf','title':'TSync User Guide'},'blocks':[{'t':'html','html':'<p>Content</p>'}]}]}
out.mkdir(parents=True, exist_ok=True); (out/'tests').mkdir(exist_ok=True)
for n in ('review.js','review_request.js','fold.js','style.css'): shutil.copy2(root/n,out/n)
for n in ('cytoscape.min.js','component-graph.js'): (out/n).write_text('',encoding='utf-8')
(out/'tests/review-request.html').write_text(dm.render_page(page,{'default':''},tmpl),encoding='utf-8')
print((out/'tests/review-request.html').resolve())
