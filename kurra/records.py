"""Parse Bhulekh khatauni 'Order Description' text (Hindi) into per-khata sale entries."""
from __future__ import annotations
import re
import unicodedata
import pandas as pd

_ZW = {0x200C: None, 0x200D: None}
COURT = "जिला एवं सत्र न्यायालय औरैया"


def norm(t: str) -> str:
    return unicodedata.normalize("NFC", t.translate(_ZW))


_CASE = re.compile(r"वाद\s*सं(?:ख्या|\S{0,2})\s*-?\s*(?P<case>[A-Za-z0-9_\-]+)")
_SALE_SQM = re.compile(
    r"(?<!ि)क्रे(?:ता|ती)\s+(?:नाम\s+)?(?P<buyer>.+?)\s+(?:पुत्र|पत्नी|पिता/पति)\s.*?"
    r"(?:(?:बैनामा|विक्रय विलेख)\s+(?:दिन\S{0,3}क\s+(?P<deed>\d{2}[\./]\d{2}[\./]\d{4})\s+)?.*?)?"
    r"(?P<sqm>\d+(?:\.\d+)?)\s*वर्गमीटर", re.S)

_SALE_HA = re.compile(
    r"(?<!ि)क्रेता\s+(?:नाम\s+)?(?P<buyer>.+?)\s+(?:पिता/पति|पुत्र|पत्नी)\s.*?"
    r"(?:रकबा|क्षे०)\s*(?P<ha>0\.\d+).*?"
    r"दिनांक\s+(?P<deed>\d{2}[\./]\d{2}[\./]\d{4})", re.S)

_COURT = re.compile(r"रकवा-?\s*(?P<ha>\d\.\d+)\s*हे0.*?(?<!ि)क्रेता\s+" + COURT + r"\s+का\s+नाम", re.S)
_KHATA = re.compile(r"Order Description For Khata No\.:-\s*(\d+)")
_SPLIT = re.compile(r"(?:^|\n|\s)(\d{1,3})\s*:\s*")


def parse_orders(text: str) -> pd.DataFrame:
    text = norm(text)
    rows = []
    sections = _KHATA.split(text)          # [pre, khata1, body1, khata2, body2, ...]
    for i in range(1, len(sections), 2):
        khata, body = sections[i], sections[i + 1]
        chunks = _SPLIT.split(body)        # [pre, n1, chunk1, n2, chunk2, ...]
        for j in range(1, len(chunks), 2):
            order_no, chunk = chunks[j], chunks[j + 1]
            cm = _CASE.search(chunk)
            case = cm.group("case") if cm else ""
            m = _COURT.search(chunk)
            if m:
                rows.append(dict(khata=khata, order_no=int(order_no), case_no=case, buyer=COURT,
                                 sqm=float(m.group("ha")) * 10000, deed_date="", kind="court_purchase"))
                continue
            m = _SALE_SQM.search(chunk)
            if m:
                rows.append(dict(khata=khata, order_no=int(order_no), case_no=case,
                                 buyer=m.group("buyer").strip(), sqm=float(m.group("sqm")),
                                 deed_date=m.group("deed") or "", kind="sale_share"))
                continue
            m = _SALE_HA.search(chunk)
            if m:
                rows.append(dict(khata=khata, order_no=int(order_no), case_no=case,
                                 buyer=m.group("buyer").strip(), sqm=round(float(m.group("ha")) * 10000, 3),
                                 deed_date=m.group("deed") or "", kind="sale_share"))
    df = pd.DataFrame(rows, columns=["khata", "order_no", "case_no", "buyer", "sqm", "deed_date", "kind"])
    # the khatauni lists each order twice (once per fasli-year block): dedupe on case number
    return df.drop_duplicates(subset=["khata", "case_no", "kind", "sqm"]).reset_index(drop=True)


def reconcile(df: pd.DataFrame, record_area_sqm: float, map_area_sqm: float | None = None) -> dict:
    sold = df[df.kind == "sale_share"].sqm.sum()
    court = df[df.kind == "court_purchase"].sqm.sum()
    out = {"record_area_sqm": record_area_sqm, "sold_by_deed_sqm": round(sold, 3),
           "court_purchases_sqm": round(court, 3),
           "unexplained_sqm": round(record_area_sqm - sold - court, 3)}
    if map_area_sqm is not None:
        out["map_vs_record_pct"] = round(100 * (map_area_sqm - record_area_sqm) / record_area_sqm, 2)
    return out
