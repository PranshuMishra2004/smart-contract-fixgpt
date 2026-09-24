from analyzer.ai_context_builder import build_ai_context
from analyzer.finding_model import SecurityFinding


finding = SecurityFinding(
    check="reentrancy-eth",
    category="Reentrancy",
    severity="High",
    confidence="Medium",
    description="External call occurs before state update.",
    function="withdraw",
    file="src/VulnerableBank.sol",
    start_line=11,
    end_line=20,
    source_code="""11: function withdraw() external {
12:     uint256 amount = balances[msg.sender];
16:     (bool success, ) = msg.sender.call{value: amount}("");
19:     balances[msg.sender] = 0;
20: }""",
)

context = build_ai_context(finding)

print(context)