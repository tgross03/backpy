import re

from docutils import nodes
from sphinx.application import Sphinx

COLOR_RE = re.compile(r"\x1b\[38;2;\d+;\d+;\d+m")
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def clean_ansi(text: str) -> str:
    text = COLOR_RE.sub("", text)
    return ANSI_RE.sub("", text)


def strip_ansi_from_nodes(node):
    for child in node.traverse(nodes.Text):
        original = child.astext()
        cleaned = clean_ansi(original)

        if cleaned != original:
            child.parent.replace(child, nodes.Text(cleaned))


def on_doctree_resolved(app, doctree, docname):
    strip_ansi_from_nodes(doctree)


def setup(app: Sphinx):
    app.connect("doctree-resolved", on_doctree_resolved)
    return {
        "version": "2.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
