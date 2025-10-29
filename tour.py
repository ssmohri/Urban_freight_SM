# tour.py — lightweight Intro.js integration for Streamlit (Py 3.8+ compatible)
from textwrap import dedent
from typing import List, Dict, Optional
import streamlit.components.v1 as components

_INTROJS_CSS = "https://unpkg.com/intro.js/minified/introjs.min.css"
_INTROJS_JS  = "https://unpkg.com/intro.js/minified/intro.min.js"

def start_intro(steps: List[Dict], options: Optional[Dict] = None) -> None:
    """
    steps: list of { 'element': '#css-selector', 'intro': 'text', 'position': 'right'|'left'|'top'|'bottom' }
    options: any Intro.js option (e.g. {'showProgress': True, 'showStepNumbers': True})
    """
    if options is None:
        options = {
            "showProgress": True,
            "showStepNumbers": True,
            "exitOnOverlayClick": False,
            "scrollToElement": True,
            "disableInteraction": False,
            "highlightClass": "",  # custom CSS class if you want extra styling
        }

    html = f"""
    <link rel="stylesheet" href="{_INTROJS_CSS}">
    <script src="{_INTROJS_JS}"></script>
    <script>
      window.addEventListener('load', () => {{
        const steps = {steps};
        const opts = {options};
        try {{
          const tour = introJs();
          tour.setOptions({{ steps, ...opts }});
          tour.start();
        }} catch(e) {{
          console.error('Intro.js failed:', e);
        }}
      }});
    </script>
    """
    components.html(dedent(html), height=1, scrolling=False)
