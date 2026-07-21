"""Tests for structural permit heuristics."""

import unittest

from app.services.permit_structural import detect_structural_signals, extract_engineer_from_text


class StructuralDetectionTests(unittest.TestCase):
    def test_detects_foundation_permit(self):
        has_structural, signals = detect_structural_signals(
            "New Residence",
            "Engineered foundation and footing design",
        )
        self.assertTrue(has_structural)
        self.assertTrue(any("foundation" in s for s in signals))

    def test_ignores_kitchen_remodel(self):
        has_structural, _ = detect_structural_signals(
            "Residential Remodel",
            "Kitchen cabinets and finishes only",
        )
        self.assertFalse(has_structural)

    def test_extracts_engineer_name_and_license(self):
        result = extract_engineer_from_text(
            "Structural Engineer: Jordan Hale PE-54321 Front Range Structural"
        )
        self.assertEqual(result["name"], "Jordan Hale")
        self.assertEqual(result["license"], "54321")


if __name__ == "__main__":
    unittest.main()
