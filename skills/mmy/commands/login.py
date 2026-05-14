#!/usr/bin/env python3
"""登录 momoyu.cc 获取会话，或管理登录状态"""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from momoyu_public_fetch import (
    BASE_URL,
    API_BASE,
    CREDENTIALS_FILE,
    load_credentials,
    save_credentials,
    login_and_save_session,
    get_source_groups,
)


def cmd_status(_args):
    creds = load_credentials()
    if not creds:
        print("未登录。使用 `python commands/login.py open` 在浏览器中登录，")
        print("或使用 `python commands/login.py save --email XX --password XX` 保存账号。")
        return 0

    email = creds.get("email", "")
    token = creds.get("token", "")
    connect_sid = creds.get("connect_sid", "")
    login_time = creds.get("login_time", "")

    if not token and not connect_sid:
        print(f"账号: {email}")
        print("会话已过期，请重新登录。")
        print("  python commands/login.py open    # 浏览器登录后自动抓取")
        print("  python commands/login.py login    # 用已保存的账号自动登录")
        return 0

    groups = get_source_groups()
    print(f"账号: {email}")
    print(f"登录时间: {login_time}")
    print(f"订阅源数: {len(groups)}")
    for g in groups:
        gkey = g.get("source_key", "")
        gname = g.get("name", "")
        gid = g.get("id", "")
        print(f"  {gid:>3}  {gkey:<16}  {gname}")
    return 0


def cmd_save(args):
    creds = load_credentials() or {}
    if args.email:
        creds["email"] = args.email
    if args.password:
        creds["password"] = args.password
    if args.token:
        creds["token"] = args.token
    if args.connect_sid:
        creds["connect_sid"] = args.connect_sid
    save_credentials(creds)
    print("凭证已保存。")
    return 0


def cmd_open(_args):
    import webbrowser
    print("将在浏览器中打开 momoyu.cc 登录页面...")
    print("登录成功后，请从浏览器开发者工具 (F12 → Application → Cookies) 中复制以下值：")
    print("  1. token 的值")
    print("  2. connect.sid 的值")
    print()
    print("然后运行:")
    print('  python commands/login.py save --token "复制的token" --connect-sid "复制的sid"')
    print()
    webbrowser.open(f"{BASE_URL}/login")
    return 0


def cmd_login(_args):
    creds = load_credentials()
    if not creds:
        print("错误：未找到保存的账号。请先运行:")
        print("  python commands/login.py save --email YOUR_EMAIL --password YOUR_PASSWORD")
        return 1

    email = creds.get("email", "")
    password = creds.get("password", "")
    if not email or not password:
        print("错误：缺少 email 或 password。请先运行:")
        print("  python commands/login.py save --email YOUR_EMAIL --password YOUR_PASSWORD")
        return 1

    print(f"正在登录 {email} ...")

    try:
        session = login_and_save_session(email, password)
        if session:
            groups = get_source_groups()
            print(f"登录成功！订阅源数: {len(groups)}")
            for g in groups:
                gkey = g.get("source_key", "")
                gname = g.get("name", "")
                gid = g.get("id", "")
                print(f"  {gid:>3}  {gkey:<16}  {gname}")
            return 0
        else:
            print("登录失败：无法获取会话。可能需要手动登录。")
            print("请运行: python commands/login.py open")
            return 1
    except Exception as e:
        print(f"登录失败: {e}")
        print("请尝试手动登录: python commands/login.py open")
        return 1


def cmd_clear(_args):
    save_credentials({})
    print("登录凭证已清除，回退到匿名模式。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="管理 momoyu.cc 登录状态")
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("status", help="查看当前登录状态")
    sub.add_parser("login", help="用已保存的账号自动登录（需要验证码则失败）")
    sub.add_parser("open", help="在浏览器中打开登录页面")
    sub.add_parser("clear", help="清除登录凭证，回退匿名模式")

    save_p = sub.add_parser("save", help="保存登录凭证（不传的参数不会覆盖）")
    save_p.add_argument("--email", help="登录邮箱")
    save_p.add_argument("--password", help="登录密码")
    save_p.add_argument("--token", help="手动设置的 token cookie")
    save_p.add_argument("--connect-sid", help="手动设置的 connect.sid cookie")

    args = parser.parse_args()

    if args.action == "status" or args.action is None:
        return cmd_status(args)
    elif args.action == "save":
        return cmd_save(args)
    elif args.action == "open":
        return cmd_open(args)
    elif args.action == "login":
        return cmd_login(args)
    elif args.action == "clear":
        return cmd_clear(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())