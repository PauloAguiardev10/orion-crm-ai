"""Entrega o bundle da Central na mesma origem da API autenticada."""

from pathlib import Path

from fastapi.staticfiles import StaticFiles


def montar_central_ui(app):
    diretorio = Path(__file__).resolve().parents[3] / "dashboard" / "central_ui" / "dist"
    if (diretorio / "index.html").is_file():
        app.mount("/central-ui", StaticFiles(directory=diretorio, html=True), name="central-ui")
