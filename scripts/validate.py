#!/usr/bin/env python3
"""データ検査: config と全 issue を読み、誤りを洗い出す。新号追加のたびに実行する。"""
import json, glob, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(ROOT, "config.json"), encoding="utf-8"))
theme_ids = {t["id"] for t in cfg["themes"]}
member_names = {m["name"] for m in cfg["members"]}

errors, warns = [], []
seen_keys = set()

for path in sorted(glob.glob(os.path.join(ROOT, "data", "issue-*.json"))):
    d = json.load(open(path, encoding="utf-8"))
    iss = d["issue"]
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

print(f"検査: issue {len([1 for _ in glob.glob(os.path.join(ROOT,'data','issue-*.json'))])}件 / 質問 {len(seen_keys)}件")
for w in warns: print("  [warn]", w)
for e in errors: print("  [ERROR]", e)
if errors:
    print(f"\nNG: {len(errors)} 件のエラー"); sys.exit(1)
print(f"\nOK（warn {len(warns)} 件）")
