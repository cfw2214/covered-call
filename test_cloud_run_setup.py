#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parent


class CloudRunSetupTests(unittest.TestCase):
    def test_dockerfile_exists_with_expected_entrypoint(self) -> None:
        dockerfile = PROJECT_ROOT / "Dockerfile"
        self.assertTrue(dockerfile.exists(), "Dockerfile should exist for Cloud Run deploys")
        body = dockerfile.read_text(encoding="utf-8")
        self.assertIn("gunicorn", body)
        self.assertIn("covered_call.app:app", body)
        self.assertIn("${PORT:-8080}", body)

    def test_dockerignore_exists_with_common_ignores(self) -> None:
        dockerignore = PROJECT_ROOT / ".dockerignore"
        self.assertTrue(dockerignore.exists(), ".dockerignore should exist for Cloud Run deploys")
        body = dockerignore.read_text(encoding="utf-8")
        self.assertIn(".git", body)
        self.assertIn("__pycache__", body)
        self.assertIn(".venv", body)

    def test_readme_mentions_cloud_run_deploy(self) -> None:
        readme = PROJECT_ROOT / "README.md"
        body = readme.read_text(encoding="utf-8")
        self.assertIn("Cloud Run", body)
        self.assertIn("gcloud run deploy", body)


if __name__ == "__main__":
    unittest.main()
