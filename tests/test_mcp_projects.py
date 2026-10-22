"""Contract tests for the MCP Projects adapter; no network calls are made."""

import unittest
from unittest.mock import patch

import mcp_projects as mcp


class McpProjectsContractTests(unittest.TestCase):
    def test_list_tools_returns_tools_from_json_rpc_result(self):
        with patch.object(
            mcp, "_sse_call", return_value={"tools": [{"name": "manage_project"}]}
        ) as call:
            self.assertEqual(mcp.list_tools(), [{"name": "manage_project"}])
        call.assert_called_once_with("tools/list", {})

    def test_call_tool_parses_json_text_content(self):
        with patch.object(
            mcp,
            "_sse_call",
            return_value={
                "content": [{"type": "text", "text": '{"projects": [{"id": "P1"}]}'}]
            },
        ):
            self.assertEqual(
                mcp.call_tool("manage_project", {"action": "list"}),
                {"projects": [{"id": "P1"}]},
            )

    def test_call_tool_preserves_non_json_text(self):
        with patch.object(
            mcp,
            "_sse_call",
            return_value={"content": [{"type": "text", "text": "plain text"}]},
        ):
            self.assertEqual(
                mcp.call_tool("manage_project", {}),
                {"raw": "plain text"},
            )

    def test_call_tool_raises_for_mcp_tool_error(self):
        with patch.object(
            mcp,
            "_sse_call",
            return_value={
                "isError": True,
                "content": [{"type": "text", "text": "invalid project id"}],
            },
        ):
            with self.assertRaisesRegex(RuntimeError, "invalid project id"):
                mcp.call_tool("manage_project", {"projectId": "missing"})

    def test_list_projects_normalizes_api_shape(self):
        with patch.object(
            mcp,
            "call_tool",
            return_value={
                "projects": [
                    {"id": "P1", "name": "Backlog"},
                    {"id": "P2", "title": "Closed", "status": "closed"},
                ]
            },
        ):
            self.assertEqual(
                mcp.list_projects(),
                [
                    {"id": "P1", "title": "Backlog", "number": None, "closed": False},
                    {"id": "P2", "title": "Closed", "number": None, "closed": True},
                ],
            )

    def test_list_project_items_falls_back_when_filter_contract_rejected(self):
        responses = [
            RuntimeError("unsupported filter"),
            RuntimeError("unsupported filterQuery"),
            {"items": [{"id": "item-1", "content": {"title": "Feature", "number": 7}}]},
        ]
        with patch.object(mcp, "call_tool", side_effect=responses) as call:
            self.assertEqual(
                mcp.list_project_items("P1"),
                [
                    {
                        "id": "item-1",
                        "contentId": None,
                        "type": "Issue",
                        "title": "Feature",
                        "number": 7,
                        "state": "",
                    }
                ],
            )
        self.assertEqual(call.call_count, 3)
        self.assertEqual(call.call_args_list[-1].args[1]["action"], "list_items")

    def test_list_project_items_raises_when_all_api_variants_fail(self):
        with patch.object(
            mcp, "call_tool", side_effect=RuntimeError("tool unavailable")
        ) as call:
            with self.assertRaisesRegex(RuntimeError, "No se pudo listar items"):
                mcp.list_project_items("P1")
        self.assertEqual(call.call_count, 3)

    def test_acceptance_criteria_supports_checkboxes_and_empty_body(self):
        body = "## Criterios de aceptación\n- [ ] Create account\n- [x] Reject duplicate"
        self.assertEqual(
            mcp._extract_acceptance_criteria(body),
            ["Create account", "Reject duplicate"],
        )
        self.assertEqual(mcp._extract_acceptance_criteria(""), [])

    def test_feature_contract_extracts_issue_fields(self):
        with patch.object(
            mcp,
            "call_tool",
            return_value={
                "issue": {
                    "title": "Create account",
                    "body": "## Acceptance criteria\n- [ ] Reject duplicate",
                }
            },
        ) as call:
            self.assertEqual(
                mcp.get_feature(42),
                {
                    "title": "Create account",
                    "description": "## Acceptance criteria\n- [ ] Reject duplicate",
                    "acceptance_criteria": ["Reject duplicate"],
                },
            )
        self.assertEqual(call.call_args.args[1]["issueNumber"], 42)


if __name__ == "__main__":
    unittest.main()
