"""
Prueba contractual: normalize_schema
Fuente real: arXiv API pública.

Simula fetch (traslado literal) y aplica una variante legacy de normalize
tomando como referencia `docs/legacy/v1/nodos/Contrato_Normalize.md`.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json

# ── Paso 1: Llamada real a arXiv ────────────────────────────────────

QUERY = "artificial intelligence"
MAX_RESULTS = 5

params = urllib.parse.urlencode({
    "search_query": f"all:{QUERY}",
    "sortBy": "submittedDate",
    "sortOrder": "descending",
    "max_results": MAX_RESULTS,
})
url = f"http://export.arxiv.org/api/query?{params}"

req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=30) as resp:
    raw_xml = resp.read().decode("utf-8")

# ── Paso 2: Simular fetch — traslado literal a external_units ───────
# Cada unidad es el string XML literal del <entry>, sin parsear ni
# seleccionar campos. raw_payload guarda el XML completo (solo debug).

raw_payload = raw_xml

root = ET.fromstring(raw_xml)
entries = root.findall("{http://www.w3.org/2005/Atom}entry")

external_units = []
for entry in entries:
    external_units.append(ET.tostring(entry, encoding="unicode"))

# ── Paso 3: Aplicar contrato normalize_schema ───────────────────────
# Schema mínimo cerrado: { title: string, link: string, raw: object }
# raw = unidad literal original (string XML del entry).

NS = {
    "atom": "http://www.w3.org/2005/Atom",
}

normalized_items = []
abort_reason = None

for unit in external_units:
    entry = ET.fromstring(unit)

    title_el = entry.find("atom:title", NS)
    id_el = entry.find("atom:id", NS)

    t = title_el.text if title_el is not None else None
    l = id_el.text if id_el is not None else None

    if not isinstance(t, str) or not isinstance(l, str):
        abort_reason = {"code": "SCHEMA_UNIT_NOT_MAPPABLE"}
        normalized_items = None
        break

    normalized_items.append({
        "title": t,
        "link": l,
        "raw": unit,
    })

# ── Paso 4: Resultado ───────────────────────────────────────────────

print("=" * 70)
print("external_units (resumen estructural)")
print("=" * 70)
print(f"Total unidades: {len(external_units)}")
for i, u in enumerate(external_units):
    print(f"  [{i}] length={len(u)} chars")
print()

if abort_reason:
    print("=" * 70)
    print("abort_reason")
    print("=" * 70)
    print(json.dumps(abort_reason, ensure_ascii=False))
else:
    print("=" * 70)
    print("normalized_items")
    print("=" * 70)
    print(f"Total items: {len(normalized_items)}")
    for i, item in enumerate(normalized_items):
        print(f"  [{i}]")
        print(f"    title: {json.dumps(item['title'].strip(), ensure_ascii=False)}")
        print(f"    link:  {json.dumps(item['link'], ensure_ascii=False)}")
        print(f"    raw:   {len(item['raw'])} chars")
