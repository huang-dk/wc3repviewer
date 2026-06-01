/* War3 Replay Analyzer — Frontend */

const WS_HOST = (location.protocol === 'http:') ? location.hostname : 'localhost';
const WS_URL  = `ws://${WS_HOST}:8125`;
const ICON_BASE = 'icons/';
const RECONNECT_DELAY = 3000;

/* ── Unit name map ─────────────────────────────────────────────────── */
// 来源: war3.w3mod:units/unitui.slk (游戏原始数据，已验证)
const UNIT_NAMES = {
  // ── 人族英雄 ──
  Hamg:'大法师',    Hpal:'圣骑士',     Hmkg:'山丘之王',  Hblm:'血法师',
  // ── 兽族英雄 ──
  Ofar:'先知',      Obla:'剑圣',       Oshd:'暗影猎手',  Otch:'牛头人酋长',
  // ── 夜精灵英雄 ──
  Ekee:'丛林守护者', Emoo:'月之女祭司', Edem:'恶魔猎手',  Ewar:'守望者',
  // ── 亡灵英雄 ──
  Ulic:'巫妖',      Udea:'死亡骑士',   Udre:'恐惧魔王',  Ucrl:'地穴领主',
  // ── 中立英雄（酒馆）──
  Nalc:'炼金术士',  Nalm:'炼金术士',
  Nbst:'兽王',      Nplh:'深渊领主',   Nbrn:'黑暗游侠',
  Nfir:'火焰领主',  Npbm:'熊猫酒仙',   Nrob:'工程师',    Nngs:'娜迦海巫',

  // ── 人族单位 (来自 unitui.slk) ──
  hpea:'农民',          // peasant
  hfoo:'步兵',          // footman
  hrif:'火枪手',        // rifleman
  hkni:'骑士',          // knight
  hmpr:'牧师',          // priest
  hsor:'女巫',          // sorceress
  hmtm:'迫击炮队',      // mortarteam
  hmtt:'攻城机器',      // siegeengine
  hgry:'鹰爪骑士',      // gryphonrider
  hgyr:'飞行机器',      // flyingmachine
  hspt:'法术破坏者',    // spellbreaker
  hmil:'民兵',          // militia
  htow:'市政厅',        // townhall
  hkee:'城楼',          // keep
  hcas:'城堡',          // castle
  hbar:'兵营',          // humanbarracks
  hhou:'农舍',          // farm
  hwtw:'哨塔',          // scouttower (正确 ID，之前 htwr 不存在)
  hgtw:'弓箭塔',        // guardtower
  hctw:'炮塔',          // cannontower

  // ── 兽族单位 (来自 unitui.slk) ──
  opeo:'苦工',          // peon
  ogru:'地精兵',        // grunt
  ocat:'毁灭者',        // demolisher
  oshm:'萨满祭司',      // shaman
  ospw:'灵魂行者',      // spiritwalker
  ospm:'变身灵魂行者',  // spiritwalkermorph
  ohun:'猎头者',        // headhunter
  otbr:'蝙蝠骑士',      // trollbatrider
  orai:'劫掠者',        // wolfrider
  otau:'牛头人',        // tauren
  owyv:'风骑士',        // windrider
  odoc:'巫医',          // witchdoctor
  okod:'科多兽',        // kotobeast
  osw1:'灵魂狼',        // spiritwolf1
  osw2:'灵魂狼',        // spiritwolf2
  osw3:'灵魂狼',        // spiritwolf3
  ogre:'大要塞',        // greathall
  ostr:'要塞',          // stronghold
  ofrt:'堡垒',          // fortress
  obar:'兽棚',          // orcbarracks
  ofor:'战争工厂',      // warmill
  owtw:'瞭望塔',        // watchtower

  // ── 夜精灵单位 (来自 unitui.slk) ──
  ewsp:'小精灵',        // wisp
  earc:'弓箭手',        // archer
  esen:'猎鹿者',        // huntress
  edry:'树精',          // dryad
  efon:'自然之力',      // forceofnature (召唤树人，非独立单位)
  emtg:'山地巨人',      // mountaingiant
  edot:'变鸦德鲁伊',    // druidofthetalon
  edtm:'变鸦形态',      // druidofthetalonmorphed
  edoc:'熊德鲁伊',      // druidoftheclaw
  edcm:'变身熊德鲁伊',  // druidoftheclawmorphed
  ehip:'角鹰兽',        // hippogryph
  ehpr:'角鹰骑士',      // riddenhippogryph
  echm:'奇美拉',        // chimaera
  efdr:'精灵龙',        // faeriedragon
  ebal:'飞刃投石车',    // glaivethrower
  espv:'复仇之灵',      // spiritofvengeance
  etol:'生命之树',      // treeoflife
  etoa:'岁月之树',      // treeofages
  etoe:'永恒之树',      // treeofeternity
  eaom:'战争古树',      // ancientofwar
  eaoe:'知识古树',      // ancientoflore
  eaow:'风之古树',      // ancientofwind
  eden:'奇迹古树',      // ancientofwonders
  etrp:'远古护卫者',    // ancientprotector
  emow:'月井',          // moonwell
  egol:'纠缠金矿',      // entangledgoldmine
  edob:'猎人大厅',      // huntershall
  edos:'奇美拉巢穴',    // chimaeraroost

  // ── 亡灵单位 (来自 unitui.slk) ──
  uaco:'接灵者',        // acolyte
  ugho:'食尸鬼',        // ghoul
  uabo:'畸变体',        // abomination
  ucry:'地穴蜘蛛',      // cryptfiend
  ucrm:'地穴蜘蛛（变身）', // cryptfiendmorph
  uban:'女妖',          // banshee
  unec:'死灵法师',      // necromancer
  ugar:'石像鬼',        // gargoyle
  ugrm:'石像鬼（飞行）', // gargoylemorphed
  ufro:'冰甲龙',        // frostwyrm
  umtw:'尸车',          // meatwagon
  ushd:'暗影',          // shade
  uobs:'黑曜石雕像',    // obsidianstatue
  ubsp:'毁灭者',        // obsidiandestroyer
  uske:'骷髅战士',      // skeletonwarrior
  uskm:'骷髅法师',      // skeletalmage
  uplg:'瘟疫病房',      // plagueward
  unpl:'黑暗灵堂',      // necropolis
  unp1:'黑暗灵堂',      // necropolis1
  unp2:'黑暗灵堂',      // necropolis2
  utod:'黑暗圣堂',      // templeofthedamned
  uaod:'黑暗祭坛',      // altarofdarkness
  uzg1:'基格拉特',      // ziggurat1
  uzg2:'冰晶箭楼',      // frosttower
  ubon:'骨场',          // boneyard
  ugrv:'墓地',          // graveyard
};

function unitName(id){ return UNIT_NAMES[id] || id; }

function raceKey(r){
  if(!r) return 'RAN';
  const u=r.toUpperCase();
  if(u.includes('HUMAN'))  return 'HUM';
  if(u.includes('ORC'))    return 'ORC';
  if(u.includes('NIGHT'))  return 'NE';
  if(u.includes('UNDEAD')) return 'UD';
  return 'RAN';
}
function raceLabel(r){
  return {HUM:'人族',ORC:'兽族',NE:'夜精灵',UD:'亡灵',RAN:'随机'}[raceKey(r)]||r;
}

/* ── helpers ─────────────────────────────────────────────────────────── */
function fmtNum(n){
  if(!n) return '0';
  return n>=1000 ? (n/1000).toFixed(1)+'k' : String(n);
}
function fmtTime(ms){
  const s=Math.floor(ms/1000), m=Math.floor(s/60);
  return `${m}:${String(s%60).padStart(2,'0')}`;
}
function pct(v,mx){ return mx ? Math.min(100,Math.max(0,v/mx*100)).toFixed(1) : 0; }

function el(tag,cls,html){
  const e=document.createElement(tag);
  if(cls) e.className=cls;
  if(html!==undefined) e.innerHTML=html;
  return e;
}
function clear(n){ while(n.firstChild) n.removeChild(n.firstChild); }

/* icon with jpg fallback to text */
function iconEl(id, size=40){
  const wrap = el('div','icon-wrap');
  wrap.style.cssText=`width:${size}px;height:${size}px;flex-shrink:0;overflow:hidden;border-radius:3px;background:#050510;`;
  const img=document.createElement('img');
  img.src=ICON_BASE+id+'.jpg';
  img.style.cssText='width:100%;height:100%;object-fit:cover;display:block;';
  img.onerror=function(){
    const sp=document.createElement('span');
    sp.style.cssText='font-size:9px;color:#555;display:flex;align-items:center;justify-content:center;width:100%;height:100%;';
    sp.textContent=id.slice(0,4);
    wrap.innerHTML='';
    wrap.appendChild(sp);
  };
  wrap.appendChild(img);
  return wrap;
}

/* ── Hero card ──────────────────────────────────────────────────────── */
function buildHeroCard(hero){
  const card=el('div',`hc${!hero.hitpoints?' hc-dead':''}`);

  /* top: portrait + info */
  const top=el('div','hc-top');

  /* portrait */
  const port=el('div','hc-port');
  port.appendChild(iconEl(hero.id,54));
  port.appendChild(el('span','hc-lvl',hero.level));
  top.appendChild(port);

  /* info column */
  const info=el('div','hc-info');

  const nameRow=el('div','hc-name-row');
  nameRow.appendChild(el('span','hc-name',unitName(hero.id)));
  nameRow.appendChild(el('span','hc-xp',`${hero.experience}/${hero.experience_max}`));
  info.appendChild(nameRow);

  /* HP bar */
  const hpRow=el('div','bar-row');
  const hpTrack=el('div','bar-track');
  const hpFill=el('div','bar-fill hp-fill');
  hpFill.style.width=pct(hero.hitpoints,hero.hitpoints_max)+'%';
  hpTrack.appendChild(hpFill);
  hpRow.appendChild(el('span','bar-lbl','血'));
  hpRow.appendChild(hpTrack);
  hpRow.appendChild(el('span','bar-val',`${hero.hitpoints}/${hero.hitpoints_max}`));
  info.appendChild(hpRow);

  /* Mana bar */
  if(hero.mana_max>0){
    const mpRow=el('div','bar-row');
    const mpTrack=el('div','bar-track');
    const mpFill=el('div','bar-fill mp-fill');
    mpFill.style.width=pct(hero.mana,hero.mana_max)+'%';
    mpTrack.appendChild(mpFill);
    mpRow.appendChild(el('span','bar-lbl','蓝'));
    mpRow.appendChild(mpTrack);
    mpRow.appendChild(el('span','bar-val',`${hero.mana}/${hero.mana_max}`));
    info.appendChild(mpRow);
  }

  top.appendChild(info);
  card.appendChild(top);

  /* damage stats */
  const dmg=el('div','hc-dmg');
  const d=el('div','ds dd'); d.appendChild(el('span','ds-lbl','造成')); d.appendChild(el('span','ds-val',fmtNum(hero.damage_dealt)));
  const r=el('div','ds dr'); r.appendChild(el('span','ds-lbl','承受')); r.appendChild(el('span','ds-val',fmtNum(hero.damage_received)));
  const h=el('div','ds dh'); h.appendChild(el('span','ds-lbl','治疗')); h.appendChild(el('span','ds-val',fmtNum(hero.damage_healed)));
  dmg.appendChild(d); dmg.appendChild(r); dmg.appendChild(h);
  card.appendChild(dmg);

  /* items */
  const inv=hero.inventory||[];
  if(inv.length>0 || true){
    const items=el('div','hc-items');
    for(let i=0;i<6;i++){
      const slot=el('div','item-slot');
      const item=inv[i];
      if(item&&item.id){
        slot.appendChild(iconEl(item.id,26));
        if(item.charges>0) slot.appendChild(el('span','item-ch',item.charges));
      }
      items.appendChild(slot);
    }
    card.appendChild(items);
  }

  /* abilities (hero skills only) */
  const abils=(hero.abilities||[]).filter(a=>
    a.id && /^A[HOEUN]/.test(a.id) &&
    !['AHer','ANpr','ANsa','ANss','ANse','ANbs','AUds','AEtr','AEsd','Aatk','Amov','AItp','AInv'].includes(a.id)
  );
  if(abils.length>0){
    const ab=el('div','hc-abils');
    abils.forEach(a=>{
      const s=el('div','ab-slot');
      s.appendChild(iconEl(a.id,22));
      if(a.level>0) s.appendChild(el('span','ab-lvl',a.level));
      ab.appendChild(s);
    });
    card.appendChild(ab);
  }

  return card;
}

/* ── Player card ─────────────────────────────────────────────────────── */
function buildPlayerCard(p){
  const card=el('div','pc');

  /* resource row */
  const res=el('div','pc-res');
  res.appendChild(el('span',`race-badge race-${raceKey(p.race)}`,raceLabel(p.race)));
  res.appendChild(el('span','pc-name',p.name));
  res.innerHTML+=`<span class="rv gold">💰${p.gold}</span>`;
  res.innerHTML+=`<span class="rv lum">🪵${p.lumber}</span>`;
  res.innerHTML+=`<span class="rv food">🍖${p.food}/${p.food_max}</span>`;
  res.innerHTML+=`<span class="rv apm">⚡${p.apm}</span>`;
  card.appendChild(res);

  /* heroes */
  if(p.heroes&&p.heroes.length){
    const hs=el('div','pc-heroes');
    p.heroes.forEach(h=>hs.appendChild(buildHeroCard(h)));
    card.appendChild(hs);
  }

  /* buildings under construction */
  const bld=(p.buildings||[]).filter(b=>b.progress<100);
  if(bld.length){
    const bs=el('div','pc-bld');
    bs.appendChild(el('div','bld-title','建造中'));
    bld.forEach(b=>{
      const row=el('div','bld-row');
      row.appendChild(iconEl(b.id,18));
      const trk=el('div','bld-track');
      const fill=el('div','bld-fill');
      fill.style.width=b.progress+'%';
      trk.appendChild(fill);
      row.appendChild(trk);
      row.appendChild(el('span','bld-pct',b.progress+'%'));
      bs.appendChild(row);
    });
    card.appendChild(bs);
  }

  return card;
}

/* ── Death Tracker ──────────────────────────────────────────────────────
   Observer API 的 total_count 始终等于 alive_count，不记录历史死亡。
   这里通过比较每帧 alive 变化来累积死亡数。
   key: "teamKey:unitId" → {prev: 上帧alive, dead: 累计死亡}
────────────────────────────────────────────────────────────────────── */
const _dt = {};
let _dtMap = '', _dtTime = 0;

function trackDeaths(teams, gameTime, mapName) {
  // 地图切换或时间倒退（replay seek）→ 重置
  if (mapName !== _dtMap || gameTime < _dtTime - 5000) {
    Object.keys(_dt).forEach(k => delete _dt[k]);
  }
  _dtMap  = mapName;
  _dtTime = gameTime;

  Object.entries(teams).forEach(([tk, players]) => {
    const seen = new Set();

    players.forEach(p => {
      (p.units || []).forEach(u => {
        const key = `${tk}:${u.id}`;
        seen.add(key);
        if (!_dt[key]) {
          _dt[key] = {prev: u.alive, dead: 0};
        } else {
          if (u.alive < _dt[key].prev) {
            _dt[key].dead += _dt[key].prev - u.alive;
          }
          _dt[key].prev = u.alive;
        }
      });
    });

    // 上帧存在、这帧消失的单位 → 剩余全部死亡
    Object.keys(_dt).forEach(key => {
      if (!key.startsWith(tk + ':')) return;
      if (!seen.has(key) && _dt[key].prev > 0) {
        _dt[key].dead += _dt[key].prev;
        _dt[key].prev = 0;
      }
    });
  });
}

function getTrackedDeaths(teamKey) {
  // 返回该队伍所有有死亡记录的单位 {unitId: deaths}
  const res = {};
  Object.entries(_dt).forEach(([key, val]) => {
    if (key.startsWith(teamKey + ':') && val.dead > 0) {
      res[key.slice(teamKey.length + 1)] = val.dead;
    }
  });
  return res;
}

/* ── Center units ────────────────────────────────────────────────────── */
function buildUnits(players, container, teamKey){
  clear(container);
  if(!players||!players.length) return;

  // 合并同队所有玩家：场上单位 + 队列
  const merged = {};
  function getOrCreate(id){
    if(!merged[id]) merged[id] = {id, alive:0, dead:0, dmg:0, recv:0, queue:0};
    return merged[id];
  }

  players.forEach(p => {
    // 场上单位
    (p.units||[]).forEach(u => {
      const m = getOrCreate(u.id);
      m.alive += u.alive;
      m.dead  += u.dead;
      m.dmg   += (u.dmg_dealt    || 0);
      m.recv  += (u.dmg_received || 0);
    });
    // 生产队列
    Object.entries(p.queue || {}).forEach(([id, cnt]) => {
      getOrCreate(id).queue += cnt;
    });
  });

  // 注入追踪到的死亡数（替代 API 里始终为 0 的 dead 字段）
  const tracked = getTrackedDeaths(teamKey);
  Object.entries(tracked).forEach(([uid, dead]) => {
    // 包含已全灭、不再出现在 units_on_map 的单位
    if (!merged[uid]) merged[uid] = {id:uid, alive:0, dead:0, dmg:0, recv:0, queue:0};
    merged[uid].dead = dead;
  });

  // 有场上存在、死亡记录或正在排队的单位都显示
  const units = Object.values(merged).filter(u => u.alive + u.dead + u.queue > 0);
  if(!units.length) return;

  // 队伍标签 + 总死亡数
  const totalDead = Object.values(tracked).reduce((s, d) => s + d, 0);
  const label = el('div','unit-label',
    players.map(p => p.name).join(' / ') +
    (totalDead > 0 ? `  ✝${totalDead}` : ''));
  container.appendChild(label);

  units.forEach(u => {
    // 格式：[icon] 名字  ⚔伤害  🛡承受  数量（✝死亡）+队列
    const row = el('div', 'unit-row');

    row.appendChild(iconEl(u.id, 16));
    row.appendChild(el('span', 'un', unitName(u.id)));

    if(u.dmg  > 0) row.appendChild(el('span', 'ud-deal', '⚔'+fmtNum(u.dmg)));
    if(u.recv > 0) row.appendChild(el('span', 'ud-recv', '🛡'+fmtNum(u.recv)));

    // 数量部分：存活（✝死亡）+队列
    let countStr = String(u.alive);
    if(u.dead  > 0) countStr += `（✝${u.dead}）`;
    if(u.queue > 0) countStr += `+${u.queue}`;
    row.appendChild(el('span', 'ua', countStr));

    container.appendChild(row);
  });
}

/* ── Main render ─────────────────────────────────────────────────────── */
function render(state){
  const waiting=document.getElementById('waiting');
  const main=document.getElementById('main');

  if(!state||!state.game||!state.game.is_in_game){
    waiting.classList.remove('hidden');
    main.classList.add('hidden');
    clear(main);
    return;
  }

  waiting.classList.add('hidden');
  main.classList.remove('hidden');

  /* rebuild entire layout each frame (simple, fast enough at 1fps) */
  clear(main);

  const game=state.game;
  const teams=state.teams||{};
  const keys=Object.keys(teams).sort();
  const left =teams[keys[0]]||[];
  const right=teams[keys[1]]||[];

  // 每帧更新死亡追踪
  trackDeaths(teams, game.game_time, game.map_name || '');

  /* ── top bar：只保留时间和地图名 ── */
  const top=el('div','top-bar');
  const mapShort=(game.map_name||'').split('/').pop().replace(/\.[^.]+$/,'').replace(/_/g,' ');
  top.innerHTML=`<span class="gt">${fmtTime(game.game_time)}</span>
                 <span class="mn">${mapShort}</span>`;
  main.appendChild(top);

  /* ── columns ── */
  const cols=el('div','cols');

  /* left panel */
  const lp=el('div','team-panel');
  left.forEach(p=>lp.appendChild(buildPlayerCard(p)));
  cols.appendChild(lp);

  /* center panel */
  const cp=el('div','center-panel');
  cp.appendChild(el('div','vs','VS'));
  const ul=el('div','units-block');
  buildUnits(left,  ul, keys[0]);
  cp.appendChild(ul);
  cp.appendChild(el('div','udiv'));
  const ur=el('div','units-block');
  buildUnits(right, ur, keys[1]);
  cp.appendChild(ur);
  cols.appendChild(cp);

  /* right panel */
  const rp=el('div','team-panel');
  right.forEach(p=>rp.appendChild(buildPlayerCard(p)));
  cols.appendChild(rp);

  main.appendChild(cols);
}

/* ── WebSocket ──────────────────────────────────────────────────────── */
let ws=null, reconnectTimer=null;
const statusEl=document.getElementById('conn-status');
const debugBar=document.getElementById('debug-bar');
function dbg(m){ if(debugBar) debugBar.textContent=`[${new Date().toLocaleTimeString()}] ${m}`; }

function connect(){
  if(reconnectTimer) clearTimeout(reconnectTimer);
  dbg(`连接中 ${WS_URL}`);
  ws=new WebSocket(WS_URL);

  ws.onopen=()=>{
    statusEl.className='connected'; statusEl.textContent='● 已连接';
    dbg(`已连接`);
  };

  ws.onmessage=(e)=>{
    try{
      const s=JSON.parse(e.data);
      dbg(`收到: in_game=${s?.game?.is_in_game}  time=${s?.game?.game_time}  teams=${Object.keys(s?.teams||{})}`);
      render(s);
    }catch(err){
      dbg(`解析错误: ${err.message}`);
    }
  };

  ws.onclose=(e)=>{
    statusEl.className='error'; statusEl.textContent='● 断开';
    dbg(`断开 code=${e.code}`);
    render(null);
    reconnectTimer=setTimeout(connect,RECONNECT_DELAY);
  };

  ws.onerror=()=>{ statusEl.className='error'; statusEl.textContent='● 失败'; dbg('连接失败'); };
}

connect();
