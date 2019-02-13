import random
from typing import Dict, List, Tuple

import requests
import rlp
from eth_account import Account
from hexbytes import HexBytes
from requests import Response

from helpers.const import (COIN_DENOMINATION, DEFAULT_FROM,
                           DEFAULT_PARITY_NODE_URL, DEFAULT_PASSWORD,
                           ETHER_ALLOC, ETHER_NAME, TOKEN_ALLOC)
from helpers.const import W3 as w3
from helpers.sparse_merkle_tree import SparseMerkleTree


def participate(deployed_contracts, address, nr_of_tokens, denomination):
    """
    Make the given address participate on plasma with the given amount of tokens.

    :param deployed_contracts: instances of the deployed contracts
    :param address: address of the user who wants to participate
    :param nr_of_tokens: number of tokens to be created
    :param denomination: denomination of each token
    :return: list of coins

    participate function is used to participate on Plasma.
    address: the user's address who wants to participate.
    nr_of_tokens: number of tokens that will be created.
    amount : the denomination of each token.
    """
    args = (denomination, )
    kwargs = {'from': address}
    fn_participate = deployed_contracts.plasma_instance.functions.participate(*args)
    gas = fn_participate.estimateGas(kwargs)
    kwargs['gas'] = gas

    for i in range(nr_of_tokens):
        w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
        tx_hash = fn_participate.transact(kwargs)
        assert w3.eth.waitForTransactionReceipt(tx_hash).status

    tokens = deployed_contracts.erc721_instance.functions.getOwnedTokens(address).call()
    assert len(tokens) == nr_of_tokens

    return tokens


def setup_accounts(count: int = 8) -> List:
    """
    Create accounts in a parity node.

    :param count: amount of accounts to create in the node
    :return: list of accounts
    """
    accounts = generate_parity_accounts(count)
    # parity.sendTransaction() is the function which sends sends some amount of ether to an account.
    for i in accounts:
        send_parity_transaction(i.address, w3.eth.accounts[0])

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
    plasma_address = deployed_contracts.plasma_instance.address

    # transfering erc20 tokens to account fro plasma participation
    erc20_transfer(account_address, w3.toWei(ETHER_ALLOC, ETHER_NAME), deployed_contracts.erc20_instance)

    # approve tokens to plasma address so when participate function is called the
    # tokens will be transferred to the plasma address
    erc20_approve(plasma_address, account_address, w3.toWei(ETHER_ALLOC, ETHER_NAME), deployed_contracts.erc20_instance)

    # allocate 10 tokens to plasma
    tokens = participate(deployed_contracts, account_address, TOKEN_ALLOC, COIN_DENOMINATION)
    return tokens


def generate_dummy_tx() -> List:
    """
    Generate dummy transactions to be included in a sparse merkle tree.

    Used so the sparse merkle tree doesn't have only one transaction.
    :return: List with id and transaction hash.
    """
    uid = random.getrandbits(64)
    prevBlock = 5
    deno = 20
    owner = bytes.fromhex("30e3862ceb1a9b8b227bd2a53948c2ba2f1aa54a")

    tx = rlp.encode([uid, prevBlock, deno, owner])

    tx_hash = HexBytes(
        w3.soliditySha3(['bytes'], [tx])  # dummy hash(leaf)
    )

    tx = [uid, tx_hash]

    return tx


def generate_tx(token_id, prev_block, denomination, addr_to, addr_from) -> Dict:
    """
    Generate tx that will be used off-chain to initiate transactions which will also be used to exit or challenge a coin

    :param token_id: id of the token we want to generate a tx for
    :param prev_block: prevBlock of the token.
    :param denomination: token denomination
    :param addr_to: address were the token is being sent
    :param addr_from: address that initiates the transaction
    :return: Dictionary with signature and rlp encoded transaction.
    """
    tx = rlp.encode([token_id, prev_block, denomination, bytes.fromhex(addr_to[2:])])

    if prev_block == 0:
        # This is a deposit transaction.
        # the kecca256 of token id since this is a deposit.
        tx_hash = w3.soliditySha3(['uint64'], [token_id])

        w3.personal.unlockAccount(addr_from, DEFAULT_PASSWORD)
        signature = w3.eth.sign(addr_from, data=tx_hash)
        tx = {
            "signature": signature,
            "tx": tx
        }
        return tx

    else:
        # Else the token was transferred before off-chain.

        # the hash of the tx encoded bytes.
        tx_hash = w3.soliditySha3(['bytes'], [tx])

        w3.personal.unlockAccount(addr_from, DEFAULT_PASSWORD)
        signature = w3.eth.sign(addr_from, data=tx_hash)
        tx = {
            "signature": signature,
            "tx": tx,
            "tx_hash": tx_hash
        }
        return tx


def generate_block(plasma_instance, token_id, tx_hash, block_number) -> Tuple:
    """
    Generate blocks to be included in PlasmaContract on-chain

    :param plasma_instance: instance of the deployed plasma contract
    :param token_id: id of the token which will be the key on the sparse merkle tree
    :param tx_hash: hash of the transaction that will be the value of the token on the sparse merkle tree
    :param block_number: block number to be submitted to the plasma contract
    :return: Tuple with proof of token id and its block number
    """
    dummy_txs = []
    hashes = {token_id: tx_hash}

    # filling dummy_txs list with dummy transactions
    for i in range(0, 20):
        dummy_txs.append(generate_dummy_tx())
    for i in dummy_txs:
        hashes.update({i[0]: i[1]})

    # create SMT, get root and proof
    tree = SparseMerkleTree(64, leaves=hashes)
    root = tree.root
    proof = tree.create_merkle_proof(token_id)

    # submitting the block to the PlasmaContract on-chain
    args = (block_number, root)
    kwargs = {'from': w3.eth.accounts[0]}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_submit = plasma_instance.functions.submitBlock(*args)
    gas = fn_submit.estimateGas(kwargs)
    kwargs['gas'] = gas
    tx_hash = fn_submit.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status, 'Block submission failure {}'.format(tx_hash)

    return proof, block_number


def generate_parity_accounts(amount: int, password: str = DEFAULT_PASSWORD) -> List:
    """
    Generate the given amount of accounts in a parity dev node.

    :param amount: amount of accounts to create
    :param password: account password
    :return: list of created accounts
    """
    accounts = []
    for i in range(0, amount):
        acct = Account.create(password)
        if w3.version.node.startswith('Parity'):
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
            requests.post(DEFAULT_PARITY_NODE_URL, json=payload)
            accounts.append(acct)
        else:
            pub_key = w3.personal.importRawKey(acct.privateKey, password)
            assert pub_key == acct.address

    return accounts


def send_parity_transaction(address: str, owner: str) -> Response:
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

    res = requests.post(DEFAULT_PARITY_NODE_URL, json=payload)
    return res


def delete_parity_account(account: str, password: str = DEFAULT_PASSWORD) -> Response:
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
    return requests.post(DEFAULT_PARITY_NODE_URL, json=payload)


def erc20_transfer(addr_to, amount, erc20_instance):
    """
    Handle ERC20 transfers to a user

    :param addr_to: address where the tokens are being transferred to
    :param amount: amount to transfer
    :param erc20_instance: instance of the ERC20 contract deployed to the node
    :return: balance of the receiver address
    """
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    gas = erc20_instance.functions.transfer(addr_to, amount).estimateGas(DEFAULT_FROM)

    # calling transfer function on erc20 contract.
    transfer1 = erc20_instance.functions.transfer(
        addr_to, amount).transact({'from': w3.eth.accounts[0], 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(transfer1).status == 1

    # checking if amount transferred is correct
    balance = erc20_instance.functions.balanceOf(addr_to).call()
    assert balance == amount

    return balance


def erc20_approve(addr_to_approve, approving_addr, amount, erc20_instance):
    """
    Handle approval on the ERC20 contract.

    :param addr_to_approve: address to be approved
    :param approving_addr: address of the approver (owner of the ERC20 tokens)
    :param amount: amount of tokens to approve
    :param erc20_instance: instance of the deployed ERC20 contract
    :return: allowance
    """
    # approve function to handle approves on erc20 contract
    # approve_address : the address we want to approve
    # address : approver(owner of erc20 tokens)
    # amount: amount to approve
    w3.personal.unlockAccount(approving_addr, DEFAULT_PASSWORD)
    gas = erc20_instance.functions.approve(addr_to_approve, amount).estimateGas({'from': approving_addr})

    # calling approve function on erc20 contract.
    approve1 = erc20_instance.functions.approve(
        addr_to_approve, amount).transact({'from': approving_addr, 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(approve1).status == 1

    # checking if amount was approved correctly.
    allowance = erc20_instance.functions.allowance(approving_addr, addr_to_approve).call()
    assert allowance == amount

    # returning amount approved
    return allowance
