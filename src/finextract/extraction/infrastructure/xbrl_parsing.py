from __future__ import annotations

from datetime import date

from lxml import etree

from finextract.extraction.domain.models import XbrlFact

_PARSER = etree.XMLParser(recover=True, huge_tree=True)
_XBRLI_NS = "http://www.xbrl.org/2003/instance"
_ENTITY_NAME_TAGS = (
    "dei:EntityRegistrantName",
    "jpdei_cor:FilerNameInEnglishDEI",
    "jpdei_cor:FilerNameInJapaneseDEI",
)


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

    contexts = _resolve_contexts(root)
    currencies = _resolve_currencies(root)

    facts = []
    for element in root.iter():
        if element.get("contextRef") is None:
            continue
        period = contexts.get(element.get("contextRef", ""))
        facts.append(
            XbrlFact(
                tag=element.get("name") or _qualified_tag(element, root.nsmap),
                value=_element_text(element),
                context_ref=element.get("contextRef", ""),
                unit_ref=element.get("unitRef"),
                decimals=_safe_int(element.get("decimals")),
                scale=_safe_int(element.get("scale")),
                sign=element.get("sign"),
                period_start=period[0] if period else None,
                period_end=period[1] if period else None,
                currency=currencies.get(element.get("unitRef", "")),
            )
        )
    return facts


def _resolve_currencies(root: etree._Element) -> dict[str, str]:
    """Map unit id -> ISO 4217 code. Only plain iso4217 measures count, so
    per-share units (a <divide> with no direct <measure>) are left out."""
    currencies: dict[str, str] = {}
    for unit in root.iter(f"{{{_XBRLI_NS}}}unit"):
        measure = unit.find(f"{{{_XBRLI_NS}}}measure")
        text = (measure.text or "").strip() if measure is not None else ""
        prefix, _, code = text.partition(":")
        if prefix.lower() == "iso4217" and unit.get("id"):
            currencies[unit.get("id", "")] = code.upper()
    return currencies


def entity_name(facts: list[XbrlFact], fallback: str) -> str:
    """The filer's name as stated in the filing's own cover-page facts."""
    by_tag = {fact.tag: fact.value for fact in facts if fact.value}
    return next((by_tag[tag] for tag in _ENTITY_NAME_TAGS if tag in by_tag), fallback)


def _resolve_contexts(root: etree._Element) -> dict[str, tuple[date, date]]:
    """Map contextRef id -> (period_start, period_end) by reading each
    filing's <xbrli:context> definitions. Instant periods (balance-sheet
    facts, e.g. "Assets" as of a single date) are represented as
    start == end == instant, so callers can treat every period uniformly as
    a (start, end) range. Contexts with unparseable/missing period data are
    dropped from the map; facts referencing them simply get no period
    resolved (see XbrlFact.period_start/period_end == None).

    Dimensional contexts (<segment>/<scenario>, e.g. revenue by product line)
    are dropped too: they share the base period, so keeping them would let a
    breakdown stand in for the consolidated total in the flat schema. The
    exception is an EDINET filer with no consolidated statements: its main
    statements are filed under NonConsolidatedMember contexts.
    """
    standalone_filer = any(
        (el.text or "").strip() == "false"
        for el in root.iter("{*}WhetherConsolidatedFinancialStatementsArePreparedDEI")
    )
    contexts: dict[str, tuple[date, date]] = {}
    for context in root.iter(f"{{{_XBRLI_NS}}}context"):
        context_id = context.get("id")
        if not context_id:
            continue
        is_main_standalone = standalone_filer and context_id.endswith("_NonConsolidatedMember")
        if _is_dimensional(context) and not is_main_standalone:
            continue
        period_el = context.find(f"{{{_XBRLI_NS}}}period")
        if period_el is None:
            continue

        instant_el = period_el.find(f"{{{_XBRLI_NS}}}instant")
        if instant_el is not None and instant_el.text:
            instant = _safe_date(instant_el.text.strip())
            if instant is not None:
                contexts[context_id] = (instant, instant)
            continue

        start_el = period_el.find(f"{{{_XBRLI_NS}}}startDate")
        end_el = period_el.find(f"{{{_XBRLI_NS}}}endDate")
        if start_el is not None and end_el is not None and start_el.text and end_el.text:
            start = _safe_date(start_el.text.strip())
            end = _safe_date(end_el.text.strip())
            if start is not None and end is not None:
                contexts[context_id] = (start, end)

    return contexts


def _is_dimensional(context: etree._Element) -> bool:
    return (
        context.find(f".//{{{_XBRLI_NS}}}segment") is not None
        or context.find(f"{{{_XBRLI_NS}}}scenario") is not None
    )


def _safe_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


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
