// 質問数で議員を序列化していないことを、実ブラウザで確かめる（docs/EDITORIAL_POLICY.md 1。hino-portal DESIGN.md 9.1）。
//   PLAYWRIGHT_MODULE=<playwright の index.mjs> node scripts/check_editorial.mjs [docs/index.html]
// 確かめること：
//   1. 議員別の並び替えのボタンが、議席番号順・会派別・五十音順だけであること（質問数による並びが無い）
//   2. 議員別のカードの既定の並びが、議席番号順であること
//   3. 議員×テーマの表の行の並びが、議席番号順であること
//   4. ページの文に「ランキング」の字が無いこと
// 終了コード：問題が無ければ 0、あれば 1。
import path from 'node:path';
const mod = process.env.PLAYWRIGHT_MODULE || 'playwright';
const { chromium } = await import(mod);
const file = path.resolve(process.argv[2] || 'docs/index.html');
const b = await chromium.launch();
const p = await b.newPage();
const errs = [];
p.on('pageerror', e => errs.push(e.message));
await p.goto('file://' + file);
await p.waitForTimeout(800);
const r = await p.evaluate(() => {
  renderMembers(); renderMatrix();   // 画面を開いたときと同じ既定の並び（memberSortMode は seat）で描く
  const seat = ROSTER.slice().sort((a, b) => a.seat - b.seat).map(x => x.member);
  const sorts = [...document.querySelectorAll('#memberSort [data-sort]')].map(x => x.dataset.sort);
  const cards = [...document.querySelectorAll('#memberGrid [data-m]')].map(x => x.dataset.m);
  const mx = [...document.querySelectorAll('#mxTable .mxhrow')].map(x => x.dataset.m);
  const inSeatOrder = list => { const idx = list.map(m => seat.indexOf(m)); return idx.every((v, i) => i === 0 || v > idx[i - 1]); };
  return { sorts, cardsOk: cards.length > 0 && inSeatOrder(cards), nCards: cards.length,
           mxOk: mx.length > 0 && inSeatOrder(mx), nMx: mx.length, ranking: document.body.innerText.includes('ランキング') };
});
await b.close();
const bad = [];
if (errs.length) bad.push('ページの JavaScript のエラー：' + errs.join(' / '));
const extra = r.sorts.filter(s => !['seat', 'kaiha', 'kana'].includes(s));
if (extra.length) bad.push('議員別の並び替えに、議席番号順・会派別・五十音順以外のものがある：' + extra.join('、'));
if (!r.cardsOk) bad.push(`議員別のカード（${r.nCards}枚）の既定の並びが議席番号順でない`);
if (!r.mxOk) bad.push(`議員×テーマの表の行（${r.nMx}行）の並びが議席番号順でない`);
if (r.ranking) bad.push('ページの文に「ランキング」がある');
if (bad.length) { console.log(`${file}：問題 ${bad.length} 件`); bad.forEach(x => console.log('  - ' + x)); process.exit(1); }
console.log(`OK  ${file}（並び替え ${r.sorts.join('・')}、カード ${r.nCards}枚と表の行 ${r.nMx}行が議席番号順、「ランキング」なし）`);
