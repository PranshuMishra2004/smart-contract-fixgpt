from analyzer.ai_prompt_builder import build_fix_prompt
from analyzer.slither_parser import analyze_report


report_file = "reports/vulnerable-bank.json"

findings = analyze_report(report_file)

for index, finding in enumerate(findings, start=1):
    print("=" * 70)
    print(f"AI PROMPT FOR FINDING #{index}")
    print("=" * 70)

    prompt = build_fix_prompt(finding)

    print(prompt)
    print()