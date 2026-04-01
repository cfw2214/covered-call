#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, Response, jsonify, request

try:
    from covered_call import service
except ModuleNotFoundError:  # pragma: no cover
    import service  # type: ignore


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
HTML_SOURCE_PATH = BASE_DIR / "covered_call.html"

app = Flask(__name__)


def resolve_output_html_path(output_dir: str | None = None) -> Path:
    raw_dir = output_dir or os.getenv("COVERED_CALL_OUTPUT_DIR") or str(BASE_DIR)
    output_path = Path(raw_dir)
    if not output_path.is_absolute():
        output_path = (PROJECT_ROOT / output_path).resolve()
    return output_path / "covered_call.html"


def sync_output_html(output_dir: str | None = None) -> Path:
    target_path = resolve_output_html_path(output_dir)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    source_text = HTML_SOURCE_PATH.read_text(encoding="utf-8")
    if target_path != HTML_SOURCE_PATH:
        target_path.write_text(source_text, encoding="utf-8")
    return target_path


@app.get("/")
def index():
    html_path = sync_output_html()
    return Response(html_path.read_text(encoding="utf-8"), mimetype="text/html")


@app.get("/api/covered-call")
def covered_call_api():
    ticker = (request.args.get("ticker") or "").strip()
    if not ticker:
        return jsonify({"error": "ticker is required"}), 400

    cost_basis_raw = (request.args.get("cost_basis") or "").strip()
    cost_basis = None
    if cost_basis_raw:
        try:
            cost_basis = float(cost_basis_raw)
        except ValueError:
            return jsonify({"error": "cost_basis must be numeric"}), 400

    try:
        report = service.fetch_covered_call_report(ticker=ticker, cost_basis=cost_basis)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 502
    except Exception as exc:  # pragma: no cover
        return jsonify({"error": f"資料來源錯誤：{exc}"}), 502
    return jsonify(report)


if __name__ == "__main__":
    sync_output_html()
    app.run(debug=True)
