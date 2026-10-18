#!/usr/bin/env python3
"""
migration: hino_questions.json (現行の確定データ) → 汎用リポジトリ構造
出力:
  council-dashboard/config.json          自治体固有の設定（議員・テーマ・会期）
  council-dashboard/data/issue-NN.json   1号=1ファイル（問・答の本文込み）
町名・議員・テーマは config.json に分離し、コードからハードコードを排除する。
"""
import json, os, collections

SRC = json.load(open("hino_questions.json", encoding="utf-8"))
META, RECS = SRC["meta"], SRC["records"]

THEME_ORDER = ["子育て・教育","行財政・行政運営","福祉・健康・医療","交通・公共交通","農林業",
    "防災・安全","自治・住民参画","まちづくり・公園・空き家","産業・観光・文化財","人口・移住定住","環境"]
THEME_COLOR = {"子育て・教育":"#D98324","行財政・行政運営":"#5B6770","福祉・健康・医療":"#C44569",
    "交通・公共交通":"#2D6A8E","農林業":"#6A8D3F","防災・安全":"#B23A48","自治・住民参画":"#7A5C9E",
    "まちづくり・公園・空き家":"#3E8E7E","産業・観光・文化財":"#A8762F","人口・移住定住":"#C77FA8","環境":"#3F8E63"}

OUT = "council-dashboard"
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)

# ---------- config.json （自治体プロファイル） ----------
config = {
    "schema_version": "1.0",
    "town": {
        "name": META["town"],
        "name_en": "Hino Town, Shiga",
        "council_term": META["term"],
        "seats": META["seats"],
        "bulletin_index_url": META["bulletin_index"],
        "minutes_index_url": "",
        "video_index_url": "",
    },
    # 既定の中立な並び順は「議席番号順」。件数では並べない。
    "default_member_order": "seat",
    "members": [
        {
            "name": m["member"], "kana": m.get("kana",""), "seat": m["seat"],
            "kaiha": m.get("kaiha",""), "party": m.get("party",""),
            "terms": m.get("terms"), "role": m.get("role",""),
            "photo": m.get("photo",""),
            # 補欠当選など、件数比較の前提となる注記（中立表示に使う）
            "note": m.get("note","")
        } for m in META["roster"]
    ],
    "themes": [
        {"id": t, "label": t, "color": THEME_COLOR.get(t, "#888"), "order": i+1}
        for i, t in enumerate(THEME_ORDER)
    ],
    "theme_policy": (
        "各質問は主たる政策領域で1テーマに分類した実務的な区分であり、境界事例は判断による。"
        "テーマは件数比較のためではなく、扱われた論点の広がりを示すためのもの。"
    ),
    "publication_rule": META["note"],
    "neutrality_policy": (
        "質問数は数え方が議員ごとに異なり、在任期間・登壇機会も一様でないため、"
        "議員間の優劣を示す指標ではない。既定表示は議席番号順とし、件数による序列化は行わない。"
    ),
    "source": META["source"],
    "license": {
        "code": "MIT",
        "data_structure": "CC BY 4.0",
        "transcribed_text": "このリポジトリのライセンスの対象外（著作権は日野町議会）",
        "member_photos": "このリポジトリのライセンスの対象外（日野町のウェブサイトの画像を表示。リポジトリには含まない）",
        "details": "https://github.com/kken78/council-dashboard/blob/main/LICENSE-DATA.md",
    },
}
json.dump(config, open(os.path.join(OUT, "config.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

# ---------- issue-NN.json （1号=1ファイル） ----------
by_issue = collections.defaultdict(list)
for r in RECS:
    by_issue[r["issue"]].append(r)

for issue, recs in sorted(by_issue.items()):
    s = recs[0]
    # 議員ごとにまとめる（order, page は議員単位）
    members = collections.OrderedDict()
    for r in sorted(recs, key=lambda x: (x["order"], x["q_num"])):
        key = r["member"]
        if key not in members:
            members[key] = {
                "name": r["member"], "kana": r["kana"],
                "order": r["order"], "page": r["page"], "questions": []
            }
        qa = r.get("qa") or {}
        q = {
            "n": r["q_num"],
            "published": r["published"],
            "theme": r["theme"],
            "title": r["text"],            # 一覧表（目次）の題名
        }
        if r["published"] and qa.get("v"):
            q["answer_title"] = qa.get("at", "")        # 答弁の見出し（金色）
            q["q"] = qa.get("q", "")                    # 問・原文
            q["a"] = [{"label": lbl, "text": txt} for lbl, txt in qa.get("a", [])]  # 答弁ブロック
            q["o"] = [{"label": lbl, "text": txt} for lbl, txt in qa.get("o", [])]  # 要望等の他ブロック
        members[key]["questions"].append(q)

    issue_obj = {
        "schema_version": "1.0",
        "issue": issue,
        "session": s["session"],
        "year": s["year"], "month": s["month"],
        "published_date": s["pub_date"],
        "index_page": 8,   # 一般質問一覧表（目次）のページ
        "links": {
            "bulletin_pdf": s["bulletin"],
            "minutes": s["minutes"],
            "video": s["video"],
        },
        "members": list(members.values()),
    }
    json.dump(issue_obj,
              open(os.path.join(OUT, "data", f"issue-{issue:02d}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

# ---------- 検算 ----------
tot_q = sum(len(m["questions"]) for i in by_issue for m in
            [mm for mm in json.load(open(os.path.join(OUT,'data',f'issue-{i:02d}.json'),encoding='utf-8'))["members"]])
print(f"config.json: 議員{len(config['members'])}名 / テーマ{len(config['themes'])}")
print(f"issue files: {len(by_issue)}  (第{min(by_issue)}〜{max(by_issue)}号)")
print(f"総質問: {tot_q}  / 掲載(原文あり): {sum(1 for r in RECS if r['published'] and (r.get('qa') or {}).get('v'))}")
