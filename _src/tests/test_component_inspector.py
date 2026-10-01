import unittest
import subprocess
import os

class TestComponentInspector(unittest.TestCase):
    def test_js_logic(self):
        test_script = """
        const assert = require('assert');
        const fs = require('fs');

        // Mock document and window
        global.window = {
            dispatchEvent: function(evt) {
                global.dispatchedEvents.push(evt);
            }
        };
        global.CustomEvent = function(name, opts) {
            this.name = name;
            this.detail = opts ? opts.detail : null;
        };
        
        class Element {
            constructor(tag) {
                this.tagName = tag;
                this.className = '';
                this.style = {};
                this.children = [];
                this.innerHTML = '';
                this.textContent = '';
                this.value = '';
                this.events = {};
                this.id = '';
            }
            appendChild(child) { this.children.push(child); }
            removeChild(child) { this.children = this.children.filter(c => c !== child); }
            addEventListener(evt, cb) {
                if(!this.events[evt]) this.events[evt] = [];
                this.events[evt].push(cb);
            }
            setAttribute(k, v) { this[k] = v; }
        }

        global.document = {
            createElement: function(tag) { return new Element(tag); },
            body: new Element('body')
        };
        
        global.prompt = function(msg) {
            return "Test rationale";
        };
        global.alert = function(msg) {};

        global.dispatchedEvents = [];

        const ScoreCurator = require('./score_curator.js');
        const ComponentInspector = require('./_src/static/component-inspector.js');

        function findNode(node, tag) {
            if (node.tagName === tag) return node;
            for (let c of node.children) {
                let res = findNode(c, tag);
                if (res) return res;
            }
            return null;
        }

        function findBtn(node, text) {
            if (node.tagName === 'button' && node.textContent === text) return node;
            for (let c of node.children) {
                let res = findBtn(c, text);
                if (res) return res;
            }
            return null;
        }

        function runTests() {
            const container = document.createElement('div');
            const data = {
                identifier: 'COMP-123',
                name: 'Test Component',
                universe: 'Adaptive',
                stereotype: '<<Application Software Component>>',
                mapped_requirements: ['REQ-1', 'REQ-2'],
                implementation_source: 'src/comp.cpp',
                status: 'Draft',
                baseline_digest: 'abcdef'
            };
            
            let lastEnvelope = null;
            const options = {
                curatorId: 'test-user',
                onDecision: function(env) { lastEnvelope = env; }
            };

            ComponentInspector.createInspector(container, data, options);

            // Test 1: Render correct attributes
            const propsPanel = container.children.find(c => c.className === 'inspector-properties');
            const dl = propsPanel.children[0];
            const terms = dl.children.filter(c => c.tagName === 'dt').map(c => c.textContent);
            const values = dl.children.filter(c => c.tagName === 'dd').map(c => c.textContent);
            
            assert.deepStrictEqual(terms, ['Identifier', 'Name', 'Universe', 'Current Stereotype', 'Mapped Requirements', 'Implementation Source', 'Status']);
            assert.deepStrictEqual(values, ['COMP-123', 'Test Component', 'Adaptive', '<<Application Software Component>>', 'REQ-1, REQ-2', 'src/comp.cpp', 'Draft']);

            // Test 2: Stereotype change produces valid updated model
            const stereoSelector = container.children.find(c => c.className === 'inspector-stereotype-selector');
            const select = stereoSelector.children.find(c => c.tagName === 'select');
            
            select.value = '<<Service Component>>';
            select.events['change'][0]({ target: select });
            
            assert.strictEqual(data.stereotype, '<<Service Component>>');
            const stereoDd = dl.children.find(c => c.id === 'inspector-stereotype-val');
            assert.strictEqual(stereoDd.textContent, '<<Service Component>>');
            assert.strictEqual(stereoDd.className, 'badge-updated stereotype-badge');

            // Test 3: Delete action generates valid deletion envelope with required fields
            const deleteBtn = findBtn(container, 'Löschen / Zuordnung aufheben');
            deleteBtn.events['click'][0]();
            
            const overlay = document.body.children[0];
            assert.strictEqual(overlay.className, 'inspector-modal-overlay');
            
            const modal = overlay.children[0];
            const confirmBtn = findBtn(modal, 'Confirm');
            const rationaleInput = findNode(modal, 'textarea');
            rationaleInput.value = 'Removed due to obsolescence';
            
            const selectAction = findNode(modal, 'select');
            selectAction.value = 'unbind_feature';
            
            confirmBtn.onclick();
            
            assert(lastEnvelope);
            assert.strictEqual(lastEnvelope.decision.outcome, 'unbind_feature');
            assert.strictEqual(lastEnvelope.decision.rationale, 'Removed due to obsolescence');
            assert.strictEqual(lastEnvelope.proposal_id, 'COMP-123');
            
            console.log('All tests passed!');
        }
        
        runTests();
        """
        script_path = "test_run.js"
        with open(script_path, "w") as f:
            f.write(test_script)
        
        try:
            result = subprocess.run(["node", script_path], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, f"JS tests failed:\\nstdout:\\n{result.stdout}\\nstderr:\\n{result.stderr}")
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)

if __name__ == '__main__':
    unittest.main()
