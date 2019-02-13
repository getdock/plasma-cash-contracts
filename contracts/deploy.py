#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    Sample deployment scripts for Dock Plasma Cash Contracts

    Note: The quick_deploy script assumes a running docker parity dev client node but
          can be easily extended to either a geth dev client node or one of the testnets.
'''
import json
import os
from secrets import token_hex
from typing import Dict, List, NewType, Tuple

import requests
import web3
from eth_account import Account

WEB3 = NewType('WEB3', web3.main.Web3)


# def deploy_contracts(w3: WEB3, master_acct: Tuple, p_erc20: str, p_plasma: str, p_erc721: str, p_checks: str) -> Dict:
def deploy_contracts(w3: WEB3, master_acct: Tuple, ctr_paths: Dict, challenge_params: Dict) -> Dict:
    '''
        deploy erc20, plasma, doChecks, er721, and erc721 proxy contracts
        master_acct is the account needed to subseqeuently manage the contracts and a tuple of
        (eth_account, password) s.t. acct[0].address, acct[0].privateKey, acct[1] is password
        ctr_paths: dict of paths to respective json files with at least [abi, bin]
        challenge_params: bonding amount (in Wei), maturity period, challenge window

        return dict of transaction receipts, gas estimates
    '''
    with open(ctr_paths['PlasmaContract']) as fd:
        c_plasma = json.load(fd)

    with open(ctr_paths['ERC20']) as fd:
        c_erc20 = json.load(fd)

    with open(ctr_paths['ERC721']) as fd:
        c_erc721 = json.load(fd)

    with open(ctr_paths['DoChecks']) as fd:
        c_dochecks = json.load(fd)

    erc20_instance = w3.eth.contract(abi=c_erc20['abi'], bytecode=c_erc20['bin'])
    dochecks_instance = w3.eth.contract(abi=c_dochecks['abi'], bytecode=c_dochecks['bin'])
    plasma_instance = w3.eth.contract(abi=c_plasma['abi'], bytecode=c_plasma['bin'])
    erc721_instance = w3.eth.contract(abi=c_erc721['abi'], bytecode=c_erc721['bin'])

    # load ERC20 (DOCK)
    kwargs = {'from': master_acct[0].address}

    w3.personal.unlockAccount(master_acct[0].address, master_acct[1])
    fn_erc20 = erc20_instance.constructor()
    erc20_contract_gas = fn_erc20.estimateGas(kwargs)
    kwargs['gas'] = erc20_contract_gas
    tx_hash_erc20 = fn_erc20.transact(kwargs)
    tx_receipt_erc20 = w3.eth.waitForTransactionReceipt(tx_hash_erc20)
    assert tx_receipt_erc20.status, 'ERC20 instance construction failed.'

    # load DoChecks
    kwargs = {'from': master_acct[0].address}
    w3.personal.unlockAccount(master_acct[0].address, master_acct[1])
    fn_dochecks = dochecks_instance.constructor()
    dochecks_contract_gas = fn_dochecks.estimateGas(kwargs)
    kwargs['gas'] = dochecks_contract_gas
    tx_hash_dochecks = fn_dochecks.transact(kwargs)
    tx_receipt_dochecks = w3.eth.waitForTransactionReceipt(tx_hash_dochecks)
    assert tx_receipt_dochecks.status, 'DoChecks instance construction failed.'

    kwargs = {'from': master_acct[0].address}
    w3.personal.unlockAccount(master_acct[0].address, master_acct[1])
    fn_erc721 = erc721_instance.constructor()
    erc721_contract_gas = fn_erc721.estimateGas(kwargs)
    kwargs['gas'] = erc721_contract_gas
    tx_hash_erc721 = fn_erc721.transact(kwargs)
    tx_receipt_erc721 = w3.eth.waitForTransactionReceipt(tx_hash_erc721)
    assert tx_receipt_erc721.status, 'ERC721 instance construction failed.'

    # load Plasma Contract
    kwargs = {'from': master_acct[0].address}
    w3.personal.unlockAccount(master_acct[0].address, master_acct[1])
    fn_plasma = plasma_instance.constructor()
    plasma_contract_gas = fn_plasma.estimateGas(kwargs)
    kwargs['gas'] = plasma_contract_gas
    tx_hash_plasma = fn_plasma.transact(kwargs)
    tx_receipt_plasma = w3.eth.waitForTransactionReceipt(tx_hash_plasma)
    assert tx_receipt_plasma.status, 'PlasmaContract instance construction failed.'

    # load address specific contract instances
    plasma_addr = tx_receipt_plasma.contractAddress
    plasma_instance = w3.eth.contract(address=plasma_addr, abi=c_plasma['abi'],)

    erc20_addr = tx_receipt_erc20.contractAddress
    erc20_instance = w3.eth.contract(address=erc20_addr, abi=c_erc20['abi'],)

    erc721_addr = tx_receipt_erc721.contractAddress
    erc721_instance = w3.eth.contract(address=erc721_addr, abi=c_erc721['abi'],)

    dochecks_addr = tx_receipt_dochecks.contractAddress
    dochecks_instance = w3.eth.contract(address=dochecks_addr, abi=c_dochecks['abi'],)

    # load PlasmaAddress
    args = (plasma_addr, )
    kwargs = {'from': master_acct[0].address}

    w3.personal.unlockAccount(master_acct[0].address, master_acct[1])
    plasma_addr_instance = erc721_instance.functions.loadPlasmaAddress(*args)
    plasma_addr_gas = plasma_addr_instance.estimateGas(kwargs)
    kwargs['gas'] = plasma_addr_gas
    tx_hash_addr_instance = plasma_addr_instance.transact(kwargs)
    tx_receipt_load_addr = w3.eth.waitForTransactionReceipt(tx_hash_addr_instance)
    assert tx_receipt_load_addr.status, 'Failed to load PlasmaAddress failed.'

    args = (challenge_params['bond-in-wei'],
            challenge_params['maturity-period'],
            challenge_params['challenge-window']
            )

    kwargs = {'from': master_acct[0].address}

    w3.personal.unlockAccount(master_acct[0].address, master_acct[1])
    fn_bonding = plasma_instance.functions.setMaturityAndBond(*args)
    bonding_gas = fn_bonding.estimateGas(kwargs)
    kwargs['gas'] = bonding_gas
    tx_hash_bonding = fn_bonding.transact(kwargs)
    tx_receipt_bonding = w3.eth.waitForTransactionReceipt(tx_hash_bonding)
    assert tx_receipt_bonding.status, 'Failed to set bonding parameters.'
    assert plasma_instance.functions.bond_amount().call() == args[0], f'Bonding failure'

    # set Addreses
    args = (erc20_addr, erc721_addr, dochecks_addr)
    kwargs = {'from': master_acct[0].address}

    w3.personal.unlockAccount(master_acct[0].address, master_acct[1])
    fn_set_addr = plasma_instance.functions.setAddresses(*args)
    set_addr_gas = fn_set_addr.estimateGas(kwargs)
    kwargs['gas'] = set_addr_gas
    tx_hash_set_addr = fn_set_addr.transact(kwargs)
    tx_receipt_set_addr = w3.eth.waitForTransactionReceipt(tx_hash_set_addr)
    assert tx_receipt_set_addr.status, 'Failed to set contract addresses for PlasmaContract.'

    receipts = {}
    receipts['erc20_contract'] = {'gas-estimate': erc20_contract_gas, 'tx-receipt': tx_receipt_erc20}
    receipts['erc721_contract'] = {'gas-estimate': erc721_contract_gas, 'tx-receipt': tx_receipt_erc721}
    receipts['plasma_contract'] = {'gas-estimate': plasma_contract_gas, 'tx-receipt': tx_receipt_plasma}
    receipts['dochecks_contract'] = {'gas-estimate': dochecks_contract_gas, 'tx-receipt': tx_receipt_dochecks}
    receipts['erc_to_plasma'] = {'gas-estimate': plasma_addr_gas, 'tx-receipt': tx_receipt_load_addr}
    receipts['set_addresses'] = {'gas-estimate': set_addr_gas, 'tx-receipt': tx_receipt_set_addr}
    receipts['bonding_value'] = {'gas-estimate': bonding_gas, 'tx-receipt': tx_receipt_bonding}

    return receipts


def reset_parity_dev_node(container_name) -> str:
    '''
        TODO: add running tests and swtich to pydocker
    '''
    reset_str = """docker stop dock-mvp;
                   docker rm dock-mvp;
                   rm -r ~/.parity;
                   mkdir ~/.parity;
                   chmod -R 777 ~/.parity;
                   docker run -d -ti -v ~/.parity/plasma-mvp/:/home/parity/.local/share/io.parity.ethereum/ \
                   -p 8545:8545 --name {} parity/parity:v2.2.5 --chain dev --jsonrpc-interface all \
                   --jsonrpc-apis all --jsonrpc-cors all --jsonrpc-hosts all \
                """.format(container_name)
    container_id = os.system(reset_str)
    return container_id


def create_eth_accounts(n_accts: int) ->List[Tuple[Account, str]]:
    '''
        create accounts offline
    '''
    accounts = []
    for _ in range(n_accts):
        pwd = token_hex(16)
        accounts.append((Account.create(pwd), pwd))
    return accounts


def account_to_eth(w3: WEB3, node_uri: str, private_key: str, password: str, node_type: str, counter: int) -> bool:
    '''
        importRawKey doesn't work in parity
    '''
    if node_type != 'parity':
        w3.personal.importRawKey(private_key, password)
    else:
        _d = {"method": "parity_newAccountFromSecret",
              "params": [private_key.hex(), password], "id": counter, "jsonrpc": "2.0"}
        res = requests.post(node_uri, json=_d)
        res.raise_for_status()

    return True


def fund_master_account(w3: WEB3, master_acct: Tuple, ether_amount: int) -> Dict:
    '''
        Needed to chnage once we get out of dev mode
        extend signature to include: funding account, funcing accout password or unlock before call
    '''
    w3.personal.unlockAccount(w3.eth.coinbase, '')
    kwargs = {'to': master_acct[0].address,
              'from': w3.eth.coinbase,
              'value': w3.toWei(ether_amount, 'ether')}
    receipt = w3.eth.sendTransaction(kwargs)
    return receipt


def quick_deploy(node_uri: str = 'http://127.0.0.1:8545') -> Tuple:
    '''
        Quick deployment of contracts to a parity dev node for subsequent hacking and testing.
        If you want to use that deploymeny, make sure the parameter values fit your context and
        you probably want to peresist the account and receipts.
        Next step is to add some partcipants.

        NOTE: We are employing the DOCK ERC20 proxy contract. For testnet and beyond, you want to replace
        the abi, bin and address from the deployed DOCK ERC20 contract (e.g., see etherscan for the
        respective testnet).
    '''
    from web3 import Web3
    # from utilities.setup_helpers import create_eth_accounts, account_to_eth, fund_master_account

    BOND_AMOUNT = 0.1
    MATURITY_PERIOD = 3
    CHALLENGE_WINDOW = 1

    assert CHALLENGE_WINDOW < MATURITY_PERIOD, 'Challenge window needs to be less than the maturity period'

    CTR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'json'))
    assert os.path.exists(CTR_DIR), f'Missing dir for json abi, bin files: {CTR_DIR}'

    w3 = Web3(Web3.HTTPProvider(node_uri))
    assert w3.isConnected(), 'No Web3 connection'

    # this is the account that runs the contracts
    master_acct = create_eth_accounts(1)[0]
    msg = 'Failed to import account {} to eth client'.format(master_acct[0].address)
    acct_imported = account_to_eth(w3, node_uri, master_acct[0].privateKey, master_acct[1], 'parity', 0)
    assert acct_imported, msg

    # Don't do this on anything but a dev node and certainly not Infura
    accts = w3.personal.listAccounts  # pylint: disable=E1101
    assert master_acct[0].address in accts, f'New master account {master_acct[0].address} not found on eth client.'

    # let's fund the master account just for kicks and future usability when gas price comes into play
    # NOTE this only works for dev nodes with default coinbase
    ether_amount = 1_000_000_000_000
    master_funding_receipt = fund_master_account(w3, master_acct, ether_amount)
    master_acct_balance = w3.fromWei(w3.eth.getBalance(master_acct[0].address), 'ether')  # pylint: disable=E1101
    msg = f'master account funding discrepancy: {ether_amount}, {master_acct_balance}.'
    assert ether_amount == master_acct_balance, msg

    # get the json file paths
    ctr_paths = {'PlasmaContract': os.path.join(CTR_DIR, 'PlasmaContract.json'),
                 'DoChecks': os.path.join(CTR_DIR, 'DoChecks.json'),
                 'ERC20': os.path.join(CTR_DIR, 'ERC20DockToken.json'),
                 'ERC721': os.path.join(CTR_DIR, 'DockPlasmaToken.json')
                 }

    # and set the challenge params
    challenge_params = {'bond-in-wei': w3.toWei(BOND_AMOUNT, 'ether'),
                        'maturity-period': MATURITY_PERIOD,
                        'challenge-window': CHALLENGE_WINDOW
                        }

    deploy_receipts = deploy_contracts(w3, master_acct, ctr_paths, challenge_params)

    total_gas = (sum([v['gas-estimate'] for v in deploy_receipts.values()]))
    msg = f'Expected total deployment gas to be between 9_786_xxx (for opt) and 14_000_xxx but got {total_gas}.'
    assert 9_786_00 < total_gas < 14_001_000, msg

    return master_acct, deploy_receipts, master_funding_receipt


if __name__ == '__main__':
    '''
        if you want a fresh docker instance and dev node:
        see reset_parity_dev_node()
    '''
    master_acct, receipts, funding_receipt = quick_deploy()

    print('quick deploy: ')
    print('accounts: ', master_acct[0].address, ' , ', master_acct[0].privateKey, master_acct[1], '\n')
    print('receipts: ', list(receipts.keys()))
    print('funding receipt: ', funding_receipt.hex())
    print('total gas: ', (sum([v['gas-estimate'] for v in receipts.values()])))
