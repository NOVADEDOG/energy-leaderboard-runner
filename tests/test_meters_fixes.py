
import unittest
import time
from unittest.mock import MagicMock, patch
from src.energy_meter.macos_meter import MacosMeter
from src.energy_meter.nvml_meter import NvmlMeter
from src.energy_meter.rapl_meter import RaplMeter
from src.energy_meter.rocm_smi_meter import RocmSmiMeter

class TestEnergyMetersFixes(unittest.TestCase):
    def test_macos_parsing_header_separation(self):
        meter = MacosMeter()
        meter.output_lines = [
            "*** Sampled system activity (Thu Jan  1 00:00:00 1970) (5000.00ms elapsed) ***",
            "CPU Power: 100 mW",
            "GPU Power: 50 mW",
            "Package Power: 150 mW",

            "*** Sampled system activity (Thu Jan  1 00:00:01 1970) (5100.00ms elapsed) ***",
            "CPU Power: 100 mW",
            "GPU Power: 50 mW",
        ]
        samples = meter._parse_power_samples()
        # Should result in 2 samples, 150 and 150.
        self.assertEqual(len(samples), 2)
        self.assertEqual(samples[0], 150.0)
        self.assertEqual(samples[1], 150.0)

    def test_macos_parsing_combined(self):
        meter = MacosMeter()
        meter.output_lines = [
            "*** Sampled system activity (Thu Jan  1 00:00:00 1970) (5000.00ms elapsed) ***",
            "CPU Power: 100 mW",
            "Combined Power (CPU + GPU + ANE): 200 mW",
        ]
        samples = meter._parse_power_samples()
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0], 200.0)

    @patch('src.energy_meter.nvml_meter.pynvml')
    def test_nvml_integration_logic(self, mock_pynvml):
        meter = NvmlMeter()
        mock_pynvml.nvmlInit.return_value = None
        meter._nvml_initialized = True

        # Manually populate samples with known timestamps
        t0 = 1000.0
        meter.start_time = t0
        meter.power_samples = [
            (t0, 10000.0),      # 10 W
            (t0 + 1.0, 10000.0), # 10 W, dt=1s
            (t0 + 2.0, 20000.0), # 20 W, dt=1s
        ]
        meter.stop_time = t0 + 2.0

        meter.start = MagicMock()

        with patch.object(meter, '_running', False):
             result = meter.stop()

        expected_wh = 25.0 / 3600.0
        self.assertAlmostEqual(result['energy_wh_raw'], expected_wh, places=6)

    @patch('src.energy_meter.rocm_smi_meter.subprocess.run')
    def test_rocm_integration_logic(self, mock_run):
        meter = RocmSmiMeter()

        t0 = 1000.0
        meter.start_time = t0
        meter.power_samples = [
            (t0, 10.0),      # 10 W
            (t0 + 1.0, 10.0), # 10 W
            (t0 + 2.0, 20.0), # 20 W
        ]
        meter.stop_time = t0 + 2.0

        with patch.object(meter, '_running', False):
             result = meter.stop()

        expected_wh = 25.0 / 3600.0
        self.assertAlmostEqual(result['energy_wh_raw'], expected_wh, places=6)

    @patch('src.energy_meter.rapl_meter.Path')
    def test_rapl_zone_selection(self, mock_path_cls):
        mock_base = MagicMock()
        mock_path_cls.return_value = mock_base
        mock_base.exists.return_value = True

        zone0 = MagicMock()
        zone0_name = MagicMock()
        zone0_name.exists.return_value = True
        zone0_name.read_text.return_value = "package-0\n"
        zone0_energy = MagicMock()
        zone0_energy.exists.return_value = True

        def zone0_div(other):
            if other == "name": return zone0_name
            if other == "energy_uj": return zone0_energy
            return MagicMock()
        zone0.__truediv__.side_effect = zone0_div

        zone00 = MagicMock()
        zone00_name = MagicMock()
        zone00_name.exists.return_value = True
        zone00_name.read_text.return_value = "core\n"
        zone00_energy = MagicMock()
        zone00_energy.exists.return_value = True

        def zone00_div(other):
            if other == "name": return zone00_name
            if other == "energy_uj": return zone00_energy
            return MagicMock()
        zone00.__truediv__.side_effect = zone00_div

        zone1 = MagicMock()
        zone1_name = MagicMock()
        zone1_name.exists.return_value = True
        zone1_name.read_text.return_value = "package-1\n"
        zone1_energy = MagicMock()
        zone1_energy.exists.return_value = True

        def zone1_div(other):
            if other == "name": return zone1_name
            if other == "energy_uj": return zone1_energy
            return MagicMock()
        zone1.__truediv__.side_effect = zone1_div

        mock_base.glob.return_value = [zone0, zone00, zone1]

        meter = RaplMeter()
        meter.is_available()

        self.assertIn(zone0, meter.rapl_paths)
        self.assertIn(zone1, meter.rapl_paths)
        self.assertNotIn(zone00, meter.rapl_paths)
        self.assertEqual(len(meter.rapl_paths), 2)
