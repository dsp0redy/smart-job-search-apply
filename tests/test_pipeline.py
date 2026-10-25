import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from pipeline import extract_urls, score


class PipelineTests(unittest.TestCase):
    def test_only_unique_https_urls(self):
        urls = extract_urls("See https://example.com/job and https://example.com/job and http://bad.example/job")
        self.assertEqual(urls, ["https://example.com/job"])

    def test_relevance_score_is_bounded(self):
        cfg = {"target_titles": ["Software Engineer", "C++ Engineer"], "skills": ["C++", "Linux", "gRPC"]}
        value, skills, titles = score("Software Engineer C++ Linux gRPC embedded systems", cfg)
        self.assertGreaterEqual(value, 0)
        self.assertLessEqual(value, 100)
        self.assertIn("C++", skills)

    def test_exclusion_forces_zero(self):
        cfg = {"target_titles": ["Software Engineer"], "skills": ["C++"], "exclude_terms": ["unpaid internship"]}
        value, _, _ = score("Software Engineer C++ unpaid internship", cfg)
        self.assertEqual(value, 0)


if __name__ == "__main__":
    unittest.main()
