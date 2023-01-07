from pathlib import Path
from requests import request
import json
from pprint import pprint
from datetime import date
from dateutil.relativedelta import relativedelta

# https://stackoverflow.com/a/46061872
TOKEN_FILE = Path(__file__).resolve().parent / ".YNAB_PERSONAL_ACCESS_TOKEN"
BUDGET_ID_FILE = Path(__file__).resolve().parent / ".YNAB_BUDGET_ID"

BASE_API_URL = "https://api.youneedabudget.com/v1/"

DEBUG = False

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


def delete_token():
    TOKEN_FILE.unlink()
    print("Deleted token.")


## BUDGETS 

def get_all_budgets_and_set_chosen():
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


## ACCOUNTS

def get_all_accounts_and_id_of_chosen():
    response = make_request_with_budget_suffix("GET", "accounts")
    if not response:
        return ""
    accounts = response.json()["data"]["accounts"]

    print("ACCOUNTS:")
    for i, account in enumerate(accounts):
        print(f"{i}: {account['name']}")

    user_input = input("Which account do you choose? Input the number (or nothing to cancel) > ").strip()
    if user_input == "":
        return ""
    i = int(user_input)

    account_name = accounts[i]["name"]
    account_id = accounts[i]["id"]
    print(f"Chose account {account_name} (ID: {account_id})")
    return account_id


def get_credit_card_openings_in_window(num_months):
    window_start = date.today() - relativedelta(months=num_months)
    print(f"ACCOUNTS OPENED IN THE LAST {num_months} MONTHS:")
    

    response = make_request_with_budget_suffix("GET", "accounts")
    if not response:
        return
    accounts = response.json()["data"]["accounts"]

    total = 0
    for account in accounts:
        if account["type"] == "creditCard":
            response = make_request_with_budget_suffix("GET", f"accounts/{account['id']}/transactions")
            if not response:
                continue
            transactions = response.json()["data"]["transactions"]

            starting_bal_transaction = next(t for t in transactions if t["payee_name"] == "Starting Balance")
            opening_date = date.fromisoformat(starting_bal_transaction["date"])

            if opening_date >= window_start:
                total += 1
                print(f"{account['name']} (Opened {opening_date})")
    
    print (f"TOTAL: {total}")


## TRANSACTIONS

def get_total_with_flag(flag):
    if flag[0] != "#":
        flag = f"#{flag}"

    response = make_request_with_budget_suffix("GET", "transactions")
    if not response:
        return

    transactions = response.json()["data"]["transactions"]

    print(f"ALL TRANSACTIONS WITH FLAG {flag}:")

    total = 0
    for t in transactions:

        if flag in (t["memo"] or "").lower():
            print(
                f"Transaction: {t['id']}\n"
                f"Account: {t['account_name']}\n"
                f"Date: {t['date']}\n"
                f"Payee: {t['payee_name']}\n"
                f"Amount: ${t['amount'] / 1000}\n"
                f"Memo: {t['memo']}\n"
            )
            total += t['amount']

        # Also search split transactions
        for st in t["subtransactions"]:
            if flag in (st["memo"] or "").lower():
                print(
                    f"Subtransaction: {st['id']}\n"
                    f"Account: {t['account_name']}\n"
                    f"Date: {t['date']}\n"
                    f"Payee: {st['payee_name'] or t['payee_name']}\n"
                    f"Amount: ${st['amount'] / 1000}\n"
                    f"Memo: {st['memo']}\n"
                )
                total += st['amount']

    print(f"TOTAL {flag}: ${total / 1000}")


def is_spend_transaction(transaction):
    t = transaction
    is_transfer = t["transfer_transaction_id"]
    is_statement_credit = t["category_name"] == "Inflow: Ready to Assign"
    return not is_transfer and not is_statement_credit


def get_spend_for_an_account():
    account_id = get_all_accounts_and_id_of_chosen()
    if not account_id:
        return

    response = make_request_with_budget_suffix("GET", f"accounts/{account_id}/transactions")
    if not response:
        return

    transactions = response.json()["data"]["transactions"]

    print("ALL TRANSACTIONS FOR THIS ACCOUNT:")
    total = 0

    for t in transactions:
        if t["subtransactions"]:
            # Search split transactions
            for st in t["subtransactions"]:
                if is_spend_transaction(st):
                    print(
                        f"Subtransaction: {st['id']}\n"
                        f"Account: {t['account_name']}\n"
                        f"Date: {t['date']}\n"
                        f"Payee: {st['payee_name'] or t['payee_name']}\n"
                        f"Amount: ${st['amount'] / 1000}\n"
                        f"Memo: {st['memo']}\n"
                    )
                    total += st['amount']
        else:
            # Check that transaction isn't a transfer and isn't statement credit
            if is_spend_transaction(t):
                print(
                    f"Transaction: {t['id']}\n"
                    f"Account: {t['account_name']}\n"
                    f"Date: {t['date']}\n"
                    f"Payee: {t['payee_name']}\n"
                    f"Amount: ${t['amount'] / 1000}\n"
                    f"Memo: {t['memo']}\n"
                )
                total += t['amount']

    print(f"TOTAL SPEND: ${-total / 1000}")


## REQUESTS

def make_request_with_budget_suffix(method, suffix):
    budget_id = get_budget_id()
    if not budget_id:
        return None
    suffix_with_budget = f"budgets/{budget_id}/{suffix}" 
    return make_request(method, suffix_with_budget)


def make_request(method, suffix):
    token = get_token()
    if not token:
        return False

    url = BASE_API_URL + suffix
    headers = {"Authorization": f"Bearer {token}"}
    response = request(method=method, url=url, headers=headers)
    
    if DEBUG:
        print("DEBUG:", method, suffix)
        print("DEBUG:", response)
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
        elif cmd == "del-token":
            if check_args_len(cmd, args, 0):
                delete_token(*args)
        elif cmd == "budget":
            if check_args_len(cmd, args, 0):
                get_all_budgets_and_set_chosen()
        elif cmd == "total":
            if check_args_len(cmd, args, 1):
                get_total_with_flag(*args)
        elif cmd == "spend":
            if check_args_len(cmd, args, 0):
                get_spend_for_an_account()
        elif cmd == "window":
            if check_args_len(cmd, args, 1):
                get_credit_card_openings_in_window(*map(int, args))
        elif cmd == "debug":
            global DEBUG
            DEBUG = not DEBUG
            print(f"Debugging mode: {DEBUG}")
        elif cmd in ["help", ""]:
            print("See README.md")
        elif cmd in ["quit", "q"]:
            print("Quitting.")
            break
        else:
            print("Command unknown.")


if __name__ == "__main__":
    main()