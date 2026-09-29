"""Clients for primary and secondary research sources.

Primary (cited in research):  NSE corporate filings / results / calendar / actions / shareholding, regulator and
central-bank feeds (RBI, SEBI, PIB, US Fed), FRED and World Bank data, and any official document by URL.
Secondary (to FIND things, never cited as fact without the primary): news RSS, GDELT, web search.

No key needed: NSE, RBI, SEBI, PIB, Fed, World Bank, GDELT, news RSS.
Keys (see .env.example): FRED_API_KEY; one of TAVILY_API_KEY / BRAVE_SEARCH_API_KEY / SERPAPI_API_KEY for web search.
Some Indian sites block cloud IP ranges and scripted access changes without notice: every client fails loudly with
the reason, never silently returns nothing.
"""

from __future__ import annotations

import io
import re
import threading
import time
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from typing import Any

import httpx

from ..env import get_key

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0 Safari/537.36")
MAX_DOWNLOAD_BYTES = 30_000_000


class SourceError(RuntimeError):
    pass


class SourceNotConfigured(SourceError):
    pass


# ------------------------------------------------------------------------------------------------ text extraction
class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "head", "nav", "footer", "form"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table", "td", "th"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in self.SKIP:
            self.skip += 1
        if tag == "title":
            self._in_title = True
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if not self.skip:
            self.parts.append(data)


def html_to_text(html: str) -> tuple[str, str]:
    p = _TextExtractor()
    try:
        p.feed(html)
    except Exception:  # noqa: BLE001 - malformed HTML: keep what was parsed
        pass
    text = re.sub(r"[ \t\r\f\v]+", " ", "".join(p.parts))
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return p.title.strip(), text


def pdf_to_text(data: bytes) -> tuple[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = [f"[page {i}]\n{page.extract_text() or ''}" for i, page in enumerate(reader.pages, start=1)]
    return "\n".join(pages), len(reader.pages)


def fetch_url_text(url: str, timeout: float = 45.0) -> dict[str, Any]:
    """Download a page or PDF and return its text. Raises SourceError with the reason on failure."""
    if not re.match(r"^https?://", url or ""):
        raise SourceError("only http(s) URLs can be fetched")
    headers = {"User-Agent": BROWSER_UA, "Accept": "text/html,application/pdf,application/xhtml+xml,*/*;q=0.8",
               "Accept-Language": "en-IN,en;q=0.9"}
    if "nseindia.com" in url:
        headers["Referer"] = "https://www.nseindia.com/"
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as c:
            r = c.get(url)
    except httpx.HTTPError as exc:
        raise SourceError(f"could not download {url}: {type(exc).__name__}: {exc}") from exc
    if r.status_code >= 400:
        raise SourceError(f"{url} returned HTTP {r.status_code}")
    data = r.content
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise SourceError(f"{url} is larger than {MAX_DOWNLOAD_BYTES // 1_000_000} MB")
    ctype = r.headers.get("content-type", "").lower()
    if "pdf" in ctype or url.lower().split("?")[0].endswith(".pdf") or data[:5] == b"%PDF-":
        text, pages = pdf_to_text(data)
        title = url.rsplit("/", 1)[-1]
        kind = "pdf"
    elif "json" in ctype:
        text, title, pages, kind = r.text, url, 0, "json"
    else:
        title, text = html_to_text(r.text)
        pages, kind = 0, "html"
    return {"url": str(r.url), "title": title or url, "text": text, "pages": pages, "kind": kind,
            "bytes": len(data)}


# ---------------------------------------------------------------------------------------------------------- NSE
class NSE:
    """NSE's public JSON endpoints (the ones the website uses). No key; needs browser-like headers."""

    BASE = "https://www.nseindia.com"

    def __init__(self, timeout: float = 30.0):
        self._client = httpx.Client(timeout=timeout, follow_redirects=True, headers={
            "User-Agent": BROWSER_UA, "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.nseindia.com/"})
        self._lock = threading.Lock()
        self._last = 0.0

    def get(self, path: str, **params: Any) -> Any:
        params = {k: v for k, v in params.items() if v not in (None, "")}
        for attempt in range(3):
            with self._lock:           # be polite: at most ~2 requests a second
                wait = 0.5 - (time.time() - self._last)
                if wait > 0:
                    time.sleep(wait)
                self._last = time.time()
            try:
                r = self._client.get(self.BASE + path, params=params)
            except httpx.HTTPError as exc:
                err = f"{type(exc).__name__}: {exc}"
            else:
                if r.status_code == 200 and "json" in r.headers.get("content-type", ""):
                    return r.json()
                err = f"HTTP {r.status_code}: {r.text[:120]}"
                if r.status_code == 404:
                    break
            time.sleep(1.5 * (attempt + 1))
        raise SourceError(f"NSE {path} failed ({err}). NSE sometimes blocks scripted or cloud traffic; retry later "
                          "or from another network.")

    @staticmethod
    def _dmy(d: str | None) -> str | None:
        return date.fromisoformat(d).strftime("%d-%m-%Y") if d else None

    def announcements(self, symbol: str | None = None, from_date: str | None = None,
                      to_date: str | None = None) -> list[dict[str, Any]]:
        if symbol and not from_date:
            from_date = (date.today() - timedelta(days=30)).isoformat()
        if from_date and not to_date:
            to_date = date.today().isoformat()
        data = self.get("/api/corporate-announcements", index="equities", symbol=(symbol or "").upper() or None,
                        from_date=self._dmy(from_date), to_date=self._dmy(to_date))
        rows = data if isinstance(data, list) else data.get("data", [])
        out = []
        for a in rows:
            out.append({"symbol": a.get("symbol"), "company": a.get("sm_name"), "subject": a.get("desc"),
                        "text": a.get("attchmntText"), "published_at": _nse_dt(a.get("sort_date") or a.get("an_dt")),
                        "attachment": a.get("attchmntFile"), "industry": a.get("smIndustry"),
                        "seq_id": a.get("seq_id")})
        return out

    def financial_results(self, symbol: str | None = None, period: str = "Quarterly") -> list[dict[str, Any]]:
        """Result filings, newest first. Since 2025 listed companies file results as SEBI 'Integrated Filing -
        Financials'; older quarters come from the classic results endpoint. `xbrl` holds the machine-readable
        numbers (read them with xbrl_financials)."""
        out: list[dict[str, Any]] = []
        if symbol:
            try:
                data = self.get("/api/integrated-filing-results", index="equities", symbol=symbol.upper())
                for r in (data or {}).get("data", []):
                    if "financial" not in str(r.get("type", "")).lower():
                        continue
                    out.append({"symbol": r.get("symbol"), "company": r.get("cmName") or r.get("smName"),
                                "period_end": _nse_date(r.get("qe_Date")), "audited": r.get("audited"),
                                "consolidated": r.get("consolidated"), "published_at": _nse_dt(r.get("broadcast_Date")),
                                "filing": r.get("type"), "xbrl": r.get("xbrl"), "ixbrl": r.get("ixbrl")})
            except SourceError:
                pass
        data = self.get("/api/corporates-financial-results", index="equities", period=period,
                        symbol=(symbol or "").upper() or None)
        rows = data if isinstance(data, list) else data.get("data", [])
        out += [{"symbol": r.get("symbol"), "company": r.get("companyName"), "period_end": _nse_date(r.get("toDate")),
                 "audited": r.get("audited"), "consolidated": r.get("consolidated"),
                 "published_at": _nse_dt(r.get("broadCastDate")), "filing": f"Financial results ({r.get('relatingTo')})",
                 "xbrl": r.get("xbrl"), "ixbrl": None} for r in rows]
        out.sort(key=lambda r: r.get("published_at") or "", reverse=True)
        return out

    def event_calendar(self, symbol: str | None = None) -> list[dict[str, Any]]:
        data = self.get("/api/event-calendar", index="equities", symbol=(symbol or "").upper() or None)
        rows = data if isinstance(data, list) else data.get("data", [])
        return [{"symbol": r.get("symbol"), "company": r.get("company"), "purpose": r.get("purpose"),
                 "date": _nse_date(r.get("date")), "details": r.get("bm_desc")} for r in rows]

    def corporate_actions(self, symbol: str | None = None) -> list[dict[str, Any]]:
        data = self.get("/api/corporates-corporateActions", index="equities", symbol=(symbol or "").upper() or None)
        rows = data if isinstance(data, list) else data.get("data", [])
        return [{"symbol": r.get("symbol"), "company": r.get("comp"), "subject": r.get("subject"),
                 "ex_date": _nse_date(r.get("exDate")), "record_date": _nse_date(r.get("recDate")),
                 "face_value": r.get("faceVal")} for r in rows]

    def shareholding(self, symbol: str) -> list[dict[str, Any]]:
        data = self.get("/api/corporate-share-holdings-master", index="equities", symbol=symbol.upper())
        rows = data if isinstance(data, list) else data.get("data", [])
        return [{"symbol": r.get("symbol"), "as_of": _nse_date(r.get("date")), "promoter_pct": r.get("pr_and_prgrp"),
                 "public_pct": r.get("public_val"), "employee_trusts_pct": r.get("employeeTrusts"),
                 "published_at": _nse_dt(r.get("broadcastDate")), "xbrl": r.get("xbrl")} for r in rows]


KEY_XBRL_ITEMS = [
    "RevenueFromOperations", "OtherIncome", "Income", "Expenses", "EmployeeBenefitExpense", "FinanceCosts",
    "DepreciationDepletionAndAmortisationExpense", "OtherExpenses", "ProfitBeforeExceptionalItemsAndTax",
    "ExceptionalItemsBeforeTax", "ProfitBeforeTax", "TaxExpense", "ProfitLossForPeriod",
    "ProfitOrLossAttributableToOwnersOfParent", "BasicEarningsLossPerShareFromContinuingAndDiscontinuedOperations",
    "DilutedEarningsLossPerShareFromContinuingAndDiscontinuedOperations", "PaidUpValueOfEquityShareCapital",
    "InterestEarned", "InterestExpended", "OperatingProfitBeforeProvisionAndContingencies", "ProvisionsOtherThanTaxAndContingencies",
    "GrossNonPerformingAssets", "NetNonPerformingAssets", "PercentageOfGrossNpa", "PercentageOfNpa",
]
_XBRL_FACT = re.compile(r"<([\w-]+):(\w+)\s+([^>]*?)>([^<]*)</\1:\2>", re.S)
_XBRL_CTX = re.compile(r"<xbrli:context\s+id=\"([^\"]+)\">(.*?)</xbrli:context>", re.S)


def xbrl_financials(url: str) -> dict[str, Any]:
    """Key line items from an NSE/BSE results XBRL file, per reporting period. INR amounts are also shown in
    crore (value / 10^7, the unit Indian results tables use)."""
    if not url or not url.lower().split("?")[0].endswith(".xml"):
        raise SourceError("pass the `xbrl` .xml link from nse_results")
    with httpx.Client(timeout=45, follow_redirects=True, headers={"User-Agent": BROWSER_UA,
                                                                    "Referer": "https://www.nseindia.com/"}) as c:
        r = c.get(url)
    if r.status_code >= 400:
        raise SourceError(f"XBRL download failed: HTTP {r.status_code}")
    xml = r.text
    contexts: dict[str, dict[str, Any]] = {}
    for cid, body in _XBRL_CTX.findall(xml):
        if "<xbrli:segment" in body or "<xbrli:scenario" in body:
            continue                                   # dimensional contexts (segments etc.) are left out
        start = re.search(r"<xbrli:startDate>([^<]+)<", body)
        end = re.search(r"<xbrli:endDate>([^<]+)<", body)
        instant = re.search(r"<xbrli:instant>([^<]+)<", body)
        contexts[cid] = {"start": start.group(1) if start else None,
                         "end": end.group(1) if end else (instant.group(1) if instant else None)}
    meta: dict[str, str] = {}
    periods: dict[str, dict[str, Any]] = {}
    for _prefix, name, attrs, value in _XBRL_FACT.findall(xml):
        cref = re.search(r'contextRef="([^"]+)"', attrs)
        if not cref or cref.group(1) not in contexts:
            continue
        value = value.strip()
        if name in ("NameOfTheCompany", "Symbol", "NatureOfReportStandaloneConsolidated", "LevelOfRoundingUsedInFinancialStatements",
                    "ReportingQuarter", "WhetherResultsAreAuditedOrUnaudited", "DateOfBoardMeetingWhenFinancialResultsWereApproved"):
            meta.setdefault(name, value)
        if name not in KEY_XBRL_ITEMS:
            continue
        try:
            num = float(value)
        except ValueError:
            continue
        ctx = contexts[cref.group(1)]
        label = f"{ctx['start'] or ''}..{ctx['end'] or ''}"
        unit = re.search(r'unitRef="([^"]+)"', attrs)
        entry = periods.setdefault(label, {"period_start": ctx["start"], "period_end": ctx["end"], "items": {}})
        if unit and unit.group(1).upper() == "INR":
            entry["items"][name] = {"inr": num, "crore": round(num / 1e7, 2)}
        else:
            entry["items"][name] = {"value": num, "unit": unit.group(1) if unit else None}
    ordered = sorted(periods.values(), key=lambda p: ((p["period_end"] or ""), -len(p["items"])), reverse=True)
    return {"url": url, "meta": meta, "periods": ordered}


_MONTHS = {m: i for i, m in enumerate(["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"], 1)}


def _nse_date(s: Any) -> str | None:
    if not s or s == "-":
        return None
    s = str(s).strip()
    for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y"):
        try:
            return datetime.strptime(s.title() if "b" in fmt else s, fmt).date().isoformat()
        except ValueError:
            continue
    return s


def _nse_dt(s: Any) -> str | None:
    if not s:
        return None
    s = str(s).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%b-%Y"):
        try:
            return datetime.strptime(s.title() if "%b" in fmt else s, fmt).isoformat()
        except ValueError:
            continue
    return s


# ---------------------------------------------------------------------------------------------- macro data APIs
def fred_series(series_id: str, start: str | None = None, end: str | None = None, limit: int = 400) -> dict[str, Any]:
    key = get_key("FRED_API_KEY")
    if not key:
        raise SourceNotConfigured("FRED_API_KEY is not set (free key: https://fred.stlouisfed.org/docs/api/api_key.html)")
    base = "https://api.stlouisfed.org/fred"
    with httpx.Client(timeout=30) as c:
        info = c.get(f"{base}/series", params={"series_id": series_id, "api_key": key, "file_type": "json"})
        obs = c.get(f"{base}/series/observations", params={
            "series_id": series_id, "api_key": key, "file_type": "json", "sort_order": "desc", "limit": limit,
            **({"observation_start": start} if start else {}), **({"observation_end": end} if end else {})})
    if obs.status_code >= 400:
        raise SourceError(f"FRED {series_id}: HTTP {obs.status_code} {obs.text[:200]}")
    meta = (info.json().get("seriess") or [{}])[0] if info.status_code == 200 else {}
    points = [{"date": o["date"], "value": None if o["value"] == "." else float(o["value"])}
              for o in obs.json().get("observations", [])]
    points.reverse()
    return {"series_id": series_id, "title": meta.get("title"), "units": meta.get("units"),
            "frequency": meta.get("frequency"), "last_updated": meta.get("last_updated"), "observations": points}


def worldbank_indicator(country: str, indicator: str, start_year: int | None = None,
                        end_year: int | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {"format": "json", "per_page": 100}
    if start_year or end_year:
        params["date"] = f"{start_year or 1960}:{end_year or date.today().year}"
    with httpx.Client(timeout=30) as c:
        r = c.get(f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}", params=params)
    if r.status_code >= 400:
        raise SourceError(f"World Bank {indicator}: HTTP {r.status_code}")
    data = r.json()
    if not isinstance(data, list) or len(data) < 2 or not data[1]:
        raise SourceError(f"World Bank {country}/{indicator}: no data ({str(data)[:200]})")
    rows = [{"year": int(x["date"]), "value": x["value"]} for x in data[1] if x.get("value") is not None]
    rows.sort(key=lambda x: x["year"])
    name = data[1][0].get("indicator", {}).get("value")
    return {"country": country, "indicator": indicator, "name": name, "values": rows}


_gdelt_lock = threading.Lock()
_gdelt_last = [0.0]


def gdelt_articles(query: str, days: int = 7, limit: int = 25) -> list[dict[str, Any]]:
    with _gdelt_lock:          # GDELT allows one request every 5 seconds
        wait = 5.5 - (time.time() - _gdelt_last[0])
        if wait > 0:
            time.sleep(wait)
        _gdelt_last[0] = time.time()
        with httpx.Client(timeout=30, headers={"User-Agent": "FinmediaResearch/0.2"}) as c:
            r = c.get("https://api.gdeltproject.org/api/v2/doc/doc", params={
                "query": query, "mode": "artlist", "format": "json", "maxrecords": min(limit, 75),
                "timespan": f"{max(1, days)}d", "sort": "datedesc"})
    if r.status_code >= 400 or not r.text.strip().startswith("{"):
        raise SourceError(f"GDELT: HTTP {r.status_code} {r.text[:150]}")
    arts = r.json().get("articles", [])
    return [{"title": a.get("title"), "url": a.get("url"), "domain": a.get("domain"),
             "published_at": _gdelt_dt(a.get("seendate")), "language": a.get("language")} for a in arts]


def _gdelt_dt(s: str | None) -> str | None:
    try:
        return datetime.strptime(s, "%Y%m%dT%H%M%SZ").isoformat() if s else None
    except ValueError:
        return s


# ---------------------------------------------------------------------------------------------------- web search
def web_search_provider() -> str | None:
    for name, key in (("tavily", "TAVILY_API_KEY"), ("brave", "BRAVE_SEARCH_API_KEY"), ("serpapi", "SERPAPI_API_KEY")):
        if get_key(key):
            return name
    return None


def web_search(query: str, limit: int = 8) -> dict[str, Any]:
    provider = web_search_provider()
    if provider is None:
        raise SourceNotConfigured("web search needs one of TAVILY_API_KEY, BRAVE_SEARCH_API_KEY or SERPAPI_API_KEY in .env")
    with httpx.Client(timeout=30) as c:
        if provider == "tavily":
            r = c.post("https://api.tavily.com/search", json={"api_key": get_key("TAVILY_API_KEY"), "query": query,
                                                               "max_results": limit, "search_depth": "basic"})
            r.raise_for_status()
            items = [{"title": x.get("title"), "url": x.get("url"), "snippet": x.get("content"),
                      "published_at": x.get("published_date")} for x in r.json().get("results", [])]
        elif provider == "brave":
            r = c.get("https://api.search.brave.com/res/v1/web/search", params={"q": query, "count": limit},
                      headers={"X-Subscription-Token": get_key("BRAVE_SEARCH_API_KEY"), "Accept": "application/json"})
            r.raise_for_status()
            items = [{"title": x.get("title"), "url": x.get("url"), "snippet": x.get("description"),
                      "published_at": x.get("page_age")} for x in (r.json().get("web") or {}).get("results", [])]
        else:
            r = c.get("https://serpapi.com/search.json", params={"q": query, "api_key": get_key("SERPAPI_API_KEY"),
                                                                 "engine": "google", "num": limit, "gl": "in"})
            r.raise_for_status()
            items = [{"title": x.get("title"), "url": x.get("link"), "snippet": x.get("snippet"),
                      "published_at": x.get("date")} for x in r.json().get("organic_results", [])]
    return {"provider": provider, "results": items[:limit]}
