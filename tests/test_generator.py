import os
import tempfile
import unittest
from pathlib import Path

from fantasy_name_generator_mcp.index import (
    STYLES,
    PLACE_KINDS,
    character_names,
    place_names,
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


if __name__ == "__main__":
    unittest.main()
