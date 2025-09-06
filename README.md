# ynab-cli
Misc. automations for YNAB

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python3 ynab-cli.py --help
```

YNAB API: https://api.ynab.com/v1

## Commands

### Authentication
```bash
python3 ynab-cli.py token <personal_access_token>
```
Sets the YNAB personal access token needed to use the API.

```bash
python3 ynab-cli.py del-token
```
Deletes the YNAB personal access token if it was set.

### Budget Management
```bash
python3 ynab-cli.py budget
```
Shows all budgets and lets user set a budget to perform actions on.

### Transaction Analysis
```bash
python3 ynab-cli.py total <flag>
```
Finds all transactions that are marked with #flag [amount], and finds their sum. Doesn't search subtransactions.

```bash
python3 ynab-cli.py unflag <flag>
```
Finds all transactions that are marked with #flag [amount], and removes the flag and amount. Doesn't search subtransactions. Assumes flag/amount is at end of the memo.

```bash
python3 ynab-cli.py flag-category <flag>
```
Pick a category and flag all of its transactions with the given flag.

```bash
python3 ynab-cli.py spend
```
Finds the total spend for an account (to see progress towards a MSR).

### Credit Card Analysis
```bash
python3 ynab-cli.py window <num_months>
```
Finds the number of new credit cards opened in the last num_months. Based on 'Starting Balance' payee, and on accounts in YNAB (be wary of AU cards).

### Data Management
```bash
python3 ynab-cli.py unused-payees
```
Lists out payees that have no transactions attributed to them.

### Debugging
```bash
python3 ynab-cli.py debug
```
Toggle debugging mode on/off.

## Requirements
- Python 3.7+
- click
- requests
- python-dateutil
