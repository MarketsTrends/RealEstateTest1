from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.schemas import AnalysisRequest
from app.services.analysis_service import run_analysis

BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


def _format_money(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.2f} €".replace(",", " ")


def _format_percent(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.2f}%"


def _format_number(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}"


def build_pdf_report(payload: AnalysisRequest) -> bytes:
    try:
        from weasyprint import CSS, HTML
    except Exception as exc:  # pragma: no cover - depends on local system deps
        raise RuntimeError(
            "PDF generation is unavailable: install WeasyPrint and required OS libraries"
        ) from exc

    result = run_analysis(payload)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html")

    html = template.render(
        request=payload,
        result=result,
        fmt_money=_format_money,
        fmt_pct=_format_percent,
        fmt_number=_format_number,
    )

    pdf = HTML(string=html, base_url=str(BASE_DIR)).write_pdf(
        stylesheets=[CSS(filename=str(STATIC_DIR / "report.css"))]
    )
    return pdf
