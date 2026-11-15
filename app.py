"""Vercel Python entrypoint — repository root, so api/app.py keeps its
`Path(__file__).resolve().parents[1]` artifact root and bundles artifacts/ + config/.

Local/dev serving stays `uvicorn api.app:app` (Makefile `dev`).
"""
from api.app import app  # noqa: F401
