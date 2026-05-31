"""PDF rendering utilities using Jinja2 + pdfkit (wkhtmltopdf).

render_html() — sync, returns HTML string
render_pdf()  — async (offloads pdfkit to thread), returns PDF bytes
"""

import asyncio
import logging
import os
from pathlib import Path

import pdfkit
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Absolute path to app/templates — works regardless of cwd
_TEMPLATES_DIR = Path(__file__).parent.parent / 'templates'

# wkhtmltopdf options matching Django's PDF_OPTIONS
_PDF_OPTIONS: dict = {
    'page-size': 'Letter',
    'margin-top': '0.3in',
    'margin-right': '0.6in',
    'margin-bottom': '0.3in',
    'margin-left': '0.6in',
    'encoding': 'UTF-8',
    'enable-local-file-access': '',
    'custom-header': [('Accept-Encoding', 'gzip')],
}

# Jinja2 environment — autoescape ON for HTML safety
# safe filter preserved for trusted DB rich-text fields
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(['html']),
)


def _get_base_dir() -> str:
    """Return BASE_DIR for static file paths in PDF templates."""
    # Resolve to the project root (two levels above app/)
    return str(Path(__file__).parent.parent.parent)


def render_html(template_name: str, context: dict) -> str:
    """Render a Jinja2 template to HTML string.

    Injects base_dir so templates can reference local static assets via
    file://{{ base_dir }}/staticfiles/... (required by wkhtmltopdf).

    Args:
        template_name: filename relative to app/templates/
        context: template variables

    Returns:
        Rendered HTML string
    """
    ctx = {'base_dir': _get_base_dir(), **context}
    template = _jinja_env.get_template(template_name)
    return template.render(ctx)


def _run_pdfkit(html: str) -> bytes:
    """Sync wrapper around pdfkit.from_string() — called via asyncio.to_thread."""
    try:
        return pdfkit.from_string(html, output_path=False, options=_PDF_OPTIONS)
    except Exception as exc:
        logger.error('pdfkit generation failed: %s', exc)
        raise RuntimeError(f'PDF generation failed: {exc}') from exc


async def render_pdf(template_name: str, context: dict) -> bytes:
    """Render template to PDF bytes asynchronously.

    Renders HTML synchronously then offloads wkhtmltopdf to a thread
    so the event loop is not blocked.

    Args:
        template_name: filename relative to app/templates/
        context: template variables

    Returns:
        Raw PDF bytes

    Raises:
        RuntimeError: if wkhtmltopdf fails
    """
    html = render_html(template_name, context)
    return await asyncio.to_thread(_run_pdfkit, html)
