#!/usr/bin/env python3
"""update_minutes_links.py ― 案内ページのままの links.minutes を、会議録ページに差し替える。

会議録が未公開の号には「本会議のご案内」ページを仮に入れておく運用のため、
会議録横断検索（config.json の minutes_search）にその会議の会議録が入ったら、
data/issue-NN.json の links.minutes を会議録ページ（…/<会議ID>.html）に書き換える。
差し替えた号を標準出力に1行ずつ出す（無ければ何も出さない）。

使い方：python scripts/update_minutes_links.py   （ローカルなら MINUTES_DATA_URL=…/public/data）
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from minutes_search import ROOT, Minutes, page_id, settings  # noqa: E402


def main():
    config = json.load(open(ROOT / "config.json", encoding="utf-8"))
    st = settings(config)
    if not st:
        return
    mins = Minutes(st["data_url"])
    by_id = {m["id"]: m for m in mins.meetings}
    for path in sorted((ROOT / "data").glob("issue-*.json")):
        text = path.read_text(encoding="utf-8")
        d = json.loads(text)
        url = d.get("links", {}).get("minutes", "")
        pid = page_id(url)
        if pid in mins.ids:
            continue  # すでに会議録ページ
        mid = mins.meeting_for(d)
        if not mid or mid not in by_id:
            continue  # 会議録が未公開（会議録横断検索に未収載）
        new_url = by_id[mid]["url"]
        # 既存ファイルの書式を保つため、該当の値だけを置き換える
        path.write_text(text.replace(json.dumps(url, ensure_ascii=False), json.dumps(new_url, ensure_ascii=False), 1), encoding="utf-8")
        print(f"#{d['issue']} {d['session']}: {url or '（空）'} → {new_url}")


if __name__ == "__main__":
    main()
