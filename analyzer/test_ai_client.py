from analyzer.ai_client import analyze_with_ai
from analyzer.slither_parser import analyze_report


report_file = "reports/vulnerable-bank.json"

findings = analyze_report(report_file)

for index, finding in enumerate(findings, start=1):
    print("=" * 70)
    print(f"AI ANALYSIS FOR FINDING #{index}")
    print("=" * 70)

    result = analyze_with_ai(finding)

    print(f"Vulnerability: {result.vulnerability}")
    print(f"Severity: {result.severity}")
    print(f"\nExplanation:\n{result.explanation}")
    print(f"\nRoot Cause:\n{result.root_cause}")
    print(f"\nRecommendation:\n{result.recommendation}")
    print(f"\nFixed Code:\n{result.fixed_code}")
    print(f"\nVerification Notes:\n{result.verification_notes}")
    print()