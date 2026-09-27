# Fantasy Name Generator MCP 🎲🏰

創作（小説・TRPG・ゲーム制作・世界観設定など）に特化した人名・地名生成 MCP (Model Context Protocol) サーバーです。

LLM が命名を行う際に陥りがちな **「ネオ〜」「シャドウ〜」「ルミナス〜」といった定型的な偏り** を、外部の言語学的音素テーブル（Onset-Nucleus-Coda）と乱数シードによって解消します。

---

## ✨ 主な特徴

- 🧝 **7種類の命名スタイル**: エルフ風、ドワーフ風、中世西洋、オーク風、和風、古代魔術、南方交易都市風。
- 🗺️ **意味付き地名生成**: 語幹＋種別ごとの接尾辞（例: `-ton`=町、`-minster`=大聖堂の街、`-kaz`=山）により、地形や歴史の一貫した地名を生成。
- 🧬 **マルコフ連鎖生成**: 既存の名前リスト（3個以上）から文字の並びを学習し、「同じ世界っぽい」新しい名前を自動生成。
- 🔖 **名前の予約・重複回避**: 採用した名前をローカルに保存（`reserve_names`）。以降の生成で同一・類似の名前（レーベンシュタイン距離）を自動回避。
- 🈲 **安心のフィルタリング**: 不適切な単語や実在の主要都市名（東京、ロンドン等）の混入を自動排除。
- 🇯🇵 **自然なカタカナ・ひらがな変換**: 洋風の名前にはカタカナ（促音・長音対応）、和風スタイルにはひらがなを自動付与。
- 📦 **超軽量**: 依存パッケージは `mcp` のみ。

---

## 🚀 クイックスタート

### 動作確認（デモ実行）

```bash
# uv で実行する場合
uv run fantasy-name-generator-mcp --demo

# または python モジュールとして実行する場合
python -m fantasy_name_generator_mcp --demo
```

---

## ⚙️ MCP クライアントの設定

### Claude Desktop

設定ファイル（Windows: `%APPDATA%\Claude\claude_desktop_config.json`, macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`）に以下を追加します。

#### ローカル環境（推奨・即座に動作）
本リポジトリのパスを指定して実行します。

```json
{
  "mcpServers": {
    "fantasy-names": {
      "command": "uv",
      "args": [
        "--directory",
        "C:/Users/nedri/Projects/fantasy-name-generator-mcp",
        "run",
        "fantasy-name-generator-mcp"
      ]
    }
  }
}
```

#### PyPI 公開後の設定（配布用）
※ パッケージを PyPI に公開した後に利用できます。

```json
{
  "mcpServers": {
    "fantasy-names": {
      "command": "uvx",
      "args": ["--from", "fantasy-name-generator-mcp", "fantasy-name-generator-mcp"]
    }
  }
}
```

### Cursor / Windsurf

MCP 設定画面にて以下を追加します：

- **ローカル環境（推奨）**:
  - **Command**: `uv --directory C:/Users/nedri/Projects/fantasy-name-generator-mcp run fantasy-name-generator-mcp`
- **PyPI 公開後**:
  - **Command**: `uvx --from fantasy-name-generator-mcp fantasy-name-generator-mcp`

---

## 🛠️ 提供ツール (Tools)

### 1. `generate_character_names`
キャラクター名を生成します。

| 引数          | 型                   | 既定値  | 説明                                                                     |
| :------------ | :------------------- | :------ | :----------------------------------------------------------------------- |
| `style`       | `Literal`            | `"elf"` | スタイル (`elf`, `dwarf`, `human`, `orc`, `wafuu`, `arcane`, `southern`) |
| `count`       | `int`                | `5`     | 生成数 (1〜50)                                                           |
| `gender`      | `Literal`            | `"any"` | 性別 (`any`, `male`, `female`, `neutral`)                                |
| `with_family` | `bool`               | `False` | 姓（ファミリーネーム）を付けるか                                         |
| `seed`        | `int \| str \| None` | `None`  | 乱数シード（同じシードなら完全に同じ結果が再現）                         |
| `starts_with` | `str \| None`        | `None`  | 名前の頭文字指定 (例: `'ka'`, `'el'`)                                    |
| `avoid`       | `list[str] \| None`  | `None`  | 除外したい名前リスト（予約済みの名前は自動除外）                         |

### 2. `generate_place_names`
地名を生成します。

| 引数          | 型                   | 既定値   | 説明                                                                                    |
| :------------ | :------------------- | :------- | :-------------------------------------------------------------------------------------- |
| `style`       | `Literal`            | `"elf"`  | 命名スタイル                                                                            |
| `kind`        | `Literal`            | `"town"` | 地名種別（下記） |
| `count`       | `int`                | `5`      | 生成数 (1〜50)                                                                          |
| `seed`        | `int \| str \| None` | `None`   | 乱数シード                                                                              |
| `starts_with` | `str \| None`        | `None`   | 地名の頭文字指定                                                                        |
| `avoid`       | `list[str] \| None`  | `None`   | 除外リスト                                                                              |

地名種別: `town`(町・村) / `city`(都市) / `mountain`(山) / `river`(川) / `forest`(森) / `lake`(湖) / `fortress`(砦・城) / `kingdom`(国) /
`plains`(平原) / `desert`(砂漠) / `wasteland`(荒野) / `swamp`(湿地) / `hills`(丘陵) / `valley`(谷) / `coast`(海岸) / `sea`(海) / `island`(島) / `cave`(洞窟) / `ruins`(遺跡)

各地名には、接尾辞とその意味 (`suffix`, `suffix_meaning`) に加えて、日本語の呼び名 `ja_name`（例: `Nidilsahra` → 「ニディル砂漠」）が付きます。

### 3. `generate_country_names`
国名を生成します。政体ごとに、日本語名 (`ja_name`)・英語の正式名 (`en_formal`)・元首の称号 (`ruler_title`) を返します。

| 引数         | 型                   | 既定値      | 説明                                                                                                     |
| :----------- | :------------------- | :---------- | :------------------------------------------------------------------------------------------------------- |
| `style`      | `Literal`            | `"elf"`     | 命名スタイル                                                                                             |
| `government` | `Literal`            | `"kingdom"` | 政体 (`kingdom` 王国 / `empire` 帝国 / `republic` 共和国 / `duchy` 公国 / `federation` 連邦 / `theocracy` 教国 / `tribal` 部族連合) |
| `count`      | `int`                | `5`         | 生成数 (1〜50)                                                                                           |
| `seed`       | `int \| str \| None` | `None`      | 乱数シード                                                                                               |
| `starts_with`| `str \| None`        | `None`      | 頭文字指定                                                                                               |
| `avoid`      | `list[str] \| None`  | `None`      | 除外リスト                                                                                               |

### 4. `generate_tavern_names`
酒場・宿屋の屋号を生成します。西洋風は日英対訳（「酔いどれ鹿亭 / The Drunken Stag」）、和風は漢字+ローマ字（「月見の宿 / Tsukimi no Yado」）です。

| 引数    | 型                   | 既定値      | 説明                                                   |
| :------ | :------------------- | :---------- | :----------------------------------------------------- |
| `tone`  | `Literal`            | `"western"` | 雰囲気 (`western` 西洋風 / `wafuu` 和風)               |
| `kind`  | `Literal`            | `"any"`     | 種別 (`any` ランダム / `tavern` 酒場 / `inn` 宿屋)     |
| `count` | `int`                | `5`         | 生成数 (1〜50)                                         |
| `seed`  | `int \| str \| None` | `None`      | 乱数シード                                             |
| `avoid` | `list[str] \| None`  | `None`      | 除外リスト（予約済みの屋号は自動除外）                 |

形容詞は「生き物にだけ合うもの（酔いどれ・眠れる…）」と「何にでも合うもの（錆びた・銀の…）」に分けてあり、「眠れるランタン」のような不自然な組み合わせは出ません。単語表は `extra_data.py` にあります。

### 5. `generate_names_from_examples`
既存の名前リストからマルコフ連鎖で「同じ世界っぽい」名前を生成します。

| 引数       | 型                   | 既定値   | 説明                                     |
| :--------- | :------------------- | :------- | :--------------------------------------- |
| `examples` | `list[str]`          | **必須** | サンプル名リスト (3個以上、10個以上推奨) |
| `count`    | `int`                | `5`      | 生成数 (1〜50)                           |
| `order`    | `int`                | `2`      | マルコフ連鎖の次数 (1〜3)                |
| `seed`     | `int \| str \| None` | `None`   | 乱数シード                               |

### 6. `reserve_names` / `list_reserved` / `release_names`
- `reserve_names(names, note)`: 採用した名前を予約リストに記録（重複回避用）。
- `list_reserved()`: 予約済みの名前一覧を取得。
- `release_names(names)`: 予約を解除。

### 7. `list_styles`
利用可能なスタイル一覧とサンプルのプレビューを返します。

---

## 📚 リソース (Resources) & プロンプト (Prompts)

### Resources
- `fantasy://styles`: 全スタイル定義と接尾辞テーブルの JSON データ
- `fantasy://reserved`: 現在予約されている名前の一覧

### Prompts
- `brainstorm_character`: キャラクターの命名から詳細な人物設定（生い立ち、能力、口調）までのブレインストーミングを支援するプロンプト
- `brainstorm_world_places`: 世界観の地図作成や地理・拠点の設計を支援するプロンプト

---

## 🎭 命名スタイル一覧

| スタイルキー | ラベル           | 特徴・サンプル                                                 |
| :----------- | :--------------- | :------------------------------------------------------------- |
| `elf`        | エルフ風         | 流麗で母音が多い（例: ロレンディル、サエララエル）             |
| `dwarf`      | ドワーフ風       | 子音が硬く短い（例: ブラクドゥル、カルグルガルン）             |
| `human`      | 中世西洋風・人間 | 古い英独仏のような素朴な響き（例: オルドリック、パレイ）       |
| `orc`        | オーク風         | 濁音や破裂音が多い荒々しい響き（例: グラクザグ、ウクモグ）     |
| `wafuu`      | 和風             | ひらがな表記の自然な和風名（例: らすけ、にしやま）             |
| `arcane`     | 古代・魔術・異形 | 古い呪文や邪神風の響き（例: ヴァクソス、ヌヴェクス）           |
| `southern`   | 南方・交易都市風 | 地中海〜中東の商業都市風の響き（例: サンタヌヤーン系、ケビノ） |

---

## 🧪 テストの実行

```bash
uv run python -m unittest discover tests
```

---

## 📄 ライセンス

MIT License
