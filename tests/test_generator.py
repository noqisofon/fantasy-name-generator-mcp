import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from fantasy_name_generator_mcp.cli import run as cli_run
from fantasy_name_generator_mcp.extra_data import ADJ_LIVING, ADJ_POETIC, KIND_JA_TERM, NOUN_OBJECT, SHOP_TYPES
from fantasy_name_generator_mcp.index import (
    MAX_COUNT,
    _SimIndex,
    _is_katakana_word,
    _mora,
    _shop_link,
    _shop_link_ro,
    _too_similar,
    _valid,
    STYLES,
    PLACE_KINDS,
    GOVERNMENTS,
    character_names,
    country_names,
    place_names,
    shop_names,
    tavern_names,
    names_from_examples,
    reserve,
    list_reserved_names,
    release,
    to_katakana,
    to_hiragana,
)


class TestFantasyNameGenerator(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store_file = Path(self.temp_dir.name) / "test_reserved.json"
        os.environ["NAME_GEN_STORE"] = str(self.store_file)

    def tearDown(self):
        self.temp_dir.cleanup()
        os.environ.pop("NAME_GEN_STORE", None)

    def test_character_names_all_styles(self):
        for style in STYLES:
            res = character_names(style=style, count=3, seed=100, with_family=True)
            self.assertEqual(res["style"], style)
            self.assertEqual(res["seed"], 100)
            self.assertEqual(len(res["names"]), 3)
            for item in res["names"]:
                self.assertIn("name", item)
                self.assertIn("kana", item)
                self.assertIn("gender", item)
                self.assertIn("family", item)
                self.assertIn("family_kana", item)

    def test_character_names_reproducibility(self):
        res1 = character_names(style="human", count=5, seed=42)
        res2 = character_names(style="human", count=5, seed=42)
        self.assertEqual(
            [n["name"] for n in res1["names"]],
            [n["name"] for n in res2["names"]]
        )

    def test_place_names(self):
        for kind in PLACE_KINDS:
            res = place_names(style="elf", kind=kind, count=2, seed=123)
            self.assertEqual(res["kind"], kind)
            self.assertEqual(len(res["names"]), 2)
            for item in res["names"]:
                self.assertIn("name", item)
                self.assertIn("kana", item)
                self.assertIn("suffix", item)
                self.assertIn("suffix_meaning", item)

    def test_names_from_examples(self):
        examples = ["Arthur", "Lancelot", "Gawain", "Percival", "Galahad", "Bedivere"]
        res = names_from_examples(examples=examples, count=3, seed=77)
        self.assertGreaterEqual(len(res["names"]), 1)
        for item in res["names"]:
            self.assertIn("name", item)

    def test_reserve_and_avoid(self):
        # 予約追加
        res_add = reserve(["Arthur", "Guinevere"], note="主人公と王妃")
        self.assertIn("Arthur", res_add["reserved"])
        self.assertIn("Guinevere", res_add["reserved"])

        # 予約一覧
        res_list = list_reserved_names()
        names = [entry["name"] for entry in res_list["names"]]
        self.assertIn("Arthur", names)
        self.assertIn("Guinevere", names)

        # 予約解除
        res_rel = release(["Arthur"])
        self.assertIn("Arthur", res_rel["released"])
        res_list2 = list_reserved_names()
        names2 = [entry["name"] for entry in res_list2["names"]]
        self.assertNotIn("Arthur", names2)
        self.assertIn("Guinevere", names2)

    def test_katakana_conversion(self):
        self.assertEqual(to_katakana("Rakk"), "ラック")
        self.assertEqual(to_katakana("Otto"), "オット")
        self.assertEqual(to_katakana("Anna"), "アンナ")
        self.assertEqual(to_katakana("Vaal"), "ヴァール")
        self.assertEqual(to_katakana("Kool"), "コール")
        self.assertEqual(to_katakana("Gash"), "ガシュ")
        self.assertEqual(to_katakana("Aldric"), "アルドリク")
        # 拗音のテスト
        self.assertEqual(to_katakana("Santanyaan"), "サンタニャーン")
        self.assertEqual(to_katakana("Ryuma"), "リュマ")
        # 連続 n のテスト
        self.assertEqual(to_katakana("Lynn"), "リン")
        self.assertEqual(to_katakana("Gwenn"), "グウェン")

    def test_wafuu_hiragana(self):
        res = character_names(style="wafuu", count=3, seed=999, with_family=True)
        for item in res["names"]:
            # かな表記がひらがなであること
            for ch in item["kana"]:
                self.assertTrue("ぁ" <= ch <= "ん" or ch == "ー")
            for ch in item["family_kana"]:
                self.assertTrue("ぁ" <= ch <= "ん" or ch == "ー")

    def test_terrain_kinds_all_styles(self):
        terrain = ["plains", "desert", "wasteland", "swamp", "hills", "valley",
                   "coast", "sea", "island", "cave", "ruins"]
        for style in STYLES:
            for kind in terrain:
                self.assertIn(kind, PLACE_KINDS)
                res = place_names(style=style, kind=kind, count=3, seed=5)
                self.assertEqual(len(res["names"]), 3, (style, kind))
                for item in res["names"]:
                    self.assertIn("ja_name", item)
                    # 語幹が1拍だけの「ロ砂漠」のような呼び名を出さない
                    term = item["suffix_meaning"] if style == "wafuu" else KIND_JA_TERM[kind]
                    self.assertTrue(item["ja_name"].endswith(term))
                    root = item["ja_name"][: -len(term)]
                    self.assertGreaterEqual(_mora(root), 2, (style, kind, item))

    def test_place_ja_name(self):
        item = place_names(style="southern", kind="desert", count=1, seed=3)["names"][0]
        self.assertTrue(item["ja_name"].endswith("砂漠"))

    def test_wafuu_ja_name_follows_suffix_meaning(self):
        # 「machi=町」の地名が「村」になる不整合が出ないこと
        for kind in ("town", "city", "forest", "mountain"):
            for seed in range(20):
                for item in place_names(style="wafuu", kind=kind, count=5, seed=seed)["names"]:
                    self.assertTrue(item["ja_name"].endswith(item["suffix_meaning"]), item)

    def test_blocklist_does_not_reject_good_names(self):
        loose = dict(max_cluster=9)
        for name in ["Cassian", "Cassandra", "Titania", "Titus", "Dietrich", "Elidiel",
                     "Nigel", "Killian", "Kroma", "Hoshine"]:
            self.assertTrue(_valid(name, loose, 3, 14), name)
        # 和風では fuk / shit を含む自然な名前も許す
        wafuu = dict(max_cluster=9, kana="hiragana")
        for name in ["Fukuda", "Fukushima", "Kashita", "Hoshito"]:
            self.assertTrue(_valid(name, wafuu, 3, 14), name)
        # 明らかに不適切なもの・実在の都市名そのものは弾く
        for name in ["Ass", "Napoli", "Unkobe", "Chinko"]:
            self.assertFalse(_valid(name, loose, 3, 14), name)

    def test_names_from_kanji_examples(self):
        ex = ["織田信長", "豊臣秀吉", "徳川家康", "武田信玄", "上杉謙信", "伊達政宗", "真田幸村", "明智光秀"]
        res = names_from_examples(examples=ex, count=3, seed=1, order=1)
        self.assertEqual(len(res["names"]), 3)
        for item in res["names"]:
            self.assertNotIn(item["name"], ex)

    def test_country_names(self):
        # 政体を指定し、型を混ぜない(decorate=False)と「名前+政体」になる
        for style in STYLES:
            for gov, info in GOVERNMENTS.items():
                res = country_names(style=style, government=gov, count=2, seed=8, decorate=False)
                self.assertEqual(len(res["names"]), 2, (style, gov))
                for item in res["names"]:
                    self.assertTrue(item["ja_name"].endswith(info["ja"]), item)
                    self.assertIn(item["name"], item["en_formal"])
                    self.assertEqual(item["ruler_title"], info["ruler"])
                    self.assertEqual(item["government"], gov)
        with self.assertRaises(ValueError):
            country_names(government="monarchy")

    def test_country_names_are_varied_by_default(self):
        # 既定 (any) は王国ばかりにならず、政体も型も散らばる
        res = country_names(style="human", count=50, seed=1)["names"]
        self.assertEqual(len(res), 50)
        govs = [n["government"] for n in res]
        self.assertGreaterEqual(len(set(govs)), 12)
        self.assertLessEqual(govs.count("kingdom"), 10)
        self.assertGreaterEqual(len({n["pattern"] for n in res}), 4)
        for n in res:
            self.assertTrue(n["ja_name"] and n["en_formal"] and n["ruler_title"])
            self.assertNotIn("_", "".join(k for k in n if k.startswith("_")))  # 作業用のキーが漏れない
            if n["pattern"] in ("bare", "no_of"):
                self.assertEqual(n["government"], "nation")

    def test_country_explicit_government_keeps_polity(self):
        # 政体を指定したら、どの型でも政体の語が残る (名前だけの型にはならない)
        for n in country_names(style="elf", government="empire", count=30, seed=4)["names"]:
            word = "エンパイア" if n["pattern"] == "katakana" else "帝国"  # 「◯◯・エンパイア」型は帝国の語が入れ替わる
            self.assertIn(word, n["ja_name"], n)

    def test_tavern_names(self):
        for tone in ("western", "wafuu"):
            for kind in ("any", "tavern", "inn"):
                res = tavern_names(tone=tone, kind=kind, count=6, seed=21)
                self.assertEqual(len(res["names"]), 6)
                self.assertEqual(len({n["en"] for n in res["names"]}), 6)
                for n in res["names"]:
                    self.assertTrue(n["ja"] and n["en"])
        # 語彙表から条件を作る: 「生き物用の形容詞 + 物」(眠れるランタン等) を判定する
        import re

        living_adj = "|".join(re.escape(en) for en, _ja in ADJ_LIVING + ADJ_POETIC)
        objects = "|".join(re.escape(en) for en, _ja in NOUN_OBJECT)
        personified = re.compile(rf"\b({living_adj}) ({objects})\b")
        # whimsy=0: 生き物用の形容詞を物に付けない
        for seed in range(10):
            for n in tavern_names("western", "any", 50, seed=seed, whimsy=0)["names"]:
                self.assertIsNone(personified.search(n["en"]), n["en"])
        # whimsy=1: 擬人化した屋号 (眠れるランタン亭など) が出る
        hits = [n for n in tavern_names("western", "any", 50, seed=1, whimsy=1)["names"]
                if personified.search(n["en"])]
        self.assertTrue(hits)
        a = tavern_names("western", "inn", 5, seed=9)
        b = tavern_names("western", "inn", 5, seed=9)
        self.assertEqual(a["names"], b["names"])

    def test_tavern_avoids_reserved(self):
        first = tavern_names("wafuu", "inn", 3, seed=4)["names"]
        reserve([n["ja"] for n in first])
        again = tavern_names("wafuu", "inn", 3, seed=4)["names"]
        self.assertFalse({n["ja"] for n in first} & {n["ja"] for n in again})

    # --- コマンドライン (CLI) ---
    def _cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli_run(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_cli_generates_each_kind(self):
        cases = [
            (["char", "-s", "wafuu", "-g", "male", "-n", "3", "--family", "--seed", "1"], 3),
            (["place", "-s", "southern", "-k", "desert", "-n", "3", "--seed", "1"], 3),
            (["country", "-s", "human", "--gov", "empire", "-n", "2", "--seed", "1"], 2),
            (["country", "-s", "human", "-n", "5", "--seed", "1"], 5),
            (["country", "-s", "human", "-n", "3", "--seed", "1", "--plain"], 3),
            (["tavern", "-t", "western", "-k", "inn", "-n", "4", "--seed", "1"], 4),
            (["tavern", "-t", "wafuu", "-n", "4", "--seed", "1"], 4),
            (["examples", "Arthur", "Lancelot", "Gawain", "Percival", "Galahad", "-n", "2", "--seed", "1"], 1),
        ]
        for argv, minimum in cases:
            code, out, err = self._cli(*argv)
            self.assertEqual(code, 0, argv)
            self.assertGreaterEqual(len(out.strip().splitlines()), minimum, argv)
            self.assertIn("# seed:", err)  # seed は標準error側 (パイプしやすい)

    def test_cli_seed_reproducible_and_json(self):
        a = self._cli("tavern", "-t", "western", "--seed", "7", "--json")
        b = self._cli("tavern", "-t", "western", "--seed", "7", "--json")
        self.assertEqual(a[1], b[1])
        data = json.loads(a[1])
        self.assertEqual(data["seed"], 7)
        self.assertEqual(len(data["names"]), 5)

    def test_cli_reserve_roundtrip(self):
        self.assertEqual(self._cli("reserve", "金の竜亭", "--note", "常宿")[0], 0)
        code, out, _ = self._cli("reserved")
        self.assertIn("金の竜亭", out)
        self.assertIn("常宿", out)
        self.assertIn("解除しました", self._cli("release", "金の竜亭")[1])
        self.assertNotIn("金の竜亭", self._cli("reserved")[1])

    def test_cli_errors(self):
        with self.assertRaises(SystemExit) as cm:  # 不正な種別は argparse が弾く
            self._cli("place", "-k", "tundra")
        self.assertEqual(cm.exception.code, 2)
        code, _out, err = self._cli("examples", "a", "b")  # 値の誤り
        self.assertEqual(code, 2)
        self.assertIn("エラー", err)
        code, out, _err = self._cli("char", "-s", "wafuu", "--starts-with", "zzzz")  # 1つも作れない
        self.assertEqual((code, out.strip()), (1, ""))

    def test_cli_styles_lists_everything(self):
        _code, out, _err = self._cli("styles")
        for word in ("wafuu", "desert", "empire"):
            self.assertIn(word, out)

    def test_tavern_pattern_variety(self):
        # 型が多様に混ざる (形容詞+名詞ばかりにならない)
        for tone, minimum in (("western", 7), ("wafuu", 6)):
            res = tavern_names(tone=tone, kind="any", count=50, seed=3)["names"]
            self.assertEqual(len(res), 50, tone)
            self.assertGreaterEqual(len({n["pattern"] for n in res}), minimum, tone)
        west = tavern_names("western", "any", 50, seed=3)["names"]
        # 語尾も一種類に偏らない (亭・酒場・宿・館…)
        endings = {n["ja"][-1] for n in west}
        self.assertGreaterEqual(len(endings), 6)
        patterns = {n["pattern"] for n in west}
        for expected in ("creature_act", "type_first", "kanji", "person_kin"):
            self.assertIn(expected, patterns)

    def test_tavern_english_is_well_formed(self):
        bad = []
        for seed in range(40):
            for n in tavern_names("western", "any", 10, seed=seed)["names"]:
                en = n["en"]
                if en.endswith("'s") or "The That" in en or "  " in en:
                    bad.append(en)
        self.assertEqual(bad, [])

    def test_tavern_person_style_and_shapes(self):
        # 人名は style で響きが変わる。「種類が前」は「宿屋 名前」の形
        for style in ("human", "elf", "wafuu"):
            res = tavern_names("western", "inn", 30, seed=2, style=style)["names"]
            self.assertEqual(len(res), 30, style)
        tf = [n for n in tavern_names("western", "any", 50, seed=5)["names"] if n["pattern"] == "type_first"]
        self.assertTrue(tf)
        for n in tf:
            self.assertIn(" ", n["ja"])
        with self.assertRaises(ValueError):
            tavern_names(style="robot")

    # --- 大量生成・個数の上限・loose ---
    def test_similarity_index_matches_bruteforce(self):
        # 高速化した索引が、従来の総当たり (_too_similar) と同じ判定を返す
        import random

        rng = random.Random(7)
        idx, taken = _SimIndex(), []
        for _ in range(600):
            n = "".join(rng.choice("abcde") for _ in range(rng.randint(3, 8)))
            expected = _too_similar(n, taken)
            self.assertEqual(idx.similar(n), expected, n)
            if not expected:
                idx.add(n)
                taken.append(n)
        self.assertGreater(len(taken), 20)

    def test_count_limits_raise_instead_of_silent_clamp(self):
        for fn in (character_names, place_names, country_names, tavern_names, shop_names):
            with self.assertRaises(ValueError):
                fn(count=0)
            with self.assertRaises(ValueError):
                fn(count=MAX_COUNT + 1)

    def test_bulk_generation(self):
        # 50個を超える大量生成も、要求どおりの個数が重複なく出る
        res = country_names(style="human", count=400, seed=1)["names"]
        self.assertEqual(len(res), 400)
        self.assertEqual(len({n["name"].lower() for n in res}), 400)
        self.assertEqual(len(tavern_names("western", "any", 300, seed=1)["names"]), 300)

    def test_loose_fills_when_strict_runs_out(self):
        strict = place_names(style="southern", kind="desert", count=800, seed=1)
        self.assertLess(len(strict["names"]), 800)
        self.assertIn("個しか作れませんでした", strict["note"])
        self.assertIn("loose", strict["note"])
        loose = place_names(style="southern", kind="desert", count=800, seed=1, loose=True)
        self.assertEqual(len(loose["names"]), 800)
        self.assertEqual(len({n["name"].lower() for n in loose["names"]}), 800)

    def test_cli_bulk_and_limits(self):
        code, out, _err = self._cli("country", "-s", "human", "-n", "120", "--seed", "1")
        self.assertEqual((code, len(out.strip().splitlines())), (0, 120))
        code, out, err = self._cli("char", "-s", "wafuu", "-n", "300", "--loose", "--seed", "1")
        self.assertEqual((code, len(out.strip().splitlines())), (0, 300))
        code, _out, err = self._cli("char", "-n", "0")
        self.assertEqual(code, 2)
        self.assertIn("count は", err)
        code, _out, err = self._cli("char", "-n", str(MAX_COUNT + 1))
        self.assertEqual(code, 2)

    # --- 店舗 ---
    def test_shop_names_all_types_and_tones(self):
        for tone in ("western", "wafuu"):
            for shop_type, info in SHOP_TYPES.items():
                res = shop_names(shop_type=shop_type, tone=tone, count=4, seed=6)
                self.assertEqual(len(res["names"]), 4, (tone, shop_type))
                for n in res["names"]:
                    self.assertEqual(n["shop_type"], shop_type)
                    self.assertEqual(n["shop_type_ja"], info["label"])
                    self.assertTrue(n["ja"] and n["en"] and n["pattern"])
                    # 店の語 (武器屋・武器店…) のどれかが必ず入る
                    self.assertTrue(any(w[0] in n["ja"] for w in info["names"]), n)

    def test_shop_names_are_varied_and_well_formed(self):
        res = shop_names("any", "western", 50, seed=4)["names"]
        self.assertEqual(len(res), 50)
        self.assertGreaterEqual(len({n["pattern"] for n in res}), 6)
        self.assertGreaterEqual(len({n["shop_type"] for n in res}), 12)
        bad = []
        for seed in range(30):
            for tone in ("western", "wafuu"):
                for n in shop_names("any", tone, 10, seed=seed)["names"]:
                    if n["en"].endswith("'s") or "  " in n["en"] or n["en"].startswith("The The"):
                        bad.append(n["en"])
        self.assertEqual(bad, [])

    def test_shop_link_joins_by_script(self):
        # 漢字の種類語には常に「の」
        self.assertEqual(_shop_link("狼", "武器屋"), "狼の武器屋")
        self.assertEqual(_shop_link_ro("Wolf", "武器屋", "Buki-ya"), "Wolf no Buki-ya")
        # カタカナの外来語は katakana_style で変わる (省略時は「の」のまま)
        self.assertTrue(_is_katakana_word("マーチャンダイズ"))
        self.assertFalse(_is_katakana_word("武器屋"))
        self.assertEqual(_shop_link("狼", "マーチャンダイズ"), "狼のマーチャンダイズ")
        self.assertEqual(_shop_link_ro("Wolf", "マーチャンダイズ", "Maachandaizu"), "Wolf no Maachandaizu")
        self.assertEqual(_shop_link("ウォリス", "ショップ", katakana_style="nakaguro"), "ウォリス・ショップ")
        self.assertEqual(
            _shop_link_ro("Wallis", "ショップ", "Shoppu", katakana_style="nakaguro"), "Wallis Shoppu"
        )
        self.assertEqual(_shop_link("六姉妹", "ドラッグ", katakana_style="bare"), "六姉妹ドラッグ")
        self.assertEqual(_shop_link_ro("Rokushimai", "ドラッグ", "Doraggu", katakana_style="bare"), "Rokushimai Doraggu")
        # 集団語でも漢字の種類語には「の」が残る
        self.assertEqual(_shop_link("親子", "武器屋", katakana_style="bare"), "親子の武器屋")

    def test_shop_new_patterns_appear_and_are_well_formed(self):
        seen_patterns = set()
        bad = []
        for seed in range(20):
            for tone in ("western", "wafuu"):
                for n in shop_names("any", tone, 40, seed=seed)["names"]:
                    seen_patterns.add(n["pattern"])
                    if not n["ja"] or not n["en"] or "None" in n["en"] or "  " in n["en"] or "  " in n["ja"]:
                        bad.append((tone, n))
        self.assertEqual(bad, [])
        # 新しく足した型 (人名直結・二人組・立地/最上級・集団血縁) が実際に出る
        for pat in ("person_bare", "two_person", "location_shop", "group_kin_shop"):
            self.assertIn(pat, seen_patterns, pat)

    def test_shop_names_errors_and_reserved(self):
        with self.assertRaises(ValueError):
            shop_names(shop_type="spaceport")
        with self.assertRaises(ValueError):
            shop_names(tone="gothic")
        first = shop_names("weapon", "wafuu", 3, seed=4)["names"]
        reserve([n["ja"] for n in first])
        again = shop_names("weapon", "wafuu", 3, seed=4)["names"]
        self.assertFalse({n["ja"] for n in first} & {n["ja"] for n in again})

    def test_cli_shop(self):
        code, out, _err = self._cli("shop", "-k", "weapon", "-n", "5", "--seed", "1")
        lines = out.strip().splitlines()
        self.assertEqual((code, len(lines)), (0, 5))
        self.assertTrue(all("[武器屋]" in ln for ln in lines))
        with self.assertRaises(SystemExit):
            self._cli("shop", "-k", "spaceport")
        self.assertIn("shop", self._cli("styles")[1])



if __name__ == "__main__":
    unittest.main()
