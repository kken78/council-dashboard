"""minutes_search.py ― 会議録横断検索（hino-council-search）の公開データを読む共通処理。

config.json の "minutes_search" で取得元を指定する（無ければ連携しない＝他自治体のフォークでも安全）。
  "minutes_search": {
    "site_url": "https://kken78.github.io/hino-council-search/",   … やりとり表示へのリンク先
    "data_url": "https://raw.githubusercontent.com/kken78/hino-council-search/main/public/data"
  }
data_url はローカルのディレクトリでもよい（例：../hino-council-search/public/data）。
環境変数 MINUTES_DATA_URL で一時的に差し替えられる。
"""
import json
import os
import re
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 異体字の吸収（build_video_map.py と同じ）
KANJI_FOLD = str.maketrans({
    "髙": "高", "﨑": "崎", "桒": "桑", "槗": "橋",
    "邊": "辺", "邉": "辺", "澤": "沢", "齋": "斎", "齊": "斉",
    "德": "徳", "廣": "広", "眞": "真",
})


def norm(s):
    """突合用の正規化：NFKC → 異体字畳み込み → 空白除去。"""
    s = unicodedata.normalize("NFKC", s or "")
    s = s.translate(KANJI_FOLD)
    return re.sub(r"\s+", "", s)


def page_id(url):
    m = re.search(r"(\d{10})\.html", url or "")
    return m.group(1) if m else None


def settings(config):
    ms = config.get("minutes_search") or {}
    data_url = os.environ.get("MINUTES_DATA_URL") or ms.get("data_url")
    if not data_url:
        return None
    return {"site_url": ms.get("site_url", ""), "data_url": data_url.rstrip("/")}


def _get(base, name, optional=False):
    try:
        if re.match(r"^https?://", base):
            req = urllib.request.Request(f"{base}/{name}", headers={
                "User-Agent": "council-dashboard (+https://github.com/kken78/council-dashboard)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        return json.load(open(os.path.join(base, name), encoding="utf-8"))
    except Exception:
        if optional:
            return None
        raise


class Minutes:
    """会議録検索のデータ（会議一覧・審議構造・会議ページ対応表）。"""

    def __init__(self, base):
        self.meetings = _get(base, "meetings.json")
        self.proceedings = _get(base, "proceedings.json", optional=True) or {}
        pages = _get(base, "meeting_pages.json", optional=True) or {}
        self.ids = {m["id"] for m in self.meetings}
        self.by_page = {page_id(u): mid for mid, u in pages.items() if page_id(u)}
        self.by_name = {norm(m["name"]).replace("会議録", ""): m["id"] for m in self.meetings}

    def meeting_for(self, issue):
        """号に対応する会議録の会議ID。会議録ページID → 案内ページの逆引き → 会議名の順に探す。"""
        pid = page_id(issue.get("links", {}).get("minutes"))
        if pid in self.ids:
            return pid
        if pid in self.by_page:
            return self.by_page[pid]
        return self.by_name.get(norm(issue.get("session", "")))

    def ippan(self, meeting_id):
        """会議の一般質問（発言順）。[{member, seat, from, turns, date}]"""
        segs = (self.proceedings.get(meeting_id) or {}).get("segments", [])
        return [s for s in segs if s.get("kind") == "ippan"]
