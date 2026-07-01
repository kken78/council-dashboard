#!/usr/bin/env python3
"""
build.py ― 議会一般質問ダッシュボードのビルド。

  config.json + data/issue-*.json
      → docs/index.html           （ダッシュボード本体）
      → docs/data/*.csv / *.json  （オープンデータ）

データソース（config + 号別JSON）から、表示用の records / meta を組み立て、
src/render_html.render() でHTMLを生成する。表示ロジックとデータを分離している。

録画配信リンクは data/videos.json（scripts/build_video_map.py が生成する
「号×議員→録画URL」の突合表）を読み込み、質問ごとに議員別の個別URLを割り当てる。
突合できない場合や videos.json が無い場合は、従来どおり号レベルの一律リンクに
フォールバックする。
"""
import json, glob, os, csv, datetime, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))
import render_html  # noqa: E402

BUILD_DATE = datetime.date.today().isoformat()


def load_sources():
    config = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
    issues = []
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "issue-*.json"))):
        issues.append(json.load(open(p, encoding="utf-8")))
    issues.sort(key=lambda d: d["issue"])
    return config, issues


def load_videos():
    """data/videos.json（号×議員→録画URLの突合表）を読み込む。無ければ空。"""
    p = os.path.join(ROOT, "data", "videos.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return {}


def build_meta(config, issues, records=None):
    sessions = {}
    for d in issues:
        sessions[str(d["issue"])] = {
            "session": d["session"], "year": d["year"], "month": d["month"],
            "pub": d.get("published_date", ""), "minutes": d["links"].get("minutes", ""),
        }
    # 議員ごとの質問数（未掲載を含む累計）。ダッシュボードのカード等で使う。
    counts = {}
    for r in (records or []):
        counts[r["member"]] = counts.get(r["member"], 0) + 1
    roster = [{
        "member": m["name"], "kana": m.get("kana", ""), "seat": m["seat"],
        "kaiha": m.get("kaiha", ""), "party": m.get("party", ""), "terms": m.get("terms"),
        "role": m.get("role", ""), "photo": m.get("photo", ""), "note": m.get("note", ""),
        "count": counts.get(m["name"], 0),
    } for m in config["members"]]

    # 表示用の派生文字列（自治体固有値を直書きしないため）
    town = config["town"]
    council_term = town.get("council_term", "")
    term_range = council_term.split("（")[0].strip()      # 例: 令和5年5月1日 〜 令和9年4月30日
    iss = [d["issue"] for d in issues]
    issue_range = f"第{min(iss)}号〜第{max(iss)}号" if iss else ""
    first, last = issues[0], issues[-1]
    session_range = (f"{first['session']}〜{last['session']}" if issues else "")

    def wareki(y, m):
        return f"令和{y - 2018}年{m}月"
    period = (f"{wareki(first['year'], first['month'])}〜{wareki(last['year'], last['month'])}"
              if issues else "")
    pubs = [d.get("published_date", "") for d in issues if d.get("published_date")]

    def fmt_pub(s):
        a = s.split("-")
        return f"{a[0]}年{int(a[1])}月"
    pub_range = (f"{fmt_pub(min(pubs))}〜{fmt_pub(max(pubs))}" if pubs else "")
    return {
        "town": config["town"]["name"],
        "town_short": town.get("name_short", config["town"]["name"]),
        "term_label": town.get("term_label", ""),
        "term_range": term_range,
        "issue_range": issue_range,
        "session_range": session_range,
        "pub_range": pub_range,
        "period": period,
        "term": config["town"]["council_term"],
        "source": config.get("source", ""),
        "seats": config["town"]["seats"],
        "bulletin_index": config["town"].get("bulletin_index_url", ""),
        "sessions": sessions,
        "roster": roster,
        "note": config.get("publication_rule", ""),
        "theme_order": config.get("default_theme_order", "config"),
        "build_date": BUILD_DATE,
    }


def build_records(issues, videos=None):
    videos = videos or {}
    records = []
    rid = 0
    for d in issues:
        iss = d["issue"]
        links = d["links"]
        issue_video = links.get("video", "")          # 号レベル（従来の一律リンク）
        vmap = videos.get(str(iss), {})               # {議員名: {result_url, play_url, ...}}
        for m in d["members"]:
            entry = vmap.get(m["name"])
            member_video = entry["result_url"] if entry else issue_video
            for q in m["questions"]:
                rid += 1
                rec = {
                    "id": rid, "issue": iss, "session": d["session"],
                    "year": d["year"], "month": d["month"], "pub_date": d.get("published_date", ""),
                    "member": m["name"], "kana": m.get("kana", ""), "order": m["order"],
                    "q_num": q["n"], "text": q["title"], "theme": q["theme"],
                    "published": q["published"], "page": m["page"],
                    "minutes": links.get("minutes", ""), "bulletin": links.get("bulletin_pdf", ""),
                    "video": member_video,            # 個別（なければ従来の一律リンク）
                    "video_issue": issue_video,       # 号レベルは従来の一律を維持
                }
                if q["published"] and q.get("q"):
                    rec["qa"] = {
                        "q": q["q"],
                        "a": [[b["label"], b["text"]] for b in q.get("a", [])],
                        "o": [[b["label"], b["text"]] for b in q.get("o", [])],
                        "at": q.get("answer_title", ""),
                        "v": True,
                    }
                else:
                    rec["qa"] = None
                records.append(rec)
    return records


def write_html(records, meta):
    html = render_html.render(records, meta)
    repl = {
        "__BUILD_DATE__": BUILD_DATE,
        "__TOWN_FULL__": meta["town"],
        "__TOWN_SHORT__": meta["town_short"],
        "__TERM_LABEL__": meta["term_label"],
        "__TERM_RANGE__": meta["term_range"],
        "__SEATS__": str(meta["seats"]),
        "__SOURCE__": meta["source"],
        "__ISSUE_RANGE__": meta["issue_range"],
        "__SESSION_RANGE__": meta["session_range"],
        "__PUB_RANGE__": meta["pub_range"],
    }
    for k, v in repl.items():
        html = html.replace(k, v)
    out = os.path.join(ROOT, "docs")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)
    return len(html)


def write_open_data(config, issues, records):
    out = os.path.join(ROOT, "docs", "data")
    os.makedirs(out, exist_ok=True)

    # questions.csv（本文を除くメタデータ。全文は questions.json）
    with open(os.path.join(out, "questions.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["issue", "published_date", "seat", "member", "order", "q_num",
                    "theme", "published", "title", "answer_title", "has_fulltext",
                    "bulletin_pdf", "minutes", "video"])
        seat = {m["name"]: m["seat"] for m in config["members"]}
        for r in records:
            w.writerow([r["issue"], r["pub_date"], seat.get(r["member"], ""), r["member"],
                        r["order"], r["q_num"], r["theme"], int(r["published"]), r["text"],
                        (r["qa"] or {}).get("at", ""), int(bool(r["qa"])),
                        r["bulletin"], r["minutes"], r["video"]])

    # questions.json（全文込み・機械判読用）
    qjson = []
    for r in records:
        item = {"issue": r["issue"], "member": r["member"], "order": r["order"],
                "q_num": r["q_num"], "theme": r["theme"], "published": r["published"],
                "title": r["text"], "pub_date": r["pub_date"], "bulletin": r["bulletin"],
                "minutes": r["minutes"], "video": r["video"]}
        if r["qa"]:
            item["answer_title"] = r["qa"]["at"]
            item["question_text"] = r["qa"]["q"]
            item["answers"] = [{"label": a[0], "text": a[1]} for a in r["qa"]["a"]]
            item["other"] = [{"label": o[0], "text": o[1]} for o in r["qa"]["o"]]
        qjson.append(item)
    json.dump({"generated": BUILD_DATE, "source": config.get("source", ""),
               "license": config.get("license", {}), "questions": qjson},
              open(os.path.join(out, "questions.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # members.csv
    with open(os.path.join(out, "members.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["seat", "name", "kana", "kaiha", "party", "terms", "role", "note"])
        for m in sorted(config["members"], key=lambda x: x["seat"]):
            w.writerow([m["seat"], m["name"], m.get("kana", ""), m.get("kaiha", ""),
                        m.get("party", ""), m.get("terms", ""), m.get("role", ""), m.get("note", "")])

    # themes.csv
    with open(os.path.join(out, "themes.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order", "id", "label", "color"])
        for t in config["themes"]:
            w.writerow([t["order"], t["id"], t["label"], t["color"]])

    # issues.csv
    with open(os.path.join(out, "issues.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["issue", "session", "year", "month", "published_date",
                    "n_questions", "n_published", "bulletin_pdf", "minutes", "video"])
        for d in issues:
            qs = [q for m in d["members"] for q in m["questions"]]
            w.writerow([d["issue"], d["session"], d["year"], d["month"], d.get("published_date", ""),
                        len(qs), sum(1 for q in qs if q["published"]),
                        d["links"].get("bulletin_pdf", ""), d["links"].get("minutes", ""),
                        d["links"].get("video", "")])


def main():
    config, issues = load_sources()
    videos = load_videos()
    records = build_records(issues, videos)
    meta = build_meta(config, issues, records)
    n = write_html(records, meta)
    write_open_data(config, issues, records)
    pub = sum(1 for r in records if r["published"])
    # 突合状況の目安：質問行のうち個別録画に当たった割合。
    linked = sum(1 for r in records if r["video"] and r["video"] != r.get("video_issue"))
    print(f"build OK  ({BUILD_DATE})")
    print(f"  docs/index.html  {n:,} bytes")
    print(f"  records {len(records)} / published {pub} / verbatim {sum(1 for r in records if r['qa'])}")
    print(f"  video linked (個別) {linked} / {len(records)}")
    print(f"  open data -> docs/data/ (questions.csv/json, members.csv, themes.csv, issues.csv)")


if __name__ == "__main__":
    main()
