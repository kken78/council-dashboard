#!/usr/bin/env python3
"""build_minutes_map.py ― 各質問から「会議録のやりとり」（会議録横断検索）へのリンク表を作る。

  config.json の minutes_search ＋ data/issue-*.json
      → data/minutes_links.json  { 号: { 議員名: { "url": …, "questions": { 質問番号: url } } } }

会議録横断検索の審議構造（proceedings.json）から、号の会議でのその議員の一般質問の範囲を探し、
やりとり表示を開く共有リンク（#thread=…）を作る。
会議録で検出した「問」の数が議会だよりの質問数と一致するときだけ、質問ごとにその問の位置を強調する
（focus）。一致しなければ一般質問の冒頭を開く（誤った問を強調しないため）。
会議録が未公開の号は作らない（ビルドは号レベルの「会議録で全文を読む」リンクのまま）。

使い方：python scripts/build_minutes_map.py   （ネット接続が必要。ローカルなら MINUTES_DATA_URL=…/public/data）
"""
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from minutes_search import ROOT, Minutes, norm, settings  # noqa: E402

OUT = ROOT / "data" / "minutes_links.json"


def thread_url(site, seg, focus=None):
    p = {"thread": seg["from"]}
    if focus:
        p["focus"] = focus
    return site + "#" + urllib.parse.urlencode(p, safe="|")


def q_turn_sids(seg):
    """一般質問の「問」（新しい質問）の発言ID（問番号順）。"""
    pre, f0 = seg["from"][:-4], int(seg["from"][-4:])
    return [f"{pre}{f0 + t[0]:04d}" for t in seg.get("turns", []) if t[1] == "q"]


def main():
    config = json.load(open(ROOT / "config.json", encoding="utf-8"))
    st = settings(config)
    if not st:
        print("config.json に minutes_search が無いため、会議録リンク表は作りません。")
        return
    mins = Minutes(st["data_url"])
    out, report = {}, []
    for path in sorted((ROOT / "data").glob("issue-*.json")):
        d = json.load(open(path, encoding="utf-8"))
        iss = d["issue"]
        mid = mins.meeting_for(d)
        segs = mins.ippan(mid) if mid else []
        if not segs:
            report.append(f"#{iss}: 会議録が未収載（{d['session']}）")
            continue
        by_member = {norm(s["member"]): s for s in segs}
        entry, miss = {}, []
        for m in d["members"]:
            seg = by_member.get(norm(m["name"]))
            if not seg:
                miss.append(m["name"])
                continue
            qs = q_turn_sids(seg)
            nums = [q["n"] for q in m["questions"]]
            per_q = {}
            if len(qs) == len(nums):  # 問の数が一致するときだけ、質問ごとに位置を合わせる
                for n, sid in zip(sorted(nums), qs):
                    per_q[str(n)] = thread_url(st["site_url"], seg, sid)
            entry[m["name"]] = {"meeting_id": mid, "url": thread_url(st["site_url"], seg), "questions": per_q}
        out[str(iss)] = entry
        aligned = sum(1 for v in entry.values() if v["questions"])
        report.append(f"#{iss}: {len(entry)}/{len(d['members'])} 人を結びつけ（質問ごとの位置合わせ {aligned} 人）"
                      + (f"／未一致 {', '.join(miss)}" if miss else ""))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"data/minutes_links.json を作成（{sum(len(v) for v in out.values())} 人分）")
    for r in report:
        print("  " + r)


if __name__ == "__main__":
    main()
