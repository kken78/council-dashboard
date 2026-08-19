#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_video_map.py — 録画配信URLの突合表 data/videos.json を生成する

日野町議会インターネット中継（jfit）を巡回し、
「議会だより号 × 議員 → 録画URL」の対応表を作る。

    実行:  python3 scripts/build_video_map.py
    出力:  data/videos.json

考え方:
    ISSUE_TO_GIKAI …… 号 → 定例会(gikai_id) の対応（要検算・編集）
    各定例会の「一般質問」を含む会議日を自動判別し、議員ごとの inquiry_id を収集。
    議員名は config.json の members と突合（NFKC・異体字・空白を吸収）。
    突合できなかった行は最後にレポート（stderr）へ出す＝取りこぼしが目視できる。
"""

import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://hino-town.stream.jfit.co.jp/"
ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config.json"
OUT = ROOT / "data" / "videos.json"
SLEEP = 1.0  # サイトへの配慮（各リクエスト間の待機秒）

# 号 → 定例会(gikai_id)。
# ※必ず検算すること。号番号と定例会の対応は自動計算できない（臨時会が混ざる）。
#   実行後のレポートで、各号の一致人数・未一致行を必ず確認する。
ISSUE_TO_GIKAI = {
    24: 111,  # 令和5年6月定例会
    25: 112,  # 令和5年9月定例会
    26: 114,  # 令和5年12月定例会
    27: 116,  # 令和6年3月定例会
    28: 118,  # 令和6年6月定例会
    29: 120,  # 令和6年9月定例会
    30: 121,  # 令和6年12月定例会
    31: 123,  # 令和7年3月定例会
    32: 125,  # 令和7年6月定例会
    33: 127,  # 令和7年9月定例会
    34: 128,  # 令和7年12月定例会
    35: 130,  # 令和8年3月定例会
    36: 132,  # 令和8年6月定例会（131は令和8年5月臨時会議）
}

# 異体字の吸収（両辺に同じ正規化をかけて突合を安定させる）
KANJI_FOLD = str.maketrans({
    "髙": "高", "﨑": "崎", "桒": "桑", "槗": "橋",
    "邊": "辺", "邉": "辺", "澤": "沢", "齋": "斎", "齊": "斉",
    "德": "徳", "廣": "広", "眞": "真",
})


def norm(s: str) -> str:
    """突合用の正規化：NFKC → 異体字畳み込み → 空白除去。"""
    s = unicodedata.normalize("NFKC", s or "")
    s = s.translate(KANJI_FOLD)
    return re.sub(r"\s+", "", s)


def fetch(url: str, tries: int = 3) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "council-dashboard video-map builder "
                      "(+https://github.com/kken78/council-dashboard)"
    })
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2 * (k + 1))
    raise RuntimeError(f"fetch failed: {url} ({last})")


def _unescape(s: str) -> str:
    return s.replace("&amp;", "&")


def parse_days(html: str):
    """days_list から [(gikai_day_id, category_id, inquiry_id, label), ...] を返す。"""
    days = []
    for m in re.finditer(r'href="([^"]*tpl=gikai_result[^"]*)"[^>]*>([^<]*)<', html):
        href = _unescape(m.group(1))
        label = m.group(2).strip()
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(href).query)
        gd = q.get("gikai_day_id", [""])[0]
        cat = q.get("category_id", [""])[0]
        inq = q.get("inquiry_id", [""])[0]
        if gd:
            days.append((gd, cat, inq, label))
    return days


def parse_result_rows(html: str):
    """result ページの各行から (inquiry_id, photo, text) を返す（日程/議案行は除外）。"""
    rows = re.findall(r"<tr\b.*?</tr>", html, re.S | re.I)
    out = []
    for row in rows:
        mi = re.search(r"tpl=play_vod&(?:amp;)?inquiry_id=(\d+)", row)
        if not mi:
            continue
        photo = ""
        mp = re.search(r"image/speaker/([^\"']+\.(?:jpe?g|png|gif))", row, re.I)
        if mp:
            photo = mp.group(1)
        if photo.lower().endswith("space.gif"):
            continue  # 日程（議案審議）行
        text = re.sub(r"<[^>]+>", " ", row)
        text = unicodedata.normalize("NFKC", text)
        out.append((mi.group(1), photo, text))
    return out


def main() -> int:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    members = [m["name"] for m in cfg.get("members", [])]
    mindex = [(name, norm(name)) for name in members if norm(name)]

    videos = {}
    report = []
    for issue, gikai in sorted(ISSUE_TO_GIKAI.items()):
        days_html = fetch(f"{BASE}?tpl=gikai_days_list&gikai_id={gikai}")
        time.sleep(SLEEP)
        days = [d for d in parse_days(days_html) if "一般質問" in d[3]]

        found, dups, unmatched = {}, [], []
        for gd, cat, inq, _label in days:
            url = f"{BASE}?tpl=gikai_result&gikai_day_id={gd}&category_id={cat}&inquiry_id={inq}"
            res = fetch(url)
            time.sleep(SLEEP)
            for inquiry_id, photo, text in parse_result_rows(res):
                ntext = norm(text)
                hit = next((name for name, nname in mindex if nname in ntext), None)
                if not hit:
                    unmatched.append((photo, text.strip()[:48]))
                    continue
                if hit in found:
                    dups.append(hit)
                found[hit] = {
                    "inquiry_id": int(inquiry_id),
                    "gikai_day_id": int(gd),
                    "category_id": int(cat),
                    "result_url": (f"{BASE}?tpl=gikai_result&gikai_day_id={gd}"
                                   f"&category_id={cat}&inquiry_id={inquiry_id}"),
                    "play_url": f"{BASE}?tpl=play_vod&inquiry_id={inquiry_id}",
                }
        videos[str(issue)] = found
        report.append((issue, gikai, sorted(found), dups, unmatched))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(videos, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("=== 突合レポート ===", file=sys.stderr)
    for issue, gikai, names, dups, unmatched in report:
        print(f"#{issue} (gikai_id={gikai}): 一致 {len(names)} 名 → "
              f"{'、'.join(names)}", file=sys.stderr)
        for d in dups:
            print(f"    ⚠ 重複: {d}（同一定例会で2ブロック）", file=sys.stderr)
        for photo, snippet in unmatched:
            print(f"    未一致: {photo or '(写真なし)'} | {snippet}", file=sys.stderr)
    print(f"\n→ {OUT} を書き出しました。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
