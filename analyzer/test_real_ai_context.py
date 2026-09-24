from analyzer.ai_context_builder import build_ai_context
from analyzer.slither_parser import analyze_report


report_file = "reports/vulnerable-bank.json"

findings = analyze_report(report_file)

print(f"Found {len(findings)} findings.\n")

for index, finding in enumerate(findings, start=1):
    print("=" * 70)
    print(f"AI CONTEXT FOR FINDING #{index}")
    print("=" * 70)

    context = build_ai_context(finding)

    print(context)
    print()