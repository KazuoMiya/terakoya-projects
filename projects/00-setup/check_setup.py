#!/usr/bin/env python3
"""課題0の答え合わせ — ローカルでPythonが動く環境が整ったかを確認する。

使い方（projects/00-setup の中で）:
    python3 check_setup.py

すべて OK なら「環境OK」と表示される。それが課題0の修了の合図だ。
何か足りなければ、直し方をこの場で教えてくれる。
このスクリプトは何も壊さない・何も送らない。ただ確認するだけ。

Checking your answer for Assignment 0 — confirms that your local Python
environment is ready.

Usage (from inside projects/00-setup):
    python3 check_setup.py

If everything is OK, it prints "環境OK / Environment OK" — that is the sign
that Assignment 0 is complete. If something is missing, it tells you right
here how to fix it. This script breaks nothing and sends nothing. It only checks.
"""
import sys


def check_python_version():
    """Python 3.9 以上か。

    Is this Python 3.9 or newer?
    """
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 9):
        return True, f"Python {major}.{minor} が使えている / Python {major}.{minor} is available"
    return False, (
        f"Python {major}.{minor} は少し古い。3.9 以上を用意しよう。 / Python {major}.{minor} is a bit old. Get 3.9 or newer.\n"
        "     → 課題0『Windows編 / Mac編』の回に戻って、python3 を入れ直す。 / Go back to the Assignment 0 lesson (Windows / Mac edition) and reinstall python3."
    )


def check_in_venv():
    """venv（プロジェクト用の道具箱）の中で動いているか。

    Are we running inside a venv (the project's own toolbox)?
    """
    # venv を有効にしていると sys.prefix が base_prefix と分かれる。
    # With a venv active, sys.prefix diverges from base_prefix.
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if in_venv:
        return True, "venv の中で動いている（プロンプトに (.venv) が出ているはず） / Running inside a venv (your prompt should show (.venv))"
    return False, (
        "venv の外で動いている。 / Running outside a venv.\n"
        "     → まず venv を作り、有効にしてからもう一度実行しよう： / First create a venv, activate it, then run this again:\n"
        "         python3 -m venv .venv\n"
        "         source .venv/bin/activate   （Windows/WSL2 も Mac もこれ / same on Windows/WSL2 and Mac）\n"
        "         python3 check_setup.py\n"
        "     ※ venv は『課題0：venvとpip』の回で扱う。まだなら先にそこへ。 / venv is covered in the Assignment 0 lesson on venv and pip. If you haven't done that yet, go there first."
    )


def main():
    print("== 課題0の答え合わせ / Checking your answer for Assignment 0 ==\n")
    checks = [check_python_version(), check_in_venv()]

    all_ok = True
    for ok, message in checks:
        mark = "OK  " if ok else "まだ"
        print(f"[{mark}] {message}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("環境OK / Environment OK")
        print("ローカルでPythonを動かす準備が整った。課題0はここで修了。 / Your local Python setup is ready. Assignment 0 ends here.")
        print("次は課題1（projects/01-healthcheck/）へ。 / Next: Assignment 1 (projects/01-healthcheck/).")
        return 0
    else:
        print("あと少し。上の『→』の手順で直して、もう一度実行しよう。 / Almost there. Fix it with the → steps above and run again.")
        print("30分ねばっても抜けられないときは、無理に一人で戦わないこと。 / If 30 minutes of trying doesn't get you through, don't keep fighting alone.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
