# services/live_search_service.py
import time
import requests
import xml.etree.ElementTree as ET

ARXIV_API_URL = "http://export.arxiv.org/api/query"
PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# 🔒 ONE shared session (CRITICAL)
_session = requests.Session()


def safe_request(url, params, retries=1, backoff=1):
    for _ in range(retries):
        try:
            r = _session.get(url, params=params, timeout=10)
            if r.status_code == 200 and r.text:
                return r
        except Exception:
            pass
        time.sleep(backoff)
    return None


def parse_arxiv(xml_text):
    papers = []
    ns = {"atom": "http://www.w3.org/2005/Atom"}

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return papers

    for entry in root.findall("atom:entry", ns):
        papers.append({
            "title": entry.findtext("atom:title", default="", namespaces=ns).strip(),
            "abstract": entry.findtext("atom:summary", default="", namespaces=ns).strip(),
            "authors": [
                a.findtext("atom:name", default="", namespaces=ns)
                for a in entry.findall("atom:author", ns)
            ],
            "source": "arXiv",
            "url": entry.findtext("atom:id", default="", namespaces=ns)
        })
    return papers


def search_arxiv(query, max_results=5):
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending"
    }

    r = safe_request(ARXIV_API_URL, params)
    return parse_arxiv(r.text) if r else []


def search_pubmed(query, max_results=5):
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "xml"
    }

    search_resp = safe_request(PUBMED_SEARCH_URL, search_params)
    if not search_resp:
        return []

    try:
        root = ET.fromstring(search_resp.text)
        ids = [e.text for e in root.findall(".//Id")]
    except ET.ParseError:
        return []

    if not ids:
        return []

    fetch_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "xml"
    }

    fetch_resp = safe_request(PUBMED_FETCH_URL, fetch_params)
    return parse_pubmed(fetch_resp.text) if fetch_resp else []


def parse_pubmed(xml_text):
    papers = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return papers

    for article in root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle", default="")
        abstract = " ".join(
            [a.text for a in article.findall(".//AbstractText") if a.text]
        )

        authors = []
        for author in article.findall(".//Author"):
            last = author.findtext("LastName")
            first = author.findtext("ForeName")
            if last and first:
                authors.append(f"{first} {last}")

        papers.append({
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "source": "PubMed",
            "url": "https://pubmed.ncbi.nlm.nih.gov/"
        })

    return papers


def unified_search(query, max_results=5):
    return search_arxiv(query, max_results) + search_pubmed(query, max_results)

