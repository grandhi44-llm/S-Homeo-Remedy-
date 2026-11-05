/* SHC Protocol engine — runs the S Homeo Protocol (Steps 1–11) on the repertory + SHC notes data.
   Works in browser and Node (for tests). Data: meta.json, rep.json, shc.json */
(function (root) {
  'use strict';

  const STOP = new Set(('a an the of to in on for with and or is are was be as at by from very much more less than then patient she he her his they them it its this that these those has have had i my me we our you your also since year years old ago after before during while when ' +
    'feels feel feeling gets get complains complaint complaints history since months month days day week weeks always sometimes often mostly usually generally especially any some all every each one two three ' +
    'cannot can not no without due because then there here but so if into onto over under about which who whom whose what when where how ' +
    'lady woman man boy girl gentleman male female suffering suffers suffer severe mild moderate diagnosed diagnosis diagnostic tools shows shown showed found reports report investigation scan test tests ' +
    'constitution skills skill good bad nature natured person patient type level high low last past present now today known case history').split(/\s+/));
  // words that carry meaning even though they are in STOP for the free-text scan
  const KEEP = new Set(['cold', 'hot', 'weak', 'loss', 'lost', 'left', 'right']);

  // patient wording -> repertory wording (lower-case). Each key expands to itself + alternatives.
  const SYN = {
    craves: ['desire', 'desires'], crave: ['desire', 'desires'], craving: ['desire'], likes: ['desire', 'desires'], like: ['desire'], fond: ['desire'], wants: ['desire'],
    aversion: ['aversion', 'aversions'], dislikes: ['aversion'], dislike: ['aversion'], hates: ['aversion'],
    lemons: ['lemon', 'sour', 'acids', 'acid'], lemon: ['lemons', 'sour', 'acids'], sour: ['acids', 'acid', 'sour things', 'lemons'], pickles: ['sour', 'acids'],
    sweets: ['sweet', 'sweets', 'sugar', 'sweetmeats'], sweet: ['sweets', 'sugar'], chocolate: ['chocolates', 'cocoa'], banana: ['bananas'], bananas: ['banana'],
    spicy: ['spices', 'spice', 'highly seasoned', 'pungent'], salty: ['salt', 'salty things'], salt: ['salty'], meat: ['meats'], fish: ['fish'], eggs: ['egg'], milk: ['milk'],
    coffee: ['coffee'], tea: ['tea'], icecream: ['ice cream', 'ice-cream', 'cold things'], 'ice-cream': ['ice cream', 'cold things'], fruit: ['fruits'], fruits: ['fruit'],
    voice: ['voice', 'aphonia', 'hoarseness', 'larynx', 'vocal'], larynx: ['larynx', 'vocal cords', 'voice'], vocal: ['voice', 'larynx', 'cords'], cords: ['cord', 'vocal cords'], cord: ['cords'],
    nodules: ['nodule', 'nodes', 'polypi', 'polyp', 'growth', 'thickening', 'nodosities'], nodule: ['nodules', 'polypi'], polyp: ['polypi', 'polypus'], polyps: ['polypi', 'polypus'],
    hoarseness: ['hoarse', 'voice'], hoarse: ['hoarseness'], loss: ['lost', 'loss', 'weak'], lost: ['loss', 'lost'],
    overuse: ['overuse of', 'talking', 'speaking', 'singing', 'exertion'], teacher: ['talking', 'speaking', 'public speakers', 'overuse of the voice'], singer: ['singers', 'singing'], speaking: ['talking'],
    motion: ['motion', 'riding', 'carriage', 'car', 'travelling', 'seasickness'], sickness: ['nausea', 'vomiting', 'seasickness'], travel: ['riding', 'travelling', 'carriage'], travelling: ['riding', 'carriage'], car: ['carriage', 'riding'], bus: ['carriage', 'riding'],
    vomiting: ['vomiting', 'vomit'], vomits: ['vomiting'], nausea: ['nausea'],
    extrovert: ['loquacity', 'company desire for', 'cheerful', 'talkative'], extroverted: ['loquacity', 'company desire for', 'talkative'], outgoing: ['company desire for', 'loquacity'], friendly: ['company desire for', 'affectionate'], shy: ['timidity', 'bashful'], timid: ['timidity'], talkative: ['loquacity'], introvert: ['reserved', 'taciturn', 'company aversion to', 'quiet'], worse: ['agg'], cause: ['agg'], causes: ['agg'], causing: ['agg'], triggers: ['agg'], increases: ['agg'], aggravated: ['agg'], aggravation: ['agg'], better: ['amel'], relieved: ['amel'], relief: ['amel'], improves: ['amel'],
    left: ['left'], right: ['right'], side: ['side', 'sided'], sleeps: ['sleep position', 'sleep', 'lying', 'lies'], sleep: ['sleep position', 'sleep'], sleeping: ['sleep position', 'sleep'], lies: ['lying', 'position'],
    abdomen: ['abdomen', 'abdominal', 'stomach'], stomach: ['stomach', 'abdomen'], belly: ['abdomen'], tummy: ['abdomen', 'stomach'],
    drowsiness: ['sleepiness', 'sleepy', 'drowsy'], drowsy: ['sleepiness'], sleepy: ['sleepiness'], sleepiness: ['sleepy', 'drowsiness'],
    chilly: ['cold', 'chilliness', 'heat vital lack of'], cold: ['cold', 'chilly'], hot: ['heat', 'warm'], warm: ['heat', 'warm'], heat: ['heat', 'warm'],
    drinks: ['drinks', 'drink', 'beverages'], drink: ['drinks'], meals: ['eating', 'eating after'], meal: ['eating'], eating: ['eating', 'food'], food: ['food', 'eating'],
    fear: ['fear', 'fears', 'anxiety'], fears: ['fear'], afraid: ['fear'], anxious: ['anxiety'], worry: ['anxiety'], worries: ['anxiety'], tension: ['anxiety'],
    thirst: ['thirst'], thirsty: ['thirst'], thirstless: ['thirstless', 'thirst'], pain: ['pain', 'pains'], pains: ['pain'], ache: ['pain'], aching: ['pain'],
    headache: ['head pain', 'head', 'headache'], migraine: ['head pain', 'migraine', 'headache'], giddiness: ['vertigo'], dizziness: ['vertigo'], dizzy: ['vertigo'],
    constipation: ['constipation', 'stool hard'], constipated: ['constipation'], loose: ['diarrhoea', 'diarrhea'], motions: ['stool', 'diarrhoea'], piles: ['haemorrhoids', 'hemorrhoids', 'piles'],
    gas: ['flatulence', 'flatus'], bloating: ['distension', 'flatulence'], bloated: ['distension'], acidity: ['heartburn', 'eructations sour', 'acidity'], heartburn: ['heartburn'],
    periods: ['menses', 'menstruation'], period: ['menses'], menses: ['menses', 'menstruation'], menstrual: ['menses'], pcod: ['ovaries', 'menses irregular'], pcos: ['ovaries', 'menses irregular'],
    knee: ['knee', 'knees'], knees: ['knee'], joint: ['joints'], joints: ['joint'], legs: ['leg', 'legs', 'lower limbs'], leg: ['legs'], arms: ['arm', 'upper limbs'], back: ['back', 'lumbar'], neck: ['cervical', 'neck'],
    itching: ['itching'], itch: ['itching'], eczema: ['eczema', 'eruptions'], pimples: ['eruptions pimples', 'acne'], acne: ['eruptions pimples', 'acne'], rash: ['eruptions'], warts: ['warts'], wart: ['warts'],
    sweat: ['perspiration'], sweating: ['perspiration'], perspiration: ['perspiration'], sweaty: ['perspiration'], profuse: ['profuse', 'copious'],
    cough: ['cough'], coughing: ['cough'], breathless: ['respiration difficult', 'dyspnoea'], breathlessness: ['respiration difficult'], asthma: ['asthmatic', 'asthma', 'respiration difficult'], wheezing: ['respiration wheezing', 'asthmatic'],
    cold: ['cold', 'coryza', 'chilly'], sneezing: ['sneezing', 'coryza'], nose: ['nose', 'nasal'], blocked: ['obstruction'], block: ['obstruction'],
    sleeplessness: ['sleeplessness', 'insomnia'], insomnia: ['sleeplessness'], dreams: ['dreams'], dream: ['dreams'], snakes: ['snakes', 'snake'],
    anger: ['anger', 'irritability'], angry: ['anger', 'irritability'], irritable: ['irritability'], irritability: ['irritability', 'anger'], sad: ['sadness'], sadness: ['sadness'], weeping: ['weeping'], cries: ['weeping'], crying: ['weeping'],
    forgetful: ['memory weakness', 'forgetful'], memory: ['memory'], weakness: ['weakness', 'weak'], weak: ['weakness', 'weak'], tired: ['weariness', 'weakness'], fatigue: ['weariness', 'weakness'], lethargy: ['weariness'],
    urine: ['urine', 'urination'], urination: ['urination', 'urine'], burning: ['burning'], frequent: ['frequent'], night: ['night'], morning: ['morning'], evening: ['evening'], afternoon: ['afternoon'],
    children: ['children', 'child'], child: ['children'], baby: ['children', 'infants'], obesity: ['obesity', 'fat'], obese: ['obesity', 'fat'], diabetes: ['diabetes', 'urine sugar'], diabetic: ['diabetes'],
    bp: ['hypertension', 'blood pressure'], hypertension: ['hypertension', 'blood pressure high'], thyroid: ['thyroid', 'goitre', 'goiter'], hair: ['hair'], fall: ['falling'], falling: ['falling'], dandruff: ['dandruff'],
    sunlight: ['sun', 'light'], sun: ['sun'], light: ['light'], movement: ['motion'], moving: ['motion'], move: ['motion'], hunger: ['hunger', 'fasting'], hungry: ['hunger', 'fasting'], fasting: ['fasting', 'hunger'],
    exertion: ['exertion'], mental: ['mental'], darkness: ['dark', 'darkness'], dark: ['dark', 'darkness'], pressure: ['pressure'], firm: ['pressure', 'hard'], vomiting: ['vomiting'], throbbing: ['pulsating', 'throbbing', 'beating'], pulsating: ['throbbing'],
    occiput: ['occiput', 'occipital'], 'back': ['back', 'occiput'], temple: ['temples'], temples: ['temple'], forehead: ['forehead', 'frontal'], eye: ['eye', 'eyes'], eyes: ['eye'],
    criticism: ['reproaches', 'criticism', 'reprimands', 'contradiction'], criticised: ['reproaches'], criticized: ['reproaches'], offended: ['offended', 'sensitive'], offence: ['offended'], suppress: ['suppressed'], suppressed: ['suppressed'], suppresses: ['suppressed'],
    consolation: ['consolation', 'consolation agg'], began: ['ailments from'], since: ['ailments from'], after: ['ailments from', 'after'], workplace: ['business', 'work'], office: ['business', 'work'], solitude: ['solitude', 'company aversion', 'alone'], alone: ['alone', 'solitude'], responsible: ['conscientious', 'responsibility'], responsibility: ['conscientious', 'responsibility'], conscientious: ['conscientious'],
    unfinished: ['business', 'duty'], work: ['business', 'work', 'occupation'], upset: ['vexation', 'grief'], stress: ['mental exertion', 'anxiety', 'overwork'], overwork: ['overwork', 'mental exertion'], 'late': ['night'], 'skipped': ['fasting', 'hunger'], 'meals': ['eating', 'eating after'],
    salty: ['salt', 'salty things'], salt: ['salt', 'salty'], water: ['water'], cold: ['cold', 'chilly'], recurrent: ['periodical', 'recurrent', 'chronic'], recurring: ['periodical', 'recurrent'], headaches: ['headache', 'head pain'],
    open: ['open'], air: ['air'], fan: ['air fanned', 'air'], ac: ['cold air', 'air'], bath: ['bathing'], bathing: ['bathing'], covering: ['covering', 'covers'], uncover: ['uncovering'],
  };

  const PHRASES = [[/voice box/g, 'larynx'], [/vocal cords?/g, 'vocal cords'], [/lemon water/g, 'lemons'], [/motion sickness/g, 'nausea riding'], [/travel sickness|car sickness/g, 'nausea riding'],
    [/semi[- ]?abdomen/g, 'abdomen'], [/after (meals?|food|eating)/g, 'eating after'], [/blood pressure/g, 'hypertension'], [/cold constitution|chilly (patient|constitution)/g, 'heat vital lack of'],
    [/hot (patient|constitution)/g, 'warm agg'], [/open air/g, 'air open'], [/left side/g, 'side left'], [/right side/g, 'side right'], [/loss of voice|voice loss/g, 'voice lost'], [/ice[- ]?cream/g, 'ice cream']];
  function normalise(s) { s = ' ' + s.toLowerCase() + ' '; for (const [re, rep] of PHRASES) s = s.replace(re, rep); return s; }
  function words(s) {
    return (normalise(s).replace(/[^a-z0-9+\-\s]/g, ' ').split(/\s+/)).filter(w => w && w.length > 1 && (!STOP.has(w) || KEEP.has(w)) && !/^\d+$/.test(w));
  }
  function stem(w) { return w.length > 4 && w.endsWith('s') ? w.slice(0, -1) : w; }
  function alts(w) {
    const a = new Set([w, stem(w)]);
    if (w.endsWith('ing') && w.length > 5) a.add(w.slice(0, -3));
    (SYN[w] || []).forEach(x => a.add(x));
    return [...a];
  }

  const CH_ALIAS = { 'respiratory system': 'Lungs / Respiration', 'respiration': 'Lungs / Respiration', 'female sexual system': 'Female organs', 'female genitalia/sex': 'Female organs', 'female': 'Female organs', 'menstruation': 'Female organs',
    'male sexual system': 'Male organs', 'male genitalia/sex': 'Male organs', 'male': 'Male organs', 'locomotor system': 'Joints / Limbs', 'limbs': 'Joints / Limbs', 'upper extremities': 'Joints / Limbs', 'lower extremities': 'Joints / Limbs', 'extremities': 'Joints / Limbs',
    'urinary system': 'Kidney / Urinary', 'bladder': 'Kidney / Urinary', 'urine': 'Kidney / Urinary', 'kidneys': 'Kidney / Urinary', 'circulatory system': 'Heart / Circulation', 'circulation': 'Heart / Circulation', 'heart': 'Heart / Circulation',
    'nervous system': 'Mind / Nerves', 'mind': 'Mind / Nerves', 'eye': 'Eyes', 'eyes': 'Eyes', 'vision': 'Eyes', 'ear': 'Ears', 'ears': 'Ears', 'hearing': 'Ears', 'larynx and trachea': 'Larynx / Voice', 'larynx': 'Larynx / Voice', 'voice': 'Larynx / Voice',
    'sweat': 'Fever', 'perspiration': 'Fever', 'fever': 'Fever', 'fevers': 'Fever', 'chill': 'Fever', 'heat and fever in general': 'Fever', 'clinical': 'Generals / Metabolic', 'generals': 'Generals / Metabolic', 'generalities': 'Generals / Metabolic',
    'skin': 'Skin', 'skin and exterior body': 'Skin', 'head': 'Head', 'headaches': 'Head', 'stomach': 'Stomach', 'food': 'Stomach', 'abdomen': 'Liver / Abdomen', 'rectum': 'Rectum / Stool', 'stool': 'Rectum / Stool', 'throat': 'Throat', 'external throat': 'Throat',
    'mouth': 'Mouth / Teeth', 'teeth': 'Mouth / Teeth', 'nose': 'Nose', 'face': 'Face', 'back': 'Back / Spine', 'sleep': 'Sleep', 'dreams': 'Sleep', 'cough': 'Cough', 'expectoration': 'Lungs / Respiration', 'chest': 'Lungs / Respiration', 'vertigo': 'Vertigo' };
  class Engine {
    constructor(meta, rep, shc, rad) {
      this.meta = meta; this.names = meta.names; this.abbr = meta.abbr;
      this.thermal = meta.thermal; this.inimical = meta.inimical; this.organs = meta.organs; this.chToOrgan = meta.ch_to_organ;
      this.chapters = rep.chapters;
      // rubrics: {src:'REP', ch, path, text(lower), rems:[[id,grade]]}
      this.rubrics = rep.rubrics.map(r => ({ src: 'REP', ch: this.chapters[r[0]], path: r[1], text: r[1].toLowerCase(), remsRaw: r[2] }));
      // RadarOpus / SHC FINAL RUBRICS list: [path, patient language, "id id id"] (no grades)
      (rad || []).forEach(r => this.rubrics.push({ src: 'RAD', ch: r[0].split(' - ')[0].split(',')[0].trim(), path: r[0], pl: r[1], text: (r[0] + ' | ' + r[1]).toLowerCase(), remsRaw: r[2] }));
      // SHC rows grouped by rubric text -> pseudo-rubric with remedies from the notes
      const groups = new Map();
      this.shcRows = shc;
      shc.forEach((row, i) => {
        const [rid, sec, rub, pl] = row;
        const key = rub || pl; if (!key) return;
        if (!groups.has(key)) groups.set(key, { src: 'SHC', ch: sec, path: rub || pl, pl: pl, text: (rub + ' | ' + pl).toLowerCase(), rems: new Map(), rows: [] });
        const g = groups.get(key); g.rows.push(i);
        g.rems.set(rid, Math.max(g.rems.get(rid) || 0, 2));
      });
      for (const g of groups.values()) { g.remsArr = [...g.rems.entries()]; this.rubrics.push(g); }
      // word index
      this.index = new Map();
      this.rubrics.forEach((r, i) => {
        const seen = new Set();
        for (const w of r.text.split(/[^a-z0-9]+/)) { if (w.length > 1 && !seen.has(w)) { seen.add(w); if (!this.index.has(w)) this.index.set(w, []); this.index.get(w).push(i); } }
      });
      // SHC rows per remedy
      this.rowsByRem = new Map();
      shc.forEach((row, i) => { if (!this.rowsByRem.has(row[0])) this.rowsByRem.set(row[0], []); this.rowsByRem.get(row[0]).push(i); });
    }
    rems(r) {
      if (r.remsArr) return r.remsArr;
      r.remsArr = r.remsRaw ? r.remsRaw.split(' ').map(t => { const [i, g] = t.split(':'); return [+i, g ? +g : 1]; }) : [];
      return r.remsArr;
    }
    organOf(r) {
      if (r.src === 'REP' || r.src === 'RAD') { const c = r.ch.toLowerCase(); return this.chToOrgan[r.ch] || CH_ALIAS[c] || Object.entries(this.chToOrgan).find(([k]) => k.toLowerCase() === c)?.[1] || null; }
      for (const [o, d] of Object.entries(this.organs)) if (d.sec.includes(r.ch)) return o;
      return null;
    }
    /* ---- Step 2: free text line -> candidate rubrics (rarity-weighted word matching) */
    idf(tok) { const ids = this.index.get(tok); return ids ? Math.log(this.rubrics.length / ids.length) : 0; }
    // rubric ids containing every token of a phrase
    idsFor(phrase) {
      const toks = phrase.split(' ').filter(Boolean);
      let set = null;
      for (const t of toks) {
        let ids = [...(this.index.get(t) || []), ...(this.index.get(t + 's') || []), ...(t.length > 4 && t.endsWith('s') ? (this.index.get(t.slice(0, -1)) || []) : [])];
        if (!ids.length && t.length >= 5) { for (const [k, v] of this.index) if (k.startsWith(t) && k.length <= t.length + 4) ids.push(...v); }
        if (!ids || !ids.length) return new Set();
        const cur = new Set(ids);
        set = set ? new Set([...set].filter(x => cur.has(x))) : cur;
      }
      return set || new Set();
    }
    findRubrics(line, limit = 8) {
      const ws = [...new Set(words(line).map(w => w.replace(/\++/g, '')).filter(Boolean))];
      if (!ws.length) return [];
      const cand = new Map();   // rubric idx -> {w: weight matched, n: words matched}
      let total = 0;
      ws.forEach(w => {
        // weight of this case word = rarity of its best-known form (literal word, else best synonym), capped
        const forms = alts(w).map(a => ({ a, lit: a === w || a === stem(w) }));
        let wt = 0; for (const f of forms) { const t = f.a.split(' ').map(x => this.idf(x)).filter(Boolean); if (t.length) wt = Math.max(wt, Math.max(...t)); }
        if (!wt) return;                       // unknown word: ignored
        wt = Math.min(wt, 7); total += wt;
        const best = new Map();
        for (const f of forms) { const fac = f.a.includes(' ') ? 1.1 : (f.lit ? 1 : 0.8); for (const i of this.idsFor(f.a)) best.set(i, Math.max(best.get(i) || 0, wt * fac)); }
        best.forEach((v, i) => { const e = cand.get(i) || { w: 0, n: 0 }; e.w += v; e.n++; cand.set(i, e); });
      });
      if (!total) return [];
      const out = [];
      for (const [i, e] of cand) {
        const frac = e.w / total; if (frac < 0.45) continue;
        const r = this.rubrics[i]; const nrem = this.rems(r).length; if (!nrem) continue;
        const ptoks = r.path.toLowerCase().split(/[^a-z]+/).filter(x => x.length > 2 && !['and', 'the', 'agg', 'amel', 'with', 'from', 'etc', 'during', 'after', 'before'].includes(x));
        const prec = e.n / Math.max(ptoks.length, 1);
        let score = frac * 2 + prec * 0.4;
        if (nrem === 1) score -= 0.25; else if (nrem === 2) score -= 0.12; if (nrem > 150) score -= 0.08; if (r.src === 'SHC') score += 0.05; if (r.src === 'RAD') score += 0.08;
        out.push({ i, n: e.n, frac, score, nrem });
      }
      out.sort((a, b) => b.score - a.score);
      return out.slice(0, limit).map(o => Object.assign(o, { r: this.rubrics[o.i], label: (this.rubrics[o.i].src === 'REP' ? '' : this.rubrics[o.i].src === 'RAD' ? 'RadarOpus list: ' : 'SHC notes: ') + this.rubrics[o.i].path }));
    }
    // default tick marks: keynote -> best repertory rubric (+ SHC notes rubrics close to it); others -> top 3 within 0.25 of best
    defaultSelect(cands, isKeynote) {
      if (!cands.length) return [];
      const best = cands[0];
      const bestOf = src => cands.find(c => c.r.src === src && c.score >= best.score - (isKeynote ? 0.3 : 0.35));
      const picks = new Set();
      if (isKeynote) {
        // keynote: prefer real rubrics (3+ remedies); best of each repertory layer (Kent-derived + RadarOpus list) plus a close SHC-notes rubric
        const adj = c => c.score + (c.nrem >= 3 ? 0.3 : 0);
        const top = cands.reduce((a, c) => adj(c) > adj(a) ? c : a, cands[0]);
        const bestAdj = src => cands.filter(c => c.r.src === src && adj(c) >= adj(top) - 0.3 && c.frac >= top.frac - 0.1).sort((a, b) => adj(b) - adj(a))[0];
        [bestAdj('RAD'), bestAdj('REP'), bestAdj('SHC')].forEach(c => { if (c) picks.add(c); });
        if (!picks.size) picks.add(top);
      } else {
        // other symptoms: the best match overall, plus the best full-repertory rubric (Kent-derived), the best RadarOpus rubric with 3+ remedies
        // and the best SHC-notes rubric, when each matches the words about as well as the best one
        picks.add(best);
        const close = c => c.frac >= best.frac - 0.1;
        const rep = cands.filter(c => c.r.src === 'REP' && close(c)).sort((a, b) => b.nrem - a.nrem)[0]; if (rep) picks.add(rep);
        const rad = cands.filter(c => c.r.src === 'RAD' && c.nrem >= 3 && close(c))[0]; if (rad) picks.add(rad);
        const shc = cands.filter(c => c.r.src === 'SHC' && close(c))[0]; if (shc) picks.add(shc);
      }
      return cands.filter(c => picks.has(c));
    }
    parseCase(text) {
      const SPLIT = /\n|;|\.\s+(?=[A-Z])|\s+but\s+|\s+also\s+|\s+whereas\s+/;
      let lines = text.split(SPLIT).map(s => s.trim()).filter(s => s.length > 1);
      let key = lines.findIndex(l => /\+\+\+|pqrs|keynote/i.test(l)); if (key < 0) key = 0;
      const topic = (() => { const m = lines[key].toLowerCase().match(/\b(headaches?|head pains?|migraines?|cough|pains?|eczema|itching|asthma|diarrh\w+|constipation|vertigo|fever|vomiting|nausea|acidity|piles|insomnia|palpitation|hoarseness|voice|menses|periods?)\b/); return m ? m[1].replace(/s$/, '') : ''; })();
      // verb cue inside a clause, e.g. "worsen from", "desires", "dislikes" -> normalised repertory wording, carried into the following short clauses
      const CUE = /\b(desires?|craves?|craving for|likes?|wants?|dislikes?|aversion to|averse to|hates?|cannot (?:tolerate|bear)|worse(?: from| in| by| with| after| during| on)?|worsens?(?: from| in| by| with| after| during| on)?|aggravated(?: by| from)?|better(?: from| in| by| with| after| during| on)?|improves?(?: in| with| after| by| from| on)?|relieved(?: by| from)?|ameliorated(?: by)?|fear of|afraid of|anxious about|sensitive to|prefers?)\b/i;
      const norm = c => { c = c.toLowerCase(); if (/^(worse|worsen|aggravated)/.test(c)) return 'agg'; if (/^(better|improve|relieved|ameliorated)/.test(c)) return 'amel'; if (/^(desire|crave|craving|like|want)/.test(c)) return 'desire'; if (/^(dislike|aversion|averse|hate|cannot)/.test(c)) return 'aversion'; if (/^(fear|afraid)/.test(c)) return 'fear'; if (/^anxious/.test(c)) return 'anxiety'; if (/^prefer/.test(c)) return 'desire'; return c; };
      const out = []; let newKey = -1;
      lines.forEach((line, li) => {
        const isKey = li === key;
        let l = line.replace(/\(?pqrs\)?/ig, '').replace(/\+{2,}/g, '').replace(/keynote:?/ig, '').trim();
        l = l.replace(/^(they|it|these|this)\s+(worsen|worsens|improve|improves|are worse|are better|get worse|get better)/i, (m, p, v) => (topic || 'complaints') + ' ' + v);
        const nWords = l.split(/\s+/).length;
        if (isKey || nWords <= 7) { if (isKey) newKey = out.length; out.push(l); return; }
        // long sentence: split into clauses, carry the verb cue (and the subject, e.g. headache) into the short clauses that follow
        const parts = l.split(/,|\s+and\s+(?=[a-z])/i).map(p => p.trim()).filter(p => p.length > 1);
        let cue = '';
        parts.forEach((p, pi) => {
          const m = p.match(CUE);
          if (m) { const subj = /^(headache|head pain|migraine|cough|pain|complaints)/i.test(p) ? p.split(/\s+/)[0] + ' ' : ''; cue = subj + norm(m[1]); out.push(p.replace(m[0], norm(m[1]))); }
          else if (cue && pi > 0 && p.split(/\s+/).length <= 3) out.push(cue + ' ' + p);
          else out.push(p);
        });
      });
      return { lines: out.map(x => x.replace(/^(and|with|also)\s+/i, '').trim()).filter(x => x.length > 1), keynote: Math.max(newKey, 0) };
    }
    thermalOf(id) { const t = this.thermal[id]; return t ? t[0] : null; }
    isInimical(a, b) { return (this.inimical[a] || []).includes(b); }
    /* ---- Steps 3–11. symptoms: [{text, rubrics:[rubricIdx], keynote:bool}], thermal: 'Hot'|'Chilly'|'Ignore' */
    analyse(symptoms, thermal) {
      const key = symptoms.find(s => s.keynote); const others = symptoms.filter(s => !s.keynote && s.rubrics.length);
      const log = [];
      if (!key || !key.rubrics.length) return { error: 'No keynote rubric selected.' };
      // Step 3-4 keynote remedies
      const kn = new Map(); // id -> {strikes, grade}
      key.rubrics.forEach(ri => this.rems(this.rubrics[ri]).forEach(([id, g]) => { const e = kn.get(id) || { strikes: 0, grade: 0 }; e.strikes++; e.grade += g; kn.set(id, e); }));
      let ranked = [...kn.entries()].map(([id, e]) => ({ id, name: this.names[id], kStrikes: e.strikes, kGrade: e.grade })).sort((a, b) => b.kStrikes - a.kStrikes || b.kGrade - a.kGrade);
      log.push({ step: '3–4 Keynote remedies', text: `${ranked.length} remedies in the keynote rubric(s)`, list: ranked.map(r => `${r.name} (${r.kStrikes}${r.kGrade ? ', grade ' + r.kGrade : ''})`) });
      // Step 5 thermal
      const removedTh = [];
      if (thermal === 'Hot' || thermal === 'Chilly') {
        const opp = thermal === 'Hot' ? 'C' : 'H';
        ranked = ranked.filter(r => { const t = this.thermalOf(r.id); if (t === opp) { removedTh.push(`${r.name} (${t === 'H' ? 'hot' : 'chilly'} remedy, ${this.thermal[r.id][2]})`); return false; } return true; });
        log.push({ step: '5 Thermal filter (' + thermal + ' patient)', text: removedTh.length ? 'Removed ' + removedTh.length + ' opposite-thermal remedies' : 'Nothing removed', list: removedTh });
      } else log.push({ step: '5 Thermal filter', text: 'Skipped (Ignore thermals)', list: [] });
      // Step 6 top of balance list
      log.push({ step: '6 Balance list', text: ranked.length + ' remedies, high to low', list: ranked.slice(0, 15).map(r => r.name) });
      // Step 7 recheck with remaining rubrics
      ranked.forEach(r => { r.strikes = 0; r.grade = 0; r.matched = []; });
      const byId = new Map(ranked.map(r => [r.id, r]));
      others.forEach(s => {
        const hit = new Map();
        s.rubrics.forEach(ri => this.rems(this.rubrics[ri]).forEach(([id, g]) => { if (byId.has(id)) hit.set(id, Math.max(hit.get(id) || 0, g)); }));
        hit.forEach((g, id) => { const r = byId.get(id); r.strikes++; r.grade += g; r.matched.push(s.text); });
      });
      ranked.sort((a, b) => b.strikes - a.strikes || b.grade - a.grade || b.kStrikes - a.kStrikes || b.kGrade - a.kGrade);
      log.push({ step: '7 Recheck with remaining rubrics', text: `${others.length} other symptoms checked`, list: ranked.slice(0, 20).map(r => `${r.name} — ${r.strikes} strike${r.strikes === 1 ? '' : 's'}${r.grade ? ' (grades ' + r.grade + ')' : ''}`) });
      // Step 8 simillimum
      const simil = ranked[0];
      log.push({ step: '8 Simillimum', text: simil.name + ' — ' + simil.strikes + ' strikes', list: simil.matched });
      // Step 9 inimical
      const removedIn = [];
      let balance = ranked.filter(r => { if (r.id !== simil.id && this.isInimical(simil.id, r.id)) { removedIn.push(r.name); return false; } return true; });
      const ev = (this.meta.inimical_evidence || []).filter(e => (e[0] === simil.id || e[1] === simil.id)).map(e => `${this.names[e[0]]} – ${this.names[e[1]]} (${e[2]})`);
      log.push({ step: '9 Inimical check', text: removedIn.length ? 'Removed: ' + removedIn.join(', ') : 'No inimicals of ' + simil.name + ' in the balance list', list: ev });
      // Step 10 organ remedy — rule (b)
      // organ of the keynote: organ words in the keynote text + selected rubric paths, chapter mapping as fallback
      const organCount = new Map();
      const ktext = (key.text + ' ' + key.rubrics.map(ri => this.rubrics[ri].path).join(' ')).toLowerCase();
      for (const [o, d] of Object.entries(this.organs)) {
        let n = 0;
        d.w.forEach(w => { const re = new RegExp('\\b' + w.replace(/[^a-z ]/g, '') + (w.length > 5 ? '' : '\\b'), 'g'); const c = (ktext.match(re) || []).length; if (c) n += Math.min(c, 4); });
        if (n) organCount.set(o, n);
      }
      key.rubrics.forEach(ri => { const o = this.organOf(this.rubrics[ri]); if (o) organCount.set(o, (organCount.get(o) || 0) + 3); });
      const organ = [...organCount.entries()].sort((a, b) => b[1] - a[1]).map(e => e[0])[0] || null;
      let organRem = null, organEv = [], organRule = '';
      if (organ) {
        const od = this.organs[organ]; const kw = words(key.text).map(stem);
        const cands = balance.filter(r => r.id !== simil.id);
        const score = (r, requireOrganopathy) => {
          const rows = (this.rowsByRem.get(r.id) || []).map(i => this.shcRows[i]);
          const ev = [];
          for (const row of rows) {
            const t = (row[2] + ' | ' + row[3] + ' | ' + row[4]).toLowerCase();
            const isOrg = /organopath/i.test(row[2]) || /organopath/i.test(row[6] || '') || /as organopath|organ remedy|organopathic/.test((row[3] + ' ' + row[4]).toLowerCase());
            const inOrgan = od.w.some(w => t.includes(w)) || (!requireOrganopathy && od.sec.includes(row[1]));
            if (!inOrgan) continue;
            if (requireOrganopathy && !isOrg) continue;
            const kwHit = kw.some(k => k.length > 3 && t.includes(k));
            if (!requireOrganopathy && !kwHit) continue;
            ev.push({ s: 1 + (isOrg ? 1 : 0) + (kwHit ? 2 : 0), row });
          }
          return ev;
        };
        let best = null;
        for (const [rule, req] of [['organ remedy named in SHC organopathy notes', true], ['organ-section rows containing the keynote words', false]]) {
          for (const c of cands) {
            const ev = score(c, req); if (!ev.length) continue;
            const s = ev.reduce((a, e) => a + e.s, 0);
            // preference agreed with SHC: fewest Step-7 strikes first (organ-specific rather than constitutional), then strongest organ evidence
            if (!best || c.strikes < best.c.strikes || (c.strikes === best.c.strikes && s > best.s)) best = { s, c, ev, rule };
          }
          if (best) break;
        }
        if (best) { organRem = best.c; organRule = best.rule + ' · fewest Step-7 strikes (' + best.c.strikes + ')'; organEv = best.ev.sort((a, b) => b.s - a.s).slice(0, 4).map(e => (e.row[2] || '') + (e.row[3] ? ' — ' + e.row[3] : '') + ' [' + e.row[5] + ']'); }
      }
      log.push({ step: '10 Organ remedy', text: organ ? (organRem ? `${organRem.name} — organ: ${organ} (${organRule})` : `No organ remedy found for ${organ} in the balance list`) : 'Keynote organ not identified', list: organEv });
      return { keynote: key.text, organ, simil, organRem, organRule, organEv, ranked, balance, removedTh, removedIn, log, thermal };
    }
  }
  root.SHCEngine = { Engine, words };
})(typeof module !== 'undefined' ? module.exports : window);
