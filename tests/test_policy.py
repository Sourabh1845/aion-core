import unittest

from aion_core.policy import Policy


class PolicyTests(unittest.TestCase):
    def test_allows_when_no_rule_matches_and_default_allow(self):
        policy = Policy.from_dict({"default_action": "allow", "rules": []})

        decision = policy.evaluate_tool_call(
            tool_name="read_file",
            arguments={"path": "README.md"},
            agent_id="agent-1",
            owner="local",
        )

        self.assertEqual(decision.action, "allow")
        self.assertEqual(decision.rule_id, "default-allow")

    def test_blocks_destructive_command_by_contains_match(self):
        policy = Policy.from_dict(
            {
                "default_action": "allow",
                "rules": [
                    {
                        "id": "no-delete",
                        "action": "block",
                        "match": {
                            "tool": "shell",
                            "argument_contains": "Remove-Item",
                        },
                    }
                ],
            }
        )

        decision = policy.evaluate_tool_call(
            tool_name="shell",
            arguments={"command": "Remove-Item -Recurse C:\\tmp"},
            agent_id="agent-1",
            owner="local",
        )

        self.assertEqual(decision.action, "block")
        self.assertEqual(decision.rule_id, "no-delete")

    def test_blocks_by_regex(self):
        policy = Policy.from_dict(
            {
                "rules": [
                    {
                        "id": "no-secrets",
                        "action": "block",
                        "match": {
                            "tool": "*",
                            "argument_regex": "password\\s*[:=]",
                        },
                    }
                ]
            }
        )

        decision = policy.evaluate_tool_call(
            tool_name="http_post",
            arguments={"body": "password = hunter2"},
            agent_id="agent-1",
            owner="local",
        )

        self.assertEqual(decision.action, "block")

    def test_default_block(self):
        policy = Policy.from_dict({"default_action": "block"})

        decision = policy.evaluate_tool_call(
            tool_name="unknown",
            arguments={},
            agent_id="agent-1",
            owner="local",
        )

        self.assertEqual(decision.action, "block")
        self.assertEqual(decision.rule_id, "default-block")


if __name__ == "__main__":
    unittest.main()
