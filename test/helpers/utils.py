from typing import List

from helpers.const import w3, DEFAULT_PASSWORD, ETHER_NAME, COIN_DENOMINATION
# participate function is used to participate on Plasma.
# address: the user's address who wants to participate.
# nr_of_tokens: number of tokens that will be created.
# amount : the denomination of each token.
from helpers import parity, erc20


def participate(deployed_contracts, address, nr_of_tokens, amount):
    for i in range(0, nr_of_tokens):
        w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
        gas = deployed_contracts.plasma_instance.functions.participate(amount).estimateGas({'from': address})
        p = deployed_contracts.plasma_instance.functions.participate(amount).transact({'from': address, 'gas': gas})
        w3.eth.waitForTransactionReceipt(p)

    coins = deployed_contracts.erc721_instance.functions.getOwnedTokens(address).call()
    assert len(coins) == nr_of_tokens

    return coins


def setup_accounts(count: int = 8) -> List:
    """Create some accounts in the parity node."""
    accounts = parity.generate_accounts(count)
    # parity.sendTransaction() is the function which sends sends some amount of ether to an account.
    for i in accounts:
        parity.send_transaction(i.address, w3.eth.accounts[0])
    # defaultAccount is the default account | if there is no ({'from'}) provided the account[0] will be taken as default caller
    w3.eth.defaultAccount = w3.eth.accounts[0]
    return accounts


def participate_account(account_address, deployed_contracts) -> List:
    """
    Make the given account participate.

    :param account_address: address to the account to participate
    :param deployed_contracts: instances of the deployed contracts
    :return: list of coins
    """
    # getting deployed plasma address
    plasma_address = deployed_contracts.plasma_instance.address
    # transfering erc20 tokens to account_address so she can participate into plasma contract.
    erc20.transfer(account_address, w3.toWei(5000000, ETHER_NAME), deployed_contracts.erc20_instance)
    # account_address approving the tokens to plasma_address so when participate function is called the
    # tokens will be transfered from her address to plasma_address
    erc20.approve(plasma_address, account_address, w3.toWei(5000000, ETHER_NAME), deployed_contracts.erc20_instance)
    # participating to plasma 10 times with denomination 5000 for each token
    coins = participate(deployed_contracts, account_address, 10, COIN_DENOMINATION)
    return coins