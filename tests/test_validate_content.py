import tempfile
import unittest
from pathlib import Path

from scripts.validate_content import validate_page


class ValidateContentTests(unittest.TestCase):
    def test_published_content_requires_review_details_and_references(self):
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "article.md"
            page.write_text(
                """---
title: Test
category: courses
tags: [高血壓]
status: published
author: Author
reviewer:
created_at: 2026-09-03
updated_at: 2026-09-03
reviewed_at:
next_review:
evidence_level:
references: []
---
""",
                encoding="utf-8",
            )
            errors = []
            validate_page(page, {"courses"}, {"高血壓"}, errors)
        self.assertIn(f"{page}: published content requires reviewer", errors)
        self.assertIn(f"{page}: published content requires at least one reference", errors)

    def test_draft_content_allows_pending_review_details(self):
        with tempfile.TemporaryDirectory() as directory:
            page = Path(directory) / "article.md"
            page.write_text(
                """---
title: Test
category: courses
tags: [高血壓]
status: draft
author: Author
reviewer:
created_at: 2026-09-03
updated_at: 2026-09-03
reviewed_at:
next_review:
evidence_level:
references: []
---
""",
                encoding="utf-8",
            )
            errors = []
            validate_page(page, {"courses"}, {"高血壓"}, errors)
        self.assertEqual([], errors)
