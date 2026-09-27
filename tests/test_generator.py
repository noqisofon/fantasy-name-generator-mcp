import os
import tempfile
import unittest
from pathlib import Path

from fantasy_name_generator_mcp.extra_data import KIND_JA_TERM, WAFUU_KIND_JA_TERM
from fantasy_name_generator_mcp.index import (
    _mora,
    STYLES,
    PLACE_KINDS,
    GOVERNMENTS,
    character_names,
    country_names,
    place_names,
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
                    term = (WAFUU_KIND_JA_TERM.get(kind) if style == "wafuu" else None) or KIND_JA_TERM[kind]
                    self.assertTrue(item["ja_name"].endswith(term))
                    root = item["ja_name"][: -len(term)]
                    self.assertGreaterEqual(_mora(root), 2, (style, kind, item))

    def test_place_ja_name(self):
        item = place_names(style="southern", kind="desert", count=1, seed=3)["names"][0]
        self.assertTrue(item["ja_name"].endswith("砂漠"))

    def test_country_names(self):
        for style in STYLES:
            for gov, info in GOVERNMENTS.items():
                res = country_names(style=style, government=gov, count=2, seed=8)
                self.assertEqual(len(res["names"]), 2, (style, gov))
                for item in res["names"]:
                    self.assertTrue(item["ja_name"].endswith(info["ja"]))
                    self.assertIn(item["name"], item["en_formal"])
                    self.assertEqual(item["ruler_title"], info["ruler"])
        with self.assertRaises(ValueError):
            country_names(government="monarchy")

    def test_tavern_names(self):
        for tone in ("western", "wafuu"):
            for kind in ("any", "tavern", "inn"):
                res = tavern_names(tone=tone, kind=kind, count=6, seed=21)
                self.assertEqual(len(res["names"]), 6)
                self.assertEqual(len({n["en"] for n in res["names"]}), 6)
                for n in res["names"]:
                    self.assertTrue(n["ja"] and n["en"])
        # 生き物にだけ合う形容詞を物に付けない (眠れるランタン等)
        for n in tavern_names("western", "any", 50, seed=1)["names"]:
            self.assertNotRegex(n["en"], r"(Sleeping|Drunken|Laughing|Dancing) (Lantern|Anchor|Barrel|Crown|Bell|Key)")
        a = tavern_names("western", "inn", 5, seed=9)
        b = tavern_names("western", "inn", 5, seed=9)
        self.assertEqual(a["names"], b["names"])

    def test_tavern_avoids_reserved(self):
        first = tavern_names("wafuu", "inn", 3, seed=4)["names"]
        reserve([n["ja"] for n in first])
        again = tavern_names("wafuu", "inn", 3, seed=4)["names"]
        self.assertFalse({n["ja"] for n in first} & {n["ja"] for n in again})


if __name__ == "__main__":
    unittest.main()
