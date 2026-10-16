import csv
import tempfile
import unittest
from pathlib import Path

from disk_audit.scanner import classify, scan


class ScannerTests(unittest.TestCase):
    def test_classification(self):
        self.assertEqual(classify("Users/alice/photo.jpg", ".jpg")[0], "photo")
        self.assertEqual(classify("Windows/System32/a.dll", ".dll")[0], "systeme_probable")
        self.assertEqual(classify("Documents/rapport.docx", ".docx")[0], "word")

    def test_reports_and_duplicates(self):
        with tempfile.TemporaryDirectory() as source, tempfile.TemporaryDirectory() as destination:
            root, out = Path(source), Path(destination)
            (root / "Documents").mkdir()
            (root / "Documents" / "a.pdf").write_bytes(b"same")
            (root / "Documents" / "b.pdf").write_bytes(b"same")
            report = scan(root, out, None, False)
            self.assertEqual(len(report["files"]), 2)
            self.assertEqual(len(report["duplicates"]), 1)
            with (out / "files.csv").open(encoding="utf-8") as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 2)
            self.assertTrue((out / "summary.html").exists())


if __name__ == "__main__":
    unittest.main()
