from pathlib import Path
from requests import request
import json

# https://stackoverflow.com/a/46061872
TOKEN_FILE = Path(__file__).resolve().parent / ".YNAB_PERSONAL_ACCESS_TOKEN"
BUDGET_ID_FILE = Path(__file__).resolve().parent / ".YNAB_BUDGET_ID"

BASE_API_URL = "https://api.youneedabudget.com/v1/"

CHURN_FLAG = "#churn"

## TOKENS

def get_token():
    if not TOKEN_FILE.exists():
        print(
            "YNAB Personal Access Token not set.\n"
            "Follow instructions to get one here: https://api.youneedabudget.com/\n"
            "Set it with `token <token>`."
        )
        return None
    return TOKEN_FILE.read_text()


def set_token(token):
    TOKEN_FILE.write_text(token)
    print("Set token.")


## BUDGETS 

def get_all_budgets_and_set():
    response = make_request("GET", "/budgets")
    budgets = response.json()["data"]["budgets"]
    
    print("BUDGETS:")
    for i, budget in enumerate(budgets):
        print(f"{i}: {budget['name']}")

    user_input = input("Which budget do you want to set? Input the number (or nothing to cancel) > ").strip()
    if user_input == "":
        return
    i = int(user_input)
    
    budget_name = budgets[i]["name"]
    budget_id = budgets[i]["id"]
    BUDGET_ID_FILE.write_text(budget_id)
    print(f"Set budget to {budget_name} (ID: {budget_id})")


def get_budget_id():
    if not BUDGET_ID_FILE.exists():
        print(
            "YNAB Budget ID not set.\n"
            "Set it with `budget`."
        )
        return None
    return BUDGET_ID_FILE.read_text()


## TRANSACTIONS

def get_total_churn():
    response = make_request_with_budget_suffix("GET", "transactions")
    all_transactions = response.json()["data"]["transactions"]

    print("ALL CHURN TRANSACTIONS:")

    total = 0
    for t in all_transactions:

        if t["memo"] and CHURN_FLAG in t["memo"]:
            print(
                f"Transaction: {t['id']}\n"
                f"Account: {t['account_name']}\n"
                f"Payee: {t['payee_name']}\n"
                f"Date: {t['date']}\n"
                f"Amount: ${t['amount'] / 1000}\n"
                f"Memo: {t['memo']}\n"
            )
            total += t['amount']

        # Also search split transactions
        for st in t["subtransactions"]:
            if st["memo"] and CHURN_FLAG in st["memo"]:
                print(
                    f"Subtransaction: {st['id']}\n"
                    f"Account: {t['account_name']}\n"
                    f"Payee: {st['payee_name'] or t['payee_name']}\n"
                    f"Date: {t['date']}\n"
                    f"Amount: ${st['amount'] / 1000}\n"
                    f"Memo: {st['memo']}\n"
                )
                total += st['amount']

    print(f"TOTAL CHURN: ${total / 1000}")


## REQUESTS

def make_request_with_budget_suffix(method, suffix):
    budget_id = get_budget_id()
    suffix_with_budget = f"budgets/{budget_id}/{suffix}" 
    return make_request(method, suffix_with_budget)


def make_request(method, suffix):
    token = get_token()
    if not token:
        return False

    url = BASE_API_URL + suffix
    headers = {"Authorization": f"Bearer {token}"}
    response = request(method=method, url=url, headers=headers)
    return response
    

## REPL

def check_args_len(cmd, args, expected_num_args):
    correct_len = len(args) == expected_num_args
    if not correct_len:
        print(f"Command {cmd} expects {expected_num_args} args, received {len(args)}.")
    return correct_len


def main():
    print(
        "=== YNAB CLI ===\n"
        "Author: @richardszhu"
    )

    while True:
        user_input = input("> ").split()
        cmd = user_input[0].lower() if user_input else ""
        args = user_input[1:]

        if cmd == "token":
            if check_args_len(cmd, args, 1):
                set_token(*args)
        elif cmd == "budget":
            if check_args_len(cmd, args, 0):
                get_all_budgets_and_set()
        elif cmd == "total-churn":
            if check_args_len(cmd, args, 0):
                get_total_churn()
        elif cmd in ["help", ""]:
            print("See README.md")
        elif cmd in ["quit", "q"]:
            print("Quitting.")
            break
        else:
            print("Command unknown.")


if __name__ == "__main__":
    main()