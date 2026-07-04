from obsidia.agents import Orchestrator
from obsidia.sources import adapters, ingest
from obsidia.sources.catalog import CATALOG

GDELT = '{"articles":[{"url":"http://x/1","title":"Coca seizure at port near go-fast vessel","domain":"news.example","seendate":"20260101T000000Z"}]}'
RELIEFWEB = '{"data":[{"id":1,"fields":{"title":"Flood displaces thousands in region","date":{"created":"2026-01-01T00:00:00+00:00"}}}]}'
USGS = '{"features":[{"id":"us1","properties":{"title":"M 6.1 - near coast","time":1700000000000,"place":"near coast","mag":6.1}}]}'
RSS = ('<?xml version="1.0"?><rss><channel>'
       '<item><title>ICS Advisory XYZ</title><description>&lt;p&gt;vuln details&lt;/p&gt;</description>'
       '<link>http://c/1</link><pubDate>Wed, 01 Jan 2026 00:00:00 GMT</pubDate></item>'
       '</channel></rss>')
IOC = "# feodo\n203.0.113.9,443\n198.51.100.3,8080\n"


class FakeClient:
    def __init__(self, mapping):
        self.mapping = mapping

    def get(self, url):
        for k, v in self.mapping.items():
            if k in url:
                return v.encode()
        raise RuntimeError("no fixture for " + url)


def test_catalog_integrity():
    assert len(CATALOG) >= 12
    names = [s["name"] for s in CATALOG]
    assert len(names) == len(set(names))
    assert all(s["keyless"] for s in CATALOG)
    assert all(s["adapter"] in ingest.ADAPTERS for s in CATALOG)


def test_adapters():
    assert adapters.gdelt(GDELT)[0]["text"].startswith("Coca seizure")
    assert adapters.reliefweb(RELIEFWEB)[0]["text"].startswith("Flood")
    assert adapters.usgs(USGS)[0]["text"].startswith("M 6.1")
    r = adapters.rss(RSS)[0]
    assert r["text"].startswith("ICS Advisory XYZ")
    assert "<p>" not in r["text"]  # html stripped
    assert len(adapters.ioc_lines(IOC)) == 2


def test_collect_and_dedupe():
    client = FakeClient({"gdeltproject": GDELT, "reliefweb": RELIEFWEB,
                         "usgs": USGS, "cisa.gov": RSS, "feodotracker": IOC})
    reports, errors = ingest.collect(client)
    assert not errors
    assert len(reports) >= 5
    ids = [r["id"] for r in reports]
    assert len(ids) == len(set(ids))  # de-duplicated


def test_live_reports_feed_the_graph():
    client = FakeClient({"gdeltproject": GDELT, "reliefweb": RELIEFWEB,
                         "usgs": USGS, "cisa.gov": RSS, "feodotracker": IOC})
    reports, _ = ingest.collect(client)
    orch = Orchestrator(reports, {})
    result = orch.answer("coca seizure port vessel", k=3)
    assert result["citations"]  # answered from live-ingested reporting


def test_stats():
    s = ingest.stats()
    assert s["total"] >= 12
    assert s["keyless"] == s["total"]
