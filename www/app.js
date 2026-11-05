/* SHC Remedy Finder — UI */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  let eng = null, symptoms = [], parsed = null;
  function toast(msg) { let t = $('toast'); if (!t) { t = document.createElement('div'); t.id = 'toast'; t.style.cssText = 'position:fixed;left:50%;bottom:90px;transform:translateX(-50%);background:#1f2a26;color:#fff;padding:10px 16px;border-radius:10px;font-size:14px;z-index:20;max-width:90%;text-align:center'; document.body.appendChild(t); } t.textContent = msg; t.style.display = 'block'; clearTimeout(t._h); t._h = setTimeout(() => t.style.display = 'none', 3000); }

  const EXAMPLE = `Nodules on the vocal cords, voice lost ++++
Hoarse voice from overuse, teacher
Craves sour drinks and lemons
Aversion to banana
Desires bitter chocolate
Extrovert
Motion sickness
Sleeps on the left side
Sleeps on abdomen
Desires sweets after meals
Sweets cause drowsiness`;

  /* ---------- loading ---------- */
  async function fetchJSON(url, frac, label) {
    $('ptxt').textContent = label;
    const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status);
    const j = await r.json(); $('pbar').style.width = (frac * 100) + '%'; return j;
  }
  async function init() {
    try {
      const meta = await fetchJSON('data/meta.json', 0.1, 'remedies, thermal and relationship tables');
      const shc = await fetchJSON('data/shc.json', 0.4, 'SHC notes database');
      const rep = await fetchJSON('data/rep.json', 0.6, 'repertory (74,000 rubrics)');
      const rad = await fetchJSON('data/rad.json', 0.92, 'RadarOpus rubric list (105,000 rubrics)');
      $('ptxt').textContent = 'indexing…';
      await new Promise(r => setTimeout(r, 30));
      eng = new SHCEngine.Engine(meta, rep, shc, rad);
      $('pbar').style.width = '100%';
      $('load').classList.add('hide'); show(1);
      const saved = localStorage.getItem('shc_case'); if (saved) $('case').value = saved;
      const th = localStorage.getItem('shc_thermal'); if (th) $('thermal').value = th;
    } catch (e) { $('load').innerHTML = '<b>Could not load the database.</b><br>' + esc(e.message) + '<br><small>If you opened this file directly, serve it over http (or install the app).</small>'; }
  }
  function show(n) { [1, 2, 3].forEach(i => { $('s' + i).classList.toggle('hide', i !== n); $('st' + i).classList.toggle('on', i === n); }); window.scrollTo(0, 0); }

  /* ---------- screen 1 -> 2 ---------- */
  $('example').onclick = () => { $('case').value = EXAMPLE; $('thermal').value = 'Chilly'; };
  $('go1').onclick = () => {
    const text = $('case').value.trim();
    if (text.length < 3) { toast('Please enter the symptoms first.'); return; }
    try { localStorage.setItem('shc_case', text); localStorage.setItem('shc_thermal', $('thermal').value); } catch (e) { }
    parsed = eng.parseCase(text);
    symptoms = parsed.lines.map((l, i) => {
      const cands = eng.findRubrics(l, 8);
      const sel = new Set(eng.defaultSelect(cands, i === parsed.keynote).map(c => c.i));
      return { text: l, cands, sel, keynote: i === parsed.keynote };
    });
    renderSymptoms(); show(2);
  };
  function optHTML(c, sel) {
    const r = c.r, isShc = r.src === 'SHC';
    return `<label class="opt"><input type="checkbox" data-i="${c.i}" ${sel ? 'checked' : ''}>
      <span class="path">${isShc ? '<small>SHC notes</small>' : r.src === 'RAD' ? `<small>RadarOpus list · ${esc(r.ch)}</small>` : `<small>${esc(r.ch)}</small>`}${esc(isShc || r.src === 'RAD' ? r.path : r.path.replace(/^[^-]+ - /, ''))}${r.src === 'RAD' && r.pl ? `<small>“${esc(r.pl)}”</small>` : ''}${isShc && r.pl && r.pl !== r.path ? `<small>“${esc(r.pl)}”</small>` : ''}</span>
      <span class="n ${isShc ? 'shc' : r.src === 'RAD' ? 'rad' : ''}">${c.nrem} rem</span></label>`;
  }
  function renderSymptoms() {
    $('symlist').innerHTML = symptoms.map((s, si) => `
      <div class="card sym ${s.keynote ? 'key' : ''}" data-si="${si}">
        <h3>${s.keynote ? '<span class="kbadge">KEYNOTE</span>' : ''}<span>${esc(s.text)}</span></h3>
        <div class="keyrow">${s.keynote ? 'Keynote (PQRS) symptom' : `<button class="btn sm sec" data-key="${si}">Make keynote</button>`}</div>
        <div class="opts">${s.cands.length ? s.cands.map(c => optHTML(c, s.sel.has(c.i))).join('') : '<div class="none">No matching rubric found — try other words below, or leave it (it will be ignored).</div>'}</div>
        <div class="search"><input type="text" placeholder="Search rubric words (e.g. larynx voice lost)" data-q="${si}"><button class="btn sm" data-sq="${si}">Add</button></div>
      </div>`).join('');
    $('symlist').querySelectorAll('input[type=checkbox]').forEach(cb => cb.onchange = e => {
      const s = symptoms[+e.target.closest('.sym').dataset.si]; const i = +e.target.dataset.i;
      e.target.checked ? s.sel.add(i) : s.sel.delete(i);
    });
    $('symlist').querySelectorAll('[data-key]').forEach(b => b.onclick = () => {
      symptoms.forEach((s, i) => { s.keynote = i === +b.dataset.key; s.sel = new Set(eng.defaultSelect(s.cands, s.keynote).map(c => c.i)); });
      renderSymptoms();
    });
    const doSearch = si => {
      const inp = $('symlist').querySelector(`input[data-q="${si}"]`); const q = inp.value.trim(); if (!q) return;
      const s = symptoms[si]; const found = eng.findRubrics(q, 10).filter(c => !s.cands.some(x => x.i === c.i));
      if (!found.length) { inp.value = ''; inp.placeholder = 'Nothing found for “' + q + '” — try other words'; return; }
      found.forEach(c => { s.cands.push(c); });
      if (found[0]) s.sel.add(found[0].i);
      renderSymptoms();
    };
    $('symlist').querySelectorAll('[data-sq]').forEach(b => b.onclick = () => doSearch(+b.dataset.sq));
    $('symlist').querySelectorAll('input[data-q]').forEach(inp => inp.onkeydown = e => { if (e.key === 'Enter') doSearch(+inp.dataset.q); });
  }
  $('back2').onclick = () => show(1);

  /* ---------- screen 2 -> 3 ---------- */
  $('go2').onclick = () => {
    const input = symptoms.map(s => ({ text: s.text, rubrics: [...s.sel], keynote: s.keynote }));
    const key = input.find(s => s.keynote);
    if (!key || !key.rubrics.length) { toast('Tick at least one rubric for the keynote symptom.'); return; }
    const res = eng.analyse(input, $('thermal').value);
    if (res.error) { toast(res.error); return; }
    renderResult(res); show(3);
  };
  function renderResult(r) {
    const sim = r.simil, org = r.organRem;
    const top = r.ranked.slice(0, 12);
    $('result').innerHTML = `
      <div class="card res sim"><div class="t">Simillimum</div><div class="name">${esc(sim.name)}</div>
        <div class="why">${sim.strikes} strike${sim.strikes === 1 ? '' : 's'} on the other symptoms · in keynote rubric${sim.kStrikes > 1 ? 's ×' + sim.kStrikes : ''}${sim.kGrade ? ' (grade ' + sim.kGrade + ')' : ''}</div>
        ${sim.matched.length ? '<ul>' + sim.matched.map(m => '<li>' + esc(m) + '</li>').join('') + '</ul>' : ''}</div>
      ${org ? `<div class="card res org"><div class="t">Organ remedy · ${esc(r.organ)}</div><div class="name">${esc(org.name)}</div>
        <div class="why">${esc(r.organRule)}</div><ul>${r.organEv.slice(0, 3).map(e => '<li>' + esc(e) + '</li>').join('')}</ul></div>`
        : `<div class="card res none"><div class="t">Organ remedy</div><div class="name">None found</div><div class="why">${r.organ ? 'No remedy in the balance list has organ affinity for ' + esc(r.organ) + ' in the database.' : 'The organ of the keynote symptom could not be identified.'}</div></div>`}
      <div class="card"><div class="rx">Prescription: ${esc(sim.name)}${org ? ' + ' + esc(org.name) : ''}</div>
        <div class="hint">Keynote: ${esc(r.keynote)} · Thermal: ${esc(r.thermal === 'Ignore' ? 'ignored' : r.thermal + ' patient')}</div></div>
      <div class="card">
        <details open><summary>Ranking after recheck (Step 7)</summary>
          <table class="tbl"><tr><th>#</th><th>Remedy</th><th>Strikes</th><th>Grades</th><th>Keynote</th></tr>
          ${top.map((x, i) => `<tr><td>${i + 1}</td><td>${esc(x.name)}${r.removedIn.includes(x.name) ? ' <small style="color:#b3261e">(inimical – removed)</small>' : ''}</td><td>${x.strikes}</td><td>${x.grade}</td><td>${x.kStrikes}${x.kGrade ? ' / g' + x.kGrade : ''}</td></tr>`).join('')}</table>
          ${r.ranked.length > 12 ? `<div class="hint">${r.ranked.length - 12} more remedies with lower strikes.</div>` : ''}
        </details>
        ${r.log.map(l => `<details><summary>Step ${esc(l.step)}</summary><div class="d">${esc(l.text)}</div>${l.list.length ? '<ul>' + l.list.slice(0, 40).map(x => '<li>' + esc(x) + '</li>').join('') + (l.list.length > 40 ? '<li>…</li>' : '') + '</ul>' : ''}</details>`).join('')}
      </div>
      <div class="foot">Result follows the S Homeo Protocol (Steps 3–11) on the selected rubrics. Repertory: Repertorium Publicum (GPL v3). Relationships: Clarke, Allen's Keynotes, SHC notes.</div>`;
  }
  $('back3').onclick = () => show(2);
  $('new3').onclick = () => { $('case').value = ''; show(1); };

  init();
})();
