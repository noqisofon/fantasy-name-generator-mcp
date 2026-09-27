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

### コマンドラインから直接使う（MCP なし）

引数なしで起動すると MCP サーバーになりますが、サブコマンドを付けると、ターミナルから直接名前を生成できます。

```bash
uv run fantasy-name-generator-mcp tavern -t western -k inn -n 5       # 西洋風の宿屋名
uv run fantasy-name-generator-mcp char -s wafuu -g male -n 5 --family # 和風の男性名(姓つき)
uv run fantasy-name-generator-mcp place -s southern -k desert         # 南方風の砂漠の地名
uv run fantasy-name-generator-mcp place -s human -k ruins --decorate  # 「失われし遺跡」のような型も混ぜる
uv run fantasy-name-generator-mcp country -s human -n 10              # 国名 (政体は毎回ランダム)
uv run fantasy-name-generator-mcp country -s human --gov empire       # 帝国名に限定
uv run fantasy-name-generator-mcp shop -k weapon -n 5                 # 武器屋の名前
uv run fantasy-name-generator-mcp examples Santanyaan Maribel Marisol # 響きを学習して新しい名前
uv run fantasy-name-generator-mcp styles                              # スタイル・種別・政体の一覧
```

| コマンド                           | 内容                     | 主なオプション                                                                  |
| :--------------------------------- | :----------------------- | :------------------------------------------------------------------------------ |
| `char`                             | キャラクター名           | `-s` スタイル, `-g` 性別, `--family` 姓つき, `--starts-with`                    |
| `place`                            | 地名                     | `-s` スタイル, `-k` 種別, `--starts-with`, `--decorate` 型を混ぜる              |
| `country`                          | 国名                     | `-s` スタイル, `--gov` 政体 (既定はランダム), `--plain` 型なし, `--starts-with` |
| `tavern`                           | 酒場・宿屋の屋号         | `-t` 西洋風/和風, `-k` 酒場/宿屋, `-w` 擬人化の率, `-s` 人名の響き              |
| `shop`                             | 店舗の名前               | `-k` 店の種類, `-t` 西洋風/和風, `-w` 詩的な形容詞の率, `-s` 人名の響き |
| `examples`                         | 既存の名前から新しい名前 | 名前を3個以上, `--order`                                                        |
| `reserve` / `reserved` / `release` | 予約の追加・一覧・解除   | `--note`                                                                        |
| `styles`                           | スタイル等の一覧と見本   |                                                                                 |

共通のオプション: `-n` 個数（1〜10000）、`--seed` 乱数シード（同じ seed なら同じ結果）、`--avoid` 除外する名前、`--json` JSON で出力。

**大量に作るとき**: `char` / `place` / `country` は、既定では「似た名前（綴りの違いが 2 文字以内）」を避けます。数千個を作ると、スタイルによっては候補が尽きて、個数が足りなくなります（そのときは標準エラーに知らせます）。`--loose` を付けると、完全な重複だけを避けるので、要求した個数がそろいます。

```bash
uv run fantasy-name-generator-mcp country -s human -n 3000            # 約5秒
uv run fantasy-name-generator-mcp char -s wafuu -n 3000 --loose       # 個数がそろわないときは --loose
```

MCP ツール（Claude から呼ぶ場合）は、AI に返す量を抑えるため、1 回 50 個までです。それ以上が必要なときは、コマンドを使ってください。
名前は標準出力に、seed や注記は標準エラーに出るので、`| clip` やファイルへのリダイレクトでも名前だけが取れます。
1 つも作れなかったときの終了コードは `1`、引数や値の誤りは `2` です。`-h` で全オプションを確認できます。

> **メモ**: Claude Desktop などが `fantasy-name-generator-mcp` を実行中だと、Windows は実行ファイルをロックします。`uv run` が同期に失敗したときは `uv run --no-sync ...` か `python -m fantasy_name_generator_mcp ...` を使ってください。

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
        "/path/to/fantasy-name-generator-mcp",
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

| 引数          | 型                   | 既定値   | 説明                                        |
| :------------ | :------------------- | :------- | :------------------------------------------ |
| `style`       | `Literal`            | `"elf"`  | 命名スタイル                                |
| `kind`        | `Literal`            | `"town"` | 地名種別（下記）                            |
| `count`       | `int`                | `5`      | 生成数 (1〜50)                              |
| `seed`        | `int \| str \| None` | `None`   | 乱数シード                                  |
| `starts_with` | `str \| None`        | `None`   | 地名の頭文字指定                            |
| `avoid`       | `list[str] \| None`  | `None`   | 除外リスト                                  |
| `decorate`    | `bool`               | `False`  | `True` で「型」を混ぜる（下記、既定は無効） |

地名種別: `town`(町・村) / `city`(都市) / `mountain`(山) / `river`(川) / `forest`(森) / `lake`(湖) / `fortress`(砦・城) / `kingdom`(国) /
`plains`(平原) / `desert`(砂漠) / `wasteland`(荒野) / `swamp`(湿地) / `hills`(丘陵) / `valley`(谷) / `coast`(海岸) / `sea`(海) / `island`(島) / `cave`(洞窟) / `ruins`(遺跡)

各地名には、接尾辞とその意味 (`suffix`, `suffix_meaning`) に加えて、日本語の呼び名 `ja_name`（例: `Nidilsahra` → 「ニディル砂漠」）が付きます。

`decorate=True` にすると、いつもの「語幹+接尾辞」に加えて次のような型も混ざります（対応する `kind` のときだけ出るものもあります）。

| 型             | 例                                     |
| :------------- | :-------------------------------------- |
| いつもの型     | ニディル砂漠                            |
| 種類が前       | 遺構 ソジャ / 州都 ザス                 |
| 方角・新旧     | 北クラズ洞窟 / 新ほそ町                 |
| 二つ名の複合   | メラル＝ハル遺跡（和風では出ません）    |
| 雅語の異名     | 失われし遺跡 / 天への階段 / 龍脈の穴    |

### 3. `generate_country_names`
国名を生成します。政体は既定でランダム (`any`) で、王国・帝国・共和国だけでなく、司教領・精霊国・魔道邦・自治領・市国・協商邦・地下戦線・誓約など 36 種類が出ます。日本語名 (`ja_name`)・英語の正式名 (`en_formal`)・元首の称号 (`ruler_title`) を返します。

| 引数          | 型                   | 既定値  | 説明                                                                                          |
| :------------ | :------------------- | :------ | :-------------------------------------------------------------------------------------------- |
| `style`       | `Literal`            | `"elf"` | 命名スタイル                                                                                  |
| `government`  | `Literal`            | `"any"` | 政体。`any` はランダム。`empire` (帝国)、`bishopric` (司教領)、`spirit` (精霊国) など指定も可 |
| `count`       | `int`                | `5`     | 生成数 (1〜50)                                                                                |
| `seed`        | `int \| str \| None` | `None`  | 乱数シード                                                                                    |
| `starts_with` | `str \| None`        | `None`  | 頭文字指定                                                                                    |
| `avoid`       | `list[str] \| None`  | `None`  | 除外リスト                                                                                    |
| `decorate`    | `bool`               | `True`  | 型を混ぜるか。`False` なら「名前+政体」だけ                                                   |

`decorate` が有効なときは、次のような型がランダムに混ざります。

| 型                | 例                                                      |
| :---------------- | :------------------------------------------------------ |
| 名前+政体         | ネルノヴァ王国                                          |
| 地域名の前置き    | 極東ヒヴィランド魔道邦 / 旧メディトランド教国           |
| 二つ名            | 星の自治領 レビア / 氷の教国 マネドル                   |
| 二つの名前の並記  | ストマルク及びコトポル連合政権 / ノランド・ウォトレ公国 |
| カタカナ型        | スタランド・フェデレーション                            |
| 王朝つき          | トラ朝レマルク帝国                                      |
| 名前だけ / 〜の国 | デマルク / ムスヴァニアの国                             |

政体を指定したときは、名前だけの型は使われず、政体の語が必ず残ります。政体の全一覧は `list_styles`（CLI では `styles`）で確認できます。表は `extra_data.py` の `GOVERNMENTS` にあり、行を足すとツールの選択肢にも自動で反映されます。

### 4. `generate_tavern_names`
酒場・宿屋の屋号を生成します。西洋風は日英対訳（「酔いどれ鹿亭 / The Drunken Stag」）、和風は漢字+ローマ字（「月見の宿 / Tsukimi no Yado」）です。

| 引数     | 型                   | 既定値      | 説明                                               |
| :------- | :------------------- | :---------- | :------------------------------------------------- |
| `tone`   | `Literal`            | `"western"` | 雰囲気 (`western` 西洋風 / `wafuu` 和風)           |
| `kind`   | `Literal`            | `"any"`     | 種別 (`any` ランダム / `tavern` 酒場 / `inn` 宿屋) |
| `count`  | `int`                | `5`         | 生成数 (1〜50)                                     |
| `seed`   | `int \| str \| None` | `None`      | 乱数シード                                         |
| `avoid`  | `list[str] \| None`  | `None`      | 除外リスト（予約済みの屋号は自動除外）             |
| `whimsy` | `float`              | `0.25`      | 擬人化の出現率 (0〜1)。西洋風のみ                  |
| `style`  | `Literal`            | `"human"`   | 屋号に入る人名（「バーブラおばあ亭」など）の響き   |

いくつもの「型」がランダムに混ざります。

| 型                   | 例                                                           |
| :------------------- | :----------------------------------------------------------- |
| 形容詞+名詞          | うなる賢者酒店 / The Growling Sage Taproom                   |
| AとB                 | ひしゃくと藁の飲み屋                                         |
| 生き物の動作・持ち物 | ケンタウロスの溜息亭 / ワイバーンの寝息亭 / 女王の玉座の酒場 |
| 人名+親族            | ウォボレン親父亭 / Old Man Woboren's Tavern                  |
| 人名の物             | レシトラの聖座の宿屋 / Lesitla's Holy Seat Inn               |
| 種類が前             | 宿屋 ソドリス / 料亭 木漏れ日 / 旅籠 忘れっぽい熊            |
| 漢字二字             | 銀海亭 / 紅嵐の宿屋 / 翠峰下宿                               |
| 抽象語               | 流浪亭 / ほら吹き旅籠 / 幽霊館                               |

語尾も、亭・館・軒・荘・酒場・酒蔵・居酒屋・食事処・小料理屋・茶屋・茶寮・旅籠・旅館・山荘・下宿・定宿・ホテル・コテージなど、酒場と宿屋それぞれ十数種類から選ばれます。

形容詞は「生き物にだけ合うもの（酔いどれ・眠れる…）」と「何にでも合うもの（錆びた・銀の…）」に分けてあります。物には基本的に前者を付けませんが、`whimsy` の確率で擬人化を許し、「眠れるランタン亭」「眠らざるランタン亭」のような詩的な屋号を出します（`0` で無効）。単語表は `extra_data.py` にあり、語を足せばそのまま生成に反映されます。和風のローマ字は、漢字の音読みを機械的に当てたもので、読みの目安です。

### 5. `generate_shop_names`
店舗（武器屋・防具屋・道具屋・薬屋・魔道具店・鍛冶屋・宝石店・書店・パン屋など 19 種類）の店名を生成します。西洋風は日英対訳（「狼の牙武具店 / The Wolf's Fang Armory」）、和風は漢字+ローマ字（「琥珀森武具店 / Kohakushin Bugu-ten」）です。

| 引数        | 型                   | 既定値      | 説明                                                                 |
| :---------- | :------------------- | :---------- | :------------------------------------------------------------------- |
| `shop_type` | `Literal`            | `"any"`     | 店の種類。`any` はランダム。`weapon` (武器屋)、`potion` (薬屋)、`magic` (魔道具店) など |
| `tone`      | `Literal`            | `"western"` | 雰囲気 (`western` 西洋風 / `wafuu` 和風)                             |
| `count`     | `int`                | `5`         | 生成数 (1〜50)                                                       |
| `seed`      | `int \| str \| None` | `None`      | 乱数シード                                                           |
| `avoid`     | `list[str] \| None`  | `None`      | 除外リスト（予約済みの店名は自動除外）                               |
| `whimsy`    | `float`              | `0.25`      | 詩的な形容詞が混ざる率 (0〜1)。西洋風のみ                            |
| `style`     | `Literal`            | `"human"`   | 店名に入る人名の響き                                                 |

| 型 | 例 |
| :-- | :-- |
| 形容詞+生き物の店 | けなげな熊の宝石店 / The Devoted Bear Jeweler |
| 生き物の品の店 | 村民の宝冠宝石店 / 天狗の原石宝石店 |
| 生き物の店 | 狐の古書店 |
| 品の店 | 苔の薬草店 / 巻物の本屋 |
| 人名の店 | ネッテの八百屋 / Nette's Greengrocer |
| 人名+直結の店 | ナサネンの薬店（人名+店名を「の」なしで直結） / Nasanen Dispensary |
| 二人組の店 | レララとレマエウィンの肉屋 / Relara & Remaewyn's Butcher |
| 人名+親族の店 | シセルトおばあの花店 / Granny Sisert's Flower Shop |
| 立地・最上級の店 | 五差路の防具屋 / 街一番の靴屋 / The Finest in Town... |
| 集団・血縁の店 | 親子の武器店 / 六人組ドラッグ |
| 種類が前 | 魔道具店 お堅い鹿 / 質屋 華天 |
| 漢字二字 | 朧氷魔法店 / 紅鷹骨董品店 |
| 抽象語の店 | 雨宿りの花店 / 夜明けの仕立て屋 |

店の種類ごとに「その店の品」（武器屋なら牙・爪・刃、薬屋なら雫・瓶・軟膏…）と、店名の語（武器屋 / 武器店 / 武具店 / 刃物店 / ウェポン…）を持っています。表は `extra_data.py` の `SHOP_TYPES` にあり、行を足すとツールの選択肢にも自動で反映されます。ウェポン・ドラッグ・トレーダーのようなカタカナの店名語には、人名なら「・」（ウォリス・ショップ）、集団・血縁の語なら直結（六人組ドラッグ）というふうに、つなぎ方も変わります。

### 6. `generate_names_from_examples`
既存の名前リストからマルコフ連鎖で「同じ世界っぽい」名前を生成します。

| 引数       | 型                   | 既定値   | 説明                                     |
| :--------- | :------------------- | :------- | :--------------------------------------- |
| `examples` | `list[str]`          | **必須** | サンプル名リスト (3個以上、10個以上推奨) |
| `count`    | `int`                | `5`      | 生成数 (1〜50)                           |
| `order`    | `int`                | `2`      | マルコフ連鎖の次数 (1〜3)                |
| `avoid`    | `list[str] \| None`  | `None`   | 除外したい名前のリスト                   |
| `seed`     | `int \| str \| None` | `None`   | 乱数シード                               |

漢字やカナの例（「織田信長」など）も渡せます。2〜4 文字の短い名前は、次数を `1` にすると安定して新しい組み合わせが出ます。ローマ字の例にはカナ表記 (`kana`) が付きますが、漢字・カナの例には付きません。

### 7. `reserve_names` / `list_reserved` / `release_names`
- `reserve_names(names, note)`: 採用した名前を予約リストに記録（重複回避用）。
- `list_reserved()`: 予約済みの名前一覧を取得。
- `release_names(names)`: 予約を解除。

### 8. `list_styles`
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
