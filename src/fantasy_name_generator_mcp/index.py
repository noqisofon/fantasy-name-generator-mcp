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
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from .extra_data import (
    ADJ_ANY,
    ADJ_LIVING,
    ADJ_POETIC,
    COUNTRY_DYNASTY_OK,
    COUNTRY_ENDINGS,
    COUNTRY_EPITHETS,
    COUNTRY_KATAKANA,
    COUNTRY_PAIR_AND,
    COUNTRY_PATTERNS,
    COUNTRY_PREFIXES,
    EXTRA_PLACE_KINDS_JA,
    EXTRA_PLACES,
    GOVERNMENTS,
    KANJI_A,
    KANJI_B,
    KANJI_COLORS,
    KIND_JA_TERM,
    NOUN_LIVING,
    NOUN_OBJECT,
    SHOP_GROUP_KIN,
    SHOP_LOCATIONS,
    SHOP_PATTERNS_WAFUU,
    SHOP_PATTERNS_WESTERN,
    SHOP_TYPES,
    TAVERN_ABSTRACT,
    TAVERN_ACTS,
    TAVERN_KIN,
    TAVERN_PATTERNS_WAFUU,
    TAVERN_PATTERNS_WESTERN,
    TAVERN_SUFFIXES,
    TAVERN_VENUES,
    WAFUU_CREATURES,
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
# "any"(ランダム) + extra_data.GOVERNMENTS の全政体。表に政体を足すと enum も自動で増える
GovernmentType = Literal[("any", *GOVERNMENTS)]  # type: ignore[valid-type]
# "any"(ランダム) + extra_data.SHOP_TYPES の全種類。表に店の種類を足すと enum も自動で増える
ShopType = Literal[("any", *SHOP_TYPES)]  # type: ignore[valid-type]
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
    "pus", "napoli", "milano", "roma", "paris", "london", "berlin", "madrid", "athens",
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


class _SimIndex:
    """類似名の判定を速くする索引 (_too_similar と同じ結果を返す)。

    名前から 2 文字まで削って作った断片を辞書に持つ。編集距離が 2 以下の名前どうしは、必ず断片を共有するので、
    候補の名前だけ本当の編集距離で確かめればよい。総当たりだと個数の2乗で遅くなる (3000個で約4分) ところが、
    ほぼ個数に比例する時間で済む。
    """

    def __init__(self, names=()):
        self._names: set[str] = set()
        self._buckets: dict[str, set[str]] = defaultdict(set)
        for n in names:
            self.add(n)

    @staticmethod
    def _variants(n: str) -> set[str]:
        out = {n}
        for i in range(len(n)):
            d1 = n[:i] + n[i + 1:]
            out.add(d1)
            for j in range(i, len(d1)):
                out.add(d1[:j] + d1[j + 1:])
        return out

    def add(self, name: str) -> None:
        n = name.lower()
        if n in self._names:
            return
        self._names.add(n)
        for v in self._variants(n):
            self._buckets[v].add(n)

    def similar(self, name: str) -> bool:
        n = name.lower()
        if n in self._names:
            return True
        cand: set[str] = set()
        for v in self._variants(n):
            b = self._buckets.get(v)
            if b:
                cand |= b
        for o in cand:
            limit = 2 if min(len(n), len(o)) >= 5 else 1
            if _levenshtein(n, o) <= limit:
                return True
        return False


class _ExactIndex:
    """完全な重複だけを避ける索引 (loose=True 用。_SimIndex と同じ口)"""

    def __init__(self, names=()):
        self._s = {n.lower() for n in names}

    def add(self, name: str) -> None:
        self._s.add(name.lower())

    def similar(self, name: str) -> bool:
        return name.lower() in self._s


def _shortfall_note(got: int, want: int, loose: bool) -> str:
    """個数が足りなかったときの注記 (CLI はこの文をそのまま表示する)"""
    hint = "" if loose else "似た名前を避けているため候補が尽きました。loose=True (CLI は --loose) で完全な重複だけを避けるようにできます。"
    return f"{got} 個しか作れませんでした (要求 {want})。{hint}starts_with や予約リストで絞っていれば、それも見直してください"


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


STALL_WINDOW = 20000  # 直近これだけの試行で、
STALL_MIN_OK = 40  # 新しい名前がこの数未満しか取れなければ、候補が尽きたとみなして打ち切る
MAX_COUNT = 10000  # ライブラリ / CLI で一度に作れる上限。MCP ツールは AI に返す量を抑えるため別途 50 まで


def _clamp_count(count) -> int:
    """個数を検証する。範囲外は黙って丸めず、エラーにして知らせる"""
    n = int(count)
    if not 1 <= n <= MAX_COUNT:
        raise ValueError(f"count は 1〜{MAX_COUNT} で指定してください (指定: {n})")
    return n


def _collect(gen, count, spec, rng, avoid, starts_with, min_len, max_len, tries=None, loose=False):
    """gen(rng) -> (name, extra_dict). 重複・類似・先頭文字の偏りを避けながら count 個集める"""
    results, taken = [], (_ExactIndex(avoid) if loose else _SimIndex(avoid))
    first_cap = max(2, math.ceil(count / 3)) if not starts_with else count
    first_seen = Counter()
    sw = (starts_with or "").lower()
    tries = tries or count * (300 if sw else 120)
    recent_ok: deque[int] = deque()  # 直近の窓で新しい名前が取れた試行の番号

    for i in range(tries):
        if len(results) >= count:
            break
        while recent_ok and recent_ok[0] <= i - STALL_WINDOW:
            recent_ok.popleft()
        if i >= STALL_WINDOW and len(recent_ok) < STALL_MIN_OK:  # 候補が尽きたら諦める
            break
        name, extra = gen(rng)
        if not _valid(name, spec, min_len, max_len):
            continue
        if sw and not name.lower().startswith(sw):
            continue
        if taken.similar(name):
            continue
        f = name[0].lower()
        if first_seen[f] >= first_cap:
            continue
        first_seen[f] += 1
        taken.add(name)
        recent_ok.append(i)
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
    loose: bool = False,
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
        starts_with, min_len, max_len, loose=loose
    )
    out = {"style": style, "seed": seed, "names": res}
    if len(res) < count:
        out["note"] = _shortfall_note(len(res), count, loose)
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
    loose: bool = False,
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
        starts_with, min_len, max_len, loose=loose
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
        out["note"] += " / " + _shortfall_note(len(res), count, loose)
    return out


def country_names(
    style: str = "elf",
    government: str = "any",
    count: int = 5,
    seed: int | str | None = None,
    starts_with: str | None = None,
    min_len: int = 4,
    max_len: int = 13,
    avoid: list[str] | None = None,
    decorate: bool = True,
    loose: bool = False,
) -> dict:
    """国名。政体は既定でランダム (any)。decorate=True なら、地域名の前置き・二つ名・二つの名前の並記・
    カタカナ型などの「型」も混ぜる。日本語名(ja_name)・英語の正式名(en_formal)・元首の称号を返す。"""
    spec = _get_style(style)
    if government != "any" and government not in GOVERNMENTS:
        raise ValueError(f"government must be 'any' or one of: {', '.join(GOVERNMENTS)}")
    endings = COUNTRY_ENDINGS[style]
    gov_keys = list(GOVERNMENTS)
    gov_weights = [GOVERNMENTS[k]["w"] for k in gov_keys]
    pat_names = list(COUNTRY_PATTERNS)
    pat_weights = [COUNTRY_PATTERNS[k] for k in pat_names]
    count = _clamp_count(count)
    seed, rng = _prep(seed)

    def second_name(r, main):
        for _ in range(8):
            n = _build_stem(spec, r, r.randint(1, 2))
            if n != main.lower() and _valid(n, spec, 2, 9):
                return n
        return None

    def gen(r):
        gkey = government if government != "any" else r.choices(gov_keys, weights=gov_weights, k=1)[0]
        stem = _build_stem(spec, r, r.randint(1, 2))
        name = _join(stem, r.choice(endings), spec)
        extra = {"government": gkey, "pattern": "plain"}
        if decorate:
            pat = r.choices(pat_names, weights=pat_weights, k=1)[0]
            if pat == "prefix":
                extra["_prefix"] = r.choice(COUNTRY_PREFIXES)
            elif pat == "epithet":
                extra["_epithet"] = r.choice(COUNTRY_EPITHETS)
            elif pat == "katakana" and gkey not in COUNTRY_KATAKANA:
                pat = "plain"
            elif pat in ("pair", "dynasty_realm"):
                n2 = second_name(r, name) if (pat == "pair" or gkey in COUNTRY_DYNASTY_OK) else None
                if n2 is None:
                    pat = "plain"
                else:
                    extra["_name2"] = n2
            if pat in ("bare", "no_of"):
                # 政体を名乗らない型。ランダム時は素直に「国」、政体を指定されたときは普通の型に戻す
                if government == "any":
                    extra["government"] = "nation"
                else:
                    pat = "plain"
            extra["pattern"] = pat
        return name, extra

    res = _collect(
        gen, count, spec, rng, _reserved_names() + list(avoid or []),
        starts_with, min_len, max_len, loose=loose
    )
    for e in res:
        _compose_country(e, spec)
    out = {"style": style, "government": government, "seed": seed, "names": res}
    if len(res) < count:
        out["note"] = _shortfall_note(len(res), count, loose)
    return out


def _compose_country(e: dict, spec: dict) -> None:
    """生成した名前(e)に、型に応じた日本語名・英語の正式名・元首の称号を付ける"""
    key, pat = e["government"], e["pattern"]
    gov = GOVERNMENTS[key]
    name, kana, term, en_t = e["name"], e["kana"], gov["ja"], gov["en"]
    n2 = e.pop("_name2", None)
    n2_kana = _kana(n2, spec) if n2 else ""
    n2_en = n2.capitalize() if n2 else ""
    prefix, epithet = e.pop("_prefix", None), e.pop("_epithet", None)
    if pat == "prefix":
        ja, en = f"{prefix[0]}{kana}{term}", en_t.format(f"{prefix[1]} {name}")
    elif pat == "epithet":
        ja, en = f"{epithet[0]}{term} {kana}", f"The {epithet[1]} {en_t.format(name)}"
    elif pat == "bare":
        ja, en = kana, name
    elif pat == "no_of":
        ja, en = f"{kana}の国", f"Land of {name}"
    elif pat == "pair":
        if key in COUNTRY_PAIR_AND:
            ja, en = f"{kana}及び{n2_kana}{term}", en_t.format(f"{name} and {n2_en}")
        else:
            ja, en = f"{kana}・{n2_kana}{term}", en_t.format(f"{name}-{n2_en}")
    elif pat == "katakana":
        kata, en_k = COUNTRY_KATAKANA[key]
        ja, en = f"{kana}・{kata}", en_k.format(name)
    elif pat == "dynasty_realm":
        ja, en = f"{n2_kana}朝{kana}{term}", f"{en_t.format(name)} under the {n2_en} Dynasty"
    else:  # plain
        ja, en = f"{kana}{term}", en_t.format(name)
    e["government_ja"] = term
    e["ja_name"] = ja
    e["en_formal"] = en
    e["ruler_title"] = gov["ruler"]


def _wpick(r, seq):
    """末尾の要素を重みとみなして seq から1つ選ぶ"""
    return r.choices(seq, weights=[x[-1] for x in seq], k=1)[0]


# 人名の屋号 (「リーター兄さん亭」など) に付けて自然な語尾
_PERSON_SUFFIX_OK = {"亭", "軒", "の宿", "の宿屋", "の酒場", "の飲み屋", "荘", "館", "酒場", "の旅館"}


def _person(r, spec):
    """屋号に入れる人名を作る。(英語表記, カナ)"""
    for _ in range(10):
        stem = _build_stem(spec, r, r.randint(1, 2))
        gender = r.choice(["male", "female", "neutral"])
        ending = ""
        if r.random() < spec["ending_p"]:
            ending = r.choice(spec["endings"].get(gender) or spec["endings"]["neutral"])
        n = _join(stem, ending, spec)
        if _valid(n, spec, 4, 9):  # 3文字以下は pus のような英単語と紛れるので避ける
            return n.capitalize(), _kana(n, spec)
    return "Ilda", "イルダ"


def _adj_noun(r, whimsy):
    """形容詞+名詞 → (英語, 日本語, 使った名詞)。物には、whimsy の確率だけ生き物用の形容詞も付ける"""
    living = r.random() < 0.55
    n_en, n_ja = r.choice(NOUN_LIVING if living else NOUN_OBJECT)
    personify = (not living) and r.random() < whimsy
    pool = ADJ_ANY + (ADJ_LIVING + ADJ_POETIC if (living or personify) else [])
    a_en, a_ja = r.choice(pool)
    return f"{a_en} {n_en}", f"{a_ja}{n_ja}", n_en


def _en_tail(core: str, sfx_en: str) -> str:
    return core + (f" {sfx_en}" if sfx_en else "")


def _pick_pattern(r, table: dict) -> str:
    return r.choices(list(table), weights=list(table.values()), k=1)[0]


def _person_suffix(r, seq):
    ok = [x for x in seq if x[1] in _PERSON_SUFFIX_OK]
    return _wpick(r, ok or seq)


def _western_tavern(r, kind, whimsy=0.25, spec=None):
    """西洋風の屋号。日本語(ja)と英語(en)の対訳を返す"""
    spec = spec or STYLES["human"]
    pat = _pick_pattern(r, TAVERN_PATTERNS_WESTERN)
    sfx_en, sfx_ja, _w = _wpick(r, TAVERN_SUFFIXES[kind])
    words = set()
    if pat == "adj":
        en_c, ja_c, n = _adj_noun(r, whimsy)
        words, en, ja = {n}, _en_tail(f"The {en_c}", sfx_en), ja_c + sfx_ja
    elif pat == "and":
        n1_en, n1_ja = r.choice(NOUN_LIVING + NOUN_OBJECT)
        n2_en, n2_ja = r.choice([w for w in NOUN_LIVING + NOUN_OBJECT if w[0] != n1_en])
        words = {n1_en, n2_en}
        en, ja = _en_tail(f"The {n1_en} and {n2_en}", sfx_en), f"{n1_ja}と{n2_ja}{sfx_ja}"
    elif pat == "bare":
        n_en, n_ja = r.choice(NOUN_LIVING + NOUN_OBJECT)
        words, en, ja = {n_en}, _en_tail(f"The {n_en}", sfx_en), n_ja + sfx_ja
    elif pat == "creature_act":
        c_en, c_ja = r.choice(NOUN_LIVING)
        a_ja, a_en, _ro = r.choice(TAVERN_ACTS)
        words = {c_en}
        en, ja = _en_tail(f"The {c_en}'s {a_en}", sfx_en), f"{c_ja}の{a_ja}{sfx_ja}"
    elif pat == "person_kin":
        sfx_en, sfx_ja, _w = _person_suffix(r, TAVERN_SUFFIXES[kind])
        n_en, n_ja = _person(r, spec)
        k_ja, k_en, _ro = r.choice(TAVERN_KIN)
        words = {n_en}
        en, ja = _en_tail(f"{k_en} {n_en}'s", sfx_en or "Tavern"), f"{n_ja}{k_ja}{sfx_ja}"
    elif pat == "person_thing":
        sfx_en, sfx_ja, _w = _person_suffix(r, TAVERN_SUFFIXES[kind])
        n_en, n_ja = _person(r, spec)
        t_ja, t_en, _ro = r.choice(TAVERN_ACTS)
        words = {n_en}
        en, ja = _en_tail(f"{n_en}'s {t_en}", sfx_en), f"{n_ja}の{t_ja}{sfx_ja}"
    elif pat == "type_first":
        v_ja, v_en, _ro, _w2 = _wpick(r, TAVERN_VENUES[kind])
        src = r.choices(["adj", "person", "abstract"], [55, 30, 15], k=1)[0]
        if src == "adj":
            en_c, ja_c, n = _adj_noun(r, whimsy)
            words, en, ja = {n}, f"The {en_c} {v_en}", f"{v_ja} {ja_c}"
        elif src == "person":
            n_en, n_ja = _person(r, spec)
            words, en, ja = {n_en}, f"{n_en}'s {v_en}", f"{v_ja} {n_ja}"
        else:
            b_ja, b_en, _ro2 = r.choice(TAVERN_ABSTRACT)
            words, en, ja = {b_en}, f"The {b_en} {v_en}", f"{v_ja} {b_ja}"
    elif pat == "kanji":
        a_ja, a_en, _r1 = r.choice(KANJI_A)
        b_ja, b_en, _r2 = r.choice(KANJI_B)
        gloss = f"{a_en} {b_en}"  # 英語は常に「色 + 自然」(Jade Moon)
        # 「月翠」のように 自然+色 の並びも、色の語のときだけ使う
        comp_ja = b_ja + a_ja if (a_ja in KANJI_COLORS and r.random() < 0.2) else a_ja + b_ja
        words, en, ja = {comp_ja}, _en_tail(f"The {gloss}", sfx_en), comp_ja + sfx_ja
    else:  # abstract
        b_ja, b_en, _ro2 = r.choice(TAVERN_ABSTRACT)
        words, en, ja = {b_en}, _en_tail(f"The {b_en}", sfx_en), b_ja + sfx_ja
    return {"ja": ja, "en": en, "kind": kind, "pattern": pat}, words


def _ro_join(base: str, sfx_ro: str) -> str:
    """ローマ字表記の連結。「 no Yu」のように空白で始まる語尾はそのまま、複数語の語幹にはハイフンを挟む"""
    if sfx_ro.startswith(" "):
        return base + sfx_ro
    return f"{base}-{sfx_ro}" if (" " in base or len(sfx_ro) > 4) else base + sfx_ro


def _wafuu_tavern(r, kind, whimsy=0.25, spec=None):
    """和風の屋号。漢字表記(ja)とローマ字(en)を返す"""
    spec = spec or STYLES["human"]
    pat = _pick_pattern(r, TAVERN_PATTERNS_WAFUU)
    sfx_ja, sfx_ro, _w = _wpick(r, WAFUU_TAVERN_SUFFIXES[kind])
    if pat == "word":
        w_ja, w_ro = r.choice(WAFUU_WORDS)
        ja, en, words = w_ja + sfx_ja, _ro_join(w_ro.capitalize(), sfx_ro), {w_ro}
    elif pat == "kanji":
        a_ja, _a_en, a_ro = r.choice(KANJI_A)
        b_ja, _b_en, b_ro = r.choice(KANJI_B)
        comp_ja, comp_ro = a_ja + b_ja, (a_ro + b_ro).capitalize()
        ja, en, words = comp_ja + sfx_ja, _ro_join(comp_ro, sfx_ro), {comp_ja}
    elif pat == "abstract":
        b_ja, _b_en, b_ro = r.choice(TAVERN_ABSTRACT)
        ja, en, words = b_ja + sfx_ja, _ro_join(b_ro.title(), sfx_ro), {b_ro}
    elif pat == "creature_act":
        c_ja, c_ro = r.choice(WAFUU_CREATURES)
        a_ja, _a_en, a_ro = r.choice(TAVERN_ACTS)
        ja = f"{c_ja}の{a_ja}{sfx_ja}"
        en = _ro_join(f"{c_ro.capitalize()} no {a_ro.capitalize()}", sfx_ro)
        words = {c_ro}
    elif pat == "person_kin":
        sfx_ja, sfx_ro, _w = _person_suffix_wafuu(r, kind, _WAFUU_KIN_SFX)
        n_en, n_ja = _person(r, spec)
        k_ja, _k_en, k_ro = r.choice(TAVERN_KIN)
        ja, en, words = f"{n_ja}{k_ja}{sfx_ja}", _ro_join(f"{n_en} {k_ro}", sfx_ro), {n_en}
    elif pat == "person_thing":
        sfx_ja, sfx_ro, _w = _person_suffix_wafuu(r, kind, _WAFUU_THING_SFX)
        n_en, n_ja = _person(r, spec)
        t_ja, _t_en, t_ro = r.choice(TAVERN_ACTS)
        ja = f"{n_ja}の{t_ja}{sfx_ja}"
        en, words = _ro_join(f"{n_en} no {t_ro.capitalize()}", sfx_ro), {n_en}
    else:  # type_first
        v_ja, _v_en, v_ro, _w2 = _wpick(r, TAVERN_VENUES[kind])
        src = r.choices(["word", "kanji", "abstract", "person"], [35, 30, 15, 20], k=1)[0]
        if src == "word":
            p_ja, p_ro = r.choice(WAFUU_WORDS)
            p_ro = p_ro.capitalize()
        elif src == "kanji":
            a_ja, _a, a_ro = r.choice(KANJI_A)
            b_ja, _b, b_ro = r.choice(KANJI_B)
            p_ja, p_ro = a_ja + b_ja, (a_ro + b_ro).capitalize()
        elif src == "abstract":
            p_ja, _e, p_ro = r.choice(TAVERN_ABSTRACT)
            p_ro = p_ro.title()
        else:
            p_ro, p_ja = _person(r, spec)
        ja, en, words = f"{v_ja} {p_ja}", f"{v_ro.capitalize()} {p_ro}", {p_ja}
    return {"ja": ja, "en": en, "kind": kind, "pattern": pat}, words


# 和風で「人名+親族」「人名の物」に付けて自然な語尾 (「おばちゃん屋」のような不自然なものを除く)
_WAFUU_KIN_SFX = {"亭", "軒", "の宿", "荘", "の酒処", "茶屋", "居酒屋", "館"}
_WAFUU_THING_SFX = _WAFUU_KIN_SFX | {"屋", "の湯", "の山荘"}


def _person_suffix_wafuu(r, kind, allowed):
    ok = [x for x in WAFUU_TAVERN_SUFFIXES[kind] if x[0] in allowed]
    return _wpick(r, ok or WAFUU_TAVERN_SUFFIXES[kind])


def tavern_names(
    tone: str = "western",
    kind: str = "any",
    count: int = 5,
    seed: int | str | None = None,
    avoid: list[str] | None = None,
    whimsy: float = 0.25,
    style: str = "human",
) -> dict:
    """酒場・宿屋の屋号。西洋風は日英対訳 (酔いどれ鹿亭 / The Drunken Stag)、和風は漢字+ローマ字。
    「生き物の動作」(ケンタウロスの溜息亭)・「人名+親族」(バーブラおばあ亭)・「種類が前」(宿屋 キャスリン)・
    漢字二字(金海亭)・抽象語(流浪亭)など、多くの型を混ぜる。人名の響きは style で選ぶ。"""
    if tone not in ("western", "wafuu"):
        raise ValueError("tone must be western / wafuu")
    if kind not in ("any", "tavern", "inn"):
        raise ValueError("kind must be any / tavern / inn")
    spec = _get_style(style)
    count = _clamp_count(count)
    seed, rng = _prep(seed)
    taken = {n.lower() for n in _reserved_names() + list(avoid or [])}
    whimsy = max(0.0, min(float(whimsy), 1.0))
    make = _western_tavern if tone == "western" else _wafuu_tavern
    results, seen, used = [], set(), set()
    tries = count * 200
    for i in range(tries):
        if len(results) >= count:
            break
        rec, words = make(rng, kind if kind != "any" else rng.choice(["tavern", "inn"]), whimsy, spec)
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


_KATAKANA_WORD_RE = re.compile(r"^[ァ-ヺー]+$")


def _is_katakana_word(s: str) -> bool:
    """店の種類語が「マーチャンダイズ」のようなカタカナの外来語かどうか。つなぎの助詞を変えるのに使う"""
    return bool(_KATAKANA_WORD_RE.match(s))


def _shop_link(main_ja: str, t_ja: str, katakana_style: str = "no") -> str:
    """名前部分と店の種類語をつなぐ助詞を選ぶ。種類語が「マーチャンダイズ」のようなカタカナの
    外来語のときだけ katakana_style に従う: "no"=「の」のまま (生き物+品など) /
    "nakaguro"=「・」でつなぐ (人名。「ウォリス・ショップ」) / "bare"=直結 (集団・血縁。「六姉妹ドラッグ」)。
    それ以外の語には常に「の」を使う"""
    if _is_katakana_word(t_ja):
        if katakana_style == "bare":
            return main_ja + t_ja
        if katakana_style == "nakaguro":
            return f"{main_ja}・{t_ja}"
    return f"{main_ja}の{t_ja}"


def _shop_link_ro(main_ro: str, t_ja: str, T: str, katakana_style: str = "no") -> str:
    """_shop_link のローマ字版。カタカナの外来語で「・」/直結になる場合は「no」を省いて空白だけでつなぐ"""
    if _is_katakana_word(t_ja) and katakana_style in ("bare", "nakaguro"):
        return f"{main_ro} {T}"
    return f"{main_ro} no {T}"


def _shop_western(r, shop_type, whimsy=0.25, spec=None):
    """西洋風の店名。日本語(ja)と英語(en)の対訳を返す"""
    spec = spec or STYLES["human"]
    st = SHOP_TYPES[shop_type]
    t_ja, t_en, _ro = r.choice(st["names"])
    pat = _pick_pattern(r, SHOP_PATTERNS_WESTERN)

    def adj_creature():
        c_en, c_ja = r.choice(NOUN_LIVING)
        pool = ADJ_ANY + ADJ_LIVING + (ADJ_POETIC if r.random() < whimsy else [])
        a_en, a_ja = r.choice(pool)
        return a_en, a_ja, c_en, c_ja

    if pat == "adj_creature":
        a_en, a_ja, c_en, c_ja = adj_creature()
        words, ja, en = {c_en}, f"{a_ja}{c_ja}の{t_ja}", f"The {a_en} {c_en} {t_en}"
    elif pat == "creature_good":
        c_en, c_ja = r.choice(NOUN_LIVING)
        g_ja, g_en, _g = r.choice(st["goods"])
        words, ja, en = {c_en}, f"{c_ja}の{g_ja}{t_ja}", f"The {c_en}'s {g_en} {t_en}"
    elif pat == "creature_shop":
        c_en, c_ja = r.choice(NOUN_LIVING)
        words, ja, en = {c_en}, _shop_link(c_ja, t_ja), f"The {c_en} {t_en}"
    elif pat == "good_shop":
        g_ja, g_en, _g = r.choice(st["goods"])
        words, ja, en = {g_en}, _shop_link(g_ja, t_ja), f"The {g_en} {t_en}"
    elif pat == "person_shop":
        n_en, n_ja = _person(r, spec)
        words, ja = {n_en}, _shop_link(n_ja, t_ja, katakana_style="nakaguro")
        en = f"{n_en}'s {t_en}"
    elif pat == "person_bare":
        n_en, n_ja = _person(r, spec)
        words, ja, en = {n_en}, n_ja + t_ja, f"{n_en} {t_en}"
    elif pat == "two_person":
        n1_en, n1_ja = _person(r, spec)
        n2_en, n2_ja = _person(r, spec)
        for _ in range(5):
            if n2_en != n1_en:
                break
            n2_en, n2_ja = _person(r, spec)
        words = {n1_en, n2_en}
        ja = _shop_link(f"{n1_ja}と{n2_ja}", t_ja, katakana_style="nakaguro")
        en = f"{n1_en} & {n2_en}'s {t_en}"
    elif pat == "person_kin":
        n_en, n_ja = _person(r, spec)
        k_ja, k_en, _k = r.choice(TAVERN_KIN)
        words, ja = {n_en}, _shop_link(f"{n_ja}{k_ja}", t_ja, katakana_style="nakaguro")
        en = f"{k_en} {n_en}'s {t_en}"
    elif pat == "location_shop":
        loc_ja, loc_en, _loc_ro = r.choice(SHOP_LOCATIONS)
        if r.random() < 0.5:
            n_en, n_ja = _person(r, spec)
            words, ja, en = {n_en}, f"{loc_ja}{n_ja}の{t_ja}", f"The {loc_en} {n_en}'s {t_en}"
        else:
            words, ja, en = set(), f"{loc_ja}{t_ja}", f"The {loc_en} {t_en}"
    elif pat == "group_kin_shop":
        g_ja, g_en, _g_ro = r.choice(SHOP_GROUP_KIN)
        if r.random() < 0.35:
            n_en, n_ja = _person(r, spec)
            words = {n_en}
            ja = _shop_link(f"{g_ja}{n_ja}", t_ja, katakana_style="bare")
            en = f"The {g_en} {n_en}'s {t_en}"
        else:
            words = set()
            ja = _shop_link(g_ja, t_ja, katakana_style="bare")
            en = f"The {g_en} {t_en}"
    elif pat == "type_first":
        src = r.choices(["adj", "person", "abstract"], [55, 30, 15], k=1)[0]
        if src == "adj":
            a_en, a_ja, c_en, c_ja = adj_creature()
            words, ja, en = {c_en}, f"{t_ja} {a_ja}{c_ja}", f"The {a_en} {c_en} {t_en}"
        elif src == "person":
            n_en, n_ja = _person(r, spec)
            words, ja, en = {n_en}, f"{t_ja} {n_ja}", f"{n_en}'s {t_en}"
        else:
            b_ja, b_en, _b = r.choice(TAVERN_ABSTRACT)
            words, ja, en = {b_en}, f"{t_ja} {b_ja}", f"The {b_en} {t_en}"
    elif pat == "kanji":
        a_ja, a_en, _a = r.choice(KANJI_A)
        b_ja, b_en, _b = r.choice(KANJI_B)
        comp = b_ja + a_ja if (a_ja in KANJI_COLORS and r.random() < 0.2) else a_ja + b_ja
        words, ja, en = {comp}, f"{comp}{t_ja}", f"The {a_en} {b_en} {t_en}"
    else:  # abstract
        b_ja, b_en, _b = r.choice(TAVERN_ABSTRACT)
        words, ja, en = {b_en}, f"{b_ja}の{t_ja}", f"The {b_en} {t_en}"
    return {"ja": ja, "en": en, "shop_type": shop_type, "shop_type_ja": st["label"], "pattern": pat}, words


def _shop_wafuu(r, shop_type, whimsy=0.25, spec=None):
    """和風の店名。漢字表記(ja)とローマ字(en)を返す"""
    spec = spec or STYLES["human"]
    st = SHOP_TYPES[shop_type]
    t_ja, _t_en, t_ro = r.choice(st["names"])
    T = t_ro.capitalize()
    pat = _pick_pattern(r, SHOP_PATTERNS_WAFUU)
    if pat == "creature_shop":
        c_ja, c_ro = r.choice(WAFUU_CREATURES)
        words, ja = {c_ro}, _shop_link(c_ja, t_ja)
        en = _shop_link_ro(c_ro.capitalize(), t_ja, T)
    elif pat == "creature_good":
        c_ja, c_ro = r.choice(WAFUU_CREATURES)
        g_ja, _g_en, g_ro = r.choice(st["goods"])
        words, ja, en = {c_ro}, f"{c_ja}の{g_ja}{t_ja}", f"{c_ro.capitalize()} no {g_ro.capitalize()} {T}"
    elif pat == "good_shop":
        g_ja, _g_en, g_ro = r.choice(st["goods"])
        words, ja = {g_ro}, _shop_link(g_ja, t_ja)
        en = _shop_link_ro(g_ro.capitalize(), t_ja, T)
    elif pat == "person_shop":
        n_en, n_ja = _person(r, spec)
        words, ja = {n_en}, _shop_link(n_ja, t_ja, katakana_style="nakaguro")
        en = _shop_link_ro(n_en, t_ja, T, katakana_style="nakaguro")
    elif pat == "person_bare":
        n_en, n_ja = _person(r, spec)
        words, ja, en = {n_en}, n_ja + t_ja, f"{n_en} {T}"
    elif pat == "two_person":
        n1_en, n1_ja = _person(r, spec)
        n2_en, n2_ja = _person(r, spec)
        for _ in range(5):
            if n2_en != n1_en:
                break
            n2_en, n2_ja = _person(r, spec)
        words = {n1_en, n2_en}
        ja = _shop_link(f"{n1_ja}と{n2_ja}", t_ja, katakana_style="nakaguro")
        combo = f"{n1_en} to {n2_en}"
        en = _shop_link_ro(combo, t_ja, T, katakana_style="nakaguro")
    elif pat == "person_kin":
        n_en, n_ja = _person(r, spec)
        k_ja, _k_en, k_ro = r.choice(TAVERN_KIN)
        words, ja = {n_en}, _shop_link(f"{n_ja}{k_ja}", t_ja, katakana_style="nakaguro")
        en = _shop_link_ro(f"{n_en} {k_ro}", t_ja, T, katakana_style="nakaguro")
    elif pat == "location_shop":
        loc_ja, _loc_en, loc_ro = r.choice(SHOP_LOCATIONS)
        if r.random() < 0.5:
            n_en, n_ja = _person(r, spec)
            words = {n_en}
            ja = f"{loc_ja}{n_ja}の{t_ja}"
            en = f"{loc_ro.capitalize()} no {n_en} no {T}"
        else:
            words, ja, en = set(), f"{loc_ja}{t_ja}", f"{loc_ro.capitalize()} no {T}"
    elif pat == "group_kin_shop":
        g_ja, _g_en, g_ro = r.choice(SHOP_GROUP_KIN)
        if r.random() < 0.35:
            n_en, n_ja = _person(r, spec)
            words = {n_en}
            ja = _shop_link(f"{g_ja}{n_ja}", t_ja, katakana_style="bare")
            en = _shop_link_ro(f"{g_ro.capitalize()} {n_en}", t_ja, T, katakana_style="bare")
        else:
            words = set()
            ja = _shop_link(g_ja, t_ja, katakana_style="bare")
            en = _shop_link_ro(g_ro.capitalize(), t_ja, T, katakana_style="bare")
    elif pat == "type_first":
        src = r.choices(["word", "kanji", "abstract", "person"], [35, 30, 15, 20], k=1)[0]
        if src == "word":
            p_ja, p_ro = r.choice(WAFUU_WORDS)
            p_ro = p_ro.capitalize()
        elif src == "kanji":
            a_ja, _a, a_ro = r.choice(KANJI_A)
            b_ja, _b, b_ro = r.choice(KANJI_B)
            p_ja, p_ro = a_ja + b_ja, (a_ro + b_ro).capitalize()
        elif src == "abstract":
            p_ja, _e, p_ro = r.choice(TAVERN_ABSTRACT)
            p_ro = p_ro.title()
        else:
            p_ro, p_ja = _person(r, spec)
        words, ja, en = {p_ja}, f"{t_ja} {p_ja}", f"{T} {p_ro}"
    elif pat == "kanji":
        a_ja, _a, a_ro = r.choice(KANJI_A)
        b_ja, _b, b_ro = r.choice(KANJI_B)
        comp = a_ja + b_ja
        words, ja, en = {comp}, f"{comp}{t_ja}", f"{(a_ro + b_ro).capitalize()} {T}"
    else:  # abstract
        b_ja, _b_en, b_ro = r.choice(TAVERN_ABSTRACT)
        words, ja, en = {b_ro}, f"{b_ja}の{t_ja}", f"{b_ro.title()} no {T}"
    return {"ja": ja, "en": en, "shop_type": shop_type, "shop_type_ja": st["label"], "pattern": pat}, words


def shop_names(
    shop_type: str = "any",
    tone: str = "western",
    count: int = 5,
    seed: int | str | None = None,
    avoid: list[str] | None = None,
    whimsy: float = 0.25,
    style: str = "human",
) -> dict:
    """店舗 (武器屋・防具屋・道具屋・薬屋・魔道具店・鍛冶屋・書店・パン屋など) の店名。
    西洋風は日英対訳 (狼の牙武具店 / The Wolf's Fang Armory)、和風は漢字+ローマ字。
    店の種類ごとの「品」や、人名 (ダルトンの武器屋・ダルトン武器屋)・親族 (バーブラおばあの薬屋)・
    二人組 (ダルトンとバーブラの武器屋)・立地や最上級 (坂の上の武器屋・街一番の靴屋)・
    集団血縁 (二人組の魔道店)・種類が前 (道具屋 ミーチャ) などの型を混ぜる。"""
    if shop_type != "any" and shop_type not in SHOP_TYPES:
        raise ValueError(f"shop_type must be 'any' or one of: {', '.join(SHOP_TYPES)}")
    if tone not in ("western", "wafuu"):
        raise ValueError("tone must be western / wafuu")
    spec = _get_style(style)
    count = _clamp_count(count)
    seed, rng = _prep(seed)
    taken = {n.lower() for n in _reserved_names() + list(avoid or [])}
    whimsy = max(0.0, min(float(whimsy), 1.0))
    make = _shop_western if tone == "western" else _shop_wafuu
    types = list(SHOP_TYPES)
    results, seen, used = [], set(), set()
    tries = count * 200
    for i in range(tries):
        if len(results) >= count:
            break
        rec, words = make(rng, shop_type if shop_type != "any" else rng.choice(types), whimsy, spec)
        if rec["en"].lower() in taken or rec["ja"].lower() in taken or rec["en"].lower() in seen:
            continue
        if i < tries * 0.3 and used & words:  # 前半は同じ単語(狼など)を使い回さない
            continue
        seen.add(rec["en"].lower())
        used |= words
        results.append(rec)
    out = {"tone": tone, "shop_type": shop_type, "seed": seed, "names": results}
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
    return {
        "styles": out,
        "place_kinds": PLACE_KIND_JA,
        "governments": {k: v["ja"] for k, v in GOVERNMENTS.items()},
        "shop_types": {k: v["label"] for k, v in SHOP_TYPES.items()},
    }


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

    @mcp.tool(description="国名を生成します。政体は既定でランダム(any)で、王国・帝国・共和国のほか、司教領・精霊国・魔道邦・自治領・市国・協商邦・地下戦線などが出ます。日本語名(ja_name)・英語の正式名(en_formal)・元首の称号を返します。")
    def generate_country_names(
        style: Annotated[
            StyleType,
            Field(description="命名スタイル: elf / dwarf / human / orc / wafuu / arcane / southern")
        ] = "elf",
        government: Annotated[
            GovernmentType,
            Field(description="政体。any (既定・ランダム) か、kingdom (王国), empire (帝国), republic (共和国), bishopric (司教領), spirit (精霊国), arcane (魔道邦), autonomous (自治領), city_state (市国), league (協商邦), socialist (社会主義国) など。全一覧は list_styles か CLI の styles で確認できます")
        ] = "any",
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
        decorate: Annotated[
            bool,
            Field(description="型を混ぜるか (既定True)。極東〜/西極〜の前置き、「常夏の帝国 ◯◯」の二つ名、「◯◯及び△△連合政権」の並記、「◯◯・リパブリック」などが出る。Falseなら「名前+政体」だけ")
        ] = True,
    ) -> dict:
        return country_names(
            style=style,
            government=government,
            count=count,
            seed=seed,
            starts_with=starts_with,
            avoid=avoid,
            decorate=decorate,
        )

    @mcp.tool(description="酒場・宿屋の屋号を生成します。西洋風は日英対訳(酔いどれ鹿亭 / The Drunken Stag)、和風は漢字+ローマ字(月見亭 / Tsukimitei)。「ケンタウロスの溜息亭」(生き物の動作)・「バーブラおばあ亭」(人名+親族)・「宿屋 キャスリン」(種類が前)・「金海亭」(漢字二字)・「流浪亭」(抽象語)など、多くの型が混ざります。")
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
        style: Annotated[
            StyleType,
            Field(description="屋号に入る人名(「バーブラおばあ亭」「宿屋 キャスリン」など)の響き。既定 human。elf / dwarf / orc / wafuu / arcane / southern も可")
        ] = "human",
    ) -> dict:
        return tavern_names(
            tone=tone,
            kind=kind,
            count=count,
            seed=seed,
            avoid=avoid,
            whimsy=whimsy,
            style=style,
        )

    @mcp.tool(description="店舗(武器屋・防具屋・道具屋・薬屋・魔道具店・鍛冶屋・宝石店・書店・パン屋・八百屋・仕立て屋・骨董品店・質屋・花屋など)の店名を生成します。西洋風は日英対訳(狼の牙武具店 / The Wolf's Fang Armory)、和風は漢字+ローマ字。店の種類ごとの品(牙・雫・杖など)、人名(ダルトンの武器屋)、親族つき(バーブラおばあの薬屋)、種類が前(道具屋 ミーチャ)などの型が混ざります。")
    def generate_shop_names(
        shop_type: Annotated[
            ShopType,
            Field(description="店の種類。any (既定・ランダム) か、weapon (武器屋), armor (防具屋), general (道具屋・雑貨店), potion (薬屋), magic (魔道具店), blacksmith (鍛冶屋), jeweler (宝石店), book (書店), bakery (パン屋), grocer (八百屋), butcher (肉屋), fishmonger (魚屋), tailor (仕立て屋), herbalist (薬草店), antiques (骨董品店), pawn (質屋), florist (花屋), chandler (蝋燭店), cartographer (地図屋)")
        ] = "any",
        tone: Annotated[
            TavernToneType,
            Field(description="雰囲気: western (西洋風・日英対訳), wafuu (和風・漢字+ローマ字)")
        ] = "western",
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
            Field(description="除外したい店名のリスト (予約済みの名前は自動で除外されます)")
        ] = None,
        whimsy: Annotated[
            float,
            Field(description="詩的な形容詞(眠らざる〜など)が混ざる率 0〜1 (既定0.25)。西洋風のみ", ge=0.0, le=1.0)
        ] = 0.25,
        style: Annotated[
            StyleType,
            Field(description="店名に入る人名(「ダルトンの武器屋」など)の響き。既定 human")
        ] = "human",
    ) -> dict:
        return shop_names(
            shop_type=shop_type,
            tone=tone,
            count=count,
            seed=seed,
            avoid=avoid,
            whimsy=whimsy,
            style=style,
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
        c = country_names(key, "any", 2, seed=1)
        print("  国名:", ", ".join(f"{n['en_formal']}→{n['ja_name']}" for n in c["names"]))
    print("\n[酒場・宿屋]")
    for tone in ("western", "wafuu"):
        t = tavern_names(tone, "any", 4, seed=1)
        print(f"  {tone}:", ", ".join(f"{n['ja']} / {n['en']}" for n in t["names"]))


def main() -> None:
    """引数なし / serve = MCP サーバー、--demo = 見本表示、それ以外 = コマンドライン (cli.py)"""
    argv = sys.argv[1:]
    if "--demo" in argv:
        _demo()
    elif not argv or argv[0] == "serve":
        try:
            server = _build_server()
        except ImportError:
            sys.exit("mcp パッケージが必要です: pip install mcp")
        server.run()
    else:
        from .cli import run

        sys.exit(run(argv))


if __name__ == "__main__":
    main()
