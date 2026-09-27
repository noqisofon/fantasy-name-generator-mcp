"""コマンドライン用の入口。MCP を介さず、ターミナルから直接名前を生成する。

    fantasy-name-generator-mcp char    -s wafuu -g male -n 5 --family
    fantasy-name-generator-mcp place   -s southern -k desert -n 5
    fantasy-name-generator-mcp country -s human --gov empire
    fantasy-name-generator-mcp tavern  -t western -k inn -n 5

引数なしで起動すると、従来どおり MCP サーバーになる (Claude Desktop などの設定はそのまま使える)。
生成結果は名前だけを標準出力へ、seed や注記は標準error へ出す (パイプしやすいように)。
"""

import argparse
import json
import sys

from .index import (
    GOVERNMENTS,
    PLACE_KIND_JA,
    PLACE_KINDS,
    STYLES,
    character_names,
    country_names,
    list_reserved_names,
    names_from_examples,
    place_names,
    release,
    reserve,
    styles_overview,
    tavern_names,
)

PROG = "fantasy-name-generator-mcp"

EPILOG = f"""\
例:
  {PROG} char -s wafuu -g male -n 5 --family      和風の男性名を姓つきで5つ
  {PROG} place -s southern -k desert              南方風の砂漠の地名
  {PROG} country -s human -n 10                   国名 (政体は毎回ランダム)
  {PROG} country -s human --gov empire -n 3       西洋風の帝国名に限定
  {PROG} tavern -t western -k inn                 西洋風の宿屋名
  {PROG} tavern -t western -w 1 -n 30             擬人化を多めに (眠らざるランタン亭など)
  {PROG} examples Santanyaan Maribel Marisol      既存の名前に響きを寄せて新しい名前を作る
  {PROG} reserve "金の竜亭" --note 主人公の常宿    採用した名前を予約(以後の生成で重複回避)
  {PROG} char -s elf --seed 42 --json             同じ seed なら同じ結果 / JSON で出力

引数なしで起動すると MCP サーバーになります。
"""

TAVERN_KIND_JA = {"tavern": "酒場", "inn": "宿屋"}


def _seed(value: str):
    """数字だけなら int、それ以外は文字列の seed"""
    try:
        return int(value)
    except ValueError:
        return value


def _common(count: bool = True, seed: bool = True, avoid: bool = True) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(add_help=False)
    if count:
        p.add_argument("-n", "--count", type=int, default=5, help="生成する個数 (1〜50, 既定5)")
    if seed:
        p.add_argument("--seed", type=_seed, default=None,
                       help="乱数シード。同じ引数と seed なら同じ結果になる (省略時は自動)")
    if avoid:
        p.add_argument("--avoid", action="append", default=None, metavar="名前",
                       help="除外したい名前 (複数回指定できる。予約済みの名前は自動で除外)")
    p.add_argument("--json", action="store_true", help="JSON で出力する")
    return p


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=PROG,
        description="創作用の名前ジェネレーター (キャラ名・地名・国名・酒場/宿屋名)。",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", metavar="<コマンド>")
    styles = list(STYLES)

    sub.add_parser("serve", help="MCP サーバーとして起動する (引数なしでも同じ)")

    c = sub.add_parser("char", aliases=["character"], parents=[_common()],
                       help="キャラクター名")
    c.add_argument("-s", "--style", choices=styles, default="elf", help="スタイル (既定 elf)")
    c.add_argument("-g", "--gender", choices=["any", "male", "female", "neutral"], default="any",
                   help="性別 (既定 any)")
    c.add_argument("--family", action="store_true", help="姓も付ける")
    c.add_argument("--starts-with", metavar="文字列", help="先頭の文字列 (例: ka)")

    pl = sub.add_parser("place", parents=[_common()], help="地名 (町・砂漠・平原など)")
    pl.add_argument("-s", "--style", choices=styles, default="elf", help="スタイル (既定 elf)")
    pl.add_argument("-k", "--kind", choices=PLACE_KINDS, default="town", metavar="種別",
                    help="地名の種別 (既定 town): " + " / ".join(PLACE_KINDS))
    pl.add_argument("--starts-with", metavar="文字列", help="先頭の文字列")

    co = sub.add_parser("country", parents=[_common()], help="国名 (政体つき)")
    co.add_argument("-s", "--style", choices=styles, default="elf", help="スタイル (既定 elf)")
    co.add_argument("--gov", "--government", dest="government", choices=["any", *GOVERNMENTS],
                    default="any", metavar="政体",
                    help="政体 (既定 any = ランダム)。empire, republic, bishopric, spirit, ... "
                         "全一覧は `styles` コマンドで確認")
    co.add_argument("--plain", action="store_true",
                    help="型を混ぜず「名前+政体」だけにする (既定は、前置き・二つ名・並記なども混ぜる)")
    co.add_argument("--starts-with", metavar="文字列", help="先頭の文字列")

    t = sub.add_parser("tavern", parents=[_common()], help="酒場・宿屋の屋号")
    t.add_argument("-t", "--tone", choices=["western", "wafuu"], default="western",
                   help="雰囲気 (既定 western)")
    t.add_argument("-k", "--kind", choices=["any", "tavern", "inn"], default="any",
                   help="種別 (既定 any)")
    t.add_argument("-w", "--whimsy", type=float, default=0.25, metavar="0〜1",
                   help="擬人化の出現率 (既定 0.25。西洋風のみ)")

    ex = sub.add_parser("examples", parents=[_common()],
                        help="既存の名前から響きを学習して新しい名前を作る")
    ex.add_argument("names", nargs="+", metavar="名前", help="お手本の名前 (3個以上、10個以上推奨)")
    ex.add_argument("--order", type=int, default=2, choices=[1, 2, 3],
                    help="マルコフ連鎖の次数 (既定2。漢字など短い名前は1が安定)")

    rs = sub.add_parser("reserve", parents=[_common(count=False, seed=False, avoid=False)],
                        help="採用した名前を予約する (以後の生成で重複・類似を避ける)")
    rs.add_argument("names", nargs="+", metavar="名前")
    rs.add_argument("--note", default="", help="メモ")

    sub.add_parser("reserved", parents=[_common(count=False, seed=False, avoid=False)],
                   help="予約済みの名前を一覧する")

    rl = sub.add_parser("release", parents=[_common(count=False, seed=False, avoid=False)],
                        help="予約を解除する")
    rl.add_argument("names", nargs="+", metavar="名前")

    sub.add_parser("styles", parents=[_common(count=False, seed=False, avoid=False)],
                   help="スタイル・地名種別・政体の一覧と見本")
    return p


# ---------------------------------------------------------------------------
# 出力
# ---------------------------------------------------------------------------
def _emit(result: dict, args, fmt) -> int:
    """結果を出力し、1つも作れなかったときは 1、それ以外は 0 を返す"""
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["names"] else 1
    for item in result["names"]:
        print(fmt(item))
    if "seed" in result:
        print(f"# seed: {result['seed']}  (同じ結果を出すには --seed {result['seed']})", file=sys.stderr)
    if "しか作れません" in result.get("note", ""):  # 固定の説明文は出さず、足りなかった時だけ知らせる
        print(f"# {result['note'].split(' / ')[-1]}", file=sys.stderr)
    return 0 if result["names"] else 1


def _fmt_char(n: dict) -> str:
    name = n["name"] + (f" {n['family']}" if "family" in n else "")
    kana = n["kana"] + (f" {n['family_kana']}" if "family_kana" in n else "")
    return f"{name}  ({kana})  [{n['gender']}]"


def _fmt_place(n: dict) -> str:
    return f"{n['name']}  ({n['kana']})  {n['ja_name']}   -{n['suffix']}: {n['suffix_meaning']}"


def _fmt_country(n: dict) -> str:
    return f"{n['ja_name']}  /  {n['en_formal']}   (元首: {n['ruler_title']})"


def _fmt_tavern(n: dict) -> str:
    return f"{n['ja']}  /  {n['en']}   [{TAVERN_KIND_JA.get(n['kind'], n['kind'])}]"


def _fmt_example(n: dict) -> str:
    return n["name"] + (f"  ({n['kana']})" if "kana" in n else "")


def _run_reserve(args) -> None:
    r = reserve(args.names, args.note)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    if r["reserved"]:
        print("予約しました: " + ", ".join(r["reserved"]))
    if r["already_reserved"]:
        print("すでに予約済み: " + ", ".join(r["already_reserved"]))
    print(f"# 予約は合計 {r['total']} 件", file=sys.stderr)


def _run_reserved(args) -> None:
    r = list_reserved_names()
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    for e in r["names"]:
        print(e["name"] + (f"   # {e['note']}" if e.get("note") else ""))
    print(f"# 合計 {r['total']} 件  保存先: {r['store_path']}", file=sys.stderr)


def _run_release(args) -> None:
    r = release(args.names)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    if r["released"]:
        print("解除しました: " + ", ".join(r["released"]))
    if r["not_found"]:
        print("見つかりません: " + ", ".join(r["not_found"]))


def _run_styles(args) -> None:
    r = styles_overview()
    r["governments"] = {k: v["ja"] for k, v in GOVERNMENTS.items()}
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return
    print("[スタイル]  (-s)")
    for s in r["styles"]:
        print(f"  {s['style']:9} {s['label']}  例: {', '.join(s['samples'])}")
    print("\n[地名の種別]  (place -k)")
    print("  " + " / ".join(f"{k}({PLACE_KIND_JA[k]})" for k in PLACE_KINDS))
    print("\n[政体]  (country --gov。any=ランダム)")
    print("  " + " / ".join(f"{k}({v['ja']})" for k, v in GOVERNMENTS.items()))


def run(argv: list[str] | None = None) -> int:
    """CLI を実行して終了コードを返す (0=成功, 2=引数や値のエラー)"""
    for stream in (sys.stdout, sys.stderr):  # Windows のコンソールでも日本語が化けないように
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = {"character": "char"}.get(args.cmd, args.cmd)
    if cmd is None:
        parser.print_help()
        return 0
    try:
        if cmd == "char":
            r = character_names(args.style, args.count, args.gender, args.seed, args.family,
                                args.starts_with, avoid=args.avoid)
            return _emit(r, args, _fmt_char)
        elif cmd == "place":
            r = place_names(args.style, args.kind, args.count, args.seed, args.starts_with,
                            avoid=args.avoid)
            return _emit(r, args, _fmt_place)
        elif cmd == "country":
            r = country_names(args.style, args.government, args.count, args.seed,
                              args.starts_with, avoid=args.avoid, decorate=not args.plain)
            return _emit(r, args, _fmt_country)
        elif cmd == "tavern":
            r = tavern_names(args.tone, args.kind, args.count, args.seed, args.avoid, args.whimsy)
            return _emit(r, args, _fmt_tavern)
        elif cmd == "examples":
            r = names_from_examples(args.names, args.count, args.seed, args.order, avoid=args.avoid)
            return _emit(r, args, _fmt_example)
        elif cmd == "reserve":
            _run_reserve(args)
        elif cmd == "reserved":
            _run_reserved(args)
        elif cmd == "release":
            _run_release(args)
        elif cmd == "styles":
            _run_styles(args)
        else:
            parser.error(f"未対応のコマンド: {cmd}")
    except ValueError as e:  # 入力値の誤り (例: examples が3個未満)
        print(f"エラー: {e}", file=sys.stderr)
        return 2
    return 0
