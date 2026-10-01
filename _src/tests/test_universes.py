import os
import unittest
import json
from pathlib import Path

class TestUniverses(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.parent.parent
        self.src = self.root / '_src'
        
    def test_pages_rendered(self):
        # We assume generator has been run and pages exist in the root
        pages = [
            'classic/index.html',
            'classic/rte.html',
            'classic/system.html',
            'classic/os.html',
            'classic/com.html',
            'classic/memory.html',
            'classic/diagnostics.html',
            'classic/crypto.html',
            'classic/can.html',
            'classic/lin.html',
            'classic/flexray.html',
            'classic/ethernet.html',
            'classic/mcal.html',
            'classic/security.html',
            'classic/modules/can.html',
            'classic/modules/canif.html',
            'classic/modules/dem.html',
            'classic/modules/dcm.html',
            'classic/modules/det.html',
            'classic/modules/dlt.html',
            'classic/modules/ecum.html',
            'classic/modules/wdgm.html',
            'classic/types.html',
            'classic/modules/platform.html',
            'classic/modules/std.html',
            'classic/modules/comstack.html',
            'score/index.html',
            'score/core.html',
            'score/communication.html',
            'score/diagnostic_adapter.html',
            'score/memory.html',
            'score/crypto.html',
            'score/process.html',
            'pt/classic/diagnostics.html',
            'pt/classic/system.html',
            'pt/score/core.html',
            'adaptive/index.html',
            'pt/adaptive/index.html',
        ]
        
        for p in pages:
            path = self.root / p
            self.assertTrue(path.exists(), f"Page not rendered: {p}")
            
    def test_diagnostics_content(self):
        diag_html = self.root / 'classic/diagnostics.html'
        self.assertTrue(diag_html.exists())
        content = diag_html.read_text(encoding='utf-8')
        # Cluster hub overview
        self.assertIn('Diagnostic Event Manager (DEM)', content)
        self.assertIn('Diagnostic Communication Manager (DCM)', content)
        self.assertIn('Default Error Tracer (DET)', content)
        self.assertIn('Diagnostic Log and Trace (DLT)', content)
        self.assertIn('href="modules/dem.html"', content)
        self.assertIn('href="modules/dcm.html"', content)
        self.assertIn('href="modules/det.html"', content)
        self.assertIn('href="modules/dlt.html"', content)
        self.assertIn('data-open-discuss="CP_DIAG"', content)

        # Dedicated module pages
        dem_html = self.root / 'classic/modules/dem.html'
        self.assertTrue(dem_html.exists())
        dem_content = dem_html.read_text(encoding='utf-8')
        self.assertIn('Dem_SetEventStatus', dem_content)
        self.assertIn('class="review-request-panel"', dem_content)
        self.assertIn('Dem.h', dem_content)
        self.assertIn('BSW-Modul-ID', dem_content)

        dcm_html = self.root / 'classic/modules/dcm.html'
        self.assertTrue(dcm_html.exists())
        self.assertIn('Dcm_GetActiveProtocol', dcm_html.read_text(encoding='utf-8'))

        det_html = self.root / 'classic/modules/det.html'
        self.assertTrue(det_html.exists())
        self.assertIn('Det_ReportError', det_html.read_text(encoding='utf-8'))

        dlt_html = self.root / 'classic/modules/dlt.html'
        self.assertTrue(dlt_html.exists())
        self.assertIn('Dlt_SendLogMessage', dlt_html.read_text(encoding='utf-8'))

    def test_system_content(self):
        sys_html = self.root / 'classic/system.html'
        self.assertTrue(sys_html.exists())
        content = sys_html.read_text(encoding='utf-8')
        # Cluster hub overview
        self.assertIn('ECU State Manager (EcuM)', content)
        self.assertIn('BSW Mode Manager (BswM)', content)
        self.assertIn('Watchdog Manager (WdgM)', content)
        self.assertIn('href="modules/ecum.html"', content)
        self.assertIn('href="modules/bswm.html"', content)
        self.assertIn('href="modules/wdgm.html"', content)
        self.assertIn('data-open-discuss="CP_SYS"', content)

        # Dedicated module pages
        ecum_html = self.root / 'classic/modules/ecum.html'
        self.assertTrue(ecum_html.exists())
        ecum_content = ecum_html.read_text(encoding='utf-8')
        self.assertIn('EcuM_Init', ecum_content)
        self.assertIn('class="review-request-panel"', ecum_content)
        self.assertIn('EcuM.h', ecum_content)

        bswm_html = self.root / 'classic/modules/bswm.html'
        self.assertTrue(bswm_html.exists())
        self.assertIn('BswM_RequestMode', bswm_html.read_text(encoding='utf-8'))

        wdgm_html = self.root / 'classic/modules/wdgm.html'
        self.assertTrue(wdgm_html.exists())
        wdgm_content = wdgm_html.read_text(encoding='utf-8')
        self.assertIn('WdgM_Init', wdgm_content)
        self.assertIn('WdgM_CheckpointReached', wdgm_content)

    def test_types_content(self):
        types_html = self.root / 'classic/types.html'
        self.assertTrue(types_html.exists())
        content = types_html.read_text(encoding='utf-8')
        self.assertIn('Platform Types', content)
        self.assertIn('Standard Types', content)
        self.assertIn('Communication Stack Types', content)
        self.assertIn('href="modules/platform.html"', content)
        self.assertIn('href="modules/std.html"', content)
        self.assertIn('href="modules/comstack.html"', content)

        # Platform module page
        plat_html = self.root / 'classic/modules/platform.html'
        self.assertTrue(plat_html.exists())
        plat_content = plat_html.read_text(encoding='utf-8')
        self.assertIn('Platform_Types.h', plat_content)
        self.assertIn('uint8', plat_content)
        self.assertIn('boolean', plat_content)

        # Std module page
        std_html = self.root / 'classic/modules/std.html'
        self.assertTrue(std_html.exists())
        std_content = std_html.read_text(encoding='utf-8')
        self.assertIn('Std_Types.h', std_content)
        self.assertIn('Std_ReturnType', std_content)
        self.assertIn('Std_VersionInfoType', std_content)

        # ComStack module page
        com_html = self.root / 'classic/modules/comstack.html'
        self.assertTrue(com_html.exists())
        com_content = com_html.read_text(encoding='utf-8')
        self.assertIn('ComStack_Types.h', com_content)
        self.assertIn('PduIdType', com_content)
        self.assertIn('PduInfoType', com_content)

    def test_score_core_content(self):
        core_html = self.root / 'score/core.html'
        self.assertTrue(core_html.exists())
        content = core_html.read_text(encoding='utf-8')
        self.assertIn('Core Execution Environment', content)
        self.assertIn('aou_req__platform__posix_operating_system', content)
        self.assertIn('stkh_req__hardware_support__container_tech', content)
        self.assertIn('data-open-discuss="SCORE_CORE"', content)
        self.assertIn('class="review-request-panel"', content)
            
    def test_cross_links(self):
        com_html = self.root / 'modules/com.html'
        self.assertTrue(com_html.exists())
        
        content = com_html.read_text(encoding='utf-8')
        self.assertIn('../classic/com.html', content)
        self.assertIn('../score/diagnostic_adapter.html', content)
        
    def test_universe_selector(self):
        classic_index = self.root / 'classic/index.html'
        content = classic_index.read_text(encoding='utf-8')
        
        # Check if the universe selector is present
        self.assertIn('<div class="universes">', content)
        # Should link to other universes
        self.assertIn('href="../adaptive/index.html"', content) # Adaptive
        self.assertIn('href="../score/index.html"', content) # Score

if __name__ == '__main__':
    unittest.main()
