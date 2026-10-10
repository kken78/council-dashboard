#!/usr/bin/env python3
"""draft_issue.py ― 新しい号の下書き（data/drafts/issue-NN.draft.json）を会議録から作る。

会議録横断検索（config.json の minutes_search）の審議構造から、その定例会議の一般質問の
質問者（発言順）・議員名の表記（config.json の members に合わせる）・よみ・会議録ページを埋め、
質問は会議録の答弁から推定した質問項目を仮の題名として入れる。
議会だより本文からの転記（題名・テーマ・掲載/未掲載・問・答・ページ）は人が行う。
下書きは data/drafts/ に置くため、ビルドと検査の対象にはならない。仕上がったら data/issue-NN.json に移す。

使い方：
  python scripts/draft_issue.py 37 "令和8年9月定例会議"
  （会議名は会議録の名称。省略すると会議録横断検索に入っている最新の定例会議）
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from minutes_search import ROOT, Minutes, norm, settings  # noqa: E402


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    issue = int(sys.argv[1])
    config = json.load(open(ROOT / "config.json", encoding="utf-8"))
    st = settings(config)
    if not st:
        print("config.json に minutes_search がありません。")
        return 1
    mins = Minutes(st["data_url"])
    if len(sys.argv) >= 3:
        mid = mins.by_name.get(norm(sys.argv[2]))
    else:
        teirei = [m for m in mins.meetings if m.get("type") == "定例会" and mins.ippan(m["id"])]
        mid = teirei[0]["id"] if teirei else None  # meetings.json は新しい順
    if not mid:
        print("会議が見つかりません（会議録横断検索に未収載か、会議名の表記違い）。")
        return 1
    meeting = next(m for m in mins.meetings if m["id"] == mid)
    members = {norm(m["name"]): m for m in config["members"]}
    prev = sorted((ROOT / "data").glob("issue-*.json"))
    last = json.load(open(prev[-1], encoding="utf-8")) if prev else {"links": {}}
    # 議会だよりPDFのURLは前号のファイル名の号数を差し替えて推定（例：hino36web.pdf → hino37web.pdf）
    pdf = re.sub(r"(\D)(\d+)(\D*\.pdf)$", lambda x: f"{x.group(1)}{issue:02d}{x.group(3)}", last["links"].get("bulletin_pdf", ""))
    name = meeting["name"].replace("会議録", "")
    ym = re.search(r"(令和|平成)(\d+|元)年.*?(\d+)月", name)
    draft = {
        "schema_version": "1.0",
        "issue": issue,
        "session": name,
        "year": meeting.get("year"),
        "month": int(ym.group(3)) if ym else None,
        "published_date": "（発行日 YYYY-MM-DD）",
        "index_page": 8,
        "links": {
            "bulletin_pdf": pdf or "（議会だよりPDFのURL）",
            "minutes": meeting["url"],
            "video": last["links"].get("video", "（録画配信）"),
        },
        "members": [],
        "_draft_note": "会議録から自動作成した下書き。題名・テーマ・published・問・答・page を議会だよりから転記し、この項目を消して data/issue-NN.json に移す。",
    }
    unknown = []
    for order, seg in enumerate(mins.ippan(mid), 1):
        cm = members.get(norm(seg["member"]))
        if not cm:
            unknown.append(seg["member"])
        topics = [t for t in seg.get("topics", []) if t.get("src") != "bulletin"]
        # 質問数は会議録から推定した質問項目の数（最低1）。会議録からの「問」の検出は多めに出るので使わない
        qs = []
        for n in range(1, max(len(topics), 1) + 1):
            t = topics[n - 1]["title"] if n <= len(topics) else None
            qs.append({"n": n, "published": True, "theme": "（テーマ）",
                       "title": f"（仮：会議録から推定）{t}" if t else "（題名）",
                       "answer_title": "", "q": "", "a": [{"label": "答弁", "text": ""}], "o": []})
        draft["members"].append({
            "name": cm["name"] if cm else seg["member"],
            "kana": cm.get("kana", "") if cm else "",
            "order": order, "page": None, "questions": qs,
        })
    out = ROOT / "data" / "drafts" / f"issue-{issue}.draft.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{out.relative_to(ROOT)} を作成：{name}（{mid}）一般質問 {len(draft['members'])} 人")
    if unknown:
        print("  config.json の members に無い議員：" + "、".join(unknown))
    return 0


if __name__ == "__main__":
    sys.exit(main())
