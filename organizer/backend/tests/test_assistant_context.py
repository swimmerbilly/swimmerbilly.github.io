import unittest
from unittest.mock import MagicMock

from app.models import Project, ProjectStatus
from app.services.assistant_context import build_workspace_context


class AssistantContextTests(unittest.TestCase):
    def test_builds_context_with_active_projects(self) -> None:
        db = MagicMock()
        project = Project(
            id=1,
            name="Kitchen Remodel",
            status=ProjectStatus.ACTIVE,
            harvest_client_name="ACME Corp",
            harvest_id=123,
        )
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.side_effect = [
            [project],
            [],
            [],
            [],
            [],
        ]

        context = build_workspace_context(db)
        self.assertIn("Kitchen Remodel", context)
        self.assertIn("ACME Corp", context)
        self.assertIn("Unread emails", context)


if __name__ == "__main__":
    unittest.main()
