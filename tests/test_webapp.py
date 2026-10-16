import tempfile
import unittest
from pathlib import Path

from disk_audit.webapp import safe_path


class WebAppSecurityTests(unittest.TestCase):
    def test_path_cannot_escape_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(PermissionError):
                safe_path(root, "../secret.txt")

    def test_path_stays_inside_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "photo.jpg").touch()
            self.assertEqual(safe_path(root, "photo.jpg"), root / "photo.jpg")


if __name__ == "__main__":
    unittest.main()
