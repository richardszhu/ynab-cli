#!/usr/bin/env python3.13
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

import click
import requests
from dateutil.relativedelta import relativedelta

# https://stackoverflow.com/a/46061872
TOKEN_FILE = Path(__file__).resolve().parent / ".YNAB_PERSONAL_ACCESS_TOKEN"
BUDGET_ID_FILE = Path(__file__).resolve().parent / ".YNAB_BUDGET_ID"

BASE_API_URL = "https://api.youneedabudget.com/v1/"
MONEY_GRANULARITY = 1000

FRACTION_WORDS: dict[str, float] = {
    "full" : 1,
    "all" : 1,
    "half" : 1 / 2,
    "third" : 1 / 3, 
    "fourth" : 1 / 4,
    "quarter": 1 / 4,
    "fifth": 1 / 5,
    "sixth": 1 / 6,
    "seventh": 1 / 7,
    "eighth": 1 / 8,
}

# Simple logging setup
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stderr
)
logger = logging.getLogger('ynab-cli')

## TOKENS

def get_token() -> str | None:
    if not TOKEN_FILE.exists():
        click.echo(
            "YNAB Personal Access Token not set.\n"
            "Follow instructions to get one here: https://api.youneedabudget.com/\n"
            "Set it with `token <token>`."
        )
        return None
    return TOKEN_FILE.read_text()


def set_token(token: str) -> None:
    TOKEN_FILE.write_text(token)
    click.echo("Set token.")


def delete_token() -> None:
    TOKEN_FILE.unlink()
    click.echo("Deleted token.")


## BUDGETS 

def get_all_budgets_and_set_chosen() -> None:
    logger.info("Fetching all budgets")
    response = make_request("GET", "/budgets")
    budgets = response.json()["data"]["budgets"]
    logger.info(f"Found {len(budgets)} budgets")
    
    click.echo("BUDGETS:")
    for i, budget in enumerate(budgets):
        click.echo(f"{i}: {budget['name']} ({budget['id']})")

    if BUDGET_ID_FILE.exists():
        click.echo(f"Current budget ID: {get_budget_id()}")

    try:
        user_input = click.prompt("Which budget do you want to set? Input the number (or nothing to cancel)", 
                                 default="", show_default=False)
        if not user_input.strip():
            return
        i = int(user_input)
    except (click.Abort, ValueError):
        return
    
    budget_name = budgets[i]["name"]
    budget_id = budgets[i]["id"]
    BUDGET_ID_FILE.write_text(budget_id)
    click.echo(f"Set budget to {budget_name} ({budget_id})")


def get_budget_id() -> str | None:
    if not BUDGET_ID_FILE.exists():
        click.echo(
            "YNAB Budget ID not set.\n"
            "Set it with `budget`."
        )
        return None
    return BUDGET_ID_FILE.read_text()


## ACCOUNTS

def get_all_accounts_and_id_of_chosen() -> str:
    response = make_request_with_budget_suffix("GET", "accounts")
    if not response:
        return ""
    accounts = response.json()["data"]["accounts"]

    click.echo("ACCOUNTS:")
    for i, account in enumerate(accounts):
        click.echo(f"{i}: {account['name']}")

    try:
        user_input = click.prompt("Which account do you choose? Input the number (or nothing to cancel)", 
                                 default="", show_default=False)
        if not user_input.strip():
            return ""
        i = int(user_input)
    except (click.Abort, ValueError):
        return ""

    account_name = accounts[i]["name"]
    account_id = accounts[i]["id"]
    click.echo(f"Chose account {account_name} (ID: {account_id})")
    return account_id


def get_credit_card_openings_in_window(num_months: int) -> None:
    window_start = date.today() - relativedelta(months=num_months)
    click.echo(f"ACCOUNTS OPENED IN THE LAST {num_months} MONTHS:")
    

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
                click.echo(f"{account['name']} (Opened {opening_date})")
    
    click.echo(f"TOTAL: {total}")


## TRANSACTIONS

def str_is_float(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False


def eval_fraction(string: str) -> float:
    """Returns 0 if str is not a fraction, else the fraction"""
    try:
        if string in FRACTION_WORDS:
            return FRACTION_WORDS[string]

        values = string.split('/')
        if len(values) == 2 and all(v.isdigit() for v in values):
            return eval(string)
        else:
            return 0
    except ValueError:
        return 0



def get_total_with_flag(flag: str) -> None:
    if flag[0] != "#":
        flag = f"#{flag}"

    logger.info(f"Searching for transactions with flag: {flag}")
    response = make_request_with_budget_suffix("GET", "transactions")
    if not response:
        return

    transactions = response.json()["data"]["transactions"]
    logger.info(f"Found {len(transactions)} total transactions")

    click.echo(f"ALL TRANSACTIONS WITH FLAG {flag}:")

    total = 0
    for t in transactions:
        memo_words = (t["memo"] or "").lower().split()

        if flag in memo_words:
            i = memo_words.index(flag)
            amount_str = memo_words[i + 1].lower() if i + 1 < len(memo_words) else ""

            if str_is_float(amount_str):
                amount = -float(memo_words[i+1]) * MONEY_GRANULARITY
            elif eval_fraction(amount_str):
                amount = t['amount'] * eval_fraction(amount_str)
            elif amount_str == "":
                amount = t['amount']
            else:
                click.echo("ERROR")

            click.echo(
                f"Transaction: {t['id']}\n"
                f"Account: {t['account_name']}\n"
                f"Date: {t['date']}\n"
                f"Payee: {t['payee_name']}\n"
                f"Amount: ${t['amount'] / MONEY_GRANULARITY}\n"
                f"Memo: {t['memo']}\n"
                f"Flagged Amount: ${amount / MONEY_GRANULARITY}\n"
            )
            total += amount

    click.echo(f"TOTAL {flag}: ${total / MONEY_GRANULARITY}")


def unflag_transactions(flag: str) -> None:
    if flag[0] != "#":
        flag = f"#{flag}"

    response = make_request_with_budget_suffix("GET", "transactions")
    if not response:
        return

    transactions = response.json()["data"]["transactions"]

    click.echo(f"UNFLAGGING ALL TRANSACTIONS WITH FLAG {flag}.")

    unflagged_transactions: list[dict[str, Any]] = []
    for t in transactions:

        memo_words = (t["memo"] or "").lower().split()
        if flag in memo_words:
            i = memo_words.index(flag)

            #remove flag and amount, update the memo
            memo = t["memo"].split()
            for _ in range(1 + int(i < len(memo) - 1)):
                memo.pop(i)
            t['memo'] = " ".join(memo)
            unflagged_transactions.append(t)

    make_request_with_budget_suffix("PATCH", f"transactions", data={"transactions": unflagged_transactions})
    click.echo(f"Unflagged {len(unflagged_transactions)} transactions.")


def flag_category_transactions(flag: str) -> None:
    response = make_request_with_budget_suffix("GET", "categories")
    cat_groups = response.json()["data"]["category_groups"]
    
    click.echo("CATEGORIES:")
    categories: list[dict[str, Any]] = []
    for cat_group in cat_groups:
        for cat in cat_group["categories"]:
            if not cat["hidden"]:
                click.echo(f"{len(categories)}: {cat['name']} ({cat['id']})")
                categories.append(cat)

    try:
        user_input = click.prompt("Which category do you want to flag? Input the number (or nothing to cancel)", 
                                 default="", show_default=False)
        if not user_input.strip():
            return
        i = int(user_input)
    except (click.Abort, ValueError):
        return
    
    category_name = categories[i]["name"]
    category_id = categories[i]["id"]
    click.echo(f"Chose category: {category_name} ({category_id})")
    
    if not click.confirm("Proceed?"):
        return

    if flag[0] != "#":
        flag = f"#{flag}"

    response = make_request_with_budget_suffix("GET", "transactions")
    if not response:
        return

    transactions = response.json()["data"]["transactions"]

    click.echo(f"FLAGGING ALL TRANSACTIONS WITH FLAG {flag}.")

    flagged_transactions: list[dict[str, Any]] = []
    for t in transactions:
        if t["category_id"] == category_id:
            # Add flag
            t['memo'] = f"{t['memo'] or ''} {flag}" 
            flagged_transactions.append(t)

    make_request_with_budget_suffix("PATCH", f"transactions", data={"transactions": flagged_transactions})
    click.echo(f"Flagged {len(flagged_transactions)} transactions.")


def is_spend_transaction(transaction: dict[str, Any]) -> bool:
    t = transaction
    is_transfer = t["transfer_transaction_id"]
    is_statement_credit = t["category_name"] == "Inflow: Ready to Assign"
    return not is_transfer and not is_statement_credit


def get_spend_for_an_account() -> None:
    account_id = get_all_accounts_and_id_of_chosen()
    if not account_id:
        return

    response = make_request_with_budget_suffix("GET", f"accounts/{account_id}/transactions")
    if not response:
        return

    transactions = response.json()["data"]["transactions"]

    click.echo("ALL TRANSACTIONS FOR THIS ACCOUNT:")
    total = 0

    for t in transactions:
        if t["subtransactions"]:
            # Search split transactions
            for st in t["subtransactions"]:
                if is_spend_transaction(st):
                    click.echo(
                        f"Subtransaction: {st['id']}\n"
                        f"Account: {t['account_name']}\n"
                        f"Date: {t['date']}\n"
                        f"Payee: {st['payee_name'] or t['payee_name']}\n"
                        f"Amount: ${st['amount'] / MONEY_GRANULARITY}\n"
                        f"Memo: {st['memo']}\n"
                    )
                    total += st['amount']
        else:
            # Check that transaction isn't a transfer and isn't statement credit
            if is_spend_transaction(t):
                click.echo(
                    f"Transaction: {t['id']}\n"
                    f"Account: {t['account_name']}\n"
                    f"Date: {t['date']}\n"
                    f"Payee: {t['payee_name']}\n"
                    f"Amount: ${t['amount'] / MONEY_GRANULARITY}\n"
                    f"Memo: {t['memo']}\n"
                )
                total += t['amount']

    click.echo(f"TOTAL SPEND: ${-total / MONEY_GRANULARITY}")


## PAYEES

def get_unused_payees() -> None:    
    response = make_request_with_budget_suffix("GET", "transactions")
    if not response:
        return

    transactions = response.json()["data"]["transactions"]
    used_payee_ids: set[str] = set()
    for t in transactions:
        used_payee_ids.add(t["payee_id"])
        for st in t["subtransactions"]:
            used_payee_ids.add(st["payee_id"])

    response = make_request_with_budget_suffix("GET", "payees")
    if not response:
        return

    click.echo("UNUSED PAYEES:")
    payees = sorted(response.json()["data"]["payees"], key=lambda p: p["name"].lower())
    for p in payees:
        if p["id"] not in used_payee_ids and p["transfer_account_id"] is None:
            click.echo(p["name"])




## REQUESTS

def make_request_with_budget_suffix(method: str, suffix: str, data: dict[str, Any] | None = None) -> requests.Response | None:
    budget_id = get_budget_id()
    if not budget_id:
        return None
    suffix_with_budget = f"budgets/{budget_id}/{suffix}" 
    return make_request(method, suffix_with_budget, data)


def make_request(method: str, suffix: str, data: dict[str, Any] | None = None) -> requests.Response | None:
    token = get_token()
    if not token:
        return None

    url = BASE_API_URL + suffix
    headers = {"Authorization": f"Bearer {token}"}
    
    logger.debug(f"Making {method} request to {suffix}")
    logger.debug(f"URL: {url}")
    if data:
        logger.debug(f"Request data: {json.dumps(data, indent=2)}")
    
    response = requests.request(method=method, url=url, headers=headers, json=data)
    
    logger.debug(f"Response status: {response.status_code}")
    logger.debug(f"Response headers: {dict(response.headers)}")
    
    if not response.ok:
        logger.error(f"Request failed: {response.status_code} - {response.text}")
    else:
        logger.debug(f"Request successful")

    return response
    

## CLI COMMANDS

@click.group()
@click.version_option(version="1.0.0")
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx: click.Context, debug: bool, verbose: bool) -> None:
    """YNAB CLI - Misc. automations for YNAB"""
    # Set logging level based on options
    if debug:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('requests').setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)


@cli.command()
@click.argument('token')
def token(token: str) -> None:
    """Set the YNAB personal access token needed to use the API."""
    set_token(token)


@cli.command()
def del_token() -> None:
    """Delete the YNAB personal access token if it was set."""
    delete_token()


@cli.command()
def budget() -> None:
    """Show all budgets and let user set a budget to perform actions on."""
    get_all_budgets_and_set_chosen()


@cli.command()
@click.argument('flag')
def total(flag: str) -> None:
    """Find all transactions that are marked with #flag [amount], and find their sum."""
    get_total_with_flag(flag)


@cli.command()
@click.argument('flag')
def unflag(flag: str) -> None:
    """Find all transactions that are marked with #flag [amount], and remove the flag and amount."""
    unflag_transactions(flag)


@cli.command()
def spend() -> None:
    """Find the total spend for an account (to see progress towards a MSR)."""
    get_spend_for_an_account()


@cli.command()
@click.argument('num_months', type=int)
def window(num_months: int) -> None:
    """Find the number of new credit cards opened in the last num_months."""
    get_credit_card_openings_in_window(num_months)


@cli.command()
def unused_payees() -> None:
    """List out payees that have no transactions attributed to them."""
    get_unused_payees()


@cli.command()
@click.argument('flag')
def flag_category(flag: str) -> None:
    """Pick a category and flag all of its transactions with the given flag."""
    flag_category_transactions(flag)


if __name__ == "__main__":
    cli()
