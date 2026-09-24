# Smart Contract FixGPT

AI-powered Solidity vulnerability detection, remediation, and verification platform.

Smart Contract FixGPT combines static security analysis with AI-assisted code remediation and automated verification to help developers identify and fix common Solidity vulnerabilities.

## Overview

FixGPT analyzes Solidity smart contracts using Slither, classifies security findings, generates remediation suggestions using Gemini, applies the proposed fixes, and verifies the resulting contract using compilation, Slither re-analysis, and vulnerability-specific Foundry security tests.

## Pipeline

```text
Solidity Contract / Foundry Project
                ↓
            Slither
                ↓
        Finding Parser
                ↓
     Vulnerability Classifier
                ↓
          Gemini AI
                ↓
         Candidate Fix
                ↓
            Compiler
                ↓
       Slither Re-analysis
                ↓
       Foundry Security Test
                ↓
        Verification Result
                ↓
          Security Report
                ↓
          React Frontend
```

## Features

- Solidity `.sol` file analysis
- Complete Foundry project `.zip` analysis
- Slither-based vulnerability detection
- Vulnerability severity classification
- AI-assisted remediation using Google Gemini
- Structured AI responses using Pydantic
- Automatic fixed-contract generation
- Code diff generation
- Solidity compilation verification
- Slither re-analysis after remediation
- Vulnerability-specific Foundry security tests
- Final verification status
- JSON security report download
- Markdown security report download
- React frontend
- FastAPI backend

## Vulnerabilities Currently Supported

### Reentrancy

Detector:

```text
reentrancy-eth
```

FixGPT can generate a remediation for the vulnerable interaction pattern and verify the resulting contract using a Foundry reentrancy security test.

### Transaction Origin Authentication

Detector:

```text
tx-origin
```

FixGPT identifies authentication logic relying on `tx.origin` and can generate a remediation using an appropriate caller-based authorization pattern.

The resulting candidate is re-analyzed and verified with a vulnerability-specific Foundry test.

## Architecture

```text
smart-contract-fixgpt/
│
├── analyzer/
│   ├── analysis_runner.py
│   ├── slither_parser.py
│   ├── vulnerability_classifier.py
│   ├── finding_model.py
│   ├── ai_context_builder.py
│   ├── ai_prompt_builder.py
│   ├── ai_response_model.py
│   ├── ai_client.py
│   ├── fix_applier.py
│   ├── diff_generator.py
│   ├── verification.py
│   ├── foundry_verifier.py
│   ├── security_test_registry.py
│   ├── fixgpt_engine.py
│   ├── project_manager.py
│   └── report_builder.py
│
├── backend/
│   └── main.py
│
├── frontend/
│   └── React application
│
├── contracts/
│   └── Solidity / Foundry contracts
│
├── e2e-test-project/
│   └── Multi-contract test project
│
├── reports/
│   └── Runtime-generated reports
│
├── .env.example
├── .gitignore
└── README.md
```

## Technology Stack

### Backend

- Python
- FastAPI
- Slither
- Pydantic
- Google Gemini API

### Smart Contract Tooling

- Solidity
- Foundry
- Forge
- `solc`

### Frontend

- React
- Vite
- JavaScript
- CSS

## Installation

Clone the repository:

```bash
git clone https://github.com/PranshuMishra2004/smart-contract-fixgpt.git
cd smart-contract-fixgpt
```

### Python Environment

Create and activate the virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the required Python dependencies used by the project.Install the Python dependencies:

```bash
pip install -r requirements.txt

### Environment Variables

Create a local `.env` file:

```bash
cp .env.example .env
```

Add your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite
```

Do not commit `.env` to GitHub.

## Running the Backend

From the project root:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

Backend:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## Running the Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

## Usage

1. Open the FixGPT frontend.
2. Upload either:
   - a Solidity `.sol` file, or
   - a complete Foundry `.zip` project.
3. Click **Analyze Contract**.
4. FixGPT runs static analysis using Slither.
5. Actionable findings are passed to Gemini for remediation.
6. FixGPT generates a candidate fixed contract.
7. The candidate is compiled.
8. Slither re-analyzes the candidate.
9. A vulnerability-specific Foundry security test is executed when available.
10. FixGPT displays the final verification result and security report.

## Verification Model

A generated fix is not considered successful merely because the AI produced valid-looking Solidity.

FixGPT verifies the candidate through multiple stages:

```text
Compilation
     +
Slither target vulnerability removed
     +
Foundry security test passed
     =
Overall verification passed
```

When no vulnerability-specific Foundry test is registered, verification falls back to compilation and Slither target removal.

## Example

For a vulnerable contract containing:

```solidity
(bool success, ) = msg.sender.call{value: amount}("");
balances[msg.sender] = 0;
```

FixGPT can identify the reentrancy finding and generate a candidate that follows the checks-effects-interactions pattern:

```solidity
balances[msg.sender] = 0;

(bool success, ) = msg.sender.call{value: amount}("");
require(success, "Transfer failed");
```

The candidate is then compiled, re-analyzed, and tested.

## Project Status

This project is an actively developed prototype demonstrating an end-to-end workflow for AI-assisted smart contract security analysis and remediation.

Current implementation includes:

- Multi-contract project analysis
- Gemini-based remediation
- Candidate fix generation
- Compilation verification
- Slither re-analysis
- Foundry security verification
- JSON and Markdown reports
- React frontend

## Security Considerations

AI-generated code should not automatically be considered production-safe.

FixGPT uses automated verification to reduce the risk of incorrect remediation, but smart contract changes should still undergo human review and appropriate security auditing before deployment.

## License

MIT