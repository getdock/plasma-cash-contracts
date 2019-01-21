from eth_account import Account
from helpers.web3Provider import w3
import requests

pwd = 'passw0rd'

accts = []

# generateAccounts generates accounts on parity.
# nrOfAccounts: number of accounts that will be generated
def generateAccounts(nrOfAccounts):

    for i in range(0, nrOfAccounts):
        # method create from eth_account module is used to generate account.
        acct = Account.create(pwd)

        # creates a new parity account from a private key.
        d = {"method": "parity_newAccountFromSecret", "params": [
            acct.privateKey.hex(), pwd], "id": i + 1, "jsonrpc": "2.0"}
        res = requests.post("http://127.0.0.1:8545", json=d)
        accts.append(acct)

    return accts

#  w3.eth.acccounts[0] is coinbase account.
owner = w3.eth.accounts[0]

# sendTransaction sents transaction(ether) from coinbase account to user.
# address: the user's address.
def sendTransaction(address):

    # parity method personal_sendTransaction.
    d = {"method": "personal_sendTransaction",
         "params": [{"from": owner,
                     "to": address,
                     "data": "0x41cd5add4fd13aedd64521e363ea279923575ff39718065d38bd46f0e6632e8e",
                     "value": "0x4140C78940F6A24FDFFC78873D4490D2100000000000000"},
                    ""],
         "id": 1,
         "jsonrpc": "2.0"}
    res = requests.post("http://127.0.0.1:8545", json=d)


# deleteAccount deletes parity account.
# account: address of the account that will be deleted.
def deleteAccount(account):

    #parity method parity_killAccount.
    d = {
        "method": "parity_killAccount",
        "params": [
            account,
            pwd],
        "id": 2,
        "jsonrpc": "2.0"}
    res = requests.post("http://127.0.0.1:8545", json=d)
