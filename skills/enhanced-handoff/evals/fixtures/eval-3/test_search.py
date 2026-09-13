import unittest
from search import search

class SearchTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(search(["中文标题"], "  "), [])
    def test_match(self):
        self.assertEqual(search(["中文标题", "其他笔记"], "标题"), ["中文标题"])

if __name__ == "__main__":
    unittest.main()
