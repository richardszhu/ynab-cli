# ynab-cli
Misc. automations for YNAB

# Commands
`token <personal_access_token>`
- Sets the YNAB personal access token needed to use the API.

`del-token`
- Deletes the YNAB personal access token if it was set.

`budget`
- Shows all budgets and lets user set a budget to perform actions on.

`total <flag>`
- Finds all transactions that are marked with #flag <amount>, and finds their sum.

`spend`
- Finds the total spend for an account (to see progress towards a MSR).

`window <num_months>`
- Finds the number of new credit cards opened in the last num_months. Based on 'Starting Balance' payee, and on accounts in YNAB (be wary of AU cards).

`unused-payees`
- Lists out payees that have no transactions attributed to them.


# Requirements
- Python 3.7+
- requests
- dateutil
