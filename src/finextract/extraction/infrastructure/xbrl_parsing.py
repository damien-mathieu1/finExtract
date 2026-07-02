from __future__ import annotations

from lxml import etree

from finextract.extraction.domain.models import XbrlFact

_PARSER = etree.XMLParser(recover=True, huge_tree=True)


def parse_xbrl_facts(content: bytes) -> list[XbrlFact]:
    """Parse raw XBRL or inline-XBRL (iXBRL) bytes into facts. Shared by any
    FilingSourcePort adapter (local file, remote download, ...) so parsing
    logic lives in one place regardless of where the bytes came from.

    Handles two shapes SEC filings come in:
    - Plain XBRL XML: the fact's identity is the element's own qualified tag
      (e.g. <us-gaap:Revenues contextRef="c1">1000</us-gaap:Revenues>).
    - Inline XBRL (iXBRL): facts are <ix:nonFraction>/<ix:nonNumeric>
      elements embedded in an XHTML document, identified by a `name`
      attribute (e.g. <ix:nonFraction name="us-gaap:Revenues" .../>) rather
      than the element's own tag. Real SEC 10-K/10-Q filings are iXBRL.

    Uses a recovering parser since iXBRL documents are HTML-flavored and not
    always strictly well-formed XML.
    """
    root = etree.fromstring(content, parser=_PARSER)
    if root is None:
        return []

    return [
        XbrlFact(
            tag=element.get("name") or _qualified_tag(element, root.nsmap),
            value=_element_text(element),
            context_ref=element.get("contextRef", ""),
            unit_ref=element.get("unitRef"),
            decimals=_safe_int(element.get("decimals")),
            scale=_safe_int(element.get("scale")),
            sign=element.get("sign"),
        )
        for element in root.iter()
        if element.get("contextRef") is not None
    ]


def _element_text(element: etree._Element) -> str:
    # iXBRL fact elements can contain nested markup (e.g. <ix:nonFraction>
    # wrapping formatted spans) - itertext() flattens that to the raw value.
    return "".join(element.itertext()).strip()


def _qualified_tag(element: etree._Element, nsmap: dict[str | None, str]) -> str:
    """Render an element's tag as "prefix:localname" using the document's
    namespace map, e.g. "{http://fasb.org/us-gaap/2023}Revenues" -> "us-gaap:Revenues"."""
    qname = etree.QName(element)
    prefix = next((p for p, uri in nsmap.items() if uri == qname.namespace and p), None)
    return f"{prefix}:{qname.localname}" if prefix else qname.localname


def _safe_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None
