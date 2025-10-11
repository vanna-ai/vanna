"""
Web components for Vanna Agents.

This module provides web components built with Lit that can be embedded
in web applications to provide rich UI for Vanna agent interactions.
"""

import os
from pathlib import Path
from typing import Dict

def get_component_files() -> Dict[str, Path]:
    """Get paths to all web component files."""
    component_dir = Path(__file__).parent
    return {
        'js': component_dir / 'index.js',
        'css': component_dir / 'style.css',
    }

def get_component_html() -> str:
    """Get HTML template for including components."""
    files = get_component_files()

    html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Vanna AI Chat</title>
</head>
<body>
    <vanna-chat title="Vanna AI Assistant"></vanna-chat>
    <script type="module" src="{js_file}"></script>
</body>
</html>
""".format(js_file=files['js'].name)

    return html

__all__ = ['get_component_files', 'get_component_html']