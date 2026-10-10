# データ仕様（データ辞書）

## config.json（自治体プロファイル：1ファイル）
| キー | 説明 |
|---|---|
| town.name / council_term / seats | 自治体名・任期・議席数 |
| default_member_order | 既定の並び順（"seat"=議席番号順。中立既定） |
| members[] | 議員。name, kana, seat, kaiha, party, terms, role, photo, note（補欠当選等の前提注記） |
| themes[] | id, label, color, order |
| publication_rule / neutrality_policy / theme_policy | 掲載ルールと中立・分類方針の明文 |
| source / license | 出典・ライセンス（code=MIT, data=CC BY 4.0） |

## data/issue-NN.json（議会だより1号＝1ファイル）
| キー | 説明 |
|---|---|
| issue / session / year / month / published_date | 号・定例会・発行 |
| index_page | 一般質問一覧表（目次）のページ（通常8） |
| links.bulletin_pdf / minutes / video | 議会だよりPDF・会議録ページ（「本会議のご案内」ではなく「…・会議録」のページ）・録画 |
| members[] | name, kana, order（発言順）, page（本文ページ）, questions[] |

### questions[] の各要素
| キー | 必須 | 説明 |
|---|---|---|
| n | ○ | 質問番号 |
| published | ○ | 掲載=true／未掲載=false（3問以上で〇の付かないもの） |
| theme | ○ | 主テーマid（config.themesのidと一致）。件数集計・グラフはこの値だけを使う |
| sub_themes[] | 任意 | 副テーマid（複数可）。分野をまたぐ質問の「もう一方」。絞り込み・検索では効くが件数集計には入れない。主テーマとの重複・配列内の重複は不可 |
| title | ○ | 一覧表（目次）の題名 |
| answer_title | 掲載時 | 答弁の見出し |
| q | 掲載時 | 問の原文（改行は \n） |
| a[] | 掲載時 | 答弁ブロック {label, text}。labelが「答弁/答」以外は発言者名 |
| o[] | 任意 | 要望・質問を終えて等の他ブロック {label, text} |

未掲載（published:false）は title までで、q/a/o は持たない。

副テーマは省略可（既定＝なし）。既存号は未記載＝副テーマなしとして扱う。1問1テーマの原則（＝合計件数と質問数が一致する）を保つため、集計・グラフ・議員×テーマ表は主テーマのみで数える。
