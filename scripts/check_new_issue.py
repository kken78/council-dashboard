#!/usr/bin/env python3
"""check_new_issue.py ― 議会だよりの一覧ページに、まだデータに無い号が公開されていないか調べる。

  config.json の town.bulletin_index_url（議会だよりの一覧ページ）を取得し、
  PDF へのリンクのファイル名から号数を読み取る（既定の形式は「hino36web.pdf」＝号数を含む名前）。
  形式は config.json の town.bulletin_pdf_pattern（号数を () で囲んだ正規表現）で変えられる。

出力（標準出力・JSON）：{"latest_in_data": 36, "new": [{"issue": 37, "pdf": "https://…"}]}
新しい号があっても終了コードは 0（週1回のワークフローが Issue を作る）。
"""
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATTERN = r"hino(\d+)web\.pdf$"


def main():
    config = json.load(open(ROOT / "config.json", encoding="utf-8"))
    town = config["town"]
    index_url = town.get("bulletin_index_url")
    if not index_url:
        print(json.dumps({"error": "town.bulletin_index_url が未設定"}, ensure_ascii=False))
        return
    pattern = re.compile(town.get("bulletin_pdf_pattern") or DEFAULT_PATTERN)
    have = {json.load(open(p, encoding="utf-8"))["issue"] for p in (ROOT / "data").glob("issue-*.json")}
    latest = max(have) if have else 0
    req = urllib.request.Request(index_url, headers={"User-Agent": "Mozilla/5.0 (council-dashboard check_new_issue.py)"})
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    found = {}
    for href in re.findall(r'href="([^"]+\.pdf)"', html):
        m = pattern.search(href.split("/")[-1])
        if m:
            found[int(m.group(1))] = urllib.parse.urljoin(index_url, href)
    new = [{"issue": n, "pdf": found[n]} for n in sorted(found) if n > latest]
    print(json.dumps({"latest_in_data": latest, "latest_on_site": max(found) if found else None, "new": new}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
