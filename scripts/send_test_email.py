"""
Send a test email via SendGrid.
Usage:
  python scripts/send_test_email.py you@example.com
"""

import sys

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
