"""
Fixtures y datos compartidos para tests contractuales v1.
"""

import xml.etree.ElementTree as ET

# ── Sample arXiv XML entries (Element objects) ────────────────────────

ARXIV_ENTRY_VALID_1 = ET.fromstring(
    '<entry xmlns="http://www.w3.org/2005/Atom">'
    "<id>http://arxiv.org/abs/2401.00001v1</id>"
    "<title>Test Paper on Machine Learning</title>"
    "<summary>This paper presents a new approach to machine learning "
    "using neural networks and transformers.</summary>"
    "<published>2025-02-10T00:00:00Z</published>"
    "</entry>"
)

ARXIV_ENTRY_NO_TITLE = ET.fromstring(
    '<entry xmlns="http://www.w3.org/2005/Atom">'
    "<id>http://arxiv.org/abs/2401.00004v1</id>"
    "<summary>This entry has no title element.</summary>"
    "<published>2025-02-07T00:00:00Z</published>"
    "</entry>"
)
