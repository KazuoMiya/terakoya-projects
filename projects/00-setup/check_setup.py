#!/usr/bin/env python3
"""課題0の答え合わせ — ローカルでPythonが動く環境が整ったかを確認する。

使い方（projects/00-setup の中で）:
    python3 check_setup.py

すべて OK なら「環境OK」と表示される。それが課題0の修了の合図だ。
何か足りなければ、直し方をこの場で教えてくれる。
このスクリプトは何も壊さない・何も送らない。ただ確認するだけ。
"""
import sys


def check_python_version():
    """Python 3.9 以上か。"""
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 9):
        return True, f"Python {major}.{minor} が使えている"
    return False, (
        f"Python {major}.{minor} は少し古い。3.9 以上を用意しよう。\n"
        "     → 課題0『Windows編 / Mac編』の回に戻って、python3 を入れ直す。"
    )


def check_in_venv():
    """venv（プロジェクト用の道具箱）の中で動いているか。"""
    # venv を有効にしていると sys.prefix が base_prefix と分かれる。
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        return True, "venv の中で動いている（プロンプトに (.venv) が出ているはず）"
    return False, (
        "venv の外で動いている。\n"
        "     → まず venv を作り、有効にしてからもう一度実行しよう：\n"
        "         python3 -m venv .venv\n"
        "         source .venv/bin/activate   （Windows/WSL2 も Mac もこれ）\n"
        "         python3 check_setup.py\n"
        "     ※ venv は『課題0：venvとpip』の回で扱う。まだなら先にそこへ。"
    )


def main():
    print("== 課題0の答え合わせ ==\n")
    checks = [check_python_version(), check_in_venv()]

    all_ok = True
    for ok, message in checks:
        mark = "OK  " if ok else "まだ"
        print(f"[{mark}] {message}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("環境OK")
        print("ローカルでPythonを動かす準備が整った。課題0はここで修了。")
        print("次は課題1（projects/01-healthcheck/）へ。")
        return 0
    else:
        print("あと少し。上の『→』の手順で直して、もう一度実行しよう。")
        print("30分ねばっても抜けられないときは、無理に一人で戦わないこと。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
