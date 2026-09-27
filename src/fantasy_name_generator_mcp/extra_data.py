"""地名(地形)・国名・酒場/宿屋名のためのデータ表。

ロジックは index.py にあり、ここは「表」だけを持つ (世界観に合わせて自由に書き換えてよい)。
接尾辞は "suffix:意味,suffix:意味" 形式で、同じスタイル内では同じ接尾辞が常に同じ意味になる。
"""

# ---------------------------------------------------------------------------
# 地名: 追加の種別 (都市以外の地形など)
# ---------------------------------------------------------------------------
EXTRA_PLACE_KINDS_JA = dict(
    plains="平原", desert="砂漠", wasteland="荒野", swamp="湿地", hills="丘陵",
    valley="谷", coast="海岸", sea="海", island="島", cave="洞窟", ruins="遺跡",
)

# ja_name (例: 「ネマル砂漠」) を作るときに、語幹のカナの後ろへ付ける語
KIND_JA_TERM = dict(
    town="の町", city="の街", mountain="山", river="川", forest="の森", lake="湖",
    fortress="砦", kingdom="王国",
    plains="平原", desert="砂漠", wasteland="荒野", swamp="湿地", hills="丘陵",
    valley="谷", coast="海岸", sea="海", island="島", cave="洞窟", ruins="遺跡",
)
# (和風は、選ばれた接尾辞の意味 = 町・村・山 など漢字の語をそのまま ja_name に使う)

# style -> kind -> "suffix:意味,..."   (既存の kind に書くと接尾辞が追加される)
EXTRA_PLACES = {
    "elf": dict(
        plains="vael:草原,lanna:野", desert="sahr:砂漠,ithra:乾いた地",
        wasteland="morn:荒れ地,dhar:荒野", swamp="nuil:湿地,lohm:沼地",
        hills="rodh:丘陵,hael:丘", valley="glenn:谷,imra:深い谷",
        coast="faer:海岸,sirae:浜", sea="aear:海,thalas:大海",
        island="tola:島,enor:小島", cave="amir:洞窟,ondu:地下の洞",
        ruins="thurin:遺跡,ondor:廃都",
    ),
    "dwarf": dict(
        plains="gard:平原,mag:野", desert="skar:砂漠,zahn:砂の地",
        wasteland="kraz:荒野,dug:荒れ地", swamp="mud:沼地,gulm:湿地",
        hills="bar:丘陵,kop:丘", valley="dal:谷,klov:峡谷",
        coast="strand:海岸,vik:入り江", sea="hav:海,mar:大海",
        island="holm:島,ey:小島", cave="kul:洞窟,gruf:坑道",
        ruins="dun:遺跡,brok:廃墟",
    ),
    "human": dict(
        plains="field:平野,mead:牧草地,plain:平原", desert="sands:砂漠,dune:砂丘",
        wasteland="moor:荒野,barrens:不毛の地,waste:荒れ地",
        swamp="fen:沼沢,marsh:湿地,bog:泥炭沼",
        hills="downs:丘陵,hill:丘,wold:高原の丘", valley="dale:谷,vale:渓谷,glen:峡谷",
        coast="shore:海岸,strand:浜,cove:入り江", sea="sea:海,deep:深海",
        island="isle:島,ey:小島", cave="cave:洞窟,hollow:洞",
        ruins="ruin:遺跡,barrow:古墳,stones:石の遺跡",
    ),
    "orc": dict(
        plains="grash:荒原,nar:野", desert="kharr:砂漠,zuul:灼熱の地",
        wasteland="skorg:荒野,ashk:焦土", swamp="murk:沼地,bruk:泥地",
        hills="krum:丘陵,dak:丘", valley="gulg:谷,ruk:峡谷",
        coast="shrak:海岸,gnash:荒磯", sea="gorr:海,zul:大海",
        island="rok:島,mub:小島", cave="gob:洞窟,hrag:巣穴",
        ruins="ghul:廃墟,krom:遺跡",
    ),
    "wafuu": dict(
        plains="hara:原,nohara:野原,heigen:平原", desert="sabaku:砂漠,sakyu:砂丘",
        wasteland="koya:荒野,arano:荒れ野", swamp="shitsugen:湿原,numa:沼",
        hills="oka:丘,kyuuryou:丘陵", valley="tani:谷,keikoku:渓谷",
        coast="hama:浜,kaigan:海岸", sea="umi:海,nada:灘",
        island="shima:島,jima:島", cave="iwaya:岩屋,doukutsu:洞窟",
        ruins="iseki:遺跡,haikyo:廃墟",
    ),
    "arcane": dict(
        plains="zhar:平原,enn:野", desert="khem:砂漠,sahk:砂の海",
        wasteland="vor:荒野,azh:荒れ地", swamp="mire:沼地,ulm:湿地",
        hills="kaal:丘陵,dur:丘", valley="nul:谷,orr:深淵の谷",
        coast="shal:海岸,ith:浜", sea="ythe:海,neth:冥き海",
        island="isk:島,ovh:小島", cave="krypt:洞窟,ghar:地下洞",
        ruins="ossu:遺跡,tomb:墓所",
    ),
    "southern": dict(
        town="abad:村,zir:集落", city="kand:都,ashar:大都市",
        plains="sahl:平原,marg:野", desert="sahra:砂漠,rimal:砂丘",
        wasteland="qafr:荒野,khar:荒れ地", swamp="hawr:湿地,sabkha:塩沼",
        hills="tell:丘,nejd:高地", valley="dara:谷,ghor:低地の谷",
        coast="sahil:海岸,ras:岬", sea="bahar:海,yam:大海",
        island="jazir:島,nes:小島", cave="ghar:洞窟,kahf:洞",
        ruins="khirb:廃墟,atar:遺跡",
    ),
}

# ---------------------------------------------------------------------------
# 国名
# ---------------------------------------------------------------------------
# 政体 -> ja=日本語の語 / en=英語の正式名テンプレート / ruler=元首の称号 / w=ランダム選択時の重み
GOVERNMENTS = {
    # --- 王国・帝国など (古典的な国) ---
    "kingdom": dict(ja="王国", en="Kingdom of {}", ruler="王", w=3),
    "empire": dict(ja="帝国", en="{} Empire", ruler="皇帝", w=3),
    "republic": dict(ja="共和国", en="Republic of {}", ruler="大統領", w=3),
    "duchy": dict(ja="公国", en="Duchy of {}", ruler="公爵", w=2),
    "grand_duchy": dict(ja="大公国", en="Grand Duchy of {}", ruler="大公", w=2),
    "grand_duchy_land": dict(ja="大公領", en="Grand Duchy of {}", ruler="大公", w=2),
    "principality": dict(ja="侯国", en="Principality of {}", ruler="侯", w=1),
    "emirate": dict(ja="首長国", en="Emirate of {}", ruler="首長", w=1),
    "sultanate": dict(ja="スルタン国", en="Sultanate of {}", ruler="スルタン", w=1),
    "dynasty": dict(ja="王朝", en="{} Dynasty", ruler="王", w=1),
    "holy_dynasty": dict(ja="聖導王朝", en="Holy Guiding Dynasty of {}", ruler="聖導王", w=1),
    "nation": dict(ja="国", en="Land of {}", ruler="国主", w=4),
    # --- 宗教・騎士団 ---
    "theocracy": dict(ja="教国", en="Holy Realm of {}", ruler="教皇", w=2),
    "bishopric": dict(ja="司教領", en="Bishopric of {}", ruler="司教", w=2),
    "monastic": dict(ja="修道院領", en="Monastic State of {}", ruler="修道院長", w=1),
    "holy_order": dict(ja="神聖騎士団領", en="Holy Order State of {}", ruler="騎士団総長", w=1),
    "law": dict(ja="法国", en="Law-State of {}", ruler="法王", w=1),
    "covenant": dict(ja="誓約", en="Covenant of {}", ruler="誓約者", w=1),
    # --- ファンタジー ---
    "spirit": dict(ja="精霊国", en="Spirit Realm of {}", ruler="精霊王", w=2),
    "fairy": dict(ja="妖精国", en="Fairy Realm of {}", ruler="妖精女王", w=2),
    "dragon": dict(ja="竜王国", en="Dragon Kingdom of {}", ruler="竜王", w=1),
    "arcane": dict(ja="魔道邦", en="Arcane League of {}", ruler="大魔導師", w=1),
    "cosmic": dict(ja="宇宙国", en="Cosmic State of {}", ruler="星帝", w=1),
    "underground": dict(ja="地下戦線", en="{} Underground Front", ruler="指導者", w=1),
    # --- 連邦・同盟・社会主義など (近現代風) ---
    "federation": dict(ja="連邦", en="{} Federation", ruler="連邦議長", w=2),
    "confederation": dict(ja="諸侯連合", en="Confederation of Lords of {}", ruler="盟主", w=1),
    "tribal": dict(ja="部族連合", en="{} Tribal Confederacy", ruler="大族長", w=1),
    "alliance": dict(ja="同盟", en="{} Alliance", ruler="盟主", w=1),
    "coalition": dict(ja="連合政権", en="{} Coalition Government", ruler="首相", w=1),
    "league": dict(ja="協商邦", en="{} Commercial League", ruler="議長", w=1),
    "autonomous": dict(ja="自治領", en="Dominion of {}", ruler="総督", w=1),
    "city_state": dict(ja="市国", en="City-State of {}", ruler="市長", w=1),
    "socialist": dict(ja="社会主義国", en="Socialist State of {}", ruler="書記長", w=1),
    "socialist_republic": dict(ja="社会主義共和国", en="Socialist Republic of {}", ruler="書記長", w=1),
    "democratic_republic": dict(ja="民主共和国", en="Democratic Republic of {}", ruler="大統領", w=1),
    "peoples_republic": dict(ja="民主人民共和国", en="Democratic People's Republic of {}", ruler="最高指導者", w=1),
}

# 国名の型 (decorate=True のとき、重みに従ってどれかを使う)
#  plain=名前+政体 / prefix=地域名の前置き / epithet=二つ名 / bare=名前だけ / no_of=「〜の国」 /
#  pair=二つの名前の並記 / katakana=「〜・リパブリック」 / dynasty_realm=「◯◯朝△△王国」
COUNTRY_PATTERNS = dict(
    plain=46, prefix=12, epithet=10, bare=6, no_of=5, pair=10, katakana=6, dynasty_realm=5,
)
# 地域名の前置き: (日本語, 英語)
COUNTRY_PREFIXES = [
    ("極東", "Far East"), ("西極", "Far West"), ("東海", "East Sea"), ("北辺", "Northern"),
    ("南洋", "Southern Sea"), ("中原", "Central"), ("大", "Greater"), ("新", "New"),
    ("旧", "Old"), ("上", "Upper"), ("下", "Lower"),
]
# 二つ名: (日本語, 英語)   例: 「常夏の帝国 ツェムァ」「川の大公国 アリアンヌ」
COUNTRY_EPITHETS = [
    ("常夏の", "Eternal Summer"), ("川の", "River"), ("森の", "Forest"), ("砂の", "Sand"),
    ("星の", "Star"), ("海の", "Sea"), ("氷の", "Ice"), ("鉄の", "Iron"), ("白き", "White"),
    ("黒き", "Black"), ("黄昏の", "Twilight"), ("霧の", "Mist"), ("翡翠の", "Jade"),
    ("琥珀の", "Amber"),
]
# 「〜・リパブリック」型: 政体 -> (カタカナ, 英語テンプレート)
COUNTRY_KATAKANA = dict(
    republic=("リパブリック", "{} Republic"), federation=("フェデレーション", "{} Federation"),
    empire=("エンパイア", "{} Empire"), kingdom=("キングダム", "{} Kingdom"),
    alliance=("ユニオン", "{} Union"), league=("リーグ", "{} League"),
)
# 二つの名前を「及び」で結ぶのが自然な政体 (それ以外は「・」)
COUNTRY_PAIR_AND = {"coalition", "federation", "alliance", "confederation"}
# 「◯◯朝△△王国」型を作れる政体
COUNTRY_DYNASTY_OK = {"kingdom", "empire", "grand_duchy", "sultanate"}

# 国名の語尾 (スタイルごと)
COUNTRY_ENDINGS = dict(
    elf=["dor", "orien", "ael", "aan", "eth"],
    dwarf=["heim", "dur", "gar", "karn", "bek"],
    human=["ia", "land", "mark", "aine", "ova", "ania"],
    orc=["mok", "gash", "ar", "zur", "gor"],
    wafuu=["no", "tsu", "ne", "sato", "shima"],
    arcane=["oth", "aeon", "ul", "ax", "azar"],
    southern=["istan", "ania", "ara", "ya", "ur"],
)

# ---------------------------------------------------------------------------
# 酒場・宿屋名  (en, ja) の対訳リスト
# ---------------------------------------------------------------------------
# 形容詞: 生き物にも物にも合うもの
ADJ_ANY = [
    ("Rusty", "錆びた"), ("Silver", "銀の"), ("Golden", "金の"), ("Broken", "壊れた"),
    ("Crooked", "曲がった"), ("Blue", "青い"), ("Red", "赤い"), ("Black", "黒い"),
    ("White", "白い"), ("Green", "緑の"), ("Old", "古びた"), ("Lucky", "幸運の"),
    ("Last", "最後の"), ("Lonely", "孤独な"), ("Hidden", "隠れた"), ("Gilded", "金箔の"),
    ("Iron", "鉄の"), ("Cracked", "ひびの入った"),
]
# 形容詞: 生き物にだけ合うもの
ADJ_LIVING = [
    ("Drunken", "酔いどれ"), ("Sleeping", "眠れる"), ("Laughing", "笑う"),
    ("Dancing", "踊る"), ("Hungry", "腹ぺこの"), ("Thirsty", "喉の渇いた"),
    ("Wandering", "さまよう"), ("Weary", "くたびれた"), ("Prancing", "跳ねる"),
    ("Merry", "上機嫌な"), ("One-Eyed", "片目の"), ("Whistling", "口笛を吹く"),
    ("Grumbling", "不機嫌な"), ("Singing", "歌う"),
]
# 形容詞: 擬人化・詩的なもの (物にも生き物にも使える。「眠らざるランタン亭」など)
ADJ_POETIC = [
    ("Sleepless", "眠らざる"), ("Weeping", "泣く"), ("Whispering", "ささやく"),
    ("Forgetful", "忘れっぽい"), ("Homesick", "郷愁の"),
    ("Unwinking", "瞬かぬ"),
]
NOUN_LIVING = [
    ("Stag", "鹿"), ("Boar", "猪"), ("Crow", "鴉"), ("Goose", "ガチョウ"), ("Owl", "梟"),
    ("Fox", "狐"), ("Wolf", "狼"), ("Dragon", "竜"), ("Griffin", "グリフォン"),
    ("Bear", "熊"), ("Cat", "猫"), ("Toad", "蛙"), ("Hound", "猟犬"), ("Swan", "白鳥"),
    ("Nightingale", "夜鳴き鳥"), ("Ram", "雄羊"), ("Hare", "野兎"), ("Badger", "穴熊"),
    ("Heron", "青鷺"), ("Minstrel", "吟遊詩人"), ("Pilgrim", "巡礼者"), ("Jester", "道化師"),
]
NOUN_OBJECT = [
    ("Anchor", "錨"), ("Barrel", "樽"), ("Lantern", "ランタン"), ("Crown", "王冠"),
    ("Kettle", "やかん"), ("Horseshoe", "蹄鉄"), ("Tankard", "ジョッキ"), ("Key", "鍵"),
    ("Bell", "鐘"), ("Wheel", "車輪"), ("Cauldron", "大鍋"), ("Sword", "剣"),
    ("Rose", "薔薇"), ("Moon", "月"), ("Sun", "太陽"), ("Star", "星"), ("Bridge", "橋"),
    ("Crossroads", "四つ辻"), ("Hearth", "炉端"), ("Candle", "蝋燭"), ("Mug", "マグ"),
    ("Compass", "羅針盤"), ("Thistle", "アザミ"), ("Oak", "樫の木"),
]
# 種別ごとの (英語の接尾, 日本語の接尾, 重み)。英語の接尾が空なら "The ◯◯" のまま
TAVERN_SUFFIXES = dict(
    tavern=[("", "亭", 4), ("Tavern", "酒場", 2), ("Alehouse", "酒場", 1)],
    inn=[("Inn", "の宿", 3), ("Inn", "亭", 3), ("Lodge", "荘", 1)],
)

# 和風: (日本語, ローマ字)
WAFUU_WORDS = [
    ("鶴", "tsuru"), ("亀", "kame"), ("月", "tsuki"), ("松", "matsu"), ("梅", "ume"),
    ("桜", "sakura"), ("雪", "yuki"), ("蛍", "hotaru"), ("狐", "kitsune"), ("狸", "tanuki"),
    ("猫", "neko"), ("鯉", "koi"), ("竹", "take"), ("藤", "fuji"), ("菊", "kiku"),
    ("鈴", "suzu"), ("霞", "kasumi"), ("月見", "tsukimi"), ("花見", "hanami"),
    ("雪見", "yukimi"), ("夕凪", "yuunagi"), ("朝霧", "asagiri"), ("松風", "matsukaze"),
    ("波音", "namioto"), ("夜桜", "yozakura"), ("狐火", "kitsunebi"), ("常盤", "tokiwa"),
    ("暁", "akatsuki"), ("朧月", "oboroduki"), ("千鳥", "chidori"), ("初雁", "hatsukari"),
    ("紅葉", "momiji"), ("夕月", "yuuzuki"), ("岩清水", "iwashimizu"),
]
# 和風の接尾: (日本語, ローマ字, 重み)
WAFUU_TAVERN_SUFFIXES = dict(
    tavern=[("屋", "ya", 4), ("亭", "tei", 3), ("の酒処", " no Sakedokoro", 2)],
    inn=[("屋", "ya", 3), ("荘", "sou", 2), ("の湯", " no Yu", 2), ("の宿", " no Yado", 2)],
)
