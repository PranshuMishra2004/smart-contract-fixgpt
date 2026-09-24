from analyzer.source_reader import read_source_lines


source_file = "contracts/src/VulnerableBank.sol"

code = read_source_lines(
    source_file,
    11,
    20,
)

print("Vulnerable source:\n")
print(code)