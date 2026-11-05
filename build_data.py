"""Build the SHC Protocol app data files.
Inputs : in/rubrics.xlsx (Srinivas's combined notes DB), Repertorium Publicum JSON (GPL v3), Clarke + Allen Keynotes (public domain)
Outputs: app/www/data/*.json
"""
import json, re, glob, collections, openpyxl, os, sys

REPO = '/home/claude/drsamonline/homoeopathic-materia-medica-repertory-json'
PUB = REPO + '/repertory/repertorium-publicum-2008'
OUT = '/home/claude/app/www/data'
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- 1. Publicum repertory
idx = json.load(open(PUB + '/index.json'))
rem_index = idx['remedy_index']                      # abbrev -> {name}
abbr_list = sorted(rem_index.keys())
abbr_id = {a: i for i, a in enumerate(abbr_list)}
canon = [rem_index[a]['name'] for a in abbr_list]    # canonical name per id

def norm_abbr(a):
    return a.rstrip('.').lower()

rubrics = []          # [chapter_id, path, "id:grade id:grade ..."]
chapters = []
all_rub = {}          # id -> rubric (for parent resolution across split files)
files_by_ch = collections.defaultdict(list)
for f in sorted(glob.glob(PUB + '/*.json')):
    if f.endswith('index.json'): continue
    d = json.load(open(f))
    sec = d['section']
    title = re.sub(r'\s*\((part )?\d+( of \d+)?\)$', '', sec['title']).strip()
    base = re.sub(r'-\d+\.json$', '.json', os.path.basename(f))
    files_by_ch[base].append((title, sec['rubrics']))
for base, parts in files_by_ch.items():
    title = parts[0][0]
    ch_id = len(chapters); chapters.append(title)
    byid = {}
    for _, rl in parts:
        for r in rl: byid[r['id']] = r
    def path(r):
        p = []
        seen = set()
        while r and r['id'] not in seen:
            seen.add(r['id']); p.append(r['text'].strip()); r = byid.get(r.get('parent'))
        return ' - '.join(reversed(p))
    for _, rl in parts:
        for r in rl:
            if not r['remedies']: continue
            rems = ' '.join(f"{abbr_id[x['abbrev']]}:{x['grade'] or 1}" for x in r['remedies'] if x['abbrev'] in abbr_id)
            rubrics.append([ch_id, path(r), rems])
print('chapters', len(chapters), 'rubrics', len(rubrics), 'remedies', len(abbr_list))

# ---------------------------------------------------------------- 2. SHC notes database
wb = openpyxl.load_workbook('/home/claude/in/rubrics.xlsx', read_only=True, data_only=True)
ws = wb['All Symptoms']; rows = list(ws.iter_rows(values_only=True)); hdr = rows[0]
ix = {h: i for i, h in enumerate(hdr)}

# remedy name -> publicum id
name_to_id = {}
for i, n in enumerate(canon):
    name_to_id[n.lower()] = i
    name_to_id[norm_abbr(abbr_list[i])] = i
ALIAS = {  # SHC standard name -> Publicum canonical (where spelling differs)
    'cinchona officinalis': 'china officinalis', 'artemisia abrotanum': 'abrotanum',
    'bryonia alba': 'bryonia', 'carboneum animalis': 'carbo animalis', 'mercurius solubilis': 'mercurius',
    'natrum muriaticum': 'natrium muriaticum', 'natrum sulphuricum': 'natrium sulphuricum',
    'natrum carbonicum': 'natrium carbonicum', 'natrum phosphoricum': 'natrium phosphoricum',
    'kali carbonicum': 'kalium carbonicum', 'kali bichromicum': 'kalium bichromicum',
    'kali phosphoricum': 'kalium phosphoricum', 'kali iodatum': 'kalium iodatum', 'kali sulphuricum': 'kalium sulphuricum',
    'kali muriaticum': 'kalium muriaticum', 'kali bromatum': 'kalium bromatum', 'kali arsenicosum': 'kalium arsenicosum',
    'kali nitricum': 'kalium nitricum', 'kali chloricum': 'kalium chloricum', 'kali cyanatum': 'kalium cyanatum',
    'acidum nitricum': 'nitricum acidum', 'acidum phosphoricum': 'phosphoricum acidum', 'acidum muriaticum': 'muriaticum acidum',
    'acidum fluoricum': 'fluoricum acidum', 'acidum sulphuricum': 'sulphuricum acidum', 'acidum picricum': 'picricum acidum',
    'acidum lacticum': 'lacticum acidum', 'acidum benzoicum': 'benzoicum acidum', 'acidum oxalicum': 'oxalicum acidum',
    'acidum salicylicum': 'salicylicum acidum', 'acidum aceticum': 'aceticum acidum', 'acidum carbolicum': 'carbolicum acidum',
    'acidum hydrocyanicum': 'hydrocyanicum acidum', 'acidum sarcolacticum': 'sarcolacticum acidum', 'acidum chromicum': 'chromicum acidum',
    'acidum formicum': 'formicum acidum', 'acidum boracicum': 'boricum acidum', 'acidum gallicum': 'gallicum acidum',
    'nux vomica': 'nux vomica', 'pulsatilla pratensis': 'pulsatilla', 'rhus toxicodendron': 'rhus toxicodendron',
    'arsenicum album': 'arsenicum album', 'conium maculatum': 'conium', 'ignatia amara': 'ignatia', 'calcarea carbonica': 'calcarea carbonica',
    'lycopodium clavatum': 'lycopodium', 'sepia officinalis': 'sepia', 'silicea terra': 'silicea', 'thuja occidentalis': 'thuja',
    'tuberculinum bovinum': 'tuberculinum', 'medorrhinum': 'medorrhinum', 'syphilinum': 'syphilinum', 'carcinosinum': 'carcinosinum',
    'bacillinum': 'bacillinum', 'psorinum': 'psorinum', 'hepar sulphuris': 'hepar sulphuris calcareum',
    'hepar sulphuris calcareum': 'hepar sulphuris calcareum', 'veratrum album': 'veratrum album', 'cocculus indicus': 'cocculus',
    'drosera rotundifolia': 'drosera', 'spongia tosta': 'spongia', 'tarentula hispanica': 'tarentula hispanica', 'tarentula cubensis': 'tarentula cubensis',
    'colocynthis': 'colocynthis', 'chamomilla': 'chamomilla', 'belladonna': 'belladonna', 'aconitum napellus': 'aconitum',
    'hyoscyamus niger': 'hyoscyamus', 'stramonium': 'stramonium', 'causticum': 'causticum', 'graphites': 'graphites',
    'mercurius iodatus flavus': 'mercurius iodatus flavus', 'mercurius iodatus ruber': 'mercurius iodatus ruber',
    'argentum nitricum': 'argentum nitricum', 'argentum metallicum': 'argentum metallicum', 'arum triphyllum': 'arum triphyllum',
    'sanguinaria canadensis': 'sanguinaria', 'sanguinaria nitrica': 'sanguinarinum nitricum', 'berberis vulgaris': 'berberis',
    'teucrium marum verum': 'teucrium marum verum', 'kalium bichromicum': 'kalium bichromicum',
    'ferrum metallicum': 'ferrum', 'ferrum phosphoricum': 'ferrum phosphoricum', 'zincum metallicum': 'zincum',
    'cuprum metallicum': 'cuprum', 'stannum metallicum': 'stannum', 'plumbum metallicum': 'plumbum', 'aurum metallicum': 'aurum',
    'platinum metallicum': 'platina', 'ambra grisea': 'ambra grisea', 'apis mellifica': 'apis', 'lachesis muta': 'lachesis',
    'naja tripudians': 'naja', 'crotalus horridus': 'crotalus horridus', 'elaps corallinus': 'elaps', 'cantharis vesicatoria': 'cantharis',
    'opium': 'opium', 'cina maritima': 'cina', 'chelidonium majus': 'chelidonium', 'podophyllum peltatum': 'podophyllum',
    'ipecacuanha': 'ipecacuanha', 'antimonium crudum': 'antimonium crudum', 'antimonium tartaricum': 'antimonium tartaricum',
    'rumex crispus': 'rumex', 'iodum': 'iodium', 'iodium': 'iodium', 'bromium': 'bromium', 'carbo vegetabilis': 'carbo vegetabilis',
    'hydrastis canadensis': 'hydrastis', 'baptisia tinctoria': 'baptisia', 'gelsemium sempervirens': 'gelsemium', 'bellis perennis': 'bellis perennis',
    'arnica montana': 'arnica', 'ledum palustre': 'ledum', 'hypericum perforatum': 'hypericum', 'calendula officinalis': 'calendula',
    'symphytum officinale': 'symphytum', 'ruta graveolens': 'ruta', 'rhododendron chrysanthum': 'rhododendron', 'dulcamara': 'dulcamara',
    'nux moschata': 'nux moschata', 'magnesia phosphorica': 'magnesium phosphoricum', 'magnesia carbonica': 'magnesium carbonicum',
    'magnesia muriatica': 'magnesium muriaticum', 'natrum arsenicosum': 'natrium arsenicosum', 'calcarea phosphorica': 'calcarea phosphorica',
    'calcarea fluorica': 'calcarea fluorica', 'calcarea sulphurica': 'calcarea sulphurica', 'calcarea iodata': 'calcarea iodata',
    'baryta carbonica': 'baryta carbonica', 'baryta muriatica': 'baryta muriatica', 'baryta iodata': 'baryta iodata',
    'lilium tigrinum': 'lilium tigrinum', 'cimicifuga racemosa': 'cimicifuga', 'caulophyllum thalictroides': 'caulophyllum',
    'sabina': 'sabina', 'secale cornutum': 'secale', 'ustilago maydis': 'ustilago', 'viburnum opulus': 'viburnum opulus',
    'helonias dioica': 'helonias', 'aletris farinosa': 'aletris farinosa', 'senecio aureus': 'senecio', 'xanthoxylum fraxineum': 'xanthoxylum',
    'ammonium carbonicum': 'ammonium carbonicum', 'ammonium muriaticum': 'ammonium muriaticum', 'alumina': 'alumina',
    'plumbum': 'plumbum', 'nitricum acidum': 'nitricum acidum', 'sulphur': 'sulphur', 'phosphorus': 'phosphorus', 'lycopodium': 'lycopodium',
    'crataegus oxyacantha': 'crataegus', 'digitalis purpurea': 'digitalis', 'cactus grandiflorus': 'cactus grandiflorus',
    'kalmia latifolia': 'kalmia', 'spigelia anthelmia': 'spigelia', 'convallaria majalis': 'convallaria', 'adonis vernalis': 'adonis vernalis',
    'strophanthus hispidus': 'strophanthus', 'terebinthina': 'terebinthina', 'sarsaparilla': 'sarsaparilla', 'solidago virgaurea': 'solidago',
    'chimaphila umbellata': 'chimaphila umbellata', 'pareira brava': 'pareira', 'equisetum hyemale': 'equisetum', 'uva ursi': 'uva ursi',
    'ocimum canum': 'ocimum canum', 'lithium carbonicum': 'lithium carbonicum', 'urtica urens': 'urtica urens', 'aesculus hippocastanum': 'aesculus',
    'collinsonia canadensis': 'collinsonia', 'hamamelis virginiana': 'hamamelis', 'paeonia officinalis': 'paeonia', 'ratanhia': 'ratanhia',
    'nitricum acidum ': 'nitricum acidum', 'mezereum': 'mezereum', 'petroleum': 'petroleum', 'vinca minor': 'vinca minor',
    'oleander': 'oleander', 'anacardium orientale': 'anacardium', 'croton tiglium': 'croton tiglium', 'cistus canadensis': 'cistus canadensis',
    'natrum iodatum': 'natrium iodatum', 'arsenicum iodatum': 'arsenicum iodatum', 'sulphur iodatum': 'sulphur iodatum',
    'aurum muriaticum natronatum': 'aurum muriaticum natronatum', 'thyroidinum': 'thyroidinum', 'fucus vesiculosus': 'fucus vesiculosus',
    'cholesterinum': 'cholesterinum', 'syzygium jambolanum': 'syzygium jambolanum', 'uranium nitricum': 'uranium nitricum',
    'gymnema sylvestre': 'gymnema sylvestre', 'cephalandra indica': 'cephalandra indica', 'abroma augusta': 'abroma augusta',
}
GENERIC = [('natrum ', 'natrium '), ('kali ', 'kalium '), ('magnesia ', 'magnesium '), ('mercurius vivus', 'mercurius solubilis'), ('mercurius (not specified)', 'mercurius solubilis'),
           ('bromium', 'bromum'), ('coffea cruda', 'coffea cruda'), ('thyroidinum', 'thyreoidinum'), ('hepar sulphuris calcareum', 'hepar sulphur'), ('hepar sulphuris', 'hepar sulphur'),
           ('amyl nitrosum', 'amylenum nitrosum'), ('asafoetida', 'asa foetida'), ('tuberculinum', 'tuberculinum bovinum kent'), ('calcarea (not specified)', 'calcarea carbonica'),
           ('iodum', 'iodium'), ('manganum aceticum', 'manganum aceticum (+ -c.)'), ('manganum', 'manganum aceticum (+ -c.)'), ('china', 'china officinalis'), ('cinchona officinalis', 'china officinalis')]
def map_name(n):
    k0 = n.lower().strip()
    r = _map_name(ALIAS.get(k0, k0))
    if r is None and k0 in ALIAS: r = _map_name(k0)      # alias target not resolvable: try the name itself
    return r
HARD = {'pulsatilla': 'pulsatilla pratensis', 'mercurius': 'mercurius solubilis', 'calcarea': 'calcarea carbonica', 'natrum mur': 'natrium muriaticum', 'kali carb': 'kalium carbonicum',
        'carbo veg': 'carbo vegetabilis', 'nux vom': 'nux vomica', 'rhus tox': 'rhus toxicodendron', 'ars alb': 'arsenicum album', 'hepar sulph': 'hepar sulphur', 'hepar': 'hepar sulphur',
        'china': 'china officinalis', 'cinchona': 'china officinalis', 'tuberculinum': 'tuberculinum bovinum kent', 'arsenicum': 'arsenicum album', 'natrum': 'natrium muriaticum'}
SUFFIX = {'carb': ['carbonicum', 'carbonica'], 'phos': ['phosphoricum', 'phosphorica', 'phosphoratum'], 'sulph': ['sulphuricum', 'sulphurica', 'sulphuratum'], 'sulp': ['sulphuricum', 'sulphurica'],
          'mur': ['muriaticum', 'muriatica'], 'iod': ['iodatum', 'iodata'], 'ars': ['arsenicosum', 'arsenicosa', 'arsenicum'], 'nit': ['nitricum', 'nitrica'], 'fluor': ['fluoricum', 'fluorica'],
          'met': ['metallicum'], 'bich': ['bichromicum'], 'brom': ['bromatum'], 'acet': ['aceticum'], 'sil': ['silicata', 'silicicum'], 'alb': ['album'], 'tox': ['toxicodendron'], 'vom': ['vomica'],
          'mosch': ['moschata'], 'nig': ['nigrum', 'nigra'], 'cor': ['corrosivus'], 'sol': ['solubilis'], 'ac': ['acidum'], 'acid': ['acidum'], 'sulf': ['sulphuricum', 'sulphurica'], 'chlor': ['chloratum', 'chloricum'],
          'cyan': ['cyanatum'], 'oxy': ['oxydatum'], 'perm': ['permanganatum'], 'hyd': ['hydriodicum'], 'ox': ['oxalicum'], 'bor': ['boricum'], 'benz': ['benzoicum'], 'picr': ['picricum'], 'lact': ['lacticum'],
          'salic': ['salicylicum'], 'tart': ['tartaricum'], 'crud': ['crudum'], 'occ': ['occidentalis'], 'can': ['canadensis'], 'virg': ['virginica'], 'off': ['officinalis', 'officinale']}
def _map_name(k):
    k = HARD.get(k, k)
    for a, b in GENERIC:
        if k == a or (a.endswith(' ') and k.startswith(a)): k = k.replace(a, b, 1); break
    k = HARD.get(k, k)
    if k in name_to_id: return name_to_id[k]
    w0 = k.split()
    if len(w0) == 2 and w0[1] in SUFFIX:                       # abbreviated second word: natrum carb, kali phos, merc cor ...
        for full in SUFFIX[w0[1]]:
            kk = w0[0] + ' ' + full
            if kk in name_to_id: return name_to_id[kk]
            if full == 'acidum' and (kk in name_to_id or (full + ' ' + w0[0]) in name_to_id): return name_to_id.get(kk, name_to_id.get(full + ' ' + w0[0]))
    # try "X acidum" <-> "acidum X"
    w = k.split()
    if len(w) == 2:
        alt = ' '.join(reversed(w))
        if alt in name_to_id: return name_to_id[alt]
    # first-word match if unique
    cands = [i for i, c in enumerate(canon) if c.lower() == w[0] or c.lower().startswith(w[0] + ' ')]
    if len(cands) == 1: return cands[0]
    # fuzzy: spelling variants (Stamonium, Crotong tiglium, Calcarea carbonicum ...)
    if len(k) >= 8:
        m = difflib.get_close_matches(k, CANON_LOW, n=1, cutoff=0.92)
        if m and m[0][:3] == k[:3]: return CANON_LOW.index(m[0])
    return None
import difflib
CANON_LOW = [c.lower() for c in canon]
_bad = [a for a, b in ALIAS.items() if b not in name_to_id and ' '.join(reversed(b.split())) not in name_to_id]
print('ALIAS targets not in Publicum:', _bad)

extra_names = []      # SHC remedies not in Publicum get ids >= len(abbr_list)
shc_rows = []
unmapped = collections.Counter()
rem_rows = collections.Counter()
for r in rows[1:]:
    rem = r[ix['Remedy']]
    if not rem or rem.startswith('(General'): continue
    rid = map_name(rem)
    if rid is None:
        ab = r[ix['Abbreviation']]
        if ab and norm_abbr(ab) in name_to_id: rid = name_to_id[norm_abbr(ab)]
    if rid is None:
        if rem not in extra_names: extra_names.append(rem)
        rid = len(abbr_list) + extra_names.index(rem)
        unmapped[rem] += 1
    rem_rows[rid] += 1
    shc_rows.append([rid, r[ix['Section']] or '', r[ix['Repertory rubric']] or '', r[ix['Patient language']] or '',
                     (r[ix['Symptom (book / notes text)']] or '')[:300], (r[ix['Source']] or '').split(' – ')[0].replace('Organopathy notes', 'Organopathy'),
                     r[ix['Topic']] or ''])
print('SHC rows', len(shc_rows), 'unmapped remedies', len(unmapped), 'rows', sum(unmapped.values()))
print(unmapped.most_common(40))
all_names = canon + extra_names

# ---------------------------------------------------------------- 3. Thermal table
def rub_rem(path_prefixes):
    out = {}
    for ch, p, rems in rubrics:
        if chapters[ch] != 'Generalities': continue
        if p in path_prefixes:
            for tok in rems.split():
                i, g = tok.split(':'); i = int(i); g = int(g)
                out[i] = max(out.get(i, 0), g)
    return out
HOT = rub_rem({'Generalities - warm - agg.', 'Generalities - warm - room - agg.', 'Generalities - warm - bed - agg.', 'Generalities - warmth - agg.',
               'Generalities - heat - agg.', 'Generalities - uncovering - amel.', 'Generalities - warm - wraps - agg.', 'Generalities - clothing - intolerance of'})
CHILLY = rub_rem({'Generalities - heat - vital - lack of', 'Generalities - cold - becoming - agg.', 'Generalities - cold - agg.',
                  'Generalities - uncovering - agg.', 'Generalities - cold - air - agg.', 'Generalities - warm - amel.', 'Generalities - cold - wet weather - agg.'})
thermal = {}
for i in set(HOT) | set(CHILLY):
    h, c = HOT.get(i, 0), CHILLY.get(i, 0)
    if h > c: thermal[i] = ['H', h, 'Publicum']
    elif c > h: thermal[i] = ['C', c, 'Publicum']
    else: thermal[i] = ['A', h, 'Publicum']       # ambithermal / both
# SHC notes override
HOTP = re.compile(r"hot patient|warm.*agg|hot\+|hot-natured|thermal: hot|heat - vital heat - excess", re.I)
COLDP = re.compile(r"chilly patient|cold.*agg\b|vital heat.*lack|lack of.*vital|cold-natured|thermal: (cold|chilly)", re.I)
shc_th = collections.defaultdict(lambda: [0, 0])
for rid, sec, rub, pl, txt, src, topic in shc_rows:
    if sec != 'Generals': continue
    t = (rub + ' ' + pl + ' ' + txt).lower()
    if 'ambithermal' in t: continue
    if HOTP.search(t): shc_th[rid][0] += 1
    if COLDP.search(t): shc_th[rid][1] += 1
for rid, (h, c) in shc_th.items():
    if h and not c: thermal[rid] = ['H', 3, 'SHC notes']
    elif c and not h: thermal[rid] = ['C', 3, 'SHC notes']
print('thermal entries', len(thermal), collections.Counter(v[0] for v in thermal.values()))

# ---------------------------------------------------------------- 4. Inimical / incompatible table
inimical = collections.defaultdict(set)   # id -> set(id)
ABBR_WORDS = {}   # loose token -> id, from Publicum abbreviations and names
for i, a in enumerate(abbr_list):
    ABBR_WORDS[norm_abbr(a)] = i
for i, c in enumerate(canon):
    ABBR_WORDS[c.lower()] = i
    ABBR_WORDS[c.lower().split()[0]] = ABBR_WORDS.get(c.lower().split()[0], i)
COMMON = {'lach': 'lachesis', 'lack': 'lachesis', 'puls': 'pulsatilla', 'puis': 'pulsatilla', 'nux': 'nux vomica', 'coff': 'coffea cruda', 'coffee': 'coffea cruda',
          'coflfea': 'coffea cruda', 'phos': 'phosphorus', 'caust': 'causticum', 'apis': 'apis', 'rhus': 'rhus toxicodendron', 'sep': 'sepia', 'sil': 'silicea',
          'merc': 'mercurius', 'zinc': 'zincum', 'cham': 'chamomilla', 'bell': 'belladonna', 'ign': 'ignatia', 'tabac': 'tabacum', 'ran-b': 'ranunculus bulbosus',
          'ran': 'ranunculus bulbosus', 'staph': 'staphysagria', 'sulph': 'sulphur', 'sul': 'sulphur', 'acet-ac': 'aceticum acidum', 'acetic acid': 'aceticum acidum',
          'carb-ac': 'carbolicum acidum', 'carbolic acid': 'carbolicum acidum', 'nit-ac': 'nitricum acidum', 'nitric acid': 'nitricum acidum', 'cocc': 'cocculus',
          'canth': 'cantharis', 'borax': 'borax', 'bry': 'bryonia', 'lyc': 'lycopodium', 'calc': 'calcarea carbonica', 'ars': 'arsenicum album',
          'all-s': 'allium sativum', 'scilla': 'squilla', 'squilla': 'squilla', 'am-c': 'ammonium carbonicum', 'kreos': 'kreosotum', 'psor': 'psorinum',
          'carb-v': 'carbo vegetabilis', 'dulc': 'dulcamara', 'ferr': 'ferrum', 'chin': 'china officinalis', 'china': 'china officinalis', 'sec': 'secale',
          'nux-v': 'nux vomica', 'thuj': 'thuja', 'led': 'ledum', 'mez': 'mezereum', 'sabin': 'sabina', 'sars': 'sarsaparilla', 'arg-n': 'argentum nitricum',
          'alum': 'alumina', 'ant-c': 'antimonium crudum', 'graph': 'graphites', 'hep': 'hepar sulphur', 'iod': 'iodium', 'tub': 'tuberculinum bovinum kent', 'kali-c': 'kalium carbonicum',
          'nat-m': 'natrium muriaticum', 'op': 'opium', 'plat': 'platina', 'plb': 'plumbum', 'stram': 'stramonium', 'verat': 'veratrum album',
          'camph': 'camphora', 'cupr': 'cuprum', 'dig': 'digitalis', 'gels': 'gelsemium', 'glon': 'glonoinum', 'hyos': 'hyoscyamus', 'ip': 'ipecacuanha',
          'mag-c': 'magnesium carbonicum', 'nat-c': 'natrium carbonicum', 'petr': 'petroleum', 'ph-ac': 'phosphoricum acidum', 'sang': 'sanguinaria',
          'spong': 'spongia', 'stann': 'stannum', 'tub': 'tuberculinum', 'med': 'medorrhinum', 'syph': 'syphilinum', 'carc': 'carcinosinum'}
def tok_to_id(tok):
    t = tok.lower().strip(' .,;:()').replace('é', 'e')
    t = re.sub(r'\s+', ' ', t)
    if t in COMMON: t = COMMON[t]
    if t in ABBR_WORDS: return ABBR_WORDS[t]
    for k, v in COMMON.items():
        if t.startswith(k) and len(t) <= len(k) + 3: return ABBR_WORDS.get(v)
    return None

evidence = []
def add_pair(a, b, src, quote):
    if a is None or b is None or a == b: return
    inimical[a].add(b); inimical[b].add(a)
    evidence.append([a, b, src, quote[:120]])

# 4a. Clarke's Dictionary + Allen's Keynotes (public domain text)
SRC = [('Clarke', REPO + '/treatise/clarke-dictionary-materia-medica-v1.json'), ('Clarke', REPO + '/treatise/clarke-dictionary-materia-medica-v2-i-p.json'),
       ('Clarke', REPO + '/treatise/clarke-dictionary-materia-medica-v3.json'), ('Allen Keynotes', REPO + '/treatise/allen-keynotes.json')]
NONREMEDY = {'wine', 'wines', 'spirits', 'vinegar', 'coffee', 'salt', 'tobacco', 'before', 'after', 'or', 'and', 'in', 'to', 'sometimes', 'especially', 'should', 'not', 'be', 'used'}
for src, f in SRC:
    d = json.load(open(f))
    for s in d['sections']:
        title = (s.get('title') or '').strip()
        a = tok_to_id(title) if title else None
        if a is None:
            a = map_name(title) if title else None
        if a is None: continue
        for m in re.finditer(r'(Incompatible|Inimical)\s*(?:to|with)?\s*[:;.\-]?\s*([^.\n]{1,140})', s['text']):
            body = m.group(2)
            body = re.split(r'\b(Compare|Complementary|Antidot|Follows|Followed|Antidotes)\b', body)[0]
            for tok in re.split(r'[;,]| and ', body):
                tok = tok.strip()
                tok = re.sub(r'\(.*?\)', '', tok).strip()
                if not tok or tok.split()[0].lower() in NONREMEDY: continue
                tok = ' '.join(tok.split()[:2])
                b = tok_to_id(tok)
                if b is None: b = tok_to_id(tok.split()[0])
                if b is not None: add_pair(a, b, src, m.group(0))
# 4b. SHC notes relationship rows
for rid, sec, rub, pl, txt, src, topic in shc_rows:
    t = rub + ' | ' + txt
    if re.search(r'inimical|incompatible', t, re.I):
        for m in re.finditer(r'(?:inimical|incompatible)[^|]*?-\s*([A-Z][a-z]+(?: [a-z]+)?)', rub):
            b = map_name(m.group(1))
            if b is None: b = tok_to_id(m.group(1))
            add_pair(rid, b, 'SHC notes', t)
# 4c. Boericke's Pocket Manual (Srinivas's clean file) — Relationship lines: Inimical / Incompatible
import pickle
BO = pickle.load(open('/home/claude/in/boericke.pkl', 'rb'))   # (Remedy, Software name, Common, Synonym, Section, Text, Source, Check)
BO_ABBR = {'bry': 'bryonia', 'lach': 'lachesis', 'laches': 'lachesis', 'puls': 'pulsatilla', 'ranunc bulb': 'ranunculus bulbosus', 'carbo': 'carbo vegetabilis', 'mercur': 'mercurius',
           'caust': 'causticum', 'rhus': 'rhus toxicodendron', 'nux': 'nux vomica', 'coffea': 'coffea cruda', 'calc': 'calcarea carbonica', 'arum triph': 'arum triphyllum',
           'kali nit': 'kalium nitricum', 'camph': 'camphora', 'coccul': 'cocculus', 'china': 'china officinalis', 'bellad': 'belladonna', 'tabac': 'tabacum',
           'acet ac': 'aceticum acidum', 'carb ac': 'carbolicum acidum', 'zinc': 'zincum', 'ferr phos': 'ferrum phosphoricum', 'sulph': 'sulphur', 'staph': 'staphysagria',
           'apis': 'apis', 'sulphur': 'sulphur', 'lachesis': 'lachesis'}
NONREM = {'wine', 'vinegar', 'glycerine', 'vegetable oils', 'acetic acid, vinegar, and wine are incompatible', 'similar in action'}
for r in BO:
    if r[4] != 'Relationship' or not re.search(r'inimical|incompatible', r[5] or '', re.I): continue
    a = map_name(r[1] or r[0])
    if a is None: a = tok_to_id(r[1] or r[0])
    if a is None: print('Boericke remedy not mapped:', r[0]); continue
    for m in re.finditer(r'(?:Inimical|Incompatible)\s*(?:to|with)?\s*[:;.]?\s*([^.]*)', r[5], re.I):
        body = re.split(r'\b(Compare|Complementary|Antidote|should not)\b', m.group(1))[0]
        for tok in re.split(r'[;,]| and ', body):
            tok = tok.strip().lower().rstrip('.')
            if not tok or tok in NONREM: continue
            b = ABBR_WORDS.get(BO_ABBR.get(tok, tok))
            if b is None: b = tok_to_id(tok)
            if b is None: print('  Boericke token not mapped:', r[0], '->', tok); continue
            add_pair(a, b, 'Boericke', (r[1] or r[0]) + ': ' + m.group(0).strip()[:100])
print('inimical pairs', sum(len(v) for v in inimical.values()) // 2, 'evidence lines', len(evidence))

# ---------------------------------------------------------------- 5. Organ map (Publicum chapter / SHC section -> organ)
ORGANS = {
 'Larynx / Voice': {'ch': ['Larynx and trachea'], 'sec': ['Throat'], 'w': ['larynx', 'voice', 'vocal', 'aphonia', 'hoarse', 'trachea', 'speech', 'speaker', 'singer']},
 'Throat': {'ch': ['Throat', 'External throat'], 'sec': ['Throat'], 'w': ['throat', 'tonsil', 'pharynx', 'swallow', 'uvula', 'thyroid', 'goitre', 'goiter']},
 'Lungs / Respiration': {'ch': ['Respiration', 'Chest', 'Expectoration'], 'sec': ['Respiratory', 'Chest & heart'], 'w': ['lung', 'bronch', 'asthma', 'breath', 'dyspn', 'respirat', 'pneumonia', 'pleur', 'expectorat', 'wheez']},
 'Cough': {'ch': ['Cough'], 'sec': ['Cough'], 'w': ['cough']},
 'Heart / Circulation': {'ch': ['Heart and circulation', 'Heart & Circulation', 'Blood'], 'sec': ['Chest & heart'], 'w': ['heart', 'cardiac', 'palpitation', 'pulse', 'hypertension', 'blood pressure', 'cholesterol', 'circulat', 'angina', 'anaemia', 'anemia', 'varicose']},
 'Stomach': {'ch': ['Stomach', 'Appetite'], 'sec': ['Stomach'], 'w': ['stomach', 'gastric', 'nausea', 'vomit', 'appetite', 'digest', 'dyspeps', 'acidity', 'heartburn', 'eructation', 'belching', 'indigestion']},
 'Liver / Abdomen': {'ch': ['Abdomen'], 'sec': ['Abdomen'], 'w': ['liver', 'hepat', 'spleen', 'pancrea', 'abdomen', 'intestin', 'gall', 'bowel', 'colic', 'flatul', 'bloat', 'jaundice']},
 'Rectum / Stool': {'ch': ['Rectum', 'Stool'], 'sec': ['Rectum & stool'], 'w': ['rectum', 'piles', 'haemorrhoid', 'hemorrhoid', 'constipat', 'diarrh', 'stool', 'anus', 'anal', 'fissure', 'fistula', 'dysenter']},
 'Kidney / Urinary': {'ch': ['Kidneys', 'Bladder', 'Urine', 'Urethra', 'Prostate gland'], 'sec': ['Urinary'], 'w': ['kidney', 'renal', 'bladder', 'urin', 'prostat', 'urethr', 'calcul', 'stone', 'nephr', 'cystitis', 'creatinine']},
 'Female organs': {'ch': ['Genitalia female'], 'sec': ['Female'], 'w': ['uter', 'ovar', 'mense', 'menstru', 'leucorrh', 'vagin', 'breast', 'mammae', 'dysmenorrh', 'pregnan', 'fibroid', 'pcod', 'pcos', 'menopaus', 'period', 'labour', 'labor']},
 'Male organs': {'ch': ['Genitalia male'], 'sec': ['Male'], 'w': ['testes', 'testicle', 'penis', 'spermat', 'impoten', 'erection', 'scrotum', 'hydrocele', 'semen']},
 'Skin': {'ch': ['Skin'], 'sec': ['Skin'], 'w': ['skin', 'eczema', 'psoriasis', 'eruption', 'itch', 'urticaria', 'acne', 'pimple', 'wart', 'ulcer', 'boil', 'ringworm', 'fungal', 'corn', 'dermat', 'rash', 'herpes', 'vitiligo', 'lichen']},
 'Head': {'ch': ['Head'], 'sec': ['Head'], 'w': ['head', 'migraine', 'scalp', 'hair', 'dandruff', 'alopecia', 'baldness']},
 'Eyes': {'ch': ['Eye', 'Vision'], 'sec': ['Eyes'], 'w': ['eye', 'vision', 'sight', 'conjunctiv', 'cataract', 'eyelid', 'glaucoma', 'retina', 'stye']},
 'Ears': {'ch': ['Ear', 'Hearing'], 'sec': ['Ears'], 'w': ['ear', 'hearing', 'deaf', 'tinnitus', 'otitis', 'otorrh']},
 'Nose': {'ch': ['Nose'], 'sec': ['Nose'], 'w': ['nose', 'nasal', 'sinus', 'coryza', 'sneez', 'epistaxis', 'polyp', 'smell', 'rhinitis', 'catarrh']},
 'Mouth / Teeth': {'ch': ['Mouth', 'Teeth'], 'sec': ['Mouth & teeth'], 'w': ['mouth', 'teeth', 'tooth', 'gum', 'tongue', 'aphth', 'saliva', 'taste', 'dental', 'pyorrh']},
 'Face': {'ch': ['Face'], 'sec': ['Face'], 'w': ['face', 'facial', 'cheek', 'lips', 'jaw']},
 'Back / Spine': {'ch': ['Back'], 'sec': ['Back'], 'w': ['back', 'spine', 'spinal', 'lumbar', 'cervical', 'sciatic', 'vertebra', 'disc', 'spondyl', 'coccyx']},
 'Joints / Limbs': {'ch': ['Extremities'], 'sec': ['Extremities'], 'w': ['knee', 'joint', 'arthrit', 'rheumat', 'gout', 'shoulder', 'hip', 'ankle', 'wrist', 'finger', 'toe', 'leg', 'arm', 'heel', 'nail', 'cramp', 'limb', 'elbow', 'foot', 'feet', 'hand', 'muscle', 'tendon', 'bone']},
 'Sleep': {'ch': ['Sleep'], 'sec': ['Sleep & dreams'], 'w': ['insomnia', 'sleepless', 'sleep']},
 'Mind / Nerves': {'ch': ['Mind'], 'sec': ['Mind'], 'w': ['depress', 'anxiety', 'memory', 'fear', 'anger', 'irritab', 'grief', 'adhd', 'hyperactiv', 'concentrat', 'mind', 'mental', 'nerv', 'stress', 'panic', 'autism']},
 'Vertigo': {'ch': ['Vertigo'], 'sec': ['Vertigo'], 'w': ['vertigo', 'giddiness', 'dizz']},
 'Fever': {'ch': ['Fever', 'Chill', 'Perspiration'], 'sec': ['Fever, chill & sweat'], 'w': ['fever', 'perspir', 'sweat', 'chill']},
 'Generals / Metabolic': {'ch': ['Generalities', 'Clinical'], 'sec': ['Generals', 'Clinical / indication'], 'w': ['diabet', 'thyroid', 'obes', 'weight', 'debility', 'weakness', 'sugar', 'cancer', 'tumour', 'tumor', 'growth']},
}
ch_to_organ = {}
for o, d in ORGANS.items():
    for c in d['ch']: ch_to_organ.setdefault(c, o)
print('chapters without organ:', [c for c in chapters if c not in ch_to_organ])

# ---------------------------------------------------------------- 5b. Boericke MM sentences -> notes rows (source 'Boericke')
BO_SEC = {'General': 'Generals', 'Head': 'Head', 'Extremities': 'Extremities', 'Stomach': 'Stomach', 'Skin': 'Skin', 'Modalities': 'Generals', 'Respiratory': 'Respiratory',
          'Female': 'Female', 'Abdomen': 'Abdomen', 'Mind': 'Mind', 'Eyes': 'Eyes', 'Mouth': 'Mouth & teeth', 'Nose': 'Nose', 'Face': 'Face', 'Throat': 'Throat', 'Sleep': 'Sleep & dreams',
          'Fever': 'Fever, chill & sweat', 'Urine': 'Urinary', 'Male': 'Male', 'Ears': 'Ears', 'Urinary': 'Urinary', 'Back': 'Back', 'Heart': 'Chest & heart', 'Stool': 'Rectum & stool',
          'Rectum': 'Rectum & stool', 'Chest': 'Chest & heart', 'Tongue': 'Mouth & teeth', 'Ear': 'Ears', 'Bones': 'Extremities', 'Nervous System': 'Mind'}
bo_rows = 0
for r in BO:
    sec = r[4] or ''
    if sec in ('Relationship', 'Dose', 'Dose / notes') or not r[5]: continue
    rid = map_name(r[1] or r[0])
    if rid is None:
        nm = (r[1] or r[0]).strip()
        if nm not in extra_names: extra_names.append(nm)
        rid = len(abbr_list) + extra_names.index(nm)
    for sent in re.split(r'(?<=[.;])\s+(?=[A-Z])', r[5].strip()):
        sent = sent.strip()
        if len(sent) < 12: continue
        shc_rows.append([rid, BO_SEC.get(sec, sec), 'BOERICKE - ' + sec.upper() + ' - ' + sent[:160].rstrip('.'), '', sent[:300], 'Boericke', r[2] or ''])
        bo_rows += 1
print('Boericke sentence rows', bo_rows)
all_names = canon + extra_names

# ---------------------------------------------------------------- 5c. RadarOpus / SHC FINAL RUBRICS list -> repertory layer (no grades)
RAD = pickle.load(open('/home/claude/in/radar.pkl', 'rb'))   # (remedy, rubric, patient language)
POT = re.compile(r'\b(\d+\s*[xXcCmM]?|q|lm\d*|1m|10m|cm|mt|\(.*?\))\s*$')
def clean_rem(n):
    n = n.replace('*', '').replace('\xa0', ' ').strip()
    if '\n' in n or len(n) > 45 or ':' in n or '&' in n or '/' in n: return None
    n = re.sub(r'\s*\(.*?\)\s*', ' ', n)
    for _ in range(3): n = POT.sub('', n).strip(' ,.-')
    if not n or len(n) < 3 or not re.match(r'^[A-Za-z][A-Za-z .\-]+$', n): return None
    return n[0].upper() + n[1:].lower()
RAD_ALIAS = {'natrum mur': 'natrium muriaticum', 'nat mur': 'natrium muriaticum', 'ars alb': 'arsenicum album', 'ars iod': 'arsenicum iodatum', 'hepar sulph': 'hepar sulphur', 'kali bich': 'kalium bichromicum',
             'kali carb': 'kalium carbonicum', 'kali phos': 'kalium phosphoricum', 'calc carb': 'calcarea carbonica', 'calc phos': 'calcarea phosphorica', 'calc fluor': 'calcarea fluorica', 'calc sulph': 'calcarea sulphurica',
             'nat sulph': 'natrium sulphuricum', 'nat phos': 'natrium phosphoricum', 'nat carb': 'natrium carbonicum', 'mag phos': 'magnesium phosphoricum', 'mag carb': 'magnesium carbonicum', 'mag mur': 'magnesium muriaticum',
             'ferrum met': 'ferrum', 'ferrum phos': 'ferrum phosphoricum', 'merc sol': 'mercurius solibilis', 'merc cor': 'mercurius corrosivus', 'arg nit': 'argentum nitricum', 'arg met': 'argentum metallicum',
             'ant tart': 'antimonium tartaricum', 'ant crud': 'antimonium crudum', 'nit acid': 'nitricum acidum', 'phos acid': 'phosphoricum acidum', 'mur acid': 'muriaticum acidum', 'fluor acid': 'fluoricum acidum',
             'carbo veg': 'carbo vegetabilis', 'carbo an': 'carbo animalis', 'rhus tox': 'rhus toxicodendron', 'nux vom': 'nux vomica', 'nux mosch': 'nux moschata', 'aurum met': 'aurum', 'cuprum met': 'cuprum',
             'zincum met': 'zincum', 'plumbum met': 'plumbum', 'stannum met': 'stannum', 'staphysagia': 'staphisagria', 'sanquinarinum nitricum': 'sanguinarinum nitricum',
             'teucrium marum varum': 'teucrium marum verum', 'calcarea arsenicum': 'calcarea arsenicosa', 'natrium muriaticum': 'natrium muriaticum', 'hydroscyanic acid': 'hydrocyanicum acidum',
             'apis mel': 'apis', 'lyco': 'lycopodium', 'merc sol': 'mercurius solubilis', 'calcarea phos': 'calcarea phosphorica', 'calcarea carb': 'calcarea carbonica', 'actea racemosa': 'cimicifuga', 'nux moschus': 'nux moschata', 'terebinthina': 'terebinthiniae oleum', 'ambrosia': 'ambrosia artemisiaefolia', 'kali': 'kalium carbonicum', 'dephtherinum': 'diphtherinum', 'carcinosin': 'carcinosinum', 'thyroidinum': 'thyreoidinum', 'thyreodinum': 'thyreoidinum', 'bacillinum burnett': 'bacillinum', 'kali silicicum': 'kalium silicatum', 'kalium silicicum': 'kalium silicatum', 'zincum valerianum': 'zincum valerianicum', 'lycopodium clavatum': 'lycopodium', 'sepia officinalis': 'sepia', 'pulsatilla nigricans': 'pulsatilla', 'thuja occ': 'thuja', 'silicea terra': 'silicea',
             'natrum sulph': 'natrium sulphuricum', 'kali mur': 'kalium muriaticum', 'kali sulph': 'kalium sulphuricum', 'kali iod': 'kalium iodatum', 'kali brom': 'kalium bromatum', 'kali ars': 'kalium arsenicosum'}
rad_name_cache = {}
def rad_id(n):
    c = clean_rem(n)
    if c is None: return None
    k = c.lower()
    if k in rad_name_cache: return rad_name_cache[k]
    k2 = RAD_ALIAS.get(k, k)
    rid = map_name(k2)
    if rid is None: rid = tok_to_id(k2) if len(k2.split()) <= 2 else None
    if rid is None:
        nm = c
        if nm not in extra_names:
            m = difflib.get_close_matches(nm.lower(), [e.lower() for e in extra_names], n=1, cutoff=0.9)
            if m and m[0][:4] == nm.lower()[:4]: nm = extra_names[[e.lower() for e in extra_names].index(m[0])]
            else: extra_names.append(nm)
        rid = len(abbr_list) + extra_names.index(nm)
    rad_name_cache[k] = rid
    return rid
rad_groups = {}   # norm rubric -> [display, pl_counter, set(ids)]
rad_dropped = collections.Counter()
def split_multi(rem):
    # cells holding several remedies, one per line ("Causticum – For Hoarse Voice ...", "NATRUM MUR:- ...", "Allium cepa\nAllium sativum")
    out = []
    for line in re.split(r'\n|;', rem):
        line = line.replace('\xa0', ' ').strip(' *')
        if not line: continue
        name = re.split(r'\s[–—-]\s|:-|:|\(|\s+for\s+|\s+is\s+|\s+helps\s+', line, 1)[0].strip()
        if 2 < len(name) <= 40 and re.match(r'^[A-Za-z][A-Za-z .\-]+$', name): out.append(name)
    return out
salvaged = 0
for rem, rub, pl in RAD:
    rub = re.sub(r'\s+', ' ', rub.replace('\xa0', ' ')).strip(' .')
    if not rub or len(rub) > 220 or '\n' in rub: rad_dropped['long/para'] += 1; continue
    rids = []
    if '\n' in rem or len(rem) > 45:
        for nm in split_multi(rem):
            r_ = rad_id(nm)
            if r_ is not None: rids.append(r_)
        if rids: salvaged += len(rids)
    else:
        r_ = rad_id(rem)
        if r_ is not None: rids.append(r_)
    if not rids: rad_dropped['bad remedy'] += 1; continue
    key = rub.lower()
    g = rad_groups.get(key)
    if g is None: g = rad_groups[key] = [rub, collections.Counter(), set()]
    g[2].update(rids)
    if pl and len(pl) < 200: g[1][pl.strip()] += 1
print('salvaged remedy entries from multi-remedy cells:', salvaged)
rad_rubrics = [[g[0], (g[1].most_common(1)[0][0] if g[1] else ''), ' '.join(str(i) for i in sorted(g[2]))] for g in rad_groups.values()]
print('RadarOpus list: rubrics', len(rad_rubrics), 'links', sum(len(g[2]) for g in rad_groups.values()), 'dropped', dict(rad_dropped), 'extra names now', len(extra_names))
all_names = canon + extra_names
json.dump(rad_rubrics, open(OUT + '/rad.json', 'w'), ensure_ascii=False, separators=(',', ':'))

# ---------------------------------------------------------------- 6. Write
json.dump({'chapters': chapters, 'rubrics': rubrics}, open(OUT + '/rep.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump(shc_rows, open(OUT + '/shc.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump({'names': all_names, 'abbr': abbr_list, 'thermal': {str(k): v for k, v in thermal.items()},
           'inimical': {str(k): sorted(v) for k, v in inimical.items()}, 'inimical_evidence': evidence,
           'organs': ORGANS, 'ch_to_organ': ch_to_organ}, open(OUT + '/meta.json', 'w'), ensure_ascii=False, separators=(',', ':'))
for f in glob.glob(OUT + '/*.json'): print(f, round(os.path.getsize(f) / 1e6, 2), 'MB')
# quick checks for the Annex 2 remedies
for n in ['Argentum nitricum', 'Argentum metallicum', 'Teucrium marum verum', 'Phosphorus', 'Causticum', 'Arum triphyllum', 'Belladonna', 'Kalium bichromicum', 'Berberis', 'Sanguinarinum nitricum', 'Lycopodium', 'Bromium']:
    i = map_name(n); print(n, i, thermal.get(i), 'inimical:', [all_names[j] for j in inimical.get(i, [])])
