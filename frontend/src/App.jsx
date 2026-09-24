import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";


function VerificationItem({ label, status }) {
  let className = "";
  let text = "";

  if (status === "passed") {
    className = "status-passed";
    text = "✓ Passed";
  } else if (status === "failed") {
    className = "status-failed";
    text = "✗ Failed";
  } else {
    className = "status-na";
    text = "Not Applicable";
  }

  return (
    <div className="verification-item">
      <span>{label}</span>

      <strong className={className}>
        {text}
      </strong>
    </div>
  );
}


function getVerificationStatus(remediation) {
  const verification = remediation?.verification;

  if (!verification) {
    return {
      compilation: "na",
      slither: "na",
      foundry: "na",
      overall: "na",
    };
  }

  return {
    compilation:
      verification.compilation === true
        ? "passed"
        : verification.compilation === false
          ? "failed"
          : "na",

    slither:
      verification.slither === true
        ? "passed"
        : verification.slither === false
          ? "failed"
          : "na",

    foundry:
      verification.foundry?.applicable
        ? verification.foundry.passed === true
          ? "passed"
          : "failed"
        : "na",

    overall:
      verification.overall === true
        ? "passed"
        : verification.overall === false
          ? "failed"
          : "na",
  };
}


function getFindingStatus(finding) {
  const remediation = finding?.remediation;

  if (!remediation) {
    return {
      label: "No remediation",
      className: "status-na",
    };
  }

  if (remediation.verification?.overall === true) {
    return {
      label: "Verified",
      className: "status-passed",
    };
  }

  if (remediation.verification?.overall === false) {
    return {
      label: "Verification Failed",
      className: "status-failed",
    };
  }

  return {
    label: "Remediation Generated",
    className: "status-na",
  };
}


function severityClass(severity) {
  return String(severity || "Unknown")
    .toLowerCase()
    .replace(/\s+/g, "-");
}


function downloadFile(content, filename, type) {
  const blob = new Blob(
    [content],
    { type }
  );

  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);

  link.click();

  link.remove();

  URL.revokeObjectURL(url);
}


function buildMarkdownReport(report) {
  let markdown = "";

  markdown += "# Smart Contract FixGPT Security Report\n\n";

  markdown += `Generated: ${report.generated_at}\n\n`;

  markdown += `Source: ${report.source_file}\n\n`;

  markdown += "---\n\n";

  markdown += "## Summary\n\n";

  markdown += `- Total findings: ${report.summary.total_findings}\n`;

  markdown += `- Actionable findings: ${report.summary.actionable_findings}\n`;

  markdown += `- Skipped findings: ${report.summary.skipped_findings}\n`;

  markdown += `- Verified fixes: ${report.summary.verified_fixes}\n\n`;

  markdown += "---\n\n";

  report.findings.forEach(
    (finding, index) => {
      markdown += `## Finding #${index + 1}: ${finding.category}\n\n`;

      markdown += `**Severity:** ${finding.severity}\n\n`;

      markdown += `**Confidence:** ${finding.confidence}\n\n`;

      markdown += `**Detector:** ${finding.check}\n\n`;

      markdown += `**Function:** ${finding.function || "N/A"}\n\n`;

      markdown += `**Lines:** ${finding.start_line}-${finding.end_line}\n\n`;

      markdown += "### Detector Description\n\n";

      markdown += `${finding.description || "No description available."}\n\n`;

      markdown += "### Source Code\n\n";

      markdown += "```solidity\n";

      markdown += `${finding.source_code || ""}\n`;

      markdown += "```\n\n";

      if (finding.remediation) {
        const remediation = finding.remediation;
        const verification = remediation.verification || {};

        markdown += "## AI Remediation\n\n";

        markdown += "### Explanation\n\n";

        markdown += `${remediation.explanation || "N/A"}\n\n`;

        markdown += "### Root Cause\n\n";

        markdown += `${remediation.root_cause || "N/A"}\n\n`;

        markdown += "### Recommendation\n\n";

        markdown += `${remediation.recommendation || "N/A"}\n\n`;

        markdown += "### Fixed Code\n\n";

        markdown += "```solidity\n";

        markdown += `${remediation.fixed_code || ""}\n`;

        markdown += "```\n\n";

        markdown += "### Code Changes\n\n";

        markdown += "```diff\n";

        markdown += `${remediation.code_diff || "No code changes detected."}\n`;

        markdown += "```\n\n";

        markdown += "### Verification\n\n";

        markdown += `- Compilation: ${
          verification.compilation
            ? "PASSED"
            : "FAILED"
        }\n`;

        markdown += `- Slither target vulnerability: ${
          verification.slither
            ? "REMOVED"
            : "STILL DETECTED"
        }\n`;

        const foundry = verification.foundry;

        if (foundry?.applicable) {
          markdown += `- Foundry security test: ${
            foundry.passed
              ? "PASSED"
              : "FAILED"
          }\n`;
        } else {
          markdown +=
            "- Foundry security test: NOT APPLICABLE\n";
        }

        markdown += `- Overall verification: ${
          verification.overall
            ? "PASSED"
            : "FAILED"
        }\n`;

        const remaining =
          verification.remaining_detectors || [];

        markdown += `- Remaining detectors: ${
          remaining.length > 0
            ? remaining.join(", ")
            : "None"
        }\n\n`;
      } else {
        markdown += "## AI Remediation\n\n";

        markdown +=
          "No AI-generated remediation was created for this finding.\n\n";
      }

      markdown += "---\n\n";
    }
  );

  return markdown;
}


function App() {
  const [file, setFile] = useState(null);

  const [report, setReport] = useState(null);

  const [error, setError] = useState("");

  const [loading, setLoading] = useState(false);


  const handleFileChange = (event) => {
    const selectedFile =
      event.target.files?.[0];

    setError("");
    setReport(null);

    if (!selectedFile) {
      setFile(null);
      return;
    }

    const fileName =
      selectedFile.name.toLowerCase();

    const validFile =
      fileName.endsWith(".sol") ||
      fileName.endsWith(".zip");

    if (!validFile) {
      setFile(null);

      setError(
        "Please select a .sol file or Foundry .zip project."
      );

      return;
    }

    setFile(selectedFile);
  };


  const handleAnalyze = async () => {
    if (!file) {
      setError(
        "Please select a Solidity file or project first."
      );

      return;
    }

    setLoading(true);
    setError("");
    setReport(null);

    const formData = new FormData();

    formData.append(
      "file",
      file
    );

    try {
      const response = await fetch(
        `${API_URL}/analyze`,
        {
          method: "POST",
          body: formData,
        }
      );

      let data;

      try {
        data = await response.json();
      } catch {
        throw new Error(
          "FixGPT returned an invalid response."
        );
      }

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Analysis failed."
        );
      }

      setReport(data.report);
    } catch (err) {
      setError(
        err.message ||
          "Unable to connect to FixGPT."
      );
    } finally {
      setLoading(false);
    }
  };


  const handleDownloadJSON = () => {
    if (!report) {
      return;
    }

    downloadFile(
      JSON.stringify(
        report,
        null,
        2
      ),
      "fixgpt-security-report.json",
      "application/json"
    );
  };


  const handleDownloadMarkdown = () => {
    if (!report) {
      return;
    }

    const markdown =
      buildMarkdownReport(report);

    downloadFile(
      markdown,
      "fixgpt-security-report.md",
      "text/markdown"
    );
  };


  const summary = report?.summary;


  return (
    <div className="app">

      <header className="header">

        <div>
          <h1>
            Smart Contract FixGPT
          </h1>

          <p>
            AI-powered Solidity vulnerability
            detection, remediation, and verification.
          </p>
        </div>

        <div className="status-badge">
          ● Engine Ready
        </div>

      </header>


      <main className="container">

        {/* UPLOAD */}

        <section className="upload-card">

          <h2>
            Analyze Smart Contract
          </h2>

          <p className="section-description">
            Upload a Solidity contract or a complete
            Foundry project and FixGPT will analyze,
            remediate, and verify security findings.
          </p>


          <label className="upload-area">

            <input
              type="file"
              accept=".sol,.zip"
              onChange={handleFileChange}
            />

            <div className="upload-icon">
              ↑
            </div>

            <strong>
              {file
                ? file.name
                : "Choose a Solidity file or Foundry project"}
            </strong>

            <span>
              {file
                ? `${(
                    file.size / 1024
                  ).toFixed(1)} KB`
                : ".sol or .zip"}
            </span>

          </label>


          {error && (
            <div className="error-message">
              {error}
            </div>
          )}


          <button
            className="analyze-button"
            onClick={handleAnalyze}
            disabled={!file || loading}
          >
            {loading
              ? "Analyzing Contract..."
              : "Analyze Contract"}
          </button>

        </section>


        {/* LOADING */}

        {loading && (
          <section className="loading-card">

            <div className="spinner"></div>

            <h3>
              FixGPT is analyzing your project
            </h3>

            <p>
              Running Slither, generating AI remediation,
              compiling the candidate, and verifying the fix.
            </p>

            <div className="pipeline">
              <span>Slither</span>
              <span>→</span>
              <span>Gemini</span>
              <span>→</span>
              <span>Compile</span>
              <span>→</span>
              <span>Foundry</span>
            </div>

          </section>
        )}


        {/* REPORT */}

        {report && (
          <section className="results-section">

            {/* REPORT HEADER */}

            <div className="results-header">

              <div>

                <h2>
                  Security Analysis
                </h2>

                <p>
                  Generated:{" "}
                  {new Date(
                    report.generated_at
                  ).toLocaleString()}
                </p>

                <p>
                  Source:{" "}
                  <strong>
                    {report.source_file}
                  </strong>
                </p>

              </div>


              <div className="summary-box">

                <strong>
                  {summary?.total_findings ?? 0}
                </strong>

                <span>
                  Findings
                </span>

              </div>

            </div>


            {/* REPORT ACTIONS */}

            <div className="report-actions">

              <button
                className="secondary-button"
                onClick={handleDownloadJSON}
              >
                Download JSON
              </button>

              <button
                className="secondary-button"
                onClick={handleDownloadMarkdown}
              >
                Download Markdown
              </button>

            </div>


            {/* SUMMARY */}

            <div className="summary-grid">

              <div className="summary-card">
                <span>
                  Total Findings
                </span>

                <strong>
                  {summary?.total_findings ?? 0}
                </strong>
              </div>


              <div className="summary-card">
                <span>
                  Actionable
                </span>

                <strong>
                  {summary?.actionable_findings ?? 0}
                </strong>
              </div>


              <div className="summary-card">
                <span>
                  Skipped
                </span>

                <strong>
                  {summary?.skipped_findings ?? 0}
                </strong>
              </div>


              <div className="summary-card">
                <span>
                  Verified Fixes
                </span>

                <strong>
                  {summary?.verified_fixes ?? 0}
                </strong>
              </div>

            </div>


            {/* FINDINGS */}

            <div className="findings-list">

              {(report.findings || []).map(
                (finding, index) => {

                  const remediation =
                    finding.remediation;

                  const findingStatus =
                    getFindingStatus(
                      finding
                    );

                  const verificationStatus =
                    getVerificationStatus(
                      remediation
                    );

                  const remainingDetectors =
                    remediation?.verification
                      ?.remaining_detectors || [];

                  return (
                    <article
                      className="finding-card"
                      key={`${finding.check}-${index}`}
                    >

                      {/* FINDING HEADER */}

                      <div className="finding-header">

                        <div>

                          <span className="finding-number">
                            Finding #{index + 1}
                          </span>

                          <h3>
                            {finding.category}
                          </h3>

                        </div>


                        <div className="finding-header-right">

                          <div
                            className={`severity ${severityClass(
                              finding.severity
                            )}`}
                          >
                            {finding.severity}
                          </div>

                          <div
                            className={`finding-status ${findingStatus.className}`}
                          >
                            {findingStatus.label}
                          </div>

                        </div>

                      </div>


                      {/* FINDING META */}

                      <div className="finding-meta">

                        <span>
                          Detector:{" "}
                          <strong>
                            {finding.check}
                          </strong>
                        </span>

                        <span>
                          Function:{" "}
                          <strong>
                            {finding.function || "N/A"}
                          </strong>
                        </span>

                        <span>
                          Lines:{" "}
                          <strong>
                            {finding.start_line}
                            -
                            {finding.end_line}
                          </strong>
                        </span>

                        <span>
                          Confidence:{" "}
                          <strong>
                            {finding.confidence}
                          </strong>
                        </span>

                      </div>


                      {/* DESCRIPTION */}

                      <div className="result-block">

                        <h4>
                          Detector Description
                        </h4>

                        <p>
                          {finding.description ||
                            "No description available."}
                        </p>

                      </div>


                      {/* SOURCE */}

                      <div className="result-block">

                        <h4>
                          Vulnerable Source
                        </h4>

                        <pre>
                          <code>
                            {finding.source_code ||
                              "Source code unavailable."}
                          </code>
                        </pre>

                      </div>


                      {/* REMEDIATION */}

                      {remediation ? (
                        <>
                          <div className="result-block">

                            <h4>
                              AI Explanation
                            </h4>

                            <p>
                              {remediation.explanation ||
                                "No explanation provided."}
                            </p>

                          </div>


                          <div className="result-block">

                            <h4>
                              Root Cause
                            </h4>

                            <p>
                              {remediation.root_cause ||
                                "No root cause provided."}
                            </p>

                          </div>


                          <div className="result-block">

                            <h4>
                              Recommendation
                            </h4>

                            <p>
                              {remediation.recommendation ||
                                "No recommendation provided."}
                            </p>

                          </div>


                          <div className="result-block">

                            <h4>
                              Generated Fix
                            </h4>

                            <pre>
                              <code>
                                {remediation.fixed_code ||
                                  "No fixed code generated."}
                              </code>
                            </pre>

                          </div>


                          <div className="result-block">

                            <h4>
                              Code Changes
                            </h4>

                            <pre>
                              <code>
                                {remediation.code_diff ||
                                  "No code changes detected."}
                              </code>
                            </pre>

                          </div>


                          {/* VERIFICATION */}

                          <div className="verification-result">

                            <div className="verification-header">

                              <h4>
                                Verification
                              </h4>

                              <strong
                                className={
                                  verificationStatus.overall ===
                                  "passed"
                                    ? "status-passed"
                                    : verificationStatus.overall ===
                                        "failed"
                                      ? "status-failed"
                                      : "status-na"
                                }
                              >
                                {verificationStatus.overall ===
                                "passed"
                                  ? "✓ VERIFIED"
                                  : verificationStatus.overall ===
                                      "failed"
                                    ? "✗ FAILED"
                                    : "NOT VERIFIED"}
                              </strong>

                            </div>


                            <div className="verification-grid">

                              <VerificationItem
                                label="Compilation"
                                status={
                                  verificationStatus.compilation
                                }
                              />


                              <VerificationItem
                                label="Slither Target"
                                status={
                                  verificationStatus.slither
                                }
                              />


                              <VerificationItem
                                label="Foundry Security Test"
                                status={
                                  verificationStatus.foundry
                                }
                              />


                              <VerificationItem
                                label="Overall Verification"
                                status={
                                  verificationStatus.overall
                                }
                              />

                            </div>


                            {/* REMAINING DETECTORS */}

                            <div className="remaining-detectors">

                              <span>
                                Remaining detectors:
                              </span>

                              <strong>
                                {remainingDetectors.length > 0
                                  ? remainingDetectors.join(", ")
                                  : "None"}
                              </strong>

                            </div>

                          </div>

                        </>
                      ) : (
                        <div className="verification-result">

                          <h4>
                            AI Remediation
                          </h4>

                          <p>
                            No AI-generated remediation
                            was created for this finding.
                          </p>

                        </div>
                      )}

                    </article>
                  );
                }
              )}

            </div>

          </section>
        )}

      </main>

    </div>
  );
}


export default App;