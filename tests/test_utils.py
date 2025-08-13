"""Unit tests for utility functions.

These tests cover the Thai date parser, citizen ID validator and filename
sanitiser. They use the built‑in unittest framework to avoid external
dependencies such as pytest. Running ``python -m unittest`` in the root of
the repository will discover and execute these tests.
"""

import unittest
import datetime as dt

from app.services.utils import parse_thai_date, validate_thai_cid, sanitize_filename


class TestThaiDateParser(unittest.TestCase):
    def test_parse_full_month(self):
        # 1 มกราคม 2565 -> 2022-01-01
        self.assertEqual(parse_thai_date("1 มกราคม 2565"), dt.date(2022, 1, 1))

    def test_parse_abbreviated_month(self):
        # 29 ก.ย. 64 -> 2021-09-29 (64 -> 2564 -> 2021)
        self.assertEqual(parse_thai_date("29 ก.ย. 64"), dt.date(2021, 9, 29))

    def test_parse_leading_zero(self):
        # 05 พ.ค. 61 -> 2018-05-05
        self.assertEqual(parse_thai_date("05 พ.ค. 61"), dt.date(2018, 5, 5))

    def test_invalid_date(self):
        # Should return None for invalid month
        self.assertIsNone(parse_thai_date("31 Foo 2565"))


class TestThaiCIDValidator(unittest.TestCase):
    def compute_checksum(self, first12: str) -> str:
        digits = [int(c) for c in first12]
        total = sum(d * w for d, w in zip(digits, range(13, 1, -1)))
        checksum = (11 - (total % 11)) % 10
        return str(checksum)

    def test_valid_cid(self):
        base = "123456789012"
        cid = base + self.compute_checksum(base)
        self.assertTrue(validate_thai_cid(cid))

    def test_invalid_cid(self):
        base = "123456789012"
        cid = base + self.compute_checksum(base)
        # Alter last digit
        invalid_cid = cid[:-1] + str((int(cid[-1]) + 1) % 10)
        self.assertFalse(validate_thai_cid(invalid_cid))

    def test_incorrect_length(self):
        self.assertFalse(validate_thai_cid("12345678901"))  # 11 digits


class TestSanitizeFilename(unittest.TestCase):
    def test_illegal_chars_replacement(self):
        original = "abc/def:ghi*?.pdf"
        expected = "abc_def_ghi__.pdf"
        self.assertEqual(sanitize_filename(original), expected)

    def test_max_length(self):
        long_name = "a" * 150 + ".pdf"
        result = sanitize_filename(long_name)
        self.assertLessEqual(len(result), 120)
        self.assertTrue(result.endswith(".pdf"))


if __name__ == "__main__":
    unittest.main()