"""PDF rendering utilities using Jinja2 + WeasyPrint.

render_html() — sync, returns HTML string
render_pdf()  — async (offloads WeasyPrint to a thread), returns PDF bytes

WeasyPrint (replaces the legacy wkhtmltopdf/pdfkit engine) supports modern
print CSS: @page margin boxes, page counters, gradients, border-radius,
embedded SVG and local web fonts. Templates resolve relative asset URLs
(images, fonts) against ``base_url`` = the project root, so a template can
reference e.g. ``static/report-assets/x.webp`` directly.
"""

import asyncio
import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import CSS, HTML

logger = logging.getLogger(__name__)

# Absolute path to app/templates — works regardless of cwd
_TEMPLATES_DIR = Path(__file__).parent.parent / 'templates'

# Project root (two levels above app/) — base for resolving local static assets
_BASE_DIR = Path(__file__).parent.parent.parent

# Default page geometry, mirroring the legacy wkhtmltopdf PDF_OPTIONS
# (Letter, 0.3in top/bottom, 0.6in left/right). Templates may override via
# their own @page rules (e.g. reports/_theme.css) — author stylesheets win.
_DEFAULT_PAGE_CSS = CSS(string='@page { size: Letter; margin: 0.3in 0.6in; }')

# base_url must end with a separator so relative URLs join against the project
# directory rather than dropping its last path segment.
_BASE_URL = _BASE_DIR.as_uri() + '/'

# Jinja2 environment — autoescape ON for HTML safety
# safe filter preserved for trusted DB rich-text fields
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(['html']),
)


def _get_base_dir() -> str:
    """Return BASE_DIR for static file paths in PDF templates."""
    return str(_BASE_DIR)


def render_html(template_name: str, context: dict) -> str:
    """Render a Jinja2 template to an HTML string.

    Injects ``base_dir`` so templates can reference local static assets.

    Args:
        template_name: filename relative to app/templates/
        context: template variables

    Returns:
        Rendered HTML string
    """
    ctx = {'base_dir': _get_base_dir(), **context}
    template = _jinja_env.get_template(template_name)
    return template.render(ctx)


def _run_weasyprint(html: str) -> bytes:
    """Sync WeasyPrint render — called via asyncio.to_thread."""
    try:
        return HTML(string=html, base_url=_BASE_URL).write_pdf(
            stylesheets=[_DEFAULT_PAGE_CSS],
        )
    except Exception as exc:
        logger.error('WeasyPrint generation failed: %s', exc)
        raise RuntimeError(f'PDF generation failed: {exc}') from exc


async def render_pdf(template_name: str, context: dict) -> bytes:
    """Render a template to PDF bytes asynchronously.

    Renders HTML synchronously then offloads WeasyPrint to a thread so the
    event loop is not blocked.

    Args:
        template_name: filename relative to app/templates/
        context: template variables

    Returns:
        Raw PDF bytes

    Raises:
        RuntimeError: if WeasyPrint fails
    """
    html = render_html(template_name, context)
    return await asyncio.to_thread(_run_weasyprint, html)
