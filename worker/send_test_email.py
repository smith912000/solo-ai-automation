"""
Send a single test email via SendGrid.
Usage: python -m worker.send_test_email test@example.com
"""

import sys

from dotenv import load_dotenv

from lib.email import send_email


def main() -> int:
    load_dotenv()
    to_email = sys.argv[1] if len(sys.argv) > 1 else ""
    if not to_email:
        raise SystemExit("Usage: python -m worker.send_test_email you@example.com")

    subject = "Solo AI Automation Test Email"
    body = "This is a SendGrid test email from Solo AI Automation."
    response = send_email(to_email, subject, body)
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
