import sys
import tempfile
import unittest
from pathlib import Path

from lxml import html as LH

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))

import i18n_translate  # pyright: ignore[reportImplicitRelativeImport]
import lib_i18n as i18n  # pyright: ignore[reportImplicitRelativeImport]


class PageContentI18nTests(unittest.TestCase):
    def test_discovers_aria_and_inline_svg_labels_only(self):
        raw = (
            '<p>Normale Prosa</p>'
            '<div aria-label="Ablauf des Prüfprozesses">'
            '<svg><style>.txt{fill:black}</style>'
            '<text>Freigabe</text><text><tspan>Warteschlange</tspan></text>'
            '<path aria-hidden="true" d="M0 0L1 1"/></svg></div>'
        )
        wrapper = LH.fragment_fromstring(raw, create_parent=True)

        self.assertEqual(
            i18n.inline_html_labels(wrapper),
            ["Ablauf des Prüfprozesses", "Freigabe", "Warteschlange"],
        )

    def test_translates_heading_aria_and_inline_svg_without_changing_anchors(self):
        heading = "3.1 Review- und Feedback-Prozesse"
        aria = "Ablauf des Curator-Entscheidungsprotokolls"
        raw = (
            '<h2 class="sect" id="review-processes">%s</h2>'
            '<div id="curator-decision-flow" aria-label="%s">'
            '<svg><text>Freigabe</text><text>queued → claimed</text></svg>'
            '</div>'
        ) % (heading, aria)
        segment_id = i18n.seg_id(heading)
        segments = {segment_id: "3.1 Review and feedback processes"}
        labels = {
            aria: "Curator decision protocol flow",
            "Freigabe": "Approval",
            "queued → claimed": "queued → claimed",
        }
        stat = i18n.Statistik(soll={segment_id}, soll_labels=set(labels))

        translated = i18n.uebersetze_html(
            raw, segments, {}, stat, lab=labels, complete=True
        )
        wrapper = LH.fragment_fromstring(translated, create_parent=True)
        heading_el = wrapper.get_element_by_id("review-processes")
        diagram = wrapper.get_element_by_id("curator-decision-flow")
        svg_text = [el.text for el in diagram.iter("text")]

        self.assertEqual(heading_el.text, "3.1 Review and feedback processes")
        self.assertEqual(diagram.get("aria-label"), "Curator decision protocol flow")
        self.assertEqual(svg_text, ["Approval", "queued → claimed"])
        self.assertEqual(heading_el.get("id"), "review-processes")
        self.assertEqual(diagram.get("id"), "curator-decision-flow")
        self.assertEqual(stat.fehlend, {})
        self.assertEqual(stat.fehlende_labels, {})

    def test_page_title_breadcrumb_and_h1_use_stable_segments(self):
        title = "Prozess der Veröffentlichung — R25-11"
        heading = "Prozess der Veröffentlichung"
        nav_source = '<a href="index.html">Start</a> / Prozess'
        nav_wrapper = LH.fragment_fromstring(nav_source, create_parent=True)
        nav_masked, _tags = i18n.maskiere(nav_wrapper)
        segments = {
            i18n.seg_id(title): "Publication process — R25-11",
            i18n.seg_id(heading): "Publication process",
            i18n.seg_id(nav_masked.strip()): "⟦0⟧ / Process",
        }
        page = {
            "file": "process.html",
            "i18n_complete": True,
            "title": title,
            "nav_html": nav_source,
            "main_lead": "",
            "main": [{"t": "html", "html": "<h1>%s</h1>" % heading}],
        }
        stat = i18n.Statistik(soll=set(segments), soll_labels=set())

        translated = i18n.uebersetze_seite(
            page,
            "en",
            segments,
            {"nav_start": "Home"},
            stat,
            lab={},
        )

        self.assertEqual(translated["title"], "Publication process — R25-11")
        self.assertEqual(
            translated["nav_html"], '<a href="index.html">Home</a> / Process'
        )
        self.assertEqual(
            translated["main"],
            [{"t": "html", "html": "<h1>Publication process</h1>"}],
        )
        self.assertEqual(stat.fehlend, {})

    def test_structural_ui_heading_still_takes_precedence(self):
        source = "Ablaufdiagramm"
        raw = '<h2 class="sect" id="flow">%s</h2>' % source
        segments = {i18n.seg_id(source): "Wrong duplicate translation"}
        stat = i18n.Statistik(soll=set(segments), soll_labels=set())

        translated = i18n.uebersetze_html(
            raw, segments, {"sect": {source: "Sequence diagram"}}, stat, lab={}
        )

        self.assertIn('id="flow"', translated)
        self.assertIn(">Sequence diagram</h2>", translated)
        self.assertNotIn("Wrong duplicate translation", translated)

    def test_register_writer_preserves_existing_indentation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pretty = root / "pretty.json"
            compact = root / "compact.json"
            pretty.write_text('{\n  "a": 1\n}', encoding="utf-8")
            compact.write_text('{\n"a": 1\n}', encoding="utf-8")

            self.assertEqual(i18n_translate._bestehender_einzug(pretty), 2)
            self.assertEqual(i18n_translate._bestehender_einzug(compact), 0)
            self.assertEqual(
                i18n_translate._bestehender_einzug(root / "missing.json"), 2
            )

    def test_merge_batch_selection_is_explicit_and_fail_closed(self):
        files = [
            "batch_01.out.jsonl",
            "batch_96.out.jsonl",
            "batch_96.jsonl",
            "notes.txt",
        ]

        self.assertEqual(
            i18n_translate._waehle_batches(
                files, only=["batch_96.out.jsonl"]
            ),
            ["batch_96.out.jsonl"],
        )
        with self.assertRaisesRegex(ValueError, "fehlt"):
            i18n_translate._waehle_batches(
                files, only=["batch_97.out.jsonl"]
            )
        with self.assertRaisesRegex(ValueError, "ungültig"):
            i18n_translate._waehle_batches(files, only=["../batch_96.out.jsonl"])

    def test_merge_validation_protects_rs_and_sws_markers(self):
        source = "Siehe [RS_AP_00111] und [SWS_CM_00701]."
        valid = "See [RS_AP_00111] and [SWS_CM_00701]."
        invalid = "See [RS_AP_00112] and [SWS_CM_00701]."

        self.assertIsNone(i18n_translate.pruefe(source, valid))
        self.assertEqual(
            i18n_translate.pruefe(source, invalid),
            "Spezifikationskennungen weichen ab",
        )


if __name__ == "__main__":
    unittest.main()
