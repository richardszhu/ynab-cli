import sys
from pathlib import Path

# https://stackoverflow.com/a/46061872
TOKEN_FILE = Path(__file__).resolve().parent / ".YNAB_PERSONAL_ACCESS_TOKEN"


def get_token():
    assert TOKEN_FILE.exists(), f"""
        YNAB Personal Access Token not set, follow instructions to get one here:
        https://api.youneedabudget.com/
        and set it with `token <token>`.
    """
    token = TOKEN_FILE.read_text()
    return token


def set_token(token):
    TOKEN_FILE.write_text(token)


def make_request():
    token = get_token()


def check_args_len(cmd, args, expected_num_args):
    if len(args) != expected_num_args:
        print(f"Command {cmd} expects {expected_num_args} args, received {len(args)}.")
        return False
    return True


def main():
    """REPL Loop"""
    get_token()

    print("""
        YNAB CLI
        Author: @richardszhu
    """)
    while True:
        user_input = input().split()
        cmd = user_input[0].lower()
        args = user_input[1:]

        if cmd == "token":
            if check_args_len(cmd, args, 1):
                set_token(**args)
        elif cmd == "churn_total":
            if check_args_len(cmd, args, 0):
                pass
        elif cmd == "quit" or cmd == "q":
            print("Quitting")
            break
        else:
            print("Command unknown.")


if __name__ == "__main__":
    main()