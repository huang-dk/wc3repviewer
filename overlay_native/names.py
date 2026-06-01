# -*- coding: utf-8 -*-
import re

UNIT_NAMES = {
    # ── 人族英雄
    'Hamg':'大法师','Hpal':'圣骑士','Hmkg':'山丘之王','Hblm':'血法师',
    # ── 兽族英雄
    'Ofar':'先知','Obla':'剑圣','Oshd':'暗影猎手','Otch':'牛头人酋长',
    # ── 夜精灵英雄
    'Ekee':'丛林守护者','Emoo':'月之女祭司','Edem':'恶魔猎手','Ewar':'守望者',
    # ── 亡灵英雄
    'Ulic':'巫妖','Udea':'死亡骑士','Udre':'恐惧魔王','Ucrl':'地穴领主',
    # ── 中立英雄
    'Nalc':'炼金术士','Nalm':'炼金术士','Nbst':'兽王','Nplh':'深渊领主',
    'Nbrn':'黑暗游侠','Nfir':'火焰领主','Npbm':'熊猫酒仙',
    'Nrob':'工程师','Nngs':'娜迦海巫',
    # ── 人族单位
    'hpea':'农民','hfoo':'步兵','hrif':'火枪手','hkni':'骑士',
    'hmpr':'牧师','hsor':'女巫','hmtm':'迫击炮','hmtt':'攻城机器',
    'hgry':'鹰爪骑士','hgyr':'飞行机器','hspt':'法术破坏者','hmil':'民兵',
    'htow':'市政厅','hkee':'城楼','hcas':'城堡',
    # ── 兽族单位
    'opeo':'苦工','ogru':'地精兵','ocat':'毁灭者','oshm':'萨满祭司',
    'ospw':'灵魂行者','ospm':'变身灵魂行者','ohun':'猎头者','otbr':'蝙蝠骑士',
    'orai':'劫掠者','otau':'牛头人','owyv':'风骑士','odoc':'巫医','okod':'科多兽',
    # ── 夜精灵单位
    'ewsp':'小精灵','earc':'弓箭手','esen':'猎鹿者','edry':'树精',
    'emtg':'山地巨人','edot':'变鸦德鲁伊','edtm':'变鸦形态',
    'edoc':'熊德鲁伊','edcm':'变身熊德鲁伊','ehip':'角鹰兽',
    'ehpr':'角鹰骑士','echm':'奇美拉','ebal':'飞刃投石车',
    # ── 亡灵单位
    'uaco':'接灵者','ugho':'食尸鬼','uabo':'畸变体','ucry':'地穴蜘蛛',
    'ucrm':'地穴蜘蛛变身','uban':'女妖','unec':'死灵法师','ugar':'石像鬼',
    'ugrm':'石像鬼飞行','ufro':'冰甲龙','umtw':'尸车','ushd':'暗影',
    'uobs':'黑曜石雕像','ubsp':'毁灭者','uske':'骷髅战士','uskm':'骷髅法师',
}

_SKIP_ABILITIES = {
    'AHer','ANpr','ANsa','ANss','ANse','ANbs',
    'AUds','AEtr','AEsd','Aatk','Amov','AItp','AInv',
}

def unit_name(uid: str) -> str:
    return UNIT_NAMES.get(uid, uid)

def race_key(race: str) -> str:
    if not race: return 'RAN'
    u = race.upper()
    if 'HUMAN' in u: return 'HUM'
    if 'ORC'   in u: return 'ORC'
    if 'NIGHT' in u: return 'NE'
    if 'UNDEAD' in u: return 'UD'
    return 'RAN'

def race_label(race: str) -> str:
    return {'HUM':'人族','ORC':'兽族','NE':'夜精灵','UD':'亡灵','RAN':'随机'
            }.get(race_key(race), race)

def fmt_num(n) -> str:
    if not n: return '0'
    n = int(n)
    return f'{n/1000:.1f}k' if n >= 1000 else str(n)

def fmt_time(ms: int) -> str:
    s = ms // 1000
    return f'{s // 60}:{s % 60:02d}'

def pct(v, mx) -> float:
    return min(1.0, max(0.0, v / mx)) if mx else 0.0

def filter_abilities(abilities: list) -> list:
    return [a for a in abilities
            if a.get('id')
            and re.match(r'^A[HOEUN]', a['id'])
            and a['id'] not in _SKIP_ABILITIES]
