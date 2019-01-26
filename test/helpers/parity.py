from typing import List

import requests
from eth_account import Account
from requests import Response

from fixtures.const import DEFAULT_PASSWORD, PARITY_NODE_URL


def generate_accounts(amount: int, password: str = DEFAULT_PASSWORD) -> List:
    """
    Generate the given amount of accounts in a parity dev node.
    :param amount: amount of accounts to create
    :param password: account password
    :return: list of created accounts
    """
    accounts = []
    for i in range(0, amount):
        acct = Account.create(password)

        # create a new parity account from a private key.
        payload = {
            "method": "parity_newAccountFromSecret",
            "params": [
                acct.privateKey.hex(),
                password,
            ],
            "id": i + 1,
            "jsonrpc": "2.0"
        }
        requests.post(PARITY_NODE_URL, json=payload)
        accounts.append(acct)

    return accounts


def send_transaction(address: str, owner: str) -> Response:
    """
    Send a transaction from owner to the given address.
    :param address: user address
    :param owner: coinbase account
    :return: request response
    """
    payload = {
        "method": "personal_sendTransaction",
        "params": [
            {
                "from": owner,
                "to": address,
                "data": "0x41cd5add4fd13aedd64521e363ea279923575ff39718065d38bd46f0e6632e8e",
                "value": "0x4140C78940F6A24FDFFC78873D4490D2100000000000000"
            },
            ""
        ],
        "id": 1,
        "jsonrpc": "2.0"
    }
    res = requests.post(PARITY_NODE_URL, json=payload)
    return res


def delete_account(account: str, password: str = DEFAULT_PASSWORD) -> Response:
    """
    Delete a parity account.
    :param account: address of the account to delete
    :param password: account password
    :return: request response
    """
    payload = {
        "method": "parity_killAccount",
        "params": [
            account,
            password,
        ],
        "id": 2,
        "jsonrpc": "2.0"
    }
    return requests.post(PARITY_NODE_URL, json=payload)
