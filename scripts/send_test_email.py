"""
Send a test email via SendGrid.
Usage:
  python scripts/send_test_email.py you@example.com
"""

import os
import sys

from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

load_dotenv()

from lib.email import send_email


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/send_test_email.py you@example.com")
        return 1

    to_email = sys.argv[1]
    response = send_email(
        to_email=to_email,
        subject="Test Email - Solo AI Automation",
        body="This is a test email from Solo AI Automation.",
    )
    print(response)
    return 0 if not response.get("error") else 2


if __name__ == "__main__":
    raise SystemExit(main())
