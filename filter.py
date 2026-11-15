"""Keep the European quant internships from the SimplifyJobs list and write offers.json (small, for the Discord bot).
Runs every 2 hours in GitHub Actions. Source: https://github.com/SimplifyJobs/Summer2027-Internships"""
import json, re, urllib.request, datetime as dt

SRC = "https://raw.githubusercontent.com/SimplifyJobs/Summer2027-Internships/dev/.github/scripts/listings.json"
EUROPE = ["UK", "United Kingdom", "England", "Scotland", "London", "Edinburgh", "Manchester", "Ireland", "Dublin",
          "Netherlands", "Amsterdam", "Rotterdam", "Switzerland", "Zurich", "Zürich", "Geneva", "Zug", "Lausanne", "Basel",
          "France", "Paris", "Germany", "Frankfurt", "Munich", "Berlin", "Hamburg", "Italy", "Milan", "Spain", "Madrid",
          "Barcelona", "Portugal", "Lisbon", "Belgium", "Brussels", "Luxembourg", "Austria", "Vienna", "Denmark",
          "Copenhagen", "Sweden", "Stockholm", "Norway", "Oslo", "Finland", "Helsinki", "Poland", "Warsaw", "Krakow",
          "Czech", "Prague", "Hungary", "Budapest", "Romania", "Bucharest", "Greece", "Athens", "Cyprus", "Limassol",
          "Estonia", "Tallinn", "Malta"]
EU_RE = re.compile(r"\b(" + "|".join(map(re.escape, EUROPE)) + r")\b", re.I)
US_RE = re.compile(r",\s*(MA|NH|CT|NY|NJ|CA|TX|IL|PA|GA|FL)\b")   # "Cambridge, MA", "Paris, TX"...
QUANT_FIRMS = ["Jane Street", "Optiver", "IMC", "Susquehanna", "SIG", "Citadel", "Hudson River", "HRT", "Jump Trading",
               "Flow Traders", "DRW", "Two Sigma", "G-Research", "Squarepoint", "Maven", "Da Vinci", "Tower Research",
               "Five Rings", "Akuna", "Old Mission", "Virtu", "XTX", "Qube", "Man Group", "Millennium", "Point72",
               "Balyasny", "D. E. Shaw", "DE Shaw", "Graviton", "Quadrature", "Winton", "Marshall Wace", "Hull Tactical",
               "Radix", "Wintermute", "Mako", "Eagle Seven", "Vivcourt", "Optiver", "Quantica", "Capula", "Brevan Howard",
               "Schonfeld", "Engineers Gate", "PDT Partners", "WorldQuant", "Cubist", "Aspect Capital", "BMLL", "Tibra",
               "Liquid Capital", "TransMarket", "Headlands", "Belvedere", "Chicago Trading", "Peak6", "Wolverine", "Hap Capital"]
FIRM_RE = re.compile(r"\b(" + "|".join(map(re.escape, QUANT_FIRMS)) + r")\b", re.I)


NOT_QUANT = re.compile(r"\b(HR|human resources|people|talent|recruit|business|marketing|legal|compliance|communications|sales|"
                       r"accounting|audit|tax|office|facilities|events|design|operations)\b", re.I)


def kind(title):
    t = title.lower()
    if re.search(r"trad|market mak", t): return "Trading"
    if re.search(r"develop|software|engineer|\bswe\b|fpga|infrastructure", t): return "Dev"
    if re.search(r"research|quantitative|quant\b|analytic|strateg|data scien|machine learning|language processing|nlp|risk|\bml\b|\bai\b", t): return "Research"
    if re.search(r"technolog|tech\b|systems|platform|hardware", t): return "Dev"
    return "Other"


def term(x):
    terms = " ".join(x.get("terms", [])) + " " + x["title"]
    if re.search(r"off.?cycle|winter|spring|fall|autumn", terms, re.I) and "Summer" not in terms: return "Off-cycle"
    if "2028" in terms: return "Summer 2028"
    if "Summer" in terms: return "Summer 2027"
    return None


def countries(locs):
    s, found = " ".join(locs), []
    for c, pat in [("UK", r"UK|United Kingdom|England|Scotland|London|Edinburgh|Manchester"),
                   ("Netherlands", r"Netherlands|Amsterdam|Rotterdam"), ("Switzerland", r"Switzerland|Zurich|Zürich|Geneva|Zug|Lausanne|Basel"),
                   ("Ireland", r"Ireland|Dublin"), ("France", r"France|Paris"), ("Germany", r"Germany|Frankfurt|Munich|Berlin|Hamburg")]:
        if re.search(pat, s, re.I): found.append(c)
    return found if len(found) == len(locs) else found + ["Other Europe"]


L = json.load(urllib.request.urlopen(SRC, timeout=60))
out, seen = [], set()
for x in sorted(L, key=lambda x: x['date_posted']):
    if not x.get("is_visible", True):
        continue
    eu_locs = [l for l in x.get("locations", []) if EU_RE.search(l) and not US_RE.search(l)]
    if not eu_locs:
        continue
    quant = x.get("category") in ("Quant", "Quantitative Finance") or (FIRM_RE.search(x.get("company_name", "")) and
                                                                      x.get("category") in ("Software", "Software Engineering", "AI/ML/Data", "Hardware", "Data Science, AI & Machine Learning"))
    if not quant or NOT_QUANT.search(x["title"]):
        continue
    key = (x["company_name"].lower(), x["title"].lower(), tuple(sorted(eu_locs)))
    if key in seen:                      # the same job is sometimes listed twice
        continue
    seen.add(key)
    out.append(dict(id=x["id"], company=x["company_name"], title=x["title"], locations=eu_locs, countries=countries(eu_locs),
                    kind=kind(x["title"]), term=term(x), terms=[t for t in x.get("terms", []) if t and t != "N/A"], url=x["url"],
                    posted=dt.datetime.fromtimestamp(x["date_posted"], dt.timezone.utc).strftime("%Y-%m-%d"),
                    active=bool(x.get("active"))))
out.sort(key=lambda o: o["posted"])
json.dump({"updated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"), "source": "SimplifyJobs/Summer2027-Internships",
           "offers": out}, open("offers.json", "w"), indent=1, ensure_ascii=False)
print(len(out), "European quant offers,", sum(o["active"] for o in out), "active")
