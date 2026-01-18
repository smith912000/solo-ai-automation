import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ClientInfo:
    client_name: str
    contact_name: str
    contact_email: str
    start_date: Optional[str] = None
    package: Optional[str] = None
    contract_signed: bool = False


def generate_checklist(info: ClientInfo) -> str:
    template_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "templates",
        "ONBOARDING_CHECKLIST.md",
    )
    template_path = os.path.abspath(template_path)
    with open(template_path, "r", encoding="utf-8") as handle:
        content = handle.read()

    content = content.replace("| Client Name | |", f"| Client Name | {info.client_name} |")
    content = content.replace("| Contact Name | |", f"| Contact Name | {info.contact_name} |")
    content = content.replace("| Contact Email | |", f"| Contact Email | {info.contact_email} |")

    contract_value = "☑ Yes" if info.contract_signed else "☐ Yes"
    content = content.replace("| Contract Signed | ☐ Yes |", f"| Contract Signed | {contract_value} |")

    if info.start_date:
        content = content.replace("| Start Date | |", f"| Start Date | {info.start_date} |")
    if info.package:
        content = content.replace("| Package | ☐ Starter / ☐ Growth / ☐ Pro |", f"| Package | {info.package} |")

    return content


def run_demo():
    info = ClientInfo(
        client_name="Acme Corp",
        contact_name="Taylor Reed",
        contact_email="taylor@acme.example",
        start_date="2026-01-20",
        package="Starter",
        contract_signed=True,
    )
    print(generate_checklist(info))


if __name__ == "__main__":
    run_demo()
