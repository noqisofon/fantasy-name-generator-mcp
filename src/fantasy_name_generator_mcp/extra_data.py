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
# 政体 -> 日本語の語 / 英語の正式名テンプレート / 元首の称号
GOVERNMENTS = {
    "kingdom": dict(ja="王国", en="Kingdom of {}", ruler="王"),
    "empire": dict(ja="帝国", en="{} Empire", ruler="皇帝"),
    "republic": dict(ja="共和国", en="Republic of {}", ruler="大統領"),
    "duchy": dict(ja="公国", en="Duchy of {}", ruler="公爵"),
    "federation": dict(ja="連邦", en="{} Federation", ruler="連邦議長"),
    "theocracy": dict(ja="教国", en="Holy Realm of {}", ruler="教皇"),
    "tribal": dict(ja="部族連合", en="{} Tribal Confederacy", ruler="大族長"),
}

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
