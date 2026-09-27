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
# 酒場・宿屋名  (en, ja) の対訳リスト。namaemaker の屋号サンプルにある型を参考にしている
# ---------------------------------------------------------------------------
# 形容詞: 生き物にも物にも合うもの
ADJ_ANY = [
    ("Rusty", "錆びた"), ("Silver", "銀の"), ("Golden", "金の"), ("Broken", "壊れた"),
    ("Crooked", "曲がった"), ("Blue", "青い"), ("Red", "赤い"), ("Black", "黒い"),
    ("White", "白い"), ("Green", "緑の"), ("Old", "古びた"), ("Lucky", "幸運の"),
    ("Last", "最後の"), ("Lonely", "孤独な"), ("Hidden", "隠れた"), ("Gilded", "金箔の"),
    ("Iron", "鉄の"), ("Cracked", "ひびの入った"), ("Shining", "輝ける"),
    ("Salty", "塩辛い"), ("Pure White", "真っ白な"), ("Fortunate", "幸多き"),
    ("Lukewarm", "生暖かい"),
]
# 形容詞: 生き物にだけ合うもの
ADJ_LIVING = [
    ("Drunken", "酔いどれ"), ("Sleeping", "眠れる"), ("Laughing", "笑う"),
    ("Dancing", "踊る"), ("Hungry", "腹ぺこの"), ("Thirsty", "喉の渇いた"),
    ("Wandering", "さまよう"), ("Weary", "くたびれた"), ("Prancing", "跳ねる"),
    ("Merry", "上機嫌な"), ("One-Eyed", "片目の"), ("Whistling", "口笛を吹く"),
    ("Grumbling", "不機嫌な"), ("Singing", "歌う"),
    ("Stiff", "お堅い"), ("Odd", "おかしな"), ("Jolly", "ひょうきんな"),
    ("Cheerful", "陽気な"), ("Growling", "うなる"), ("Tipsy", "酔いしれる"),
    ("Winged", "翼の生えた"), ("Lively", "元気な"), ("Passed-Out", "酔い潰れた"),
    ("Devoted", "けなげな"), ("Meticulous", "几帳面な"), ("Dozing", "まどろむ"),
    ("Timid", "気弱な"), ("Silent", "無口な"), ("Diligent", "勤勉な"),
    ("Clumsy", "不調法な"), ("Soft-Spoken", "声の小さい"), ("Contrary", "ひねくれた"),
    ("Cheeky", "生意気な"), ("Bashful", "はにかむ"), ("Snoring", "いびきをかく"),
]
# 形容詞: 擬人化・詩的なもの (物にも生き物にも使える。「眠らざるランタン亭」など)
ADJ_POETIC = [
    ("Sleepless", "眠らざる"), ("Weeping", "泣く"), ("Whispering", "ささやく"),
    ("Forgetful", "忘れっぽい"), ("Homesick", "郷愁の"),
    ("Unwinking", "瞬かぬ"), ("Far-Flung", "遥けき"), ("Soaring", "天翔ける"),
]
NOUN_LIVING = [
    ("Stag", "鹿"), ("Boar", "猪"), ("Crow", "鴉"), ("Goose", "ガチョウ"), ("Owl", "梟"),
    ("Fox", "狐"), ("Wolf", "狼"), ("Dragon", "竜"), ("Griffin", "グリフォン"),
    ("Bear", "熊"), ("Cat", "猫"), ("Toad", "蛙"), ("Hound", "猟犬"), ("Swan", "白鳥"),
    ("Nightingale", "夜鳴き鳥"), ("Ram", "雄羊"), ("Hare", "野兎"), ("Badger", "穴熊"),
    ("Heron", "青鷺"), ("Minstrel", "吟遊詩人"), ("Pilgrim", "巡礼者"), ("Jester", "道化師"),
    ("Centaur", "ケンタウロス"), ("Unicorn", "ユニコーン"), ("Slime", "スライム"),
    ("Skeleton", "スケルトン"), ("Goblin", "ゴブリン"), ("Dwarf", "ドワーフ"),
    ("Gnome", "ノーム"), ("Giant", "巨人"), ("Wyvern", "ワイバーン"), ("Chimera", "キマイラ"),
    ("Ghost", "幽霊"), ("Spirit", "精霊"), ("Goddess", "女神"), ("Sage", "賢者"),
    ("Knight", "騎士"), ("Thieving Cat", "泥棒猫"), ("Black Cat", "黒猫"),
    ("Calico Cat", "三毛猫"), ("Foal", "仔馬"), ("Piglet", "子豚"), ("Lamb", "子羊"),
    ("Puppy", "子犬"), ("Turkey", "七面鳥"), ("Pelican", "ペリカン"), ("Lark", "ヒバリ"),
    ("Mule", "ラバ"), ("Packhorse", "駄馬"), ("Hedgehog", "ハリネズミ"),
    ("Pirate", "海賊"), ("Swordsman", "剣客"), ("Queen", "女王"), ("Cowherd", "牛飼い"),
    ("Thunder Eagle", "雷鷲"), ("Three-Eyed One", "三つ目"), ("Stray Dog", "野良犬"),
    ("Green Whale", "緑鯨"), ("Great Horse", "大馬"), ("Villager", "村民"),
]
NOUN_OBJECT = [
    ("Anchor", "錨"), ("Barrel", "樽"), ("Lantern", "ランタン"), ("Crown", "王冠"),
    ("Kettle", "やかん"), ("Horseshoe", "蹄鉄"), ("Tankard", "ジョッキ"), ("Key", "鍵"),
    ("Bell", "鐘"), ("Wheel", "車輪"), ("Cauldron", "大鍋"), ("Sword", "剣"),
    ("Rose", "薔薇"), ("Moon", "月"), ("Sun", "太陽"), ("Star", "星"), ("Bridge", "橋"),
    ("Crossroads", "四つ辻"), ("Hearth", "炉端"), ("Candle", "蝋燭"), ("Mug", "マグ"),
    ("Compass", "羅針盤"), ("Thistle", "アザミ"), ("Oak", "樫の木"),
    ("Ladle", "ひしゃく"), ("Wheelbarrow", "手押し車"), ("Raft", "いかだ"), ("Mast", "マスト"),
    ("Pirate Flag", "海賊旗"), ("Coral", "珊瑚"), ("Straw", "藁"), ("Amber", "琥珀"),
]
# 「◯◯の△△」の△△: 生き物の動作・音・持ち物。(日本語, 英語, ローマ字)
#   例: 仔豚の寝息 / ケンタウロスの溜息 / ゴブリンのささやき / 狐の曲芸 / 子豚の玉座
TAVERN_ACTS = [
    ("溜息", "Sigh", "tameiki"), ("笑い声", "Laughter", "waraigoe"), ("鼻歌", "Humming", "hanauta"),
    ("涙", "Tear", "namida"), ("曲芸", "Trick", "kyokugei"), ("寝息", "Slumber", "neiki"),
    ("ささやき", "Whisper", "sasayaki"), ("しずく", "Drop", "shizuku"), ("歌声", "Song", "utagoe"),
    ("帰還", "Return", "kikan"), ("遠吠え", "Howl", "tooboe"), ("あくび", "Yawn", "akubi"),
    ("いびき", "Snore", "ibiki"), ("足音", "Footsteps", "ashioto"), ("夢", "Dream", "yume"),
    ("祈り", "Prayer", "inori"), ("鼻ちょうちん", "Snot Bubble", "hanachouchin"),
    ("玉座", "Throne", "gyokuza"), ("寝床", "Bed", "nedoko"), ("味", "Taste", "aji"),
    ("聖座", "Holy Seat", "seiza"), ("忘れ物", "Lost Item", "wasuremono"),
]
# 人名につく親族・愛称: (日本語, 英語, ローマ字)   例: リーター兄さん亭 / バーブラおばあ亭 / ヴケの親父宿
TAVERN_KIN = [
    ("兄さん", "Brother", "niisan"), ("姉さん", "Sister", "neesan"), ("おばあ", "Granny", "obaa"),
    ("親父", "Old Man", "oyaji"), ("若女将", "Young Landlady", "wakaokami"),
    ("女将", "Landlady", "okami"), ("おじさん", "Uncle", "ojisan"),
    ("おばちゃん", "Auntie", "obachan"), ("大将", "Boss", "taishou"), ("爺さん", "Old-Timer", "jiisan"),
]
# 漢字二字の飾り (色・性質 + 自然・生き物)。(日本語, 英語, 音読みのローマ字)
#   例: 金海 / 蒼空 / 紅天 / 翠陽 / 華雪 / 白狼 / 嵐鯨 / 月翠(自然+色の逆順もある)
KANJI_A = [
    ("紅", "Crimson", "kou"), ("蒼", "Azure", "sou"), ("翠", "Jade", "sui"), ("金", "Golden", "kin"),
    ("銀", "Silver", "gin"), ("白", "White", "haku"), ("黒", "Black", "koku"), ("赤", "Red", "seki"),
    ("碧", "Emerald", "heki"), ("華", "Blossom", "ka"), ("朧", "Hazy", "rou"), ("玄", "Dark", "gen"),
    ("琥珀", "Amber", "kohaku"), ("輝", "Shining", "ki"),
]
# KANJI_A のうち「色」の語。自然+色 の逆順 (月翠など) に使えるのはこれだけ
KANJI_COLORS = {"紅", "蒼", "翠", "金", "銀", "白", "黒", "赤", "碧", "玄", "琥珀"}
KANJI_B = [
    ("陽", "Sun", "you"), ("月", "Moon", "getsu"), ("星", "Star", "sei"), ("空", "Sky", "kuu"),
    ("海", "Sea", "kai"), ("雪", "Snow", "setsu"), ("虹", "Rainbow", "kou"), ("花", "Flower", "ka"),
    ("嵐", "Storm", "ran"), ("鯨", "Whale", "gei"), ("狼", "Wolf", "rou"), ("鹿", "Stag", "roku"),
    ("鶴", "Crane", "kaku"), ("天", "Heaven", "ten"), ("霧", "Mist", "mu"), ("風", "Wind", "fuu"),
    ("波", "Wave", "ha"), ("峰", "Peak", "hou"), ("泉", "Spring", "sen"), ("森", "Forest", "shin"),
    ("楓", "Maple", "fuu"), ("鷹", "Hawk", "you"), ("竜", "Dragon", "ryuu"), ("鳳", "Phoenix", "hou"),
    ("雷", "Thunder", "rai"), ("氷", "Ice", "hyou"),
]
# 抽象語・気分の言葉: (日本語, 英語, ローマ字)   例: 流浪亭 / 酔狂亭 / あの日の宿 / 出会い亭
TAVERN_ABSTRACT = [
    ("流浪", "Wanderer", "rurou"), ("酔狂", "Whimsy", "suikyou"), ("出会い", "Encounter", "deai"),
    ("親友", "Old Friend", "shinyuu"), ("古神", "Elder God", "koshin"), ("大神", "Great Deity", "ookami"),
    ("幽霊", "Ghost", "yuurei"), ("あの日", "Bygone Day", "ano hi"), ("真夜中", "Midnight", "mayonaka"),
    ("夜明け", "Daybreak", "yoake"), ("黄昏", "Dusk", "tasogare"), ("雨宿り", "Rain Shelter", "amayadori"),
    ("木漏れ日", "Dappled Sun", "komorebi"), ("片道切符", "One-Way Ticket", "katamichi kippu"),
    ("千鳥足", "Stumbling Steps", "chidoriashi"), ("ほら吹き", "Braggart", "horafuki"),
    ("道草", "Detour", "michikusa"), ("寄り道", "Side Trip", "yorimichi"),
    ("なごり雪", "Lingering Snow", "nagoriyuki"), ("星降り", "Starfall", "hoshifuri"),
    ("夕焼け", "Sunset", "yuuyake"), ("三日月", "Crescent Moon", "mikazuki"),
    ("落とし物", "Lost Property", "otoshimono"), ("無礼講", "Revel", "bureikou"),
]
# 種別ごとの (英語の接尾, 日本語の接尾, 重み)。英語の接尾が空なら "The ◯◯" のまま
TAVERN_SUFFIXES = dict(
    tavern=[
        ("", "亭", 4), ("Tavern", "酒場", 3), ("Tavern", "の酒場", 2), ("Alehouse", "の飲み屋", 2),
        ("Cellar", "酒蔵", 1), ("Taproom", "酒店", 1), ("Pub", "酒亭", 1), ("Pub", "居酒屋", 1),
        ("Eatery", "食事処", 1), ("Bistro", "小料理屋", 1), ("Teahouse", "茶屋", 1),
        ("Tea Room", "茶寮", 1), ("", "軒", 1),
    ],
    inn=[
        ("Inn", "の宿", 3), ("Inn", "の宿屋", 2), ("Inn", "亭", 3), ("Inn", "宿屋", 1),
        ("Lodge", "旅籠", 1), ("Guesthouse", "の旅館", 1), ("Lodge", "旅荘", 1),
        ("Chalet", "の山荘", 1), ("Boarding House", "下宿", 1), ("Inn", "の定宿", 1),
        ("Manor", "館", 1), ("Lodge", "荘", 1), ("Hotel", "ホテル", 1), ("Cottage", "コテージ", 1),
        ("Inn", "軒", 1),
    ],
)
# 「種類が前」の型で使う語: (日本語, 英語, ローマ字, 重み)   例: 宿屋 キャスリン / 飲み屋 心地良い親不孝
TAVERN_VENUES = dict(
    tavern=[
        ("酒場", "Tavern", "sakaba", 4), ("酒亭", "Pub", "shutei", 1), ("酒蔵", "Cellar", "sakagura", 1),
        ("飲み屋", "Alehouse", "nomiya", 2), ("居酒屋", "Pub", "izakaya", 1),
        ("酒店", "Taproom", "sakaten", 1), ("酒舗", "Taproom", "shuho", 1),
        ("料亭", "Restaurant", "ryoutei", 1), ("茶寮", "Tea Room", "saryou", 1),
        ("サロン", "Salon", "saron", 1),
    ],
    inn=[
        ("宿屋", "Inn", "yadoya", 4), ("旅籠", "Lodge", "hatago", 2), ("旅荘", "Lodge", "ryosou", 1),
        ("旅館", "Guesthouse", "ryokan", 2), ("下宿", "Boarding House", "geshuku", 1),
        ("山荘", "Chalet", "sansou", 1), ("ホテル", "Hotel", "hoteru", 1),
    ],
)
# 屋号の型と重み。西洋風は日英対訳、和風は漢字+ローマ字
#   adj=形容詞+名詞 / and=AとB / bare=名詞だけ / creature_act=生き物の動作 / person_kin=人名+親族 /
#   person_thing=人名の物 / type_first=種類が前 / kanji=漢字二字 / abstract=抽象語 / word=和の単語
TAVERN_PATTERNS_WESTERN = dict(
    adj=20, **{"and": 9}, bare=5, creature_act=16, person_kin=8, person_thing=6,
    type_first=10, kanji=14, abstract=8,
)
TAVERN_PATTERNS_WAFUU = dict(
    word=26, kanji=24, abstract=10, creature_act=14, person_kin=8, person_thing=6, type_first=12,
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
# 和風の「◯◯の△△」で使う生き物: (日本語, ローマ字)
WAFUU_CREATURES = [
    ("鶴", "tsuru"), ("亀", "kame"), ("狐", "kitsune"), ("狸", "tanuki"), ("猫", "neko"),
    ("鯉", "koi"), ("鹿", "shika"), ("猪", "inoshishi"), ("鴉", "karasu"), ("梟", "fukurou"),
    ("狼", "ookami"), ("熊", "kuma"), ("兎", "usagi"), ("馬", "uma"), ("竜", "ryuu"),
    ("鶏", "niwatori"), ("蛍", "hotaru"), ("河童", "kappa"), ("天狗", "tengu"), ("鬼", "oni"),
]
# 和風の接尾: (日本語, ローマ字, 重み)
WAFUU_TAVERN_SUFFIXES = dict(
    tavern=[
        ("屋", "ya", 4), ("亭", "tei", 3), ("の酒処", " no Sakedokoro", 2), ("酒蔵", "sakagura", 1),
        ("茶屋", "chaya", 2), ("茶寮", "saryou", 1), ("小料理屋", "koryouriya", 1),
        ("食事処", "shokujidokoro", 1), ("居酒屋", "izakaya", 1), ("軒", "ken", 1),
    ],
    inn=[
        ("屋", "ya", 3), ("荘", "sou", 2), ("の湯", " no Yu", 2), ("の宿", " no Yado", 2),
        ("旅籠", "hatago", 1), ("旅館", "ryokan", 1), ("旅荘", "ryosou", 1), ("館", "kan", 1),
        ("の山荘", " no Sansou", 1), ("下宿", "geshuku", 1), ("の定宿", " no Jouyado", 1),
        ("軒", "ken", 1),
    ],
)

# ---------------------------------------------------------------------------
# 店舗 (武器屋・道具屋・薬屋など)
# ---------------------------------------------------------------------------
# 店の種類ごとに:
#   label = 日本語の種類名 (一覧表示用)
#   names = 店名の語尾に使う語 [(日本語, 英語, ローマ字)]   例: 武器屋 / Arms / buki-ya
#   goods = その店の品 [(日本語, 英語, ローマ字)]           例: 狼の「牙」武器店
SHOP_TYPES = {
    "weapon": dict(
        label="武器屋",
        names=[("武器屋", "Arms", "buki-ya"), ("武器店", "Weaponsmith", "buki-ten"),
               ("武具店", "Armory", "bugu-ten"), ("刃物店", "Bladeworks", "hamono-ten")],
        goods=[("牙", "Fang", "kiba"), ("爪", "Claw", "tsume"), ("刃", "Blade", "yaiba"),
               ("穂先", "Spearhead", "hosaki"), ("矢", "Arrow", "ya"), ("剣", "Sword", "tsurugi")],
    ),
    "armor": dict(
        label="防具屋",
        names=[("防具屋", "Armory", "bougu-ya"), ("防具店", "Armor Shop", "bougu-ten"),
               ("甲冑店", "Harness", "katchuu-ten")],
        goods=[("鱗", "Scale", "uroko"), ("鎧", "Mail", "yoroi"), ("兜", "Helm", "kabuto"),
               ("盾", "Shield", "tate"), ("籠手", "Gauntlet", "kote")],
    ),
    "general": dict(
        label="道具屋・雑貨店",
        names=[("道具屋", "General Store", "dougu-ya"), ("雑貨店", "Sundries", "zakka-ten"),
               ("よろず屋", "Goods & Wares", "yorozuya"), ("何でも屋", "Odds & Ends", "nandemoya")],
        goods=[("袋", "Sack", "fukuro"), ("背負い袋", "Pack", "seoibukuro"), ("縄", "Rope", "nawa"),
               ("鍋", "Pot", "nabe"), ("提灯", "Lantern", "chouchin")],
    ),
    "potion": dict(
        label="薬屋",
        names=[("薬屋", "Apothecary", "kusuri-ya"), ("薬店", "Dispensary", "yaku-ten"),
               ("薬種店", "Drugstore", "yakushu-ten"), ("霊薬店", "Elixir Shop", "reiyaku-ten")],
        goods=[("雫", "Drop", "shizuku"), ("瓶", "Vial", "bin"), ("霊薬", "Elixir", "reiyaku"),
               ("軟膏", "Salve", "nankou"), ("煎じ薬", "Tincture", "senjigusuri")],
    ),
    "magic": dict(
        label="魔道具店",
        names=[("魔道具店", "Arcane Emporium", "madougu-ten"), ("魔法店", "Magic Shop", "mahou-ten"),
               ("呪具店", "Charm Shop", "jugu-ten"), ("魔導書店", "Grimoire Shop", "madousho-ten")],
        goods=[("杖", "Staff", "tsue"), ("水晶球", "Crystal Ball", "suishoudama"),
               ("護符", "Talisman", "gofu"), ("羅針盤", "Compass", "rashinban"),
               ("魔石", "Mana Stone", "maseki")],
    ),
    "blacksmith": dict(
        label="鍛冶屋",
        names=[("鍛冶屋", "Smithy", "kaji-ya"), ("鍛冶場", "Forge", "kajiba"),
               ("鋳物店", "Foundry", "imono-ten")],
        goods=[("金床", "Anvil", "kanatoko"), ("槌", "Hammer", "tsuchi"), ("炉", "Furnace", "ro"),
               ("火花", "Spark", "hibana"), ("鉄", "Iron", "tetsu")],
    ),
    "jeweler": dict(
        label="宝石店",
        names=[("宝石店", "Jeweler", "houseki-ten"), ("宝飾店", "Jewelry", "houshoku-ten"),
               ("貴金属店", "Gold & Silver", "kikinzoku-ten")],
        goods=[("指輪", "Ring", "yubiwa"), ("首飾り", "Necklace", "kubikazari"),
               ("原石", "Gemstone", "genseki"), ("耳飾り", "Earring", "mimikazari"),
               ("宝冠", "Tiara", "houkan")],
    ),
    "book": dict(
        label="書店",
        names=[("書店", "Bookshop", "sho-ten"), ("古書店", "Rare Books", "kosho-ten"),
               ("本屋", "Booksellers", "hon-ya"), ("貸本屋", "Lending Library", "kashihon-ya")],
        goods=[("紙", "Paper", "kami"), ("栞", "Bookmark", "shiori"), ("羊皮紙", "Parchment", "youhishi"),
               ("インク", "Ink", "inku"), ("巻物", "Scroll", "makimono")],
    ),
    "bakery": dict(
        label="パン屋・菓子店",
        names=[("パン屋", "Bakery", "pan-ya"), ("焼き菓子店", "Pastry Shop", "yakigashi-ten"),
               ("菓子店", "Confectioner", "kashi-ten")],
        goods=[("麦穂", "Wheat Ear", "mugiho"), ("窯", "Oven", "kama"),
               ("粉", "Flour", "kona"), ("小麦", "Wheat", "komugi"),
               ("蜂蜜", "Honey", "hachimitsu")],
    ),
    "grocer": dict(
        label="八百屋",
        names=[("八百屋", "Greengrocer", "yaoya"), ("青果店", "Produce Stall", "seika-ten"),
               ("食料品店", "Provisions", "shokuryouhin-ten")],
        goods=[("籠", "Basket", "kago"), ("収穫", "Harvest", "shuukaku"), ("根菜", "Root Veg", "konsai"),
               ("林檎", "Apple", "ringo"), ("畑", "Field", "hatake")],
    ),
    "butcher": dict(
        label="肉屋",
        names=[("肉屋", "Butcher", "niku-ya"), ("精肉店", "Meat Shop", "seiniku-ten")],
        goods=[("骨", "Bone", "hone"), ("燻製", "Smoked Meat", "kunsei"), ("包丁", "Cleaver", "houchou"),
               ("腸詰め", "Sausage", "chouzume")],
    ),
    "fishmonger": dict(
        label="魚屋",
        names=[("魚屋", "Fishmonger", "sakana-ya"), ("鮮魚店", "Fresh Fish", "sengyo-ten")],
        goods=[("網", "Net", "ami"), ("潮", "Tide", "shio"), ("銀鱗", "Silver Scale", "ginrin"),
               ("釣り針", "Fishhook", "tsuribari"), ("波止場", "Wharf", "hatoba")],
    ),
    "tailor": dict(
        label="仕立て屋",
        names=[("仕立て屋", "Tailor", "shitate-ya"), ("服飾店", "Clothier", "fukushoku-ten"),
               ("古着屋", "Second-Hand Clothes", "furugi-ya")],
        goods=[("針", "Needle", "hari"), ("糸", "Thread", "ito"), ("外套", "Cloak", "gaitou"),
               ("襟", "Collar", "eri"), ("反物", "Bolt of Cloth", "tanmono")],
    ),
    "herbalist": dict(
        label="薬草店",
        names=[("薬草店", "Herbalist", "yakusou-ten"), ("香草店", "Spice & Herb Shop", "kousou-ten"),
               ("草根屋", "Root & Herb Shop", "kusane-ya")],
        goods=[("薬草", "Herb", "yakusou"), ("根", "Root", "ne"), ("葉", "Leaf", "ha"),
               ("苔", "Moss", "koke"), ("露", "Dew", "tsuyu")],
    ),
    "antiques": dict(
        label="骨董品店",
        names=[("骨董品店", "Antiques", "kottouhin-ten"), ("古道具屋", "Curios", "furudougu-ya"),
               ("蒐集店", "Collector's Shop", "shuushuu-ten")],
        goods=[("古時計", "Old Clock", "furudokei"), ("遺物", "Relic", "ibutsu"), ("壺", "Urn", "tsubo"),
               ("古地図", "Old Map", "furuchizu"), ("硝子玉", "Glass Bead", "garasudama")],
    ),
    "pawn": dict(
        label="質屋",
        names=[("質屋", "Pawnshop", "shichi-ya"), ("買取店", "Buy & Sell", "kaitori-ten")],
        goods=[("担保", "Pledge", "tanpo"), ("預かり", "Deposit", "azukari"),
               ("形見", "Keepsake", "katami"), ("天秤", "Scale", "tenbin")],
    ),
    "florist": dict(
        label="花屋",
        names=[("花屋", "Florist", "hana-ya"), ("花店", "Flower Shop", "hana-ten")],
        goods=[("花束", "Bouquet", "hanataba"), ("蕾", "Bud", "tsubomi"), ("花弁", "Petal", "hanabira"),
               ("鉢", "Pot", "hachi"), ("種", "Seed", "tane")],
    ),
    "chandler": dict(
        label="蝋燭店",
        names=[("蝋燭店", "Chandlery", "rousoku-ten"), ("灯り屋", "Lamp Shop", "akari-ya")],
        goods=[("灯火", "Flame", "tomoshibi"), ("芯", "Wick", "shin"), ("蝋", "Wax", "rou"),
               ("燭台", "Candlestick", "shokudai")],
    ),
    "cartographer": dict(
        label="地図屋",
        names=[("地図屋", "Cartographer", "chizu-ya"), ("測量店", "Surveyor", "sokuryou-ten")],
        goods=[("羅針盤", "Compass", "rashinban"), ("等高線", "Contour", "toukousen"),
               ("海図", "Sea Chart", "kaizu"), ("方位", "Bearing", "houi")],
    ),
}
# 店名の型と重み (西洋風は日英対訳、和風は漢字+ローマ字)
#   adj_creature=形容詞+生き物の◯◯屋 / creature_good=生き物の品の◯◯屋 / creature_shop=生き物の◯◯屋 /
#   good_shop=品の◯◯屋 / person_shop=人名の◯◯屋 / person_kin=人名+親族の◯◯屋 /
#   type_first=種類が前 / kanji=漢字二字 / abstract=抽象語の◯◯屋
SHOP_PATTERNS_WESTERN = dict(
    adj_creature=18, creature_good=14, creature_shop=12, good_shop=8, person_shop=14,
    person_kin=8, type_first=12, kanji=12, abstract=10,
)
SHOP_PATTERNS_WAFUU = dict(
    creature_shop=18, creature_good=12, good_shop=8, person_shop=10, person_kin=8,
    type_first=14, kanji=18, abstract=12,
)
