import math
import unittest

from core import (check_overload_protection, conductor_resistance, dimension_line,
                  mean_power_factor, operating_current, voltage_drop)


class CoreTests(unittest.TestCase):
    def test_three_phase_operating_current(self):
        self.assertAlmostEqual(operating_current(15, 400, .9, 3, .95), 25.32, delta=.26)

    def test_resistance_temperature_increases(self):
        self.assertGreater(conductor_resistance(100, 16, "Kupfer", 70), conductor_resistance(100, 16, "Kupfer", 20))

    def test_voltage_drop_known_formula(self):
        drop, percent = voltage_drop(20, 50, 10, 400, .9, 3, "Kupfer", 20, 0)
        expected = math.sqrt(3)*.05*20*(1000/(54*10))*.9
        self.assertAlmostEqual(drop, expected)
        self.assertAlmostEqual(percent, drop/4)

    def test_dimensioning_returns_valid_result(self):
        result = dimension_line(power_kw=10, voltage=400, power_factor=.9, phases=3, efficiency=1,
            simultaneity=1, installation="C", loaded_conductors=3, correction_factor=.9,
            length_m=20, material="Kupfer", temperature_c=70, max_drop_percent=3,
            reactance_ohm_km=.08, trip_factor=1.45)
        self.assertTrue(result.successful)
        self.assertIsNotNone(result.section_mm2)

    def test_mean_power_factor(self):
        pf, _, _ = mean_power_factor([(10, .8), (10, 1.0)])
        self.assertTrue(.8 < pf < 1)

    def test_ls_protection_valid(self):
        result = check_overload_protection(24, 25, 32, "LS")
        self.assertTrue(result.successful)
        self.assertAlmostEqual(result.trip_current_a, 36.25)

    def test_gg_trip_rule_can_fail(self):
        result = check_overload_protection(24, 25, 26, "gG")
        self.assertTrue(result.rated_current_ok)
        self.assertFalse(result.trip_rule_ok)

    def test_protection_rejects_unknown_device(self):
        with self.assertRaises(ValueError):
            check_overload_protection(10, 16, 20, "unknown")

    def test_high_current_standard_fuse_is_available(self):
        from core import STANDARD_FUSES
        self.assertIn(400, STANDARD_FUSES)


if __name__ == "__main__":
    unittest.main()

