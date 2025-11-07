# ynab-cli
Misc. automations for YNAB
YNAB API: https://api.ynab.com/v1

## Installation
```bash
pip install -r requirements.txt
```

## Setup (Make Executable)
```bash
chmod +x ynab_cli.py
```

## Usage
```bash
# Direct execution
./ynab_cli.py --help
./ynab_cli.py spend

# Or with python
python3.13 ynab_cli.py --help
```

### Logging Options
```bash
./ynab_cli.py budget              # Normal (errors only)
./ynab_cli.py --verbose budget    # + info messages  
./ynab_cli.py --debug budget      # + API details
```

## Commands

### Authentication
```bash
./ynab_cli.py token <personal_access_token>
```
Sets the YNAB personal access token needed to use the API.

```bash
./ynab_cli.py del-token
```
Deletes the YNAB personal access token if it was set.

### Budget Management
```bash
./ynab_cli.py budget
```
Shows all budgets and lets user set a budget to perform actions on.

### Transaction Analysis
```bash
./ynab_cli.py total <flag>
```
Finds all transactions that are marked with #flag [amount], and finds their sum. Doesn't search subtransactions.

```bash
./ynab_cli.py unflag <flag>
```
Finds all transactions that are marked with #flag [amount], and removes the flag and amount. Doesn't search subtransactions. Assumes flag/amount is at end of the memo.

```bash
./ynab_cli.py rename-flag <old_flag> <new_flag>
```
Finds all transactions with old_flag and renames it to new_flag.

```bash
./ynab_cli.py flag-category <flag>
```
Pick a category and flag all of its transactions with the given flag.

```bash
./ynab_cli.py spend
```
Finds the total spend for an account (to see progress towards a MSR).

### Credit Card Analysis
```bash
./ynab_cli.py window <num_months>
```
Finds the number of new credit cards opened in the last num_months. Based on 'Starting Balance' payee, and on accounts in YNAB (be wary of AU cards).

### Data Management
```bash
./ynab_cli.py unused-payees
```
Lists out payees that have no transactions attributed to them.

### Debugging
Use the `--debug` flag with any command to enable detailed logging:
```bash
./ynab_cli.py --debug budget
```

## Requirements
- Python 3.7+
- click
- requests
- python-dateutil

See requirements.txt
