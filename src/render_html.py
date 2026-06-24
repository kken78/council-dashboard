# -*- coding: utf-8 -*-
# 議会一般質問ダッシュボードのHTMLレンダラ。
# build.py から render(records, meta) を呼び出して使う。
import json


# テーマ順とカラー
THEME_ORDER = [
    "子育て・教育","行財政・行政運営","福祉・健康・医療","交通・公共交通","農林業",
    "防災・安全","自治・住民参画","まちづくり・公園・空き家","産業・観光・文化財",
    "人口・移住定住","環境",
]
THEME_COLOR = {
    "子育て・教育":"#D98324",
    "行財政・行政運営":"#5B6770",
    "福祉・健康・医療":"#C44569",
    "交通・公共交通":"#2D6A8E",
    "農林業":"#6A8D3F",
    "防災・安全":"#B23A48",
    "自治・住民参画":"#7A5C9E",
    "まちづくり・公園・空き家":"#3E8E7E",
    "産業・観光・文化財":"#A8762F",
    "人口・移住定住":"#C77FA8",
    "環境":"#3F8E63",
}

# 議員の発言順（最新号での順）で並べる用に、各号の order を保持済み。
# 議員リスト（初登場順）は render 内で構築する。

HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TOWN_SHORT__議会 議会だより・一般質問ダッシュボード</title>
<style>
:root{
  --paper:#FAF7F2; --paper-2:#F2ECE3; --card:#FFFFFF;
  --ink:#231B26; --ink-2:#5A4E5E; --muted:#6E6377;
  --plum:#7A1F5C; --plum-d:#5E1646; --plum-l:#F3E4ED;
  --gold:#B08A3E; --line:#E4DAD0; --line-2:#D9CEC2;
  --good:#3F7D54;
  --shadow:0 1px 2px rgba(60,30,50,.05),0 4px 16px rgba(60,30,50,.06);
  --r:14px;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--paper); color:var(--ink);
  font-family:"Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic UI","Yu Gothic","Noto Sans JP","Meiryo",system-ui,sans-serif;
  font-feature-settings:"palt" 1;
  line-height:1.6; -webkit-font-smoothing:antialiased;
}
.num{font-variant-numeric:tabular-nums;font-family:"DIN Alternate","Helvetica Neue",Arial,"Hiragino Kaku Gothic ProN",sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:0 20px}

/* Header */
header.top{
  background:var(--plum-d);
  color:#fff;position:relative;overflow:hidden;
}
header.top::after{content:"";position:absolute;right:-60px;top:-60px;width:280px;height:280px;border-radius:50%;background:rgba(255,255,255,.05)}
.top .wrap{padding:26px 20px 24px}
.eyebrow{font-size:12px;letter-spacing:.22em;color:#E9C9DD;font-weight:700;margin:0 0 8px}
header.top h1{font-size:clamp(22px,3.4vw,32px);margin:0;font-weight:800;letter-spacing:.01em}
.sub{margin:8px 0 0;color:#EAD3E1;font-size:13.5px;max-width:760px}
.termtag{display:inline-block;margin-top:14px;padding:6px 13px;border:1px solid rgba(255,255,255,.4);border-radius:999px;font-size:12.5px;font-weight:600;letter-spacing:.02em}

/* Nav tabs */
nav.tabs{position:sticky;top:0;z-index:30;background:rgba(250,247,242,.92);backdrop-filter:saturate(1.2) blur(8px);border-bottom:1px solid var(--line)}
nav.tabs .wrap{display:flex;gap:4px;overflow-x:auto;padding:0 14px}
.tab{appearance:none;border:0;background:transparent;color:var(--ink-2);font:inherit;font-weight:700;font-size:14px;
  padding:14px 14px 12px;border-bottom:3px solid transparent;cursor:pointer;white-space:nowrap;letter-spacing:.02em}
.tab:hover{color:var(--plum)}
.tab[aria-selected="true"]{color:var(--plum);border-color:var(--plum)}

main .wrap{padding:24px 20px 64px}
.view{display:none;animation:fade .35s ease}
.view.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

h2.sec{font-size:16px;font-weight:800;margin:30px 0 14px;letter-spacing:.02em;display:flex;align-items:center;gap:9px}
h2.sec::before{content:"";width:5px;height:17px;background:var(--plum);border-radius:2px}
h2.sec:first-child{margin-top:6px}
.lead{color:var(--ink-2);font-size:13.5px;margin:-6px 0 16px}

/* Stat cards */
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}
@media(max-width:720px){.stats{grid-template-columns:repeat(2,1fr)}}
.stat{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:16px 16px 14px;box-shadow:var(--shadow)}
.stat .v{font-size:30px;font-weight:800;line-height:1;color:var(--plum)}
.stat .v small{font-size:14px;font-weight:700;color:var(--ink-2);margin-left:3px}
.stat .l{font-size:12.5px;color:var(--ink-2);margin-top:7px;font-weight:600}
.stat .x{font-size:11.5px;color:var(--muted);margin-top:2px}

.card{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:18px;box-shadow:var(--shadow);min-width:0}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.grid2>*{min-width:0}
@media(max-width:860px){.grid2{grid-template-columns:1fr}}

/* Bars */
.barrow{display:grid;grid-template-columns:140px 1fr 56px;align-items:center;gap:10px;margin:7px 0;font-size:13px}
.barrow .lab{color:var(--ink);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:pointer}
.barrow .lab:hover{color:var(--plum);text-decoration:underline}
.bartrack{background:var(--paper-2);border-radius:6px;height:18px;overflow:hidden}
.barfill{height:100%;border-radius:6px;min-width:2px;transition:width .6s cubic-bezier(.2,.7,.2,1)}
.barrow .cnt{text-align:right;font-weight:700;font-size:13px;color:var(--ink-2);line-height:1.15}
.barrow .cnt .pct{display:block;font-weight:600;font-size:10.5px;color:var(--muted)}
.sortnote{margin:8px 2px 0;font-size:12px;color:var(--ink-2);background:var(--plum-l);border-radius:8px;padding:8px 10px;line-height:1.6}
.viewkind{font-size:11.5px;font-weight:700;color:var(--plum);letter-spacing:.04em;margin:0 0 2px}
:focus-visible{outline:2.5px solid var(--plum);outline-offset:2px;border-radius:4px}
.clickable,.mcard{cursor:pointer}
.barrow.clickable{cursor:pointer;border-radius:8px;padding:2px 6px;margin-left:-6px;margin-right:-6px;transition:background .12s}
.barrow.clickable:hover{background:var(--plum-l)}
.barrow.clickable:hover .lab{color:var(--plum)}
@media(max-width:520px){.barrow{grid-template-columns:96px 1fr 46px;font-size:12px}}

/* Session timeline */
.tl{display:flex;align-items:stretch;gap:10px;max-width:100%;padding:6px 0 2px;margin-top:8px}
.tlcol{flex:1;display:grid;grid-template-rows:20px 130px auto;align-items:end;justify-items:center;gap:6px;min-width:0}
.tlbar{width:70%;max-width:38px;background:var(--plum);border-radius:4px 4px 0 0;position:relative;transition:height .6s}
.tlbar .pub{position:absolute;left:0;right:0;bottom:0;background:rgba(255,255,255,.34)}
.tlcap{align-self:start;font-size:10.5px;color:var(--ink-2);text-align:center;line-height:1.25;font-weight:600}
.tlnum{font-size:13px;font-weight:800;color:var(--plum)}
@media(max-width:640px){
  .tl{overflow-x:auto;overscroll-behavior-inline:contain;scroll-snap-type:x proximity;padding-bottom:10px;-webkit-overflow-scrolling:touch}
  .tlcol{flex:0 0 58px;scroll-snap-align:start}
  .tlcap{font-size:10px}
}

/* Legend */
.legend{display:flex;flex-wrap:wrap;gap:8px 14px;margin:14px 0 0}
.lg{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--ink-2);cursor:pointer}
.lg .sw{width:11px;height:11px;border-radius:3px}
.lg:hover{color:var(--ink)}

/* Member cards */
.mgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:13px}
.mcard{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:15px 15px 13px;cursor:pointer;box-shadow:var(--shadow);transition:transform .15s,box-shadow .15s,border-color .15s}
.mcard:hover{border-color:var(--plum);box-shadow:var(--shadow)}
.mcard .mh{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.mcard .mn{font-size:16px;font-weight:800}
.mcard .mk{font-size:11px;color:var(--muted);font-weight:600}
.mcard .mtot{font-size:22px;font-weight:800;color:var(--plum)}
.mtot small{font-size:11px;color:var(--ink-2);font-weight:700}
.stack{display:flex;gap:1px;height:10px;border-radius:5px;overflow:hidden;margin:11px 0 8px;background:var(--paper-2)}
.stack i{display:block;height:100%}
.chips{display:flex;flex-wrap:wrap;gap:4px;margin-top:8px}
.chip{font-size:10.5px;padding:2px 7px;border-radius:999px;background:var(--paper-2);color:var(--ink-2);font-weight:600}

/* Matrix */
.mxwrap{overflow-x:visible;border:1px solid var(--line);border-radius:var(--r);background:var(--card);box-shadow:var(--shadow)}
.mxhint{display:none}
table.mx{border-collapse:collapse;font-size:11px;width:100%;table-layout:fixed}
table.mx th,table.mx td{border:1px solid var(--line);padding:0;text-align:center;overflow:hidden}
table.mx thead th{background:var(--paper-2);font-weight:700;color:var(--ink-2);padding:7px 2px;font-size:9.5px;vertical-align:bottom;line-height:1.2;white-space:normal;overflow:visible}
table.mx thead th:first-child{width:16%;min-width:80px;font-size:10px}
table.mx thead th:last-child{width:6%}
table.mx tbody th{background:var(--paper-2);text-align:right;padding:6px 7px;font-weight:700;white-space:nowrap;font-size:11.5px}
.mxdot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-bottom:3px}
.mxcell{width:100%;height:30px;display:flex;align-items:center;justify-content:center;font-weight:700;color:#fff;font-variant-numeric:tabular-nums;font-size:12px}
.mxtot{font-weight:800;color:var(--plum);background:#fff}
.mxhcol{cursor:pointer}
.mxhcol:hover{background:var(--plum-l);color:var(--plum)}
.mxhrow{cursor:pointer}
.mxhrow:hover{background:var(--plum-l);color:var(--plum);text-decoration:underline}
.mxc-click{cursor:pointer}
.mxc-click:hover{outline:2px solid var(--ink);outline-offset:-2px}
@media(max-width:640px){
  .mxwrap{overflow-x:auto}
  table.mx{table-layout:auto;min-width:600px}
  .mxhint{display:block;font-size:11.5px;color:var(--muted);margin:0 0 8px}
}

/* Table */
.controls{display:flex;flex-wrap:wrap;gap:9px;align-items:center;margin-bottom:14px}
.controls input,.controls select{font:inherit;font-size:13px;padding:8px 11px;border:1px solid var(--line-2);border-radius:9px;background:#fff;color:var(--ink)}
.controls input{flex:1;min-width:180px}
.controls input:focus,.controls select:focus{outline:2px solid var(--plum-l);border-color:var(--plum)}
.tcount{font-size:12.5px;color:var(--ink-2);font-weight:600;margin-left:auto}
.qtable{width:100%;border-collapse:collapse;font-size:13px}
.qtable th{text-align:left;font-size:11.5px;color:var(--muted);font-weight:700;letter-spacing:.04em;padding:8px 10px;border-bottom:2px solid var(--line-2);position:sticky;top:53px;background:var(--paper);cursor:pointer;white-space:nowrap}
.qtable th:hover{color:var(--plum)}
.qtable td{padding:10px;border-bottom:1px solid var(--line);vertical-align:top}
.qtable tr:hover td{background:#fff}
.qt-text{max-width:480px}
/* スマホ：横幅前提のテーブルをカード縦積みに切り替える（セルが潰れて縦書き化するのを防ぐ） */
@media(max-width:680px){
  #qtable thead{display:none}
  #qtable,#qtable tbody{display:block;width:100%}
  #qtable tr{display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px;border:1px solid var(--line);border-radius:12px;background:var(--card);margin:0 0 12px;padding:12px 14px;box-shadow:var(--shadow)}
  #qtable tr:hover td{background:transparent}
  #qtable td{display:block;border:none;padding:0;max-width:none}
  #qtable td:nth-child(1){order:1}
  #qtable td:nth-child(2){order:2}
  #qtable td:nth-child(4){order:3}
  #qtable td:nth-child(5){order:4}
  #qtable td:nth-child(6){display:none}
  #qtable td.qt-text{flex:1 1 100%;order:9;margin-top:6px;border-top:1px dashed var(--line);padding-top:8px}
  #qtable td.qt-text .qcellhead{max-width:none}
  #qtable .pg{font-size:11px;color:var(--muted)}
}
.tg{display:inline-flex;align-items:center;gap:5px;font-size:11.5px;font-weight:700;padding:3px 9px;border-radius:999px;white-space:nowrap}
.tg .d{width:8px;height:8px;border-radius:50%}
.badge{font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:6px;white-space:nowrap}
.b-pub{background:var(--plum-l);color:var(--plum-d)}
.b-non{background:#EFE9E1;color:#8A7F72;border:1px dashed #C9BCAA}
.mlink{color:var(--plum);font-weight:700;cursor:pointer;white-space:nowrap}
.mlink:hover{text-decoration:underline}
.pg{color:var(--muted);font-variant-numeric:tabular-nums;font-size:12px}

/* Note */
.note{background:var(--plum-l);border:1px solid #E6CDDD;border-radius:var(--r);padding:13px 16px;font-size:12.5px;color:var(--plum-d);margin-top:18px;display:flex;gap:10px;line-height:1.55}
.note b{font-weight:800}
.note .ico{flex:0 0 auto;width:20px;height:20px;border-radius:50%;background:var(--plum);color:#fff;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;margin-top:1px}

/* Modal */
.modal{position:fixed;inset:0;background:rgba(35,20,40,.45);backdrop-filter:blur(2px);display:none;align-items:flex-start;justify-content:center;z-index:60;padding:30px 16px;overflow:auto}
.modal.open{display:flex}
.sheet{background:var(--paper);border-radius:18px;max-width:760px;width:100%;box-shadow:0 24px 60px rgba(40,10,40,.3);overflow:hidden}
.sheet .sh{background:var(--plum-d);color:#fff;padding:18px 22px;position:relative}
.sheet .sh h3{margin:0;font-size:21px;font-weight:800}
.sheet .sh .sk{font-size:12px;color:#EAD0E0;margin-top:3px;font-weight:600}
.sheet .sh .sm{display:flex;gap:18px;margin-top:12px}
.sheet .sh .sm div{font-size:11.5px;color:#EAD0E0}
.sheet .sh .sm b{display:block;font-size:20px;font-weight:800;color:#fff}
.xbtn{position:absolute;right:14px;top:14px;width:32px;height:32px;border-radius:50%;border:0;background:rgba(255,255,255,.18);color:#fff;font-size:18px;cursor:pointer}
.xbtn:hover{background:rgba(255,255,255,.3)}
.sheet .sb{padding:18px 22px 26px;max-height:60vh;overflow:auto}
.qitem{padding:11px 0;border-bottom:1px solid var(--line)}
.qitem:last-child{border:0}
.qmeta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px}
.qmeta .ss{font-size:11.5px;color:var(--ink-2);font-weight:700}
.qbody{font-size:14px;font-weight:700;color:var(--ink);line-height:1.5}

/* Photos & member meta */
.avwrap{position:relative;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;flex:0 0 auto;overflow:hidden;background:var(--plum-l);border:2px solid #fff;box-shadow:0 1px 3px rgba(60,30,50,.18);vertical-align:middle}
.avfb{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:var(--plum-d);font-weight:800;background:var(--plum-l)}
.av{position:relative;width:100%;height:100%;object-fit:cover;object-position:center top;display:block}
.mid{display:flex;align-items:center;gap:11px;min-width:0}
.rolebadge{font-size:10px;font-weight:800;color:#fff;background:var(--gold);padding:1px 7px;border-radius:5px;vertical-align:middle;margin-left:4px;letter-spacing:.02em}
.rolebadge-lg{font-size:12px;padding:2px 9px;background:rgba(255,255,255,.25)}
.kaiha{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--ink-2);font-weight:700;margin-top:10px}
.kdot{width:7px;height:7px;border-radius:50%;background:var(--plum)}
.reptag{font-size:9.5px;font-weight:800;color:var(--plum-d);background:var(--plum-l);padding:1px 6px;border-radius:5px;margin-left:2px}
.mcard-zero{opacity:.96;background:repeating-linear-gradient(135deg,#fff,#fff 14px,#FBF7F1 14px,#FBF7F1 28px)}
.zeronote{margin-top:11px;font-size:12px;color:var(--ink-2);background:var(--paper-2);border-radius:8px;padding:8px 11px}
.mlink-av{display:inline-flex;align-items:center;gap:7px}
.mlink-av .avwrap{flex:0 0 auto}
/* modal head */
.shhead{display:flex;align-items:center;gap:14px}
.shface .avwrap{border-width:3px}
.themedot{display:block;width:46px;height:46px;border-radius:14px}
.shtxt{min-width:0}
.qgrp{margin:16px 0 6px;font-size:12px;font-weight:800;color:var(--plum);border-top:1px solid var(--line);padding-top:12px}
.qgrp:first-child{border:0;padding-top:0;margin-top:2px}
.emptybox{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;font-size:13.5px;color:var(--ink);text-align:center;margin-top:6px}
/* QA expand */
.qa-yes{font-size:10px;font-weight:800;color:#fff;background:var(--good);padding:1px 7px;border-radius:5px}
.qa-sum{font-size:10px;font-weight:800;color:#fff;background:#9aa0a6;padding:1px 7px;border-radius:5px}
.qexp{appearance:none;border:1px solid var(--line-2);background:#fff;color:var(--plum);font:inherit;font-size:11.5px;font-weight:700;padding:4px 11px;border-radius:8px;cursor:pointer;margin-top:8px}
.qexp:hover{background:var(--plum-l);border-color:var(--plum-l)}
.qexp.open{background:var(--plum-l)}
.qdetail{margin-top:10px;padding:13px 14px;background:var(--paper-2);border-radius:10px;border:1px solid var(--line)}
.qa-q,.qa-a{display:flex;gap:9px;font-size:13px;line-height:1.65;margin:0 0 9px}
.qa-atitle{display:flex;gap:9px;font-size:13px;line-height:1.6;margin:0 0 9px;font-weight:600}
.qa-atitle span:last-child{color:#9a7b3a;white-space:pre-wrap}
.qa-o{display:flex;gap:9px;font-size:12.5px;line-height:1.6;margin:10px 0 4px;padding-top:10px;border-top:1px dashed var(--line-2)}
.qa-o span:last-child{color:var(--ink-2);white-space:pre-wrap}
.qa-o b{color:var(--teal,#2c7a7b)}
.qa-a{margin-bottom:7px}
.qa-q span:last-child{color:var(--ink);white-space:pre-wrap}
.qa-a span:last-child{color:var(--ink-2);white-space:pre-wrap}
.qa-a b{color:var(--ink);font-weight:700}
.qa-tag{flex:0 0 auto;width:24px;height:24px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:800;color:#fff}
.qa-tag.tq{background:var(--plum)}
.qa-tag.ta{background:var(--gold)}
.qa-tag.tb{background:#c98a2b}
.qa-tag.to{background:#2c7a7b;width:auto;padding:0 7px}
.qa-note{font-size:12.5px;color:var(--ink-2);line-height:1.6;margin-bottom:10px}
.qcellhead{font-size:13.5px;font-weight:700;color:var(--ink);line-height:1.5;margin-bottom:4px}
.qa-prov{font-size:11px;color:var(--muted);margin-top:10px}
.qa-links{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;border-top:1px dashed var(--line-2);padding-top:10px}
.qa-link{font-size:12px;font-weight:700;color:var(--plum);text-decoration:none;background:#fff;border:1px solid var(--line-2);border-radius:7px;padding:5px 11px}
.qa-link:hover{background:var(--plum);color:#fff;border-color:var(--plum)}

/* 議会だより chips */
.bulletins{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
@media(max-width:760px){.bulletins{grid-template-columns:1fr 1fr}}
@media(max-width:480px){.bulletins{grid-template-columns:1fr}}
.bchip{display:flex;flex-direction:column;gap:1px;text-decoration:none;border:1px solid var(--line-2);border-radius:10px;padding:10px 13px;background:#fff;transition:border-color .15s,transform .15s,box-shadow .15s}
.bchip:hover{border-color:var(--plum);transform:translateY(-1px);box-shadow:var(--shadow)}
.bchip .bn{font-weight:800;color:var(--plum);font-size:14px}
.bchip .bs{font-size:12.5px;color:var(--ink);font-weight:600}
.bchip .bd{font-size:11px;color:var(--muted)}
.inlink{color:var(--plum);font-weight:700}
a.tlcap{text-decoration:none;color:var(--ink-2)}
a.tlcap:hover{color:var(--plum);text-decoration:underline}
/* テーマ内訳 */
.tbreak{background:var(--paper-2);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:14px}
.tbreak-h{font-size:11.5px;font-weight:800;color:var(--ink-2);margin-bottom:9px;letter-spacing:.02em}
.tb-row{display:grid;grid-template-columns:96px 1fr 28px;align-items:center;gap:10px;margin:5px 0;font-size:12.5px}
.tb-name{font-weight:700;color:var(--ink);cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tb-name:hover{color:var(--plum);text-decoration:underline}
.tb-bar{background:#fff;border-radius:5px;height:14px;overflow:hidden;border:1px solid var(--line)}
.tb-bar i{display:block;height:100%;border-radius:5px;min-width:2px}
.tb-c{text-align:right;font-weight:700;color:var(--ink-2)}
.tb-pct{color:var(--muted);font-weight:600;font-size:11px;margin-left:3px}
.tb-unit{font-weight:600;font-size:10.5px;color:var(--ink-2);margin-left:1px}
.tbreak-m .tb-row{grid-template-columns:7em 1fr 92px}
.tbreak-m .tb-name{cursor:pointer}

footer{border-top:1px solid var(--line);background:var(--paper-2)}
footer .wrap{padding:20px;font-size:12px;color:var(--muted);line-height:1.7}
footer b{color:var(--ink-2)}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <p class="eyebrow">__TOWN_FULL__議会</p>
  <h1>議会だより・一般質問ダッシュボード</h1>
  <p class="sub"><b>__TERM_LABEL____TOWN_SHORT__議会議員の活動を紹介する</b>ため、議会だより各号に掲載された一般質問のやりとりを、議員別・テーマ別に蓄積した記録です。有権者の判断材料に、議員ご自身の振り返りに、役場の施策動向の把握にお使いいただけます。</p>
  <span class="termtag">__TERM_LABEL__（議員定数__SEATS__名）　任期：__TERM_RANGE__</span>
</div></header>

<nav class="tabs"><div class="wrap" role="tablist">
  <button class="tab" id="tab-overview" data-view="overview" role="tab" aria-selected="true" aria-controls="overview">概要</button>
  <button class="tab" id="tab-members" data-view="members" role="tab" aria-selected="false" aria-controls="members">議員別</button>
  <button class="tab" id="tab-matrix" data-view="matrix" role="tab" aria-selected="false" aria-controls="matrix">議員 × テーマ</button>
  <button class="tab" id="tab-table" data-view="table" role="tab" aria-selected="false" aria-controls="table">質問一覧</button>
</div></nav>

<main><div class="wrap">

<!-- OVERVIEW -->
<section class="view active" id="overview" role="tabpanel" aria-labelledby="tab-overview">
  <p class="viewkind">提示ビュー｜全体をつかむ</p>
  <div class="stats" id="statcards"></div>

  <div class="grid2" style="margin-top:22px">
    <div class="card">
      <h2 class="sec" style="margin-top:0">テーマ別の質問数</h2>
      <p class="lead" style="margin:-2px 0 12px;font-size:12px">バーをクリックすると、そのテーマの全質問と発言議員が表示されます。</p>
      <div id="themeBars"></div>
    </div>
    <div class="card">
      <h2 class="sec" style="margin:0 0 6px">定例会ごとの質問数</h2>
      <div class="tl" id="sessionTL"></div>
      <p class="lead" style="margin:14px 0 0;font-size:12px">下部の薄い色は「議会だより未掲載」の質問数（3問以上で〇のつかなかったもの）。</p>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <h2 class="sec" style="margin-top:0">議会だより 各号（出典・PDF）</h2>
    <p class="lead">本ダッシュボードは、下記の議会だより各号に掲載された一般質問をもとにしています。号をクリックするとPDFが開きます。議会だよりは年4回発行され、町内全戸に配布されています。</p>
    <div class="bulletins" id="bulletinList"></div>
    <p class="lead" style="margin:14px 0 0;font-size:12px">▶ <a class="inlink" id="bulletinIndexLink" href="#" target="_blank" rel="noopener">議会だより一覧ページ（__TOWN_SHORT__公式サイト）</a></p>
  </div>

  <div class="note">
    <span class="ico">i</span>
    <div><b>掲載と〈問・答〉について。</b> 議会だよりでは、3つ以上一般質問がある場合、スペースの関係で〇のついた番号の質問と答弁のみを掲載しています。本ダッシュボードでは<b>実際に行われた全ての一般質問</b>を収録し、掲載分を「掲載」、未掲載分を「未掲載」として区別。質問を開くと<b>議会だよりに掲載された〈問・答〉の文面（原文）</b>と<b>議会だより・会議録・録画配信へのリンク</b>が表示されます。<b>原文</b>バッジは掲載文そのまま、<b>要約</b>バッジは暫定要約（順次、原文へ置換中）です。逐語の全文は会議録もご参照ください。</div>
  </div>
</section>

<!-- MEMBERS -->
<section class="view" id="members" role="tabpanel" aria-labelledby="tab-members">
  <h2 class="sec">議員別の質問</h2>
  <p class="lead">カードをクリックすると、その議員の全質問と内訳が表示されます。帯はテーマ構成、数字は任期中の累計質問数（未掲載を含む）です。</p>
  <div class="sortbar" id="memberSort">
    <span class="sortlab">並び替え：</span>
    <button class="sortbtn is-on" data-sort="seat">議席番号順</button>
    <button class="sortbtn" data-sort="kaiha">会派別</button>
    <button class="sortbtn" data-sort="kana">五十音順</button>
  </div>
  <div class="mgrid" id="memberGrid"></div>
</section>

<!-- MATRIX -->
<section class="view" id="matrix" role="tabpanel" aria-labelledby="tab-matrix">
  <p class="viewkind">探索ビュー｜分野の広がりを見る</p>
  <h2 class="sec">議員 × テーマ マトリクス</h2>
  <p class="lead">どの議員がどの分野を取り上げたかを一覧できます。数字は質問数、色の濃さはマス間の相対的な多さです（質問数の多寡は活動量の優劣を示すものではありません）。<b>議員名をクリックで議員別、テーマ名をクリックでテーマ別</b>に移動します。<b>数字（交差するマス）をクリックすると、その議員×テーマの質問が「質問一覧」で絞り込み表示</b>されます。</p>
  <p class="mxhint">← 横にスクロールできます →</p>
  <div class="mxwrap"><table class="mx" id="mxTable"></table></div>
  <div class="legend" id="mxLegend"></div>
</section>

<!-- TABLE -->
<section class="view" id="table" role="tabpanel" aria-labelledby="tab-table">
  <p class="viewkind">探索ビュー｜条件で絞り込んで探す</p>
  <h2 class="sec">質問一覧</h2>
  <div class="controls">
    <input type="search" id="q" placeholder="キーワードで検索（例：給食、防災、わたむき自動車…）">
    <select id="fMember"><option value="">議員すべて</option></select>
    <select id="fKaiha"><option value="">会派すべて</option></select>
    <select id="fTheme"><option value="">テーマすべて</option></select>
    <select id="fSession"><option value="">定例会すべて</option></select>
    <select id="fPub"><option value="">掲載・未掲載すべて</option><option value="1">掲載のみ</option><option value="0">未掲載のみ</option></select>
    <span class="tcount" id="tcount"></span>
  </div>
  <table class="qtable" id="qtable">
    <thead><tr>
      <th data-k="issue">号 / 定例会</th>
      <th data-k="member">議員</th>
      <th data-k="text">質問内容</th>
      <th data-k="theme">テーマ</th>
      <th data-k="published">掲載</th>
      <th data-k="page">頁</th>
    </tr></thead>
    <tbody id="qbody"></tbody>
  </table>
</section>

</div></main>

<div class="modal" id="modal"><div class="sheet" role="dialog" aria-modal="true" aria-labelledby="shTitle" tabindex="-1">
  <div class="sh">
    <button class="xbtn" id="xbtn" aria-label="閉じる">×</button>
    <div class="shhead"><div id="shFace" class="shface"></div><div class="shtxt">
      <h3 id="shTitle"></h3>
      <div class="sk" id="shKana"></div>
    </div></div>
    <div class="sm" id="shStats"></div>
  </div>
  <div class="sb" id="shBody"></div>
</div></div>

<footer><div class="wrap">
  出典：<b>__SOURCE__</b>（__SESSION_RANGE__／発行 __PUB_RANGE__）。〈問・答〉は議会だより掲載のままの原文（改行再現）です。正確な質疑・答弁は各号の本文または会議録をご参照ください。本ダッシュボードは議会だより等の公開情報を、有権者・議員・役場の参考に供する目的で整理したものです。写真は公式サイトの画像を参照表示しており、ネットワーク非接続時は氏名表示に切り替わります。
  <br><b>最終更新：__BUILD_DATE__</b>　／　オープンデータ（CSV・JSON）：data/ ディレクトリ　／　ライセンス：コード MIT・データ CC BY 4.0
</div></footer>

<script>
const DB = __DATA__;
const R = DB.records, TORDER = DB.themeOrder, TCOLOR = DB.themeColor, TCTEXT = DB.themeTextColor;
const ROSTER = DB.roster;                 // 全議員（議席番号順）
const META = DB.meta;
function periodLabel(){const ys=[...new Set(R.map(r=>r.issue))].sort((a,b)=>a-b);if(!ys.length)return '';const f=R.find(r=>r.issue===ys[0]),l=R.find(r=>r.issue===ys[ys.length-1]);const w=(y,m)=>`令和${y-2018}年${m}月`;return `${w(f.year,f.month)}〜${w(l.year,l.month)}`;}
const ROSTER_BY = {}; ROSTER.forEach(r=>ROSTER_BY[r.member]=r);
const ACTIVE = ROSTER.filter(r=>r.count>0); // 一般質問を行った議員
const $=(s,el=document)=>el.querySelector(s), $$=(s,el=document)=>[...el.querySelectorAll(s)];
const sum=a=>a.reduce((x,y)=>x+y,0);
const groupCount=(arr,key)=>{const m={};arr.forEach(r=>{const k=typeof key==='function'?key(r):r[key];m[k]=(m[k]||0)+1});return m;};
const seatIdx=m=>ROSTER_BY[m]?ROSTER_BY[m].seat:99;

// 顔写真（公式URL）。読み込めない環境では氏名イニシャル風のフォールバック。
function initials(m){return m.replace(/\s/g,'').slice(0,1);}
function avatar(m,size){
  const info=ROSTER_BY[m]||{};const s=size||44;
  const init=initials(m);const fz=Math.round(s*0.42);
  const fb=`<span class=\"avfb\" style=\"font-size:${fz}px\">${init}</span>`;
  if(!info.photo)return `<span class=\"avwrap\" style=\"width:${s}px;height:${s}px\">${fb}</span>`;
  return `<span class=\"avwrap\" style=\"width:${s}px;height:${s}px\">${fb}<img class=\"av\" src=\"${info.photo}\" alt=\"${m}\" loading=\"lazy\" onerror=\"this.style.display='none'\"></span>`;
}
function roleBadge(m){const i=ROSTER_BY[m]||{};return i.role?`<span class=\"rolebadge\">${i.role}</span>`:'';}

// sessions sorted
const sessions=[...new Set(R.map(r=>r.issue))].sort((a,b)=>a-b);
const ISSUE={};R.forEach(r=>{if(!ISSUE[r.issue])ISSUE[r.issue]={issue:r.issue,session:r.session,pub:r.pub_date,bulletin:r.bulletin,minutes:r.minutes,video:r.video};});
const sessLabel=i=>{const r=R.find(x=>x.issue===i);return r.session;};
const sessShort=i=>{const r=R.find(x=>x.issue===i);return r.session.replace('定例会議','').replace('定例会','').replace('令和','R').replace('年','.').replace('月','');};

// 一般質問を行った議員（議席番号順）
const members=ACTIVE.map(r=>r.member);

/* ---------- OVERVIEW ---------- */
function renderOverview(){
  const total=R.length, pub=R.filter(r=>r.published).length;
  const cards=[
    {v:total,s:'問',l:'一般質問の総数',x:'任期中に行われた全質問'},
    {v:META.seats,s:'名',l:'議員定数',x:'うち議長は質問に立たない慣例'},
    {v:sessions.length,s:'回',l:'対象の定例会',x:periodLabel()},
    {v:pub,s:'問',l:'議会だより掲載',x:'未掲載 '+(total-pub)+'問（〇印なし）'},
  ];
  $('#statcards').innerHTML=cards.map(c=>`<div class="stat"><div class="v num">${c.v}<small>${c.s}</small></div><div class="l">${c.l}</div><div class="x">${c.x}</div></div>`).join('');

  // theme bars（件数の多い順・割合つき）
  const tc=groupCount(R,'theme');
  const max=Math.max(...Object.values(tc));
  const totalQ=R.length;
  const orderedT=TORDER.slice();  // テーマの定義順（件数では並べない）
  $('#themeBars').innerHTML=orderedT.map(t=>{
    const n=tc[t]||0;const pct=totalQ?Math.round(n/totalQ*100):0;
    return `<div class="barrow clickable" data-theme="${t}" title="${t}の質問を見る"><div class="lab">${t}</div><div class="bartrack"><div class="barfill" style="width:${n/max*100}%;background:${TCOLOR[t]}"></div></div><div class="cnt num">${n}</div></div>`;
  }).join('');
  $$('#themeBars .barrow').forEach(el=>el.onclick=()=>openTheme(el.dataset.theme));

  // session timeline（号ラベルはPDFへのリンク）
  const maxS=Math.max(...sessions.map(i=>R.filter(r=>r.issue===i).length));
  $('#sessionTL').innerHTML=sessions.map(i=>{
    const rs=R.filter(r=>r.issue===i);const n=rs.length;const np=rs.filter(r=>!r.published).length;
    const h=n/maxS*130;const ph=np/n*100;
    return `<div class="tlcol"><span class="tlnum num">${n}</span>
      <div class="tlbar" style="height:${h}px" title="${sessLabel(i)}：${n}問（未掲載${np}）"><div class="pub" style="height:${ph}%"></div></div>
      <a class="tlcap" href="${ISSUE[i].bulletin}" target="_blank" rel="noopener" title="第${i}号PDFを開く">第${i}号<br>${sessShort(i)}</a></div>`;
  }).join('');

  // 議会だより 各号
  const fmtPub=s=>{const m=s.split('-');return `${m[0]}.${parseInt(m[1])}`;};
  $('#bulletinList').innerHTML=sessions.map(i=>{
    const it=ISSUE[i];
    return `<a class="bchip" href="${it.bulletin}" target="_blank" rel="noopener">
      <span class="bn">第${i}号</span><span class="bs">${it.session}</span><span class="bd">発行 ${fmtPub(it.pub)}　PDF ↗</span></a>`;
  }).join('');
  $('#bulletinIndexLink').href=DB.meta.bulletin_index;
}

/* ---------- MEMBERS ---------- */
let memberSortMode='seat';
function renderMembers(){
  let list=ROSTER.slice();
  if(memberSortMode==='kaiha'){
    list.sort((a,b)=> (a.kaiha||'').localeCompare(b.kaiha||'','ja') || a.seat-b.seat);
  }else if(memberSortMode==='kana'){
    list.sort((a,b)=> (a.kana||'').localeCompare(b.kana||'','ja') || a.seat-b.seat);
  }else{ // seat（既定・議席番号順）
    list.sort((a,b)=> a.seat-b.seat);
  }
  $('#memberGrid').innerHTML=list.map(info=>{
    const m=info.member;const n=info.count;
    const rs=R.filter(r=>r.member===m);
    const kaiha=(info.kaiha||'').replace('（会派代表）','');
    const isRep=(info.kaiha||'').includes('会派代表');
    if(n===0){
      return `<div class="mcard mcard-zero" data-m="${m}">
        <div class="mh"><div class="mid">${avatar(m,46)}<div><div class="mn">${m} ${roleBadge(m)}</div><div class="mk">${info.kana}・議席番号${info.seat}・${info.terms}期</div></div></div>
        <div class="mtot num" style="color:var(--muted)">0<small> 問</small></div></div>
        <div class="zeronote">${info.note||'一般質問の記録なし'}</div></div>`;
    }
    const tc=groupCount(rs,'theme');
    const segs=TORDER.filter(t=>tc[t]).map(t=>`<i style="width:${tc[t]/n*100}%;background:${TCOLOR[t]}" title="${t} ${tc[t]}"></i>`).join('');
    const top=Object.entries(tc).sort((a,b)=>b[1]-a[1]).slice(0,3)
      .map(([t,c])=>`<span class="chip" style="border-left:3px solid ${TCOLOR[t]}">${t} ${c}</span>`).join('');
    return `<div class="mcard" data-m="${m}">
      <div class="mh"><div class="mid">${avatar(m,46)}<div><div class="mn">${m} ${roleBadge(m)}</div><div class="mk">${info.kana}・議席番号${info.seat}・${info.terms}期</div></div></div>
      <div class="mtot num">${n}<small> 問</small></div></div>
      <div class="kaiha"><span class="kdot"></span>${kaiha}${isRep?'<span class="reptag">代表</span>':''}</div>
      <div class="stack">${segs}</div>
      <div class="chips">${top}</div></div>`;
  }).join('');
  $$('#memberGrid .mcard').forEach(el=>el.onclick=()=>openMember(el.dataset.m));
  $$('#memberSort .sortbtn').forEach(el=>el.classList.toggle('is-on', el.dataset.sort===memberSortMode));
}

/* ---------- THEMES ---------- */
/* ---------- MATRIX ---------- */
function renderMatrix(){
  const TLABEL={'子育て・教育':'子育て・<br>教育','行財政・行政運営':'行財政・<br>行政運営','福祉・健康・医療':'福祉・健康・<br>医療','交通・公共交通':'交通・<br>公共交通','農林業':'農林業','防災・安全':'防災・<br>安全','自治・住民参画':'自治・<br>住民参画','まちづくり・公園・空き家':'まちづくり・<br>公園・空き家','産業・観光・文化財':'産業・観光・<br>文化財','人口・移住定住':'人口・<br>移住定住','環境':'環境'};
  const byTotal=ACTIVE.map(r=>r.member).sort((a,b)=>seatIdx(a)-seatIdx(b));  // 議席番号順
  let maxCell=0;
  byTotal.forEach(m=>TORDER.forEach(t=>{const c=R.filter(r=>r.member===m&&r.theme===t).length;if(c>maxCell)maxCell=c;}));
  const head=`<thead><tr><th style="text-align:right">議員＼テーマ</th>${TORDER.map(t=>`<th class="mxhcol" data-theme="${t}" title="${t}（テーマ別へ）"><span class="mxdot" style="background:${TCOLOR[t]}"></span><br>${TLABEL[t]}</th>`).join('')}<th class="mxtot">計</th></tr></thead>`;
  const rows=byTotal.map(m=>{
    const tot=R.filter(r=>r.member===m).length;
    const cells=TORDER.map(t=>{
      const c=R.filter(r=>r.member===m&&r.theme===t).length;
      if(!c)return `<td></td>`;
      const op=0.25+0.75*(c/maxCell);
      const col=TCOLOR[t];
      return `<td><div class="mxcell mxc-click" data-m="${m}" data-theme="${t}" style="background:${col};opacity:${op}" title="${m}｜${t}：${c}問（一覧で絞り込み）">${c}</div></td>`;
    }).join('');
    return `<tr><th class="mxhrow" data-m="${m}" title="${m}（議員別へ）">${m}</th>${cells}<td class="mxtot num">${tot}</td></tr>`;
  }).join('');
  $('#mxTable').innerHTML=head+'<tbody>'+rows+'</tbody>';
  $$('#mxTable .mxhcol').forEach(el=>el.onclick=()=>openTheme(el.dataset.theme));
  $$('#mxTable .mxhrow').forEach(el=>el.onclick=()=>openMember(el.dataset.m));
  $$('#mxTable .mxc-click').forEach(el=>el.onclick=()=>gotoListFiltered(el.dataset.m,el.dataset.theme));
  $('#mxLegend').innerHTML=TORDER.map(t=>`<span class="lg" data-theme="${t}"><span class="sw" style="background:${TCOLOR[t]}"></span>${t}</span>`).join('');
  $$('#mxLegend .lg').forEach(el=>el.onclick=()=>openTheme(el.dataset.theme));
}

/* ---------- TABLE ---------- */
let sortKey='issue',sortDir=1;
function kaihaShort(m){const i=ROSTER_BY[m]||{};return (i.kaiha||'').replace('（会派代表）','');}
function fillSelects(){
  const ms=members.map(m=>`<option value="${m}">${m}</option>`).join('');
  $('#fMember').insertAdjacentHTML('beforeend',ms);
  const kaihaCount={};ROSTER.forEach(r=>{const k=kaihaShort(r.member);kaihaCount[k]=(kaihaCount[k]||0)+1;});
  const kaihas=[...new Set(members.map(kaihaShort))].sort((a,b)=>a.localeCompare(b,'ja'));
  $('#fKaiha').insertAdjacentHTML('beforeend',kaihas.map(k=>`<option value="${k}">${k}（${kaihaCount[k]}名）</option>`).join(''));
  $('#fTheme').insertAdjacentHTML('beforeend',TORDER.map(t=>`<option value="${t}">${t}</option>`).join(''));
  $('#fSession').insertAdjacentHTML('beforeend',sessions.map(i=>`<option value="${i}">第${i}号 ${sessLabel(i)}</option>`).join(''));
}
function tgPill(t){return `<span class="tg" style="background:${TCOLOR[t]}1A;color:${TCTEXT[t]}"><span class="d" style="background:${TCOLOR[t]}"></span>${t}</span>`;}
function qaDetail(r){
  let inner='';
  if(r.qa){
    const q=r.qa;
    inner+=`<div class="qa-q"><span class="qa-tag tq">問</span><span>${escapeHtml(q.q)}</span></div>`;
    if(q.at){inner+=`<div class="qa-atitle"><span class="qa-tag ta">答</span><span>${escapeHtml(q.at)}</span></div>`;}
    (q.a||[]).forEach(a=>{
      const by=(a[0] && a[0]!=='答弁' && a[0]!=='答')?`<b>${escapeHtml(a[0])}</b>　`:'';
      const tag=q.at?'答弁':'答';
      inner+=`<div class="qa-a"><span class="qa-tag tb">${tag}</span><span>${by}${escapeHtml(a[1])}</span></div>`;
    });
    (q.o||[]).forEach(o=>{
      inner+=`<div class="qa-o"><span class="qa-tag to">他</span><span><b>${escapeHtml(o[0])}</b><br>${escapeHtml(o[1])}</span></div>`;
    });
  }else if(r.published){
    inner+=`<div class="qa-note">この質問の〈問・答〉は順次収録中です。やりとりの全文は会議録でご確認いただけます。</div>`;
  }else{
    inner+=`<div class="qa-note"><b>議会だより本文には未掲載の質問です</b>（3問以上で〇のつかなかったもの）。題名は<b>一般質問一覧表（目次・P.8）</b>に記載されていますが、〈問・答〉の本文はどの本文ページにも掲載されていません。やりとりの全文は会議録・録画でご確認いただけます。</div>`;
  }
  const links=[];
  if(r.bulletin){
    if(r.published)links.push(`<a class="qa-link" href="${r.bulletin}" target="_blank" rel="noopener">議会だより第${r.issue}号（PDF・P.${r.page}）</a>`);
    else links.push(`<a class="qa-link" href="${r.bulletin}" target="_blank" rel="noopener">議会だより第${r.issue}号 一般質問一覧表（PDF・P.8）</a>`);
  }
  if(r.minutes)links.push(`<a class="qa-link" href="${r.minutes}" target="_blank" rel="noopener">会議録で全文を読む</a>`);
  if(r.video)links.push(`<a class="qa-link" href="${r.video}" target="_blank" rel="noopener">録画配信を見る</a>`);
  inner+=`<div class="qa-links">${links.join('')}</div>`;
  if(r.qa){inner+=`<div class="qa-prov">${r.qa.v?'本文は議会だより掲載のまま（原文・改行再現）':'要約（原文への置換を順次実施中）'}</div>`;}
  return inner;
}
function qItemHtml(r,showMember){
  const badge=r.published?'<span class="badge b-pub">掲載</span>':'<span class="badge b-non">未掲載</span>';
  const hasQa=r.qa?(r.qa.v?'<span class="qa-yes">原文</span>':'<span class="qa-sum">要約</span>'):'';
  const head=`<div class="qmeta">${showMember?`<span class="mlink" data-m="${r.member}">${r.member}</span>`:''}${tgPill(r.theme)}${badge}${hasQa}${r.published?`<span class="ss num">P.${r.page}</span>`:`<span class="ss num" title="本文未掲載。一般質問一覧表（目次・P.8）に題名のみ記載">一覧</span>`}</div><div class="qbody">${escapeHtml(r.text)}</div>`;
  return `<div class="qitem">${head}<button class="qexp" type="button">問・答を開く ▾</button><div class="qdetail" hidden>${qaDetail(r)}</div></div>`;
}
function renderTable(){
  const q=$('#q').value.trim();
  const fm=$('#fMember').value,fk=$('#fKaiha').value,ft=$('#fTheme').value,fs=$('#fSession').value,fp=$('#fPub').value;
  let rows=R.filter(r=>{
    if(fm&&r.member!==fm)return false;
    if(fk&&kaihaShort(r.member)!==fk)return false;
    if(ft&&r.theme!==ft)return false;
    if(fs&&r.issue!=fs)return false;
    if(fp!==''&&(r.published?1:0)!=fp)return false;
    if(q&&!(r.text.includes(q)||r.member.includes(q)||r.theme.includes(q)||r.session.includes(q)))return false;
    return true;
  });
  rows.sort((a,b)=>{
    let x=a[sortKey],y=b[sortKey];
    if(sortKey==='member'){x=seatIdx(a.member);y=seatIdx(b.member);}
    if(x<y)return -1*sortDir;if(x>y)return 1*sortDir;
    return (a.order-b.order)||(a.q_num-b.q_num);
  });
  $('#tcount').textContent=rows.length+' 件';
  $('#qbody').innerHTML=rows.map(r=>`<tr>
    <td><b class="num">第${r.issue}号</b><br><span class="pg">${r.session}</span></td>
    <td><span class="mlink mlink-av" data-m="${r.member}">${avatar(r.member,26)}<span>${r.member}</span></span></td>
    <td class="qt-text"><div class="qcellhead">${escapeHtml(r.text)}</div><button class="qexp qexp-t" type="button">問・答 ▾</button><div class="qdetail" hidden>${qaDetail(r)}</div></td>
    <td>${tgPill(r.theme)}</td>
    <td>${r.published?'<span class="badge b-pub">掲載</span>':'<span class="badge b-non">未掲載</span>'}${r.qa?(r.qa.v?'<br><span class="qa-yes" style="margin-top:4px;display:inline-block">原文</span>':'<br><span class="qa-sum" style="margin-top:4px;display:inline-block">要約</span>'):''}</td>
    <td class="pg num">${r.published?'P.'+r.page:'<span title="本文未掲載。一般質問一覧表（目次・P.8）に題名のみ記載">一覧</span>'}</td>
  </tr>`).join('');
  $$('#qbody .mlink').forEach(el=>el.onclick=()=>openMember(el.dataset.m));
}
function escapeHtml(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}

/* ---------- MODALS ---------- */
function openMember(m){
  const info=ROSTER_BY[m]||{};
  const rs=R.filter(r=>r.member===m).sort((a,b)=>a.issue-b.issue||a.q_num-b.q_num);
  const n=rs.length;const pub=rs.filter(r=>r.published).length;
  $('#shTitle').innerHTML=`${m} ${info.role?'<span class="rolebadge rolebadge-lg">'+info.role+'</span>':''}`;
  $('#shKana').innerHTML=`${info.kana}　｜　議席番号${info.seat}・${info.terms}期　｜　${info.kaiha}${info.note?'　｜　'+info.note:''}`;
  $('#shFace').innerHTML=avatar(m,72);
  if(n===0){
    $('#shStats').innerHTML=`<div><b class="num">0</b>一般質問</div>`;
    $('#shBody').innerHTML=`<div class="emptybox">${info.note||'この任期では一般質問の記録がありません。'}${info.role==='議長'?'<br><span style="color:var(--ink-2);font-size:12.5px">議長は議事を主宰する立場のため、慣例として一般質問には立ちません。</span>':''}</div>`;
    openModal();return;
  }
  const tc=groupCount(rs,'theme');const topT=Object.entries(tc).sort((a,b)=>b[1]-a[1])[0];
  $('#shStats').innerHTML=`<div><b class="num">${n}</b>質問数（任期中）</div><div><b class="num">${pub}</b>うち掲載</div><div><b class="num">${Object.keys(tc).length}</b>扱った分野</div>`;
  // テーマ内訳（この議員の質問が、どの分野にどれだけの割合で向けられたか）
  const tbOrder=TORDER.filter(t=>tc[t]).sort((a,b)=>tc[b]-tc[a]||TORDER.indexOf(a)-TORDER.indexOf(b));
  const tbMax=tc[tbOrder[0]];
  let tb=`<div class="tbreak tbreak-m"><div class="tbreak-h">テーマ内訳（${n}件の質問の内訳）</div>`;
  tbOrder.forEach(t=>{const c=tc[t];const pv=Math.round(c/n*100);
    tb+=`<div class="tb-row"><span class="tb-name mtlink" data-theme="${t}" style="color:${TCTEXT[t]}" title="${t}（テーマ別へ）">${t}</span><span class="tb-bar"><i style="width:${c/tbMax*100}%;background:${TCOLOR[t]}"></i></span><span class="tb-c" aria-label="${c}問、全体の約${pv}パーセント"><b class="num">${c}</b><span class="tb-unit">問</span><span class="tb-pct">（${pv}%）</span></span></div>`;});
  tb+=`</div>`;
  let html=tb;let lastIssue=null;
  rs.forEach(r=>{
    if(r.issue!==lastIssue){html+=`<div class="qgrp">第${r.issue}号　${r.session}</div>`;lastIssue=r.issue;}
    html+=qItemHtml(r,false);
  });
  $('#shBody').innerHTML=html;
  $$('#shBody .mtlink').forEach(el=>el.onclick=()=>openTheme(el.dataset.theme));
  openModal();
}
function openTheme(t){
  const rs=R.filter(r=>r.theme===t).sort((a,b)=>a.issue-b.issue);
  const n=rs.length;const mc=groupCount(rs,'member');
  $('#shFace').innerHTML=`<span class="themedot" style="background:${TCOLOR[t]}"></span>`;
  $('#shTitle').textContent=t;$('#shKana').textContent='テーマ別の質問一覧';
  $('#shStats').innerHTML=`<div><b class="num">${n}</b>質問数</div><div><b class="num">${Object.keys(mc).length}</b>取り上げた議員</div>`;
  const mcSorted=Object.entries(mc).sort((a,b)=>seatIdx(a[0])-seatIdx(b[0]));  // 議席番号順
  const maxc=mcSorted[0][1];
  let bd=`<div class="tbreak"><div class="tbreak-h">議員ごとの質問数（このテーマ）</div>`;
  mcSorted.forEach(([m,c])=>{bd+=`<div class="tb-row"><span class="tb-name mlink" data-m="${m}">${m}</span><span class="tb-bar"><i style="width:${c/maxc*100}%;background:${TCOLOR[t]}"></i></span><span class="tb-c" aria-label="${c}問"><b class="num">${c}</b><span class="tb-unit">問</span></span></div>`;});
  bd+=`</div>`;
  let html=bd;let lastIssue=null;
  rs.forEach(r=>{
    if(r.issue!==lastIssue){html+=`<div class="qgrp">第${r.issue}号　${r.session}</div>`;lastIssue=r.issue;}
    html+=qItemHtml(r,true);
  });
  $('#shBody').innerHTML=html;
  $$('#shBody .mlink').forEach(el=>el.onclick=()=>openMember(el.dataset.m));
  openModal();
}
let _lastFocus=null;
function _focusables(c){return $$('a[href],button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex="-1"])',c).filter(el=>el.offsetParent!==null);}
function openModal(){_lastFocus=document.activeElement;const md=$('#modal');md.classList.add('open');document.body.style.overflow='hidden';const sheet=md.querySelector('.sheet');sheet.scrollTop=0;setTimeout(()=>{($('#xbtn')||sheet).focus();},0);}
function closeModal(){const md=$('#modal');if(!md.classList.contains('open'))return;md.classList.remove('open');document.body.style.overflow='';if(_lastFocus&&_lastFocus.focus)_lastFocus.focus();}
// フォーカストラップ：モーダル内でTabを閉じ込める
$('#modal').addEventListener('keydown',e=>{
  if(e.key!=='Tab')return;
  const f=_focusables($('#modal').querySelector('.sheet'));if(!f.length)return;
  const first=f[0],last=f[f.length-1];
  if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
  else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
});
$('#xbtn').onclick=closeModal;
$('#shBody').addEventListener('click',e=>{
  const b=e.target.closest('.qexp');if(!b)return;
  const d=b.nextElementSibling;
  if(d.hasAttribute('hidden')){d.removeAttribute('hidden');b.textContent='問・答を閉じる ▴';b.classList.add('open');}
  else{d.setAttribute('hidden','');b.textContent='問・答を開く ▾';b.classList.remove('open');}
});
$('#modal').onclick=e=>{if(e.target.id==='modal')closeModal();};
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeModal();});

/* ---------- TABS ---------- */
let built={overview:0,members:0,themes:0,matrix:0,table:0};
function show(v){
  $$('.tab').forEach(t=>t.setAttribute('aria-selected',t.dataset.view===v));
  $$('.view').forEach(s=>s.classList.toggle('active',s.id===v));
  if(!built[v]){({overview:renderOverview,members:renderMembers,matrix:renderMatrix,table:()=>{fillSelects();renderTable();}}[v])();built[v]=1;}
  window.scrollTo({top:0,behavior:'smooth'});
}
$$('.tab').forEach(t=>t.onclick=()=>show(t.dataset.view));

// マトリクスのセル→質問一覧を「議員×テーマ」で絞り込み表示
function gotoListFiltered(m,t){
  show('table');                 // 初回は fillSelects+renderTable を実行
  if($('#q')) $('#q').value='';
  if($('#fMember')) $('#fMember').value=m||'';
  if($('#fKaiha')) $('#fKaiha').value='';
  if($('#fTheme')) $('#fTheme').value=t||'';
  if($('#fSession')) $('#fSession').value='';
  if($('#fPub')) $('#fPub').value='';
  renderTable();
}

// 議員別の並び替え
$('#memberSort').addEventListener('click',e=>{
  const b=e.target.closest('.sortbtn');if(!b)return;
  memberSortMode=b.dataset.sort;renderMembers();
});

// table events
['q','fMember','fKaiha','fTheme','fSession','fPub'].forEach(id=>{
  document.addEventListener('input',e=>{if(e.target.id===id)renderTable();});
});
$$('#qtable thead th').forEach(th=>th.onclick=()=>{
  const k=th.dataset.k;if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=1;}renderTable();
});
$('#qbody').addEventListener('click',e=>{
  const b=e.target.closest('.qexp-t');if(!b)return;
  const d=b.nextElementSibling;
  if(d.hasAttribute('hidden')){d.removeAttribute('hidden');b.textContent='問・答を閉じる ▴';b.classList.add('open');}
  else{d.setAttribute('hidden','');b.textContent='問・答 ▾';b.classList.remove('open');}
});

// アクセシビリティ：動的に生成される clickable 要素をキーボード操作可能にする
function _setKbd(el){if(el&&el.setAttribute&&!el.hasAttribute('tabindex')&&!el.matches('button,a,input,select,textarea')){el.setAttribute('tabindex','0');el.setAttribute('role','button');}}
new MutationObserver(ms=>ms.forEach(m=>m.addedNodes.forEach(n=>{if(n.nodeType===1){if(n.matches&&n.matches('.clickable,.mcard'))_setKbd(n);n.querySelectorAll&&n.querySelectorAll('.clickable,.mcard').forEach(_setKbd);}}))).observe(document.body,{childList:true,subtree:true});
document.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){const el=document.activeElement;if(el&&el.matches&&el.matches('.clickable,.mcard')&&!el.matches('button,a,input,select,textarea')){e.preventDefault();el.click();}}});

renderOverview();built.overview=1;
</script>
</body>
</html>
"""

def render(records, meta):
    """records と meta から完成HTML文字列を返す。"""
    # テーマのピル文字用に、各テーマ色を「読める濃さ」まで暗くした文字色を用意する
    # （色＝識別の補助にとどめ、文字のコントラスト 4.5:1 以上を確保）
    def _hex2rgb(h):
        h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    def _lin(c):
        c /= 255; return c/12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4
    def _lum(rgb):
        r, g, b = (_lin(x) for x in rgb); return 0.2126*r+0.7152*g+0.0722*b
    def _contrast(a, b):
        L1, L2 = _lum(a), _lum(b); hi, lo = max(L1, L2), min(L1, L2); return (hi+0.05)/(lo+0.05)
    def _blend(fg, bg, a):
        return tuple(round(fg[i]*a+bg[i]*(1-a)) for i in range(3))
    def _text_color(hexcol):
        rgb = _hex2rgb(hexcol)
        bg = _blend(rgb, (255, 255, 255), 0x1A/255)   # ピル背景＝10%ティント
        k = 1.0
        while k >= 0:
            cand = tuple(round(c*k) for c in rgb)
            if _contrast(cand, bg) >= 4.5:
                return "#%02X%02X%02X" % cand
            k -= 0.04
        return "#231B26"
    theme_text = {t: _text_color(c) for t, c in THEME_COLOR.items()}

    payload = {
        "records": records,
        "meta": meta,
        "themeOrder": THEME_ORDER,
        "themeColor": THEME_COLOR,
        "themeTextColor": theme_text,
        "roster": meta["roster"],
    }
    return HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
