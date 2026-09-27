#!/usr/bin/env python3
"""
name-generator MCP — 創作用の名前ジェネレーター (キャラ名・地名)

LLM が「ネオ〜」「シャドウ〜」に偏る問題を、外部の音素テーブル + seed 付き乱数で避けるための
MCP サーバー。依存は `mcp` パッケージのみ。

ツール:
  list_styles                  使えるスタイル一覧と見本
  generate_character_names     キャラ名 (性別・姓つき)
  generate_place_names         地名 (町/都市/山/川/森/湖/砦/王国)
  generate_names_from_examples 既存の名前群からマルコフ連鎖で「同じ世界っぽい」名前を作る
  reserve_names / list_reserved / release_names
                               採用した名前を記録し、以降の生成で重複・類似を自動回避

リソース:
  fantasy://styles             スタイル定義と接尾辞一覧
  fantasy://reserved           現在採用・予約されている名前の一覧

プロンプト:
  brainstorm_character         キャラクター命名・設定ブレインストーミング
  brainstorm_world_places      世界観・地名構築支援

同じ seed + 同じ引数 + 同じ予約状態なら、結果は再現される。
予約リストの保存先: 環境変数 NAME_GEN_STORE (既定 ~/.name_generator_mcp/reserved.json)

起動:      python -m fantasy_name_generator_mcp
試し撃ち:  python -m fantasy_name_generator_mcp --demo
"""

import json
import math
import os
import random
import re
import secrets
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from .extra_data import (
    ADJ_ANY,
    ADJ_LIVING,
    ADJ_POETIC,
    COUNTRY_ENDINGS,
    EXTRA_PLACE_KINDS_JA,
    EXTRA_PLACES,
    GOVERNMENTS,
    KIND_JA_TERM,
    NOUN_LIVING,
    NOUN_OBJECT,
    TAVERN_SUFFIXES,
    WAFUU_TAVERN_SUFFIXES,
    WAFUU_WORDS,
)

# ---------------------------------------------------------------------------
# 型定義
# ---------------------------------------------------------------------------
StyleType = Literal["elf", "dwarf", "human", "orc", "wafuu", "arcane", "southern"]
GenderType = Literal["any", "male", "female", "neutral"]
PlaceKindType = Literal[
    "town", "city", "mountain", "river", "forest", "lake", "fortress", "kingdom",
    "plains", "desert", "wasteland", "swamp", "hills", "valley", "coast", "sea",
    "island", "cave", "ruins",
]
GovernmentType = Literal[
    "kingdom", "empire", "republic", "duchy", "federation", "theocracy", "tribal"
]
TavernToneType = Literal["western", "wafuu"]
TavernKindType = Literal["any", "tavern", "inn"]

VOW = "aeiou"
ROWV = "aiueo"  # カナ表の母音順

# ---------------------------------------------------------------------------
# ローマ字 -> カナ
# ---------------------------------------------------------------------------
_ROWS = {
    "": ["ア", "イ", "ウ", "エ", "オ"],
    "k": ["カ", "キ", "ク", "ケ", "コ"],
    "g": ["ガ", "ギ", "グ", "ゲ", "ゴ"],
    "s": ["サ", "シ", "ス", "セ", "ソ"],
    "z": ["ザ", "ジ", "ズ", "ゼ", "ゾ"],
    "t": ["タ", "ティ", "トゥ", "テ", "ト"],
    "d": ["ダ", "ディ", "ドゥ", "デ", "ド"],
    "n": ["ナ", "ニ", "ヌ", "ネ", "ノ"],
    "h": ["ハ", "ヒ", "フ", "ヘ", "ホ"],
    "b": ["バ", "ビ", "ブ", "ベ", "ボ"],
    "p": ["パ", "ピ", "プ", "ペ", "ポ"],
    "m": ["マ", "ミ", "ム", "メ", "モ"],
    "y": ["ヤ", "イ", "ユ", "イェ", "ヨ"],
    "r": ["ラ", "リ", "ル", "レ", "ロ"],
    "l": ["ラ", "リ", "ル", "レ", "ロ"],
    "w": ["ワ", "ウィ", "ウ", "ウェ", "ウォ"],
    "f": ["ファ", "フィ", "フ", "フェ", "フォ"],
    "v": ["ヴァ", "ヴィ", "ヴ", "ヴェ", "ヴォ"],
    "j": ["ジャ", "ジ", "ジュ", "ジェ", "ジョ"],
    "x": ["クサ", "クシ", "クス", "クセ", "クソ"],
    "q": ["クァ", "クィ", "ク", "クェ", "クォ"],
    "sh": ["シャ", "シ", "シュ", "シェ", "ショ"],
    "ch": ["チャ", "チ", "チュ", "チェ", "チョ"],
    "ts": ["ツァ", "ツィ", "ツ", "ツェ", "ツォ"],
    "th": ["サ", "シ", "ス", "セ", "ソ"],
}
_ALIAS = {"ph": "f", "gh": "g", "ck": "k", "kh": "k", "wh": "w"}
_STAND = {
    "k": "ク", "g": "グ", "s": "ス", "z": "ズ", "t": "ト", "d": "ド", "n": "ン",
    "h": "フ", "b": "ブ", "p": "プ", "m": "ム", "r": "ル", "l": "ル", "f": "フ",
    "v": "ヴ", "j": "ジ", "w": "ウ", "y": "イ", "x": "クス", "q": "ク",
    "sh": "シュ", "ch": "チ", "ts": "ツ", "th": "ス",
}
_DIGRAPHS = {"sh", "ch", "th", "ts", "ph", "gh", "ck", "kh", "wh"}


_YOUON = {
    "k": {"a": "キャ", "u": "キュ", "e": "キェ", "o": "キョ"},
    "g": {"a": "ギャ", "u": "ギュ", "e": "ギェ", "o": "ギョ"},
    "s": {"a": "シャ", "u": "シュ", "e": "シェ", "o": "ショ"},
    "z": {"a": "ジャ", "u": "ジュ", "e": "ジェ", "o": "ジョ"},
    "j": {"a": "ジャ", "u": "ジュ", "e": "ジェ", "o": "ジョ"},
    "t": {"a": "チャ", "u": "チュ", "e": "チェ", "o": "チョ"},
    "d": {"a": "ヂャ", "u": "デュ", "e": "デェ", "o": "ヂョ"},
    "n": {"a": "ニャ", "u": "ニュ", "e": "ニェ", "o": "ニョ"},
    "h": {"a": "ヒャ", "u": "ヒュ", "e": "ヒェ", "o": "ヒョ"},
    "b": {"a": "ビャ", "u": "ビュ", "e": "ビェ", "o": "ビョ"},
    "p": {"a": "ピャ", "u": "ピュ", "e": "ピェ", "o": "ピョ"},
    "m": {"a": "ミャ", "u": "ミュ", "e": "ミェ", "o": "ミョ"},
    "r": {"a": "リャ", "u": "リュ", "e": "リェ", "o": "リョ"},
    "l": {"a": "リャ", "u": "リュ", "e": "リェ", "o": "リョ"},
    "f": {"a": "フィャ", "u": "フュ", "e": "フェ", "o": "フィョ"},
    "v": {"a": "ヴィャ", "u": "ヴュ", "e": "ヴェ", "o": "ヴィョ"},
}


def to_katakana(name: str, is_wafuu: bool = False) -> str:
    s = name.lower().replace("'", "").replace("-", "").replace(" ", "")
    out = []
    i = 0
    n_len = len(s)

    while i < n_len:
        c = s[i]

        # 単語先頭での同一母音の連続: aa -> アー (洋風) / アア (和風)
        if i + 1 < n_len and c in VOW and s[i + 1] == c:
            base_v = _ROWS[""][ROWV.index(c)]
            out.append(base_v)
            out.append(base_v if is_wafuu else "ー")
            i += 2
            continue

        # 単母音
        if c in VOW:
            out.append(_ROWS[""][ROWV.index(c)])
            i += 1
            continue

        # 連続子音の処理
        # nn の処理
        if c == "n" and i + 1 < n_len and s[i + 1] == "n":
            out.append("ン")
            # 次の文字(i+2)が母音なら、2つ目のnは母音と結合させる (例: Anna -> ア+ン+ナ)
            if i + 2 < n_len and s[i + 2] in VOW:
                i += 1
            else:
                # 母音が続かないなら連続するnをまとめて「ン」1つにする (例: Lynn -> リン, Gwenn -> グウェン)
                while i < n_len and s[i] == "n":
                    i += 1
            continue

        # ll, rr, mm -> 単子音に圧縮 (ll -> l など)
        if c in ("l", "r", "m") and i + 1 < n_len and s[i + 1] == c:
            i += 1
            continue

        # 促音 'ッ': kk, tt, pp, ss, gg, dd, bb, ff, zz, または ck
        if (i + 1 < n_len and c in ("k", "t", "p", "s", "g", "d", "b", "f", "z") and s[i + 1] == c) or (
            c == "c" and i + 1 < n_len and s[i + 1] == "k"
        ):
            out.append("ッ")
            if c == "c" and s[i + 1] == "k":
                i += 1
                c = "k"
            else:
                i += 1

        # 二重音字 (digraph)
        two = s[i:i + 2]
        if two in _DIGRAPHS:
            cons, step = _ALIAS.get(two, two), 2
        elif c == "c":
            nxt = s[i + 1] if i + 1 < n_len else ""
            cons, step = ("s" if nxt in ("e", "i") else "k"), 1
        else:
            cons, step = c, 1

        if cons not in _ROWS and cons not in _STAND:
            i += 1
            continue

        j = i + step
        nc = s[j] if j < n_len else ""

        # 拗音チェック: cons + 'y' + 母音 (例: nya -> ニャ, kyo -> キョ, ryu -> リュ)
        if nc == "y" and j + 1 < n_len and s[j + 1] in VOW:
            y_vow = s[j + 1]
            if cons in _YOUON and y_vow in _YOUON[cons]:
                out.append(_YOUON[cons][y_vow])
                # 長音チェック (例: nyaan -> ニャーン)
                if not is_wafuu and j + 2 < n_len and s[j + 2] == y_vow:
                    out.append("ー")
                    i = j + 3
                else:
                    i = j + 2
                continue
            elif y_vow == "i" and cons in _ROWS:
                # nyi -> ニ, kyi -> キ
                out.append(_ROWS[cons][1])
                i = j + 2
                continue

        if nc in VOW and nc != "" and cons in _ROWS:
            out.append(_ROWS[cons][ROWV.index(nc)])
            # 子音 + 同一母音連続 (例: vaar -> ヴァー + r)
            if not is_wafuu and j + 1 < n_len and s[j + 1] == nc:
                out.append("ー")
                i = j + 2
            else:
                i = j + 1
        elif nc == "y" and cons in _ROWS and cons != "y" and (j + 1 >= n_len or s[j + 1] not in VOW):
            out.append(_ROWS[cons][1])  # wyn -> ウィン, ry -> リ
            i = j + 1
        else:
            out.append(_STAND.get(cons, "ク"))
            i = j

    return "".join(out)


def to_hiragana(kata: str) -> str:
    return "".join(chr(ord(ch) - 0x60) if "ァ" <= ch <= "ヶ" else ch for ch in kata)


# ---------------------------------------------------------------------------
# スタイル定義 (音素テーブル)
# ---------------------------------------------------------------------------
def _sfx(s: str):
    """'orn:山,thor:峰' -> [('orn','山'),('thor','峰')]"""
    return [tuple(p.split(":", 1)) for p in s.split(",")]


STYLES = {
    "elf": dict(
        label="エルフ風", desc="流麗で母音が多い (例: ロレンディル)",
        onsets={"": 2, "l": 5, "r": 4, "n": 4, "th": 2, "s": 3, "m": 3, "v": 2, "f": 1, "k": 2},
        vowels={"a": 4, "e": 4, "i": 4, "o": 2, "u": 1, "ae": 1, "ia": 1},
        codas={"": 10, "l": 2, "n": 2, "r": 2, "s": 1, "th": 1}, coda_mode="final", coda_p=0.35,
        syll=(1, 2), ending_p=0.9, max_cluster=2,
        endings={"male": ["ion", "or", "il", "ir", "as", "en", "and", "orn"],
                 "female": ["iel", "wen", "ia", "ith", "ara", "ine", "ael", "wyn"],
                 "neutral": ["ae", "el", "is", "in", "ar"]},
        family="ael,orn,ithil,las,riel,dor,wen",
        places=dict(town=_sfx("ven:集落,thil:里"), city=_sfx("lond:都,rion:都"),
                    mountain=_sfx("orn:山,thor:峰"), river=_sfx("duin:川,rill:小川"),
                    forest=_sfx("las:森,wenn:木立"), lake=_sfx("mere:湖,nen:湖水"),
                    fortress=_sfx("mir:砦,dil:塔"), kingdom=_sfx("dor:国,orien:王国")),
    ),
    "dwarf": dict(
        label="ドワーフ風", desc="子音が硬く短い (例: ブラクドゥル)",
        onsets={"b": 4, "d": 5, "g": 4, "k": 3, "m": 3, "t": 3, "th": 2, "br": 3, "dr": 3,
                "gr": 3, "kr": 2, "r": 2, "n": 2, "h": 1, "": 1},
        vowels={"a": 4, "o": 4, "u": 4, "i": 1, "e": 1},
        codas={"r": 4, "n": 3, "m": 2, "k": 3, "l": 3, "d": 3, "g": 3, "": 2}, coda_mode="any", coda_p=0.5,
        syll=(1, 2), ending_p=0.85, max_cluster=3,
        endings={"male": ["in", "ur", "ar", "or", "ik", "ak", "dur", "grim", "bek"],
                 "female": ["a", "na", "ra", "ild", "dis", "ga"],
                 "neutral": ["im", "um", "un", "ok"]},
        family="kar,zul,bek,drum,garn,gard,dur",
        places=dict(town=_sfx("heim:集落,bek:村"), city=_sfx("dun:城市,grad:都"),
                    mountain=_sfx("kaz:山,tor:峰,zul:大山"), river=_sfx("ruk:川,drun:急流"),
                    forest=_sfx("barr:森,gund:森"), lake=_sfx("tarn:湖,mur:池"),
                    fortress=_sfx("hold:要塞,borg:砦"), kingdom=_sfx("dur:王国,heim:王国")),
    ),
    "human": dict(
        label="中世西洋風・人間", desc="古い英独仏っぽい素朴な響き (例: オルドリック)",
        onsets={"": 2, "b": 3, "c": 3, "d": 4, "f": 2, "g": 3, "h": 3, "j": 1, "l": 4, "m": 4,
                "n": 3, "p": 2, "r": 4, "s": 4, "t": 4, "v": 2, "w": 3, "br": 2, "cr": 1,
                "dr": 1, "gr": 2, "tr": 2, "st": 2},
        vowels={"a": 4, "e": 4, "i": 3, "o": 4, "u": 2},
        codas={"": 8, "n": 3, "r": 3, "l": 3, "s": 2, "d": 2, "m": 1, "t": 2}, coda_mode="any", coda_p=0.3,
        syll=(1, 2), ending_p=0.85, max_cluster=3,
        endings={"male": ["an", "ard", "ric", "mund", "as", "el", "en", "on", "us", "ert", "ald"],
                 "female": ["a", "ia", "ine", "elle", "ette", "wyn", "la", "ta", "ith", "ana"],
                 "neutral": ["en", "el", "in", "is"]},
        family="ton,well,ford,wick,ley,worth,field,bury,ham,stead",
        places=dict(town=_sfx("ton:町,ham:村,wick:集落"), city=_sfx("burg:都市,chester:城市,minster:大聖堂の街"),
                    mountain=_sfx("fell:山,crag:岩山,peak:峰"), river=_sfx("water:川,brook:小川,ford:浅瀬"),
                    forest=_sfx("wood:森,holt:雑木林,weald:森林"), lake=_sfx("mere:湖,loch:湖"),
                    fortress=_sfx("keep:砦,hold:要塞,castle:城"), kingdom=_sfx("land:国,mark:辺境国,realm:王国")),
    ),
    "orc": dict(
        label="オーク風", desc="濁音と破裂音が多い荒々しい響き (例: グラクザグ)",
        onsets={"g": 5, "k": 4, "gr": 5, "kr": 4, "z": 3, "r": 3, "m": 3, "b": 3, "d": 2,
                "sh": 2, "": 2, "gh": 2},
        vowels={"u": 5, "a": 4, "o": 4, "i": 1, "e": 1},
        codas={"k": 4, "g": 4, "r": 3, "z": 3, "sh": 2, "t": 3, "": 3}, coda_mode="any", coda_p=0.55,
        syll=(1, 2), ending_p=0.7, max_cluster=3,
        endings={"male": ["ak", "uk", "ag", "ug", "gash", "mok", "zog", "rok", "dush"],
                 "female": ["a", "ka", "ga", "ush", "ra"],
                 "neutral": ["uz", "ok", "ag"]},
        family="gash,gruk,mog,zag,bash,rakk",
        places=dict(town=_sfx("gash:巣,grub:集落"), city=_sfx("gor:大砦,mok:砦都市"),
                    mountain=_sfx("gorm:山,krag:岩山"), river=_sfx("shuk:川,zur:濁流"),
                    forest=_sfx("zug:森,gruk:暗い森"), lake=_sfx("mur:沼,glub:澱み"),
                    fortress=_sfx("gro:砦,dush:要塞"), kingdom=_sfx("mok:氏族領,gash:部族領")),
    ),
    "wafuu": dict(
        label="和風", desc="日本語の音 (ひらがな表記) (例: あきまる / まつやま)",
        onsets={"": 2, "k": 5, "s": 4, "t": 4, "n": 4, "h": 3, "m": 4, "y": 3, "r": 3, "w": 1,
                "g": 2, "z": 1, "d": 1, "b": 1, "sh": 2, "ch": 1, "ts": 1, "j": 1},
        vowels={"a": 5, "i": 4, "u": 3, "e": 3, "o": 4},
        allowed={"y": "auo", "w": "a", "ts": "u", "sh": "iauo", "ch": "iauo", "j": "iauo",
                 "t": "aeo", "d": "aeo", "z": "aou", "h": "aieo", "": "aiueo"},
        codas={"n": 1}, coda_mode="any", coda_p=0.15, n_guard=True,
        syll=(1, 2), ending_p=1.0, max_cluster=2, kana="hiragana", no_elide=True, allow_repeat=True,
        endings={"male": ["ro", "ta", "ki", "ya", "o", "to", "suke", "maru", "hiko", "shi"],
                 "female": ["ko", "mi", "ka", "na", "e", "yo", "ri", "ha", "ne", "no"],
                 "neutral": ["ki", "to", "ya", "mi", "ru"]},
        family="mura,yama,kawa,hara,zaki,mori,numa,shima,oka,ta,sawa,no,hashi",
        places=dict(town=_sfx("mura:村,machi:町"), city=_sfx("kyo:京,fu:府"),
                    mountain=_sfx("yama:山,dake:岳,mine:峰"), river=_sfx("gawa:川,kawa:川"),
                    forest=_sfx("mori:森,bayashi:林"), lake=_sfx("ko:湖,numa:沼"),
                    fortress=_sfx("jo:城,toride:砦"), kingdom=_sfx("koku:国,nokuni:国")),
    ),
    "arcane": dict(
        label="古代・魔術・異形", desc="古い呪文や邪神っぽい響き (例: ヴァクソス)",
        onsets={"z": 3, "x": 2, "v": 4, "k": 3, "th": 3, "n": 2, "": 3, "m": 3, "sh": 2, "zh": 0},
        vowels={"a": 4, "e": 3, "i": 2, "o": 4, "u": 3, "ua": 1},
        codas={"th": 3, "x": 3, "n": 2, "s": 3, "r": 2, "m": 2, "z": 3, "l": 2, "": 1}, coda_mode="any", coda_p=0.45,
        syll=(1, 2), ending_p=0.8, max_cluster=2,
        endings={"male": ["oth", "ul", "ax", "ir", "ion", "ath", "os"],
                 "female": ["ael", "eth", "ira", "ith", "ael", "essa"],
                 "neutral": ["um", "is", "yx", "on"]},
        family="thul,vex,noth,zael,mor",
        places=dict(town=_sfx("thek:集落,ul:穴居"), city=_sfx("zul:都,vaar:大都市"),
                    mountain=_sfx("kor:山,thaal:峰"), river=_sfx("ish:川,vel:流れ"),
                    forest=_sfx("vael:森,nyx:闇森"), lake=_sfx("zeth:湖,mor:淵"),
                    fortress=_sfx("dol:塔,gor:砦"), kingdom=_sfx("oth:王国,aeon:古王国")),
    ),
    "southern": dict(
        label="南方・交易都市風", desc="地中海〜中東の商業都市っぽい響き (例: サンタヌヤーン系)",
        onsets={"s": 5, "t": 3, "m": 4, "n": 4, "r": 4, "l": 3, "k": 3, "z": 2, "sh": 2, "h": 3,
                "b": 3, "d": 3, "": 2, "j": 1},
        vowels={"a": 8, "i": 4, "u": 2, "e": 3, "o": 2},
        codas={"": 8, "n": 3, "r": 3, "l": 2, "m": 2, "s": 2, "h": 1}, coda_mode="final", coda_p=0.4,
        syll=(1, 2), ending_p=0.85, max_cluster=2,
        endings={"male": ["an", "ar", "im", "el", "ah", "io", "ur"],
                 "female": ["ya", "ira", "ina", "ia", "ela", "ana", "ea"],
                 "neutral": ["i", "en", "ay", "ir"]},
        family="adi,ari,essa,ino,oun,iel,ova",
        places=dict(town=_sfx("ya:町,dar:村"), city=_sfx("ara:都,poli:都市"),
                    mountain=_sfx("tor:山,jebel:山"), river=_sfx("wadi:涸れ川,nahr:川"),
                    forest=_sfx("vil:森,sel:木陰"), lake=_sfx("bahr:湖,luna:湖"),
                    fortress=_sfx("qal:砦,kasr:城"), kingdom=_sfx("istan:国,ania:王国")),
    ),
}

PLACE_KINDS = ["town", "city", "mountain", "river", "forest", "lake", "fortress", "kingdom"]
PLACE_KIND_JA = dict(
    town="町・村", city="都市", mountain="山", river="川", forest="森",
    lake="湖", fortress="砦・城", kingdom="国"
)

# 都市以外の地形(平原・砂漠など)と追加の接尾辞を、各スタイルの表へ統合する
PLACE_KIND_JA.update(EXTRA_PLACE_KINDS_JA)
PLACE_KINDS.extend(k for k in EXTRA_PLACE_KINDS_JA if k not in PLACE_KINDS)
for _style, _tbl in EXTRA_PLACES.items():
    for _kind, _raw in _tbl.items():
        _cur = STYLES[_style]["places"].setdefault(_kind, [])
        _cur.extend(x for x in _sfx(_raw) if x not in _cur)

# 和風の自然な名字生成用テーブル
WAFUU_FAMILY_PREFIXES = [
    "ao", "aka", "kuro", "shiro", "taka", "matsu", "sugi", "take",
    "fuji", "iwa", "ishi", "kami", "shimo", "naka", "kita", "minami",
    "higashi", "nishi", "hira", "naga", "hoshino", "kasa", "waka", "fuku",
    "kawa", "yama", "tani", "mori", "sawa", "oka", "tsuka", "yoshi",
    "haru", "aki", "mura"
]
WAFUU_FAMILY_SUFFIXES = [
    "yama", "kawa", "mura", "hara", "zaki", "mori", "numa", "shima",
    "oka", "ta", "tani", "sawa", "no", "kura", "hashi", "moto",
    "bashi", "guchi", "da"
]
WAFUU_STANDALONE_FAMILIES = [
    "suzuki", "tanaka", "watanabe", "ito", "yamamoto", "nakamura",
    "kobayashi", "kato", "yoshida", "hayashi", "saito", "ikeda",
    "hashimoto", "yamazaki", "mori", "shimizu"
]

for _k, _s in STYLES.items():
    if isinstance(_s["family"], str):  # importlib.reload() でも壊れないように
        _s["family"] = _s["family"].split(",")

# 部分一致で弾く語 (英語圏で不適切なもの。和風では「ふく」「かした」等を巻き込むので対象外)
BLOCK_SUBSTR_EN = ["fuk", "fuc", "shit", "kkk", "nigg", "nigr"]
# 部分一致で弾く語 (日本語で不適切なもの。全スタイル対象)
BLOCK_SUBSTR_JP = ["unko", "chinko", "manko", "chinpo", "oppai"]
# 名前全体がこれと一致するときだけ弾く語 (Cassian の "ass" や Titania の "tit" を巻き込まないため)
BLOCK_EXACT = [
    "ass", "sex", "cum", "tit", "baka", "aho", "shine", "kill", "die", "poo",
    "napoli", "milano", "roma", "paris", "london", "berlin", "madrid", "athens",
    "tokyo", "kyoto", "osaka",
]
BLOCKLIST = BLOCK_SUBSTR_EN + BLOCK_SUBSTR_JP + BLOCK_EXACT  # 互換用 (全部入りの一覧)


# ---------------------------------------------------------------------------
# 生成エンジン
# ---------------------------------------------------------------------------
def _wchoice(rng, table):
    keys = list(table.keys())
    w = [table[k] for k in keys]
    return rng.choices(keys, weights=w, k=1)[0]


def _build_stem(spec, rng, n):
    sylls = []
    for k in range(n):
        onsets = spec["onsets"]
        on = _wchoice(rng, onsets)
        if k > 0 and on == "":
            on = _wchoice(rng, {o: w for o, w in onsets.items() if o != "" and w > 0})
        allowed = spec.get("allowed", {}).get(on)
        vs = {v: w for v, w in spec["vowels"].items() if allowed is None or v in allowed}
        v = _wchoice(rng, vs or spec["vowels"])
        sylls.append([on, v, ""])

    if spec["coda_mode"] != "none":
        for k, s in enumerate(sylls):
            last = k == n - 1
            if spec["coda_mode"] == "final" and not last:
                continue
            if rng.random() < spec["coda_p"]:
                co = _wchoice(rng, spec["codas"])
                if not last:
                    next_on = sylls[k + 1][0]
                    # 母音と直接結びついて「kan+a → kana」のような読み替わりを避ける
                    if next_on == "":
                        co = ""
                    # 和風で「ん」の直後に h, y, w が来ると不自然なため抑止
                    elif spec.get("n_guard") and co == "n" and next_on in ("h", "y", "w"):
                        co = ""
                s[2] = co

    return "".join("".join(s) for s in sylls)


def _build_wafuu_family(rng: random.Random) -> str:
    """和風の自然で創作向きな名字を生成する"""
    if rng.random() < 0.15:
        return rng.choice(WAFUU_STANDALONE_FAMILIES)
    pref = rng.choice(WAFUU_FAMILY_PREFIXES)
    valid_suffixes = [s for s in WAFUU_FAMILY_SUFFIXES if s != pref]
    suf = rng.choice(valid_suffixes)
    return pref + suf


def _join(stem, suf, spec):
    if not suf:
        return stem
    if stem and stem[-1] in VOW and suf[0] in VOW:
        if not spec.get("no_elide"):
            stem = stem[:-1]
    elif stem and stem[-1] == suf[0]:
        stem = stem[:-1]
    elif spec.get("n_guard") and stem.endswith("n") and (suf[0] in VOW or suf[0] == "y"):
        stem = stem[:-1]
    return stem + suf


def _max_cluster(name):
    t = name.lower()
    for d in ("sh", "ch", "th", "ts", "gh", "ph", "ck", "kh", "wh", "zh"):
        t = t.replace(d, "X")
    runs = re.findall(r"[^aeiouy]+", t)
    return max((len(r) for r in runs), default=0)


def _levenshtein(a, b):
    if a == b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _too_similar(name, others):
    n = name.lower()
    for o in others:
        o = o.lower()
        if n == o:
            return True
        limit = 2 if min(len(n), len(o)) >= 5 else 1
        if _levenshtein(n, o) <= limit:
            return True
    return False


_SMALL_KANA = set("ァィゥェォャュョッぁぃぅぇぉゃゅょっ")


def _mora(kana: str) -> int:
    """拍数 (ファ→2, シャ→1 のように小さいカナは数えない)"""
    return sum(1 for ch in kana if ch not in _SMALL_KANA)


def _valid(name, spec, min_len, max_len):
    n = name.lower()
    if not (min_len <= len(n) <= max_len):
        return False
    if re.search(r"(.)\1\1", n):
        return False
    if not spec.get("allow_repeat") and re.search(r"(.{2,})\1", n):
        return False
    if _max_cluster(n) > spec.get("max_cluster", 3):
        return False
    if n in BLOCK_EXACT or any(b in n for b in BLOCK_SUBSTR_JP):
        return False
    if spec.get("kana") != "hiragana" and any(b in n for b in BLOCK_SUBSTR_EN):
        return False
    return True


def _kana(name, spec):
    is_wafuu = spec.get("kana") == "hiragana"
    k = to_katakana(name, is_wafuu=is_wafuu)
    return to_hiragana(k) if is_wafuu else k


def _prep(seed):
    if seed is None:
        seed = secrets.randbelow(10 ** 9)
    return seed, random.Random(f"name-gen:{seed}")


def _get_style(style):
    if style not in STYLES:
        raise ValueError(f"unknown style '{style}'. available: {', '.join(STYLES)}")
    return STYLES[style]


def _clamp_count(count):
    return max(1, min(int(count), 50))


def _collect(gen, count, spec, rng, avoid, starts_with, min_len, max_len, tries=None):
    """gen(rng) -> (name, extra_dict). 重複・類似・先頭文字の偏りを避けながら count 個集める"""
    results, taken = [], list(avoid)
    first_cap = max(2, math.ceil(count / 3)) if not starts_with else count
    first_seen = Counter()
    sw = (starts_with or "").lower()
    tries = tries or count * (300 if sw else 120)

    for _ in range(tries):
        if len(results) >= count:
            break
        name, extra = gen(rng)
        if not _valid(name, spec, min_len, max_len):
            continue
        if sw and not name.lower().startswith(sw):
            continue
        if _too_similar(name, taken):
            continue
        f = name[0].lower()
        if first_seen[f] >= first_cap:
            continue
        first_seen[f] += 1
        taken.append(name)
        entry = {"name": name.capitalize(), "kana": _kana(name, spec)}
        entry.update(extra)
        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# 予約ストア
# ---------------------------------------------------------------------------
def _store_path():
    p = os.environ.get("NAME_GEN_STORE")
    return Path(p) if p else Path.home() / ".name_generator_mcp" / "reserved.json"


def _load_store():
    try:
        return json.loads(_store_path().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save_store(d):
    p = _store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(d, ensure_ascii=False, indent=2)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(content, encoding="utf-8")
    try:
        os.replace(tmp, p)
    except OSError:
        # Windows で一時的にロックされている場合のフォールバック
        time.sleep(0.05)
        try:
            os.replace(tmp, p)
        except OSError:
            p.write_text(content, encoding="utf-8")
            if tmp.exists():
                try:
                    tmp.unlink(missing_ok=True)
                except OSError:
                    pass


def _reserved_names():
    return [v["name"] for v in _load_store().values()]


# ---------------------------------------------------------------------------
# 公開関数
# ---------------------------------------------------------------------------
def character_names(
    style: str = "elf",
    count: int = 5,
    gender: str = "any",
    seed: int | str | None = None,
    with_family: bool = False,
    starts_with: str | None = None,
    min_len: int = 3,
    max_len: int = 11,
    avoid: list[str] | None = None,
) -> dict:
    spec = _get_style(style)
    if gender not in ("any", "male", "female", "neutral"):
        raise ValueError("gender must be any / male / female / neutral")
    count = _clamp_count(count)
    seed, rng = _prep(seed)

    def gen(r):
        g = gender if gender != "any" else r.choices(["male", "female", "neutral"], [4, 4, 2])[0]
        stem = _build_stem(spec, r, r.randint(*spec["syll"]))
        ending = ""
        if r.random() < spec["ending_p"]:
            ending = r.choice(spec["endings"].get(g) or spec["endings"]["neutral"])
        name = _join(stem, ending, spec)
        extra = {"gender": g}
        if with_family:
            if style == "wafuu":
                fam = _build_wafuu_family(r)
            else:
                fstem = _build_stem(spec, r, r.randint(1, 2))
                fam = _join(fstem, r.choice(spec["family"]), spec)
            extra["family"] = fam.capitalize()
            extra["family_kana"] = _kana(fam, spec)
        return name, extra

    res = _collect(
        gen, count, spec, rng, _reserved_names() + list(avoid or []),
        starts_with, min_len, max_len
    )
    out = {"style": style, "seed": seed, "names": res}
    if len(res) < count:
        out["note"] = f"条件が厳しく {len(res)} 個しか作れませんでした (starts_with や予約リストを見直してください)"
    return out


def place_names(
    style: str = "elf",
    kind: str = "town",
    count: int = 5,
    seed: int | str | None = None,
    starts_with: str | None = None,
    min_len: int = 4,
    max_len: int = 14,
    avoid: list[str] | None = None,
) -> dict:
    spec = _get_style(style)
    if kind not in PLACE_KINDS:
        raise ValueError(f"kind must be one of: {', '.join(PLACE_KINDS)}")
    count = _clamp_count(count)
    seed, rng = _prep(seed)
    sfxs = spec["places"][kind]

    def gen(r):
        n_syl = r.randint(1, 2)
        while True:
            stem = _build_stem(spec, r, n_syl)
            suf, gloss = r.choice(sfxs)
            name = _join(stem, suf, spec)
            root = name[: len(name) - len(suf)] if name.endswith(suf) else name
            # 語幹が1拍だと「ロ砂漠」のようになるので、その場合だけ2音節でやり直す
            if _mora(_kana(root or name, spec)) >= 2 or n_syl == 2:
                break
            n_syl = 2
        # 和風は「machi=町」のように接尾辞ごとの漢字をそのまま使う (町なのに「村」になるのを防ぐ)
        term = gloss if style == "wafuu" else KIND_JA_TERM[kind]
        return name, {
            "kind": kind,
            "suffix": suf,
            "suffix_meaning": gloss,
            "ja_name": _kana(root or name, spec) + term,
        }

    res = _collect(
        gen, count, spec, rng, _reserved_names() + list(avoid or []),
        starts_with, min_len, max_len
    )
    out = {
        "style": style,
        "kind": kind,
        "kind_ja": PLACE_KIND_JA[kind],
        "seed": seed,
        "names": res,
        "note": "suffix_meaning は各スタイル固定の設定表 (同じ接尾辞は常に同じ意味)。地名の世界内一貫性に使える",
    }
    if len(res) < count:
        out["note"] += f" / {len(res)} 個しか作れませんでした"
    return out


def country_names(
    style: str = "elf",
    government: str = "kingdom",
    count: int = 5,
    seed: int | str | None = None,
    starts_with: str | None = None,
    min_len: int = 4,
    max_len: int = 13,
    avoid: list[str] | None = None,
) -> dict:
    """国名。語幹+国名の語尾に、政体ごとの日本語/英語の正式名と元首の称号を添える。"""
    spec = _get_style(style)
    if government not in GOVERNMENTS:
        raise ValueError(f"government must be one of: {', '.join(GOVERNMENTS)}")
    gov = GOVERNMENTS[government]
    endings = COUNTRY_ENDINGS[style]
    count = _clamp_count(count)
    seed, rng = _prep(seed)

    def gen(r):
        stem = _build_stem(spec, r, r.randint(1, 2))
        return _join(stem, r.choice(endings), spec), {}

    res = _collect(
        gen, count, spec, rng, _reserved_names() + list(avoid or []),
        starts_with, min_len, max_len
    )
    for e in res:
        e["government"] = government
        e["ja_name"] = e["kana"] + gov["ja"]
        e["en_formal"] = gov["en"].format(e["name"])
        e["ruler_title"] = gov["ruler"]
    out = {"style": style, "government": government, "seed": seed, "names": res}
    if len(res) < count:
        out["note"] = f"{len(res)} 個しか作れませんでした"
    return out


def _wpick(r, seq):
    """末尾の要素を重みとみなして seq から1つ選ぶ"""
    return r.choices(seq, weights=[x[-1] for x in seq], k=1)[0]


def _western_tavern(r, kind, whimsy=0.25):
    living = r.random() < 0.55
    n_en, n_ja = r.choice(NOUN_LIVING if living else NOUN_OBJECT)
    sfx_en, sfx_ja, _w = _wpick(r, TAVERN_SUFFIXES[kind])
    pattern = r.choices(["adj", "and", "bare"], [55, 30, 15], k=1)[0]
    words = {n_en}
    if pattern == "adj":
        # 物には本来「生き物用」の形容詞を付けないが、whimsy の確率で擬人化を許す
        # (眠れるランタン亭・眠らざるランタン亭のような詩的な屋号)
        personify = (not living) and r.random() < whimsy
        pool = ADJ_ANY + (ADJ_LIVING + ADJ_POETIC if (living or personify) else [])
        a_en, a_ja = r.choice(pool)
        core_en, core_ja = f"{a_en} {n_en}", f"{a_ja}{n_ja}"
    elif pattern == "and":
        n2_en, n2_ja = r.choice([w for w in NOUN_LIVING + NOUN_OBJECT if w[0] != n_en])
        words.add(n2_en)
        core_en, core_ja = f"{n_en} and {n2_en}", f"{n_ja}と{n2_ja}"
    else:
        core_en, core_ja = n_en, n_ja
    en = f"The {core_en}" + (f" {sfx_en}" if sfx_en else "")
    return {"ja": core_ja + sfx_ja, "en": en, "kind": kind}, words


def _wafuu_tavern(r, kind):
    w_ja, w_ro = r.choice(WAFUU_WORDS)
    sfx_ja, sfx_ro, _w = _wpick(r, WAFUU_TAVERN_SUFFIXES[kind])
    return {"ja": w_ja + sfx_ja, "en": w_ro.capitalize() + sfx_ro, "kind": kind}, {w_ro}


def tavern_names(
    tone: str = "western",
    kind: str = "any",
    count: int = 5,
    seed: int | str | None = None,
    avoid: list[str] | None = None,
    whimsy: float = 0.25,
) -> dict:
    """酒場・宿屋の屋号。西洋風は日英対訳 (酔いどれ鹿亭 / The Drunken Stag)、和風は漢字+ローマ字。"""
    if tone not in ("western", "wafuu"):
        raise ValueError("tone must be western / wafuu")
    if kind not in ("any", "tavern", "inn"):
        raise ValueError("kind must be any / tavern / inn")
    count = _clamp_count(count)
    seed, rng = _prep(seed)
    taken = {n.lower() for n in _reserved_names() + list(avoid or [])}
    whimsy = max(0.0, min(float(whimsy), 1.0))
    if tone == "western":
        def make(r, k):
            return _western_tavern(r, k, whimsy)
    else:
        make = _wafuu_tavern
    results, seen, used = [], set(), set()
    tries = count * 200
    for i in range(tries):
        if len(results) >= count:
            break
        rec, words = make(rng, kind if kind != "any" else rng.choice(["tavern", "inn"]))
        if rec["en"].lower() in taken or rec["ja"].lower() in taken or rec["en"].lower() in seen:
            continue
        # 前半は同じ単語(鹿など)を使い回さない。候補が尽きそうなら後半は許す
        if i < tries * 0.3 and used & words:
            continue
        seen.add(rec["en"].lower())
        used |= words
        results.append(rec)
    out = {"tone": tone, "seed": seed, "names": results}
    if len(results) < count:
        out["note"] = f"{len(results)} 個しか作れませんでした"
    return out


def names_from_examples(
    examples: list[str],
    count: int = 5,
    seed: int | str | None = None,
    order: int = 2,
    min_len: int | None = None,
    max_len: int | None = None,
    avoid: list[str] | None = None,
) -> dict:
    names = [e.strip() for e in examples if e and e.strip()]
    if len(names) < 3:
        raise ValueError("examples は3個以上ください (10個以上だと安定します)")
    count = _clamp_count(count)
    order = max(1, min(int(order), 3))
    seed, rng = _prep(seed)
    ascii_only = all(n.isascii() for n in names)
    norm = [n.lower() if ascii_only else n for n in names]

    models = {o: defaultdict(Counter) for o in range(1, order + 1)}
    for n in norm:
        seq = "^" * order + n + "$"
        for o in range(1, order + 1):
            for i in range(order, len(seq)):
                models[o][seq[i - o:i]][seq[i]] += 1

    lens = [len(n) for n in norm]
    lo = min_len or max(2, min(lens) - 1)
    hi = max_len or max(lens) + 2

    def gen(r):
        seq = "^" * order
        for _ in range(hi + 2):
            use = order if r.random() > 0.15 else max(1, order - 1)
            while use > 1 and seq[-use:] not in models[use]:
                use -= 1
            dist = models[use].get(seq[-use:])
            if not dist:
                break
            ch = r.choices(list(dist.keys()), weights=list(dist.values()))[0]
            if ch == "$":
                break
            seq += ch
        return seq[order:], {}

    class _Spec(dict):
        pass

    spec = _Spec(max_cluster=4, kana="katakana")
    base_avoid = names + _reserved_names() + list(avoid or [])

    if ascii_only:
        res = _collect(gen, count, spec, rng, base_avoid, None, lo, hi, tries=count * 400)
    else:
        res, taken = [], list(base_avoid)
        for _ in range(count * 400):
            if len(res) >= count:
                break
            nm, _e = gen(rng)
            # 2〜4文字の漢字名は1文字違いでも別の名前なので、完全一致だけを避ける
            if not (lo <= len(nm) <= hi) or nm in taken:
                continue
            taken.append(nm)
            res.append({"name": nm})

    out = {"seed": seed, "order": order, "names": res}
    if len(res) < count:
        out["note"] = f"{len(res)} 個しか作れませんでした。examples を増やすか order を下げてください"
    return out


def reserve(names: list[str], note: str = "") -> dict:
    store = _load_store()
    added, already = [], []
    for n in names:
        n = n.strip()
        if not n:
            continue
        k = n.lower()
        if k in store:
            already.append(n)
            continue
        store[k] = {
            "name": n,
            "note": note,
            "reserved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        added.append(n)
    _save_store(store)
    return {"reserved": added, "already_reserved": already, "total": len(store)}


def list_reserved_names() -> dict:
    store = _load_store()
    return {"total": len(store), "names": list(store.values()), "store_path": str(_store_path())}


def release(names: list[str]) -> dict:
    store = _load_store()
    removed, missing = [], []
    for n in names:
        k = n.strip().lower()
        if k in store:
            removed.append(store.pop(k)["name"])
        else:
            missing.append(n)
    _save_store(store)
    return {"released": removed, "not_found": missing, "total": len(store)}


def styles_overview() -> dict:
    out = []
    for key, spec in STYLES.items():
        rng = random.Random(f"demo:{key}")
        sample = []
        for _ in range(4):
            stem = _build_stem(spec, rng, rng.randint(*spec["syll"]))
            g = rng.choice(["male", "female"])
            sample.append(_join(stem, rng.choice(spec["endings"][g]), spec).capitalize())
        out.append({
            "style": key,
            "label": spec["label"],
            "description": spec["desc"],
            "samples": sample,
        })
    return {"styles": out, "place_kinds": PLACE_KIND_JA}


# ---------------------------------------------------------------------------
# MCP サーバー構築
# ---------------------------------------------------------------------------
def _build_server():
    try:
        from mcp.server.mcpserver import MCPServer
        ServerClass = MCPServer
    except (ImportError, ModuleNotFoundError):
        from mcp.server.fastmcp import FastMCP
        ServerClass = FastMCP

    mcp = ServerClass("fantasy-name-generator")

    # -----------------------------------------------------------------------
    # MCP Tools
    # -----------------------------------------------------------------------
    @mcp.tool(description="利用可能なスタイル一覧(elf/dwarf/human/orc/wafuu/arcane/southern)と地名種別を見本付きで返します。")
    def list_styles() -> dict:
        return styles_overview()

    @mcp.tool(description="キャラクター名を生成します。音素テーブル+乱数によりLLM特有の命名バイアスを回避します。")
    def generate_character_names(
        style: Annotated[
            StyleType,
            Field(description="命名スタイル: elf (エルフ), dwarf (ドワーフ), human (中世西洋), orc (オーク), wafuu (和風), arcane (古代魔術), southern (南方交易都市)")
        ] = "elf",
        count: Annotated[
            int,
            Field(description="生成する名前の個数 (1〜50)", ge=1, le=50)
        ] = 5,
        gender: Annotated[
            GenderType,
            Field(description="性別: any (指定なし), male (男性), female (女性), neutral (中性)")
        ] = "any",
        with_family: Annotated[
            bool,
            Field(description="姓 (ファミリーネーム) も合わせて生成するかどうか")
        ] = False,
        seed: Annotated[
            int | str | None,
            Field(description="乱数シード。同じシード・引数・予約状態なら完全に同じ結果が再現されます")
        ] = None,
        starts_with: Annotated[
            str | None,
            Field(description="名前の先頭文字列 (例: 'ka', 'el')")
        ] = None,
        avoid: Annotated[
            list[str] | None,
            Field(description="生成結果から除外したい名前のリスト (予約済みの名前は自動で除外されます)")
        ] = None,
    ) -> dict:
        return character_names(
            style=style,
            count=count,
            gender=gender,
            seed=seed,
            with_family=with_family,
            starts_with=starts_with,
            avoid=avoid,
        )

    @mcp.tool(description="地名を生成します。語幹+種別ごとの接尾辞(意味付き)により、世界観に一貫性のある地名を生成します。")
    def generate_place_names(
        style: Annotated[
            StyleType,
            Field(description="命名スタイル: elf / dwarf / human / orc / wafuu / arcane / southern")
        ] = "elf",
        kind: Annotated[
            PlaceKindType,
            Field(description="地名の種類: town (町・村), city (都市), mountain (山), river (川), forest (森), lake (湖), fortress (砦・城), kingdom (国), plains (平原), desert (砂漠), wasteland (荒野), swamp (湿地), hills (丘陵), valley (谷), coast (海岸), sea (海), island (島), cave (洞窟), ruins (遺跡)")
        ] = "town",
        count: Annotated[
            int,
            Field(description="生成する名前の個数 (1〜50)", ge=1, le=50)
        ] = 5,
        seed: Annotated[
            int | str | None,
            Field(description="乱数シード。再現性に利用可能")
        ] = None,
        starts_with: Annotated[
            str | None,
            Field(description="地名の先頭文字列 (例: 'al', 'gro')")
        ] = None,
        avoid: Annotated[
            list[str] | None,
            Field(description="除外したい名前のリスト")
        ] = None,
    ) -> dict:
        return place_names(
            style=style,
            kind=kind,
            count=count,
            seed=seed,
            starts_with=starts_with,
            avoid=avoid,
        )

    @mcp.tool(description="国名を生成します。政体(王国・帝国・共和国・公国・連邦・教国・部族連合)ごとの日本語名(ja_name)・英語の正式名(en_formal)・元首の称号を返します。")
    def generate_country_names(
        style: Annotated[
            StyleType,
            Field(description="命名スタイル: elf / dwarf / human / orc / wafuu / arcane / southern")
        ] = "elf",
        government: Annotated[
            GovernmentType,
            Field(description="政体: kingdom (王国), empire (帝国), republic (共和国), duchy (公国), federation (連邦), theocracy (教国), tribal (部族連合)")
        ] = "kingdom",
        count: Annotated[
            int,
            Field(description="生成する名前の個数 (1〜50)", ge=1, le=50)
        ] = 5,
        seed: Annotated[
            int | str | None,
            Field(description="乱数シード。再現性に利用可能")
        ] = None,
        starts_with: Annotated[
            str | None,
            Field(description="国名の先頭文字列 (例: 'al', 'gro')")
        ] = None,
        avoid: Annotated[
            list[str] | None,
            Field(description="除外したい名前のリスト")
        ] = None,
    ) -> dict:
        return country_names(
            style=style,
            government=government,
            count=count,
            seed=seed,
            starts_with=starts_with,
            avoid=avoid,
        )

    @mcp.tool(description="酒場・宿屋の屋号を生成します。西洋風は日英対訳(酔いどれ鹿亭 / The Drunken Stag)、和風は漢字+ローマ字(月見亭 / Tsukimitei)。")
    def generate_tavern_names(
        tone: Annotated[
            TavernToneType,
            Field(description="雰囲気: western (西洋風・日英対訳), wafuu (和風・漢字+ローマ字)")
        ] = "western",
        kind: Annotated[
            TavernKindType,
            Field(description="種別: any (酒場か宿屋をランダム), tavern (酒場), inn (宿屋)")
        ] = "any",
        count: Annotated[
            int,
            Field(description="生成する名前の個数 (1〜50)", ge=1, le=50)
        ] = 5,
        seed: Annotated[
            int | str | None,
            Field(description="乱数シード。再現性に利用可能")
        ] = None,
        avoid: Annotated[
            list[str] | None,
            Field(description="除外したい屋号のリスト (予約済みの名前は自動で除外されます)")
        ] = None,
        whimsy: Annotated[
            float,
            Field(description="擬人化の出現率 0〜1 (既定0.25)。物に「眠れる」「眠らざる」などを付けた詩的な屋号(眠らざるランタン亭)が出る割合。0で無効。西洋風のみ", ge=0.0, le=1.0)
        ] = 0.25,
    ) -> dict:
        return tavern_names(
            tone=tone,
            kind=kind,
            count=count,
            seed=seed,
            avoid=avoid,
            whimsy=whimsy,
        )

    @mcp.tool(description="既存の名前リストからマルコフ連鎖で文字連接を学習し、「同じ世界っぽい」新しい名前を生成します。")
    def generate_names_from_examples(
        examples: Annotated[
            list[str],
            Field(description="既存の名前リスト (3個以上、10個以上推奨。ローマ字・カナ・漢字に対応)")
        ],
        count: Annotated[
            int,
            Field(description="生成する名前の個数 (1〜50)", ge=1, le=50)
        ] = 5,
        seed: Annotated[
            int | str | None,
            Field(description="乱数シード")
        ] = None,
        order: Annotated[
            int,
            Field(description="マルコフ連鎖の次数 (1〜3、既定2)。次数が高いほど元の名前に近くなります", ge=1, le=3)
        ] = 2,
        avoid: Annotated[
            list[str] | None,
            Field(description="除外したい名前のリスト")
        ] = None,
    ) -> dict:
        return names_from_examples(
            examples=examples,
            count=count,
            seed=seed,
            order=order,
            avoid=avoid,
        )

    @mcp.tool(description="採用した名前を予約リストに記録します。以降の生成では同一・類似の名前が自動的に回避されます。")
    def reserve_names(
        names: Annotated[
            list[str],
            Field(description="予約・登録したい名前のリスト")
        ],
        note: Annotated[
            str,
            Field(description="メモやキャラクター・場所の役割説明")
        ] = "",
    ) -> dict:
        return reserve(names, note)

    @mcp.tool(description="現在予約済みの名前一覧を取得します。")
    def list_reserved() -> dict:
        return list_reserved_names()

    @mcp.tool(description="予約リストから指定した名前の予約を解除します。")
    def release_names(
        names: Annotated[
            list[str],
            Field(description="予約解除したい名前のリスト")
        ],
    ) -> dict:
        return release(names)

    # -----------------------------------------------------------------------
    # MCP Resources
    # -----------------------------------------------------------------------
    @mcp.resource("fantasy://styles")
    def get_styles_resource() -> str:
        """すべての命名スタイルと地名種別、見本サンプルのJSONデータ"""
        return json.dumps(styles_overview(), ensure_ascii=False, indent=2)

    @mcp.resource("fantasy://reserved")
    def get_reserved_resource() -> str:
        """現在採用・予約されている名前のリストとメモ"""
        return json.dumps(list_reserved_names(), ensure_ascii=False, indent=2)

    # -----------------------------------------------------------------------
    # MCP Prompts
    # -----------------------------------------------------------------------
    @mcp.prompt()
    def brainstorm_character(
        style: StyleType = "elf",
        role: str = "冒険者",
        gender: GenderType = "any",
    ) -> str:
        """キャラクターの命名と背景設定のブレインストーミング支援プロンプト"""
        label = STYLES.get(style, {}).get("label", style)
        return (
            f"あなたはファンタジー作品のクリエイティブ・アドバイザーです。\n"
            f"以下の設定に合わせて、魅力的で一貫性のあるキャラクターの名前と背景設定を作成してください。\n\n"
            f"- スタイル: {style} ({label})\n"
            f"- 役割・立場: {role}\n"
            f"- 性別: {gender}\n\n"
            f"【手順】\n"
            f"1. `generate_character_names` ツールを使って複数の名前候補 (with_family=True) を生成してください。\n"
            f"2. 生成された候補から最もイメージに合う名前を1〜2つ選定し、キャラクターの生い立ち・能力・性格を提案してください。\n"
            f"3. 決定した名前を `reserve_names` ツールで予約リストに登録してください。"
        )

    @mcp.prompt()
    def brainstorm_world_places(
        style: StyleType = "human",
        region_theme: str = "交易都市と国境の要塞",
    ) -> str:
        """世界観の構築と拠点・地理の命名支援プロンプト"""
        label = STYLES.get(style, {}).get("label", style)
        return (
            f"あなたはファンタジー世界の地理・世界観設定の専門家です。\n"
            f"以下の地域テーマに沿って、地図に載せるべき主要な拠点の地名と地理的特徴を設計してください。\n\n"
            f"- テーマ: {region_theme}\n"
            f"- 命名スタイル: {style} ({label})\n\n"
            f"【手順】\n"
            f"1. `generate_place_names` ツールを複数回呼び出し、都市(city)、町(town)、砦(fortress)、山(mountain)、川(river)などの地名を生成してください。\n"
            f"2. 各地名の接尾辞の意味 (suffix_meaning) を活かして、その土地の歴史・地形・文化の解説を作成してください。\n"
            f"3. 気に入った地名は `reserve_names` ツールで記録してください。"
        )

    return mcp


# ---------------------------------------------------------------------------
# CLI / デモ実行 / エントリポイント
# ---------------------------------------------------------------------------
def _demo():
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    os.environ.setdefault(
        "NAME_GEN_STORE",
        str(Path(os.environ.get("TMPDIR", "/tmp")) / "name_gen_demo.json"),
    )
    for key in STYLES:
        r = character_names(key, 5, seed=1, with_family=True)
        print(f"\n[{key}] {STYLES[key]['label']}")
        for n in r["names"]:
            fam_str = f" {n['family']}" if "family" in n else ""
            fam_kana = f" {n['family_kana']}" if "family_kana" in n else ""
            print(f"  {n['name']}{fam_str}  ({n['kana']}{fam_kana})  [{n['gender']}]")
        p = place_names(key, "town", 3, seed=1)
        print("  地名 (町):", ", ".join(f"{n['name']}({n['kana']}: {n['suffix_meaning']})" for n in p["names"]))
        d = place_names(key, "desert", 2, seed=1)
        print("  地名 (砂漠):", ", ".join(f"{n['name']}→{n['ja_name']}" for n in d["names"]))
        c = country_names(key, "kingdom", 2, seed=1)
        print("  国名:", ", ".join(f"{n['en_formal']}→{n['ja_name']}" for n in c["names"]))
    print("\n[酒場・宿屋]")
    for tone in ("western", "wafuu"):
        t = tavern_names(tone, "any", 4, seed=1)
        print(f"  {tone}:", ", ".join(f"{n['ja']} / {n['en']}" for n in t["names"]))


def main():
    if "--demo" in sys.argv:
        _demo()
    else:
        try:
            server = _build_server()
        except ImportError:
            sys.exit("mcp パッケージが必要です: pip install mcp")
        server.run()


if __name__ == "__main__":
    main()
