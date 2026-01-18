import json
from dataclasses import asdict

from .cold_emailer import draft_cold_email


def run_demo():
    draft = draft_cold_email(
        name="Jordan Lee",
        role="Operations Lead",
        company="Northwind Logistics",
        website="https://northwind.example",
        pain_points="Manual lead routing and slow follow-ups",
        notes="Referred by a partner",
    )
    print(json.dumps(asdict(draft), indent=2))


if __name__ == "__main__":
    run_demo()
