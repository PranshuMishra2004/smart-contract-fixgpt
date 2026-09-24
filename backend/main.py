from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from analyzer.fixgpt_engine import run_fixgpt
from analyzer.project_manager import (
    create_workspace,
    get_analysis_target,
)
from analyzer.report_builder import build_security_report


app = FastAPI(
    title="Smart Contract FixGPT API",
    version="1.0.0",
    description=(
        "AI-powered Solidity smart contract "
        "vulnerability detection and remediation API."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = Path(
    "reports/uploads"
).resolve()

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@app.get("/")
def home():
    return {
        "service": "Smart Contract FixGPT API",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "Smart Contract FixGPT API",
    }


@app.post("/analyze")
async def analyze_contract(
    file: UploadFile = File(...),
):
    """
    Analyze either:

    - a single Solidity .sol file
    - a .zip containing a Solidity/Foundry project
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    filename = Path(
        file.filename
    ).name

    extension = Path(
        filename
    ).suffix.lower()

    if extension not in {
        ".sol",
        ".zip",
    }:
        raise HTTPException(
            status_code=400,
            detail=(
                "Only .sol files or .zip "
                "project archives are supported."
            ),
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    safe_filename = (
        f"{uuid4().hex}_{filename}"
    )

    upload_path = (
        UPLOAD_DIR / safe_filename
    ).resolve()

    upload_path.write_bytes(contents)

    print()
    print("=" * 70)
    print("FIXGPT ANALYSIS REQUEST")
    print("=" * 70)
    print(
        f"Original filename: {filename}"
    )
    print(
        f"Uploaded file: {upload_path}"
    )
    print("=" * 70)

    try:
        # ---------------------------------------------
        # CREATE ISOLATED WORKSPACE
        # ---------------------------------------------

        workspace = (
            create_workspace(
                str(upload_path)
            )
            .resolve()
        )

        print(
            f"Workspace: {workspace}"
        )

        # ---------------------------------------------
        # FIND ANALYSIS TARGET
        # ---------------------------------------------

        analysis_target = (
            get_analysis_target(
                workspace
            )
            .resolve()
        )

        print(
            f"Analysis target: "
            f"{analysis_target}"
        )

        # ---------------------------------------------
        # RUN FIXGPT ENGINE
        # ---------------------------------------------

        engine_result = run_fixgpt(
            source_file=str(
                analysis_target
            ),
            project_root=str(
                workspace
            ),
        )

        # ---------------------------------------------
        # BUILD CLEAN REPORT
        # ---------------------------------------------

        report = build_security_report(
            engine_result
        )

    except Exception as exc:

        print()
        print(
            "FixGPT analysis failed:"
        )
        print(exc)

        raise HTTPException(
            status_code=500,
            detail=(
                f"FixGPT analysis failed: "
                f"{exc}"
            ),
        ) from exc

    return {
        "message": (
            "FixGPT analysis completed."
        ),
        "filename": filename,
        "workspace": str(workspace),
        "report": report,
    }