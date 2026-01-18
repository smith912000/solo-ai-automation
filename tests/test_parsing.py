import json
import os
import sys
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AGENT_ROOT = os.path.join(ROOT_DIR, "automations", "lead-qualifier")
if AGENT_ROOT not in sys.path:
    sys.path.append(AGENT_ROOT)

from agent.qualifier import _parse_qualification_response  # noqa: E402
from agent.email_drafter import _parse_email_response  # noqa: E402


class ParsingTests(unittest.TestCase):
    def test_parse_qualification_strips_code_fence(self):
        payload = {
            "qualification_score": 72,
            "qualification_label": "qualified",
            "key_reason": "Clear intent and strong fit",
            "personalization_points": ["Mentioned scaling", "Asked about onboarding"],
        }
        response = "```json\n" + json.dumps(payload) + "\n```"
        result = _parse_qualification_response(response, 100, 50)
        self.assertEqual(result.score, 72)
        self.assertEqual(result.label, "qualified")
        self.assertEqual(result.tokens_used, 150)

    def test_parse_email_strips_code_fence(self):
        payload = {
            "email_subject": "Quick idea",
            "email_body": "Hi there, thanks for reaching out.",
            "follow_up_task": "Send reminder in 3 days",
        }
        response = "```\n" + json.dumps(payload) + "\n```"
        draft = _parse_email_response(response, 80, 20)
        self.assertEqual(draft.subject, "Quick idea")
        self.assertEqual(draft.tokens_used, 100)


if __name__ == "__main__":
    unittest.main()
