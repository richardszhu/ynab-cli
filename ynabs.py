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
    print(repr(token))
    return token


def set_token(token):
    TOKEN_FILE.write_text(token)


def make_request():
    token = get_token()


def check_args_len(cmd, args, expected_num_args):
    assert len(args) == expected_num_args, f"""
        Command {cmd} expects {expected_num_args} args, received {len(args)}.
    """


def main(cmd, args):

    if cmd == "token":
        check_args_len(cmd, args, 1)
        set_token(**args)
    elif cmd == "churn_total":
        pass

if __name__ == "__main__":
   main("", [])
