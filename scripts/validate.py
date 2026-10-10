#!/usr/bin/env python3
"""データ検査: config と全 issue を読み、誤りを洗い出す。新号追加のたびに実行する。"""
import json, glob, os, re, sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
theme_ids = {t["id"] for t in cfg["themes"]}
member_names = {m["name"] for m in cfg["members"]}

errors, warns = [], []
seen_keys = set()
ONLINE = "--online" in sys.argv  # 会議録リンク先のページタイトルも確認する（要ネット）
minutes_ids = []  # (号, 会議録ページID)


def check_minutes_link(iss, url):
    """links.minutes は会議録のページ（タイトルが「〇〇・会議録」）を指す。
    「本会議のご案内」ページを入れてしまうと、会議録との照合（統合MCP等）が失敗する。
    会議録が未公開の号は案内ページを仮に入れてよいが、公開後に差し替える。"""
    if not url:
        warns.append(f"#{iss} links.minutes が空")
        return
    m = re.match(r"^https?://[^/]+/(\d{10})\.html$", url)
    if not m:
        warns.append(f"#{iss} links.minutes が会議録ページの形式（…/0000000000.html）ではない: {url}")
        return
    minutes_ids.append((iss, int(m.group(1))))
    if ONLINE:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (council-dashboard validate.py)"})
            html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "replace")
            t = re.search(r"<title>([^<]*)", html)
            title = t.group(1) if t else ""
            if "会議録" not in title:
                warns.append(f"#{iss} links.minutes が会議録ページではない（タイトル「{title.strip()}」）。会議録の公開後に差し替える: {url}")
        except Exception as e:
            warns.append(f"#{iss} links.minutes を確認できない（{e}）: {url}")

for path in sorted(glob.glob(os.path.join(ROOT, "data", "issue-*.json"))):
    d = json.load(open(path, encoding="utf-8"))
    iss = d["issue"]
    check_minutes_link(iss, (d.get("links") or {}).get("minutes"))
    for m in d["members"]:
        if m["name"] not in member_names:
            warns.append(f"#{iss} 議員名がconfigに無い: {m['name']}")
        for q in m["questions"]:
            key = f"{iss}|{m['name']}|{q['n']}"
            if key in seen_keys:
                errors.append(f"重複キー: {key}")
            seen_keys.add(key)
            if q["theme"] not in theme_ids:
                errors.append(f"{key}: 未知のテーマ '{q['theme']}'")
            subs = q.get("sub_themes") or []
            if not isinstance(subs, list):
                errors.append(f"{key}: sub_themes は配列で書く")
                subs = []
            for st in subs:
                if st not in theme_ids:
                    errors.append(f"{key}: 未知の副テーマ '{st}'")
                elif st == q["theme"]:
                    errors.append(f"{key}: 副テーマが主テーマと同一 '{st}'")
            if len(set(subs)) != len(subs):
                errors.append(f"{key}: 副テーマが重複している")
            if q.get("published"):
                if not q.get("q") or not q.get("a"):
                    errors.append(f"{key}: 掲載なのに問・答が空")
                if not q.get("answer_title"):
                    warns.append(f"{key}: 答弁見出し(answer_title)が空")
            else:
                if q.get("q") or q.get("a"):
                    warns.append(f"{key}: 未掲載なのに本文がある")

# 会議録ページのIDは号を追うごとに大きくなる。小さくなる号は案内ページ等を入れている可能性が高い
mx = (None, 0)
for iss, mid in sorted(minutes_ids):
    if mid <= mx[1]:
        warns.append(f"#{iss} links.minutes のページIDが第{mx[0]}号より小さい（会議録ではなく案内ページの可能性。未公開なら公開後に差し替え）")
    else:
        mx = (iss, mid)

print(f"検査: issue {len([1 for _ in glob.glob(os.path.join(ROOT,'data','issue-*.json'))])}件 / 質問 {len(seen_keys)}件")
for w in warns: print("  [warn]", w)
for e in errors: print("  [ERROR]", e)
if errors:
    print(f"\nNG: {len(errors)} 件のエラー"); sys.exit(1)
print(f"\nOK（warn {len(warns)} 件）")
