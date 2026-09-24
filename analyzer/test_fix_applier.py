from analyzer.fix_applier import apply_function_fix


source_file = "contracts/src/VulnerableBank.sol"

fixed_code = """
function withdraw() external {
    uint256 amount = balances[msg.sender];

    require(amount > 0, "No balance");

    balances[msg.sender] = 0;

    (bool success, ) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}
"""

output_file = "reports/generated/VulnerableBank_fixed.sol"

result = apply_function_fix(
    source_file=source_file,
    start_line=11,
    end_line=20,
    fixed_code=fixed_code,
    output_file=output_file,
)

print(f"Fixed contract created at: {result}")