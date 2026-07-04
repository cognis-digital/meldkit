"""Catalog of keyless live feeds that materialize into Vanguard reports.

category: osint-news | situational | threat-intel | advisories
adapter:  gdelt | reliefweb | usgs | rss | ioc_lines
"""

from __future__ import annotations

_RAW = [
    # name, category, url, keyless, adapter, doc
    ("gdelt_conflict", "osint-news",
     "https://api.gdeltproject.org/api/v2/doc/doc?query=conflict&mode=artlist&format=json&maxrecords=75",
     True, "gdelt", "https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/"),
    ("gdelt_maritime", "osint-news",
     "https://api.gdeltproject.org/api/v2/doc/doc?query=maritime%20security&mode=artlist&format=json&maxrecords=75",
     True, "gdelt", "https://blog.gdeltproject.org"),
    ("gdelt_narcotics", "osint-news",
     "https://api.gdeltproject.org/api/v2/doc/doc?query=narcotics%20trafficking&mode=artlist&format=json&maxrecords=75",
     True, "gdelt", "https://blog.gdeltproject.org"),
    ("reliefweb_reports", "situational",
     "https://api.reliefweb.int/v1/reports?appname=obsidia&profile=list&limit=75&sort[]=date:desc",
     True, "reliefweb", "https://apidoc.reliefweb.int"),
    ("usgs_significant", "situational",
     "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson",
     True, "usgs", "https://earthquake.usgs.gov/fdsnws/event/1/"),
    ("usgs_45day", "situational",
     "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_month.geojson",
     True, "usgs", "https://earthquake.usgs.gov"),
    ("gdacs_alerts", "situational", "https://www.gdacs.org/xml/rss.xml",
     True, "rss", "https://www.gdacs.org"),
    ("cisa_advisories", "advisories", "https://www.cisa.gov/cybersecurity-advisories/all.xml",
     True, "rss", "https://www.cisa.gov/news-events/cybersecurity-advisories"),
    ("cisa_ics_advisories", "advisories",
     "https://www.cisa.gov/cybersecurity-advisories/ics-advisories.xml",
     True, "rss", "https://www.cisa.gov"),
    ("defense_news_rss", "osint-news",
     "https://www.defensenews.com/arc/outboundfeeds/rss/?outputType=xml",
     True, "rss", "https://www.defensenews.com"),
    ("dvidshub_news", "osint-news", "https://www.dvidshub.net/rss/news",
     True, "rss", "https://www.dvidshub.net"),
    ("feodo_iocs", "threat-intel", "https://feodotracker.abuse.ch/downloads/ipblocklist.csv",
     True, "ioc_lines", "https://feodotracker.abuse.ch"),
    ("urlhaus_iocs", "threat-intel", "https://urlhaus.abuse.ch/downloads/csv_recent/",
     True, "ioc_lines", "https://urlhaus.abuse.ch"),
    ("threatfox_iocs", "threat-intel", "https://threatfox.abuse.ch/export/csv/recent/",
     True, "ioc_lines", "https://threatfox.abuse.ch"),
]

CATALOG = [
    {"name": n, "category": c, "url": u, "keyless": k, "adapter": a, "doc": d}
    for (n, c, u, k, a, d) in _RAW
]
