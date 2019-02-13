import json
from typing import Dict, Tuple

from web3 import Web3
from web3.datastructures import AttributeDict

from helpers.const import (CHALLENGE_PARAMS, CHECKS_CONTRACT_PATH,
                           DEFAULT_FROM, DOCK_PLASMA_CONTRACT_PATH,
                           ERC20_CONTRACT_PATH, PLASMA_CONTRACT_PATH)


def deploy_contract(compiled_contract_path: str, w3: Web3) -> Tuple[Dict, AttributeDict]:
    """
    Deploy the given compiled contract using the default account in the given Web3 instance.

    :param compiled_contract_path: path to the compiled contract in json format
    :param w3: Web3 instance to use
    :return: transaction receipt
    """
    account = w3.eth.defaultAccount
    with open(compiled_contract_path) as f:
        contract_data = json.load(f)

    contract_to_deploy = w3.eth.contract(
        abi=contract_data['abi'],
        bytecode=contract_data['bytecode']
    )

    kwargs = {'from': account}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_deploy = contract_to_deploy.constructor()
    kwargs['gas'] = fn_deploy.estimateGas(kwargs)
    tx_hash = fn_deploy.transact(kwargs)
    tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
    assert tx_receipt.status

    return contract_data, tx_receipt


def deploy_all_contracts(w3: Web3) -> AttributeDict:
    """
    Deploy all contracts needed for this POC.

    :param w3: w3 instance to use
    :return: AttributeDict with web3.utils.datatypes.Contract instances of the deployed contracts
    """
    account = w3.eth.defaultAccount
    erc_data, tx_receipt_ERC20 = deploy_contract(ERC20_CONTRACT_PATH, w3)
    do_checks_data, tx_receipt_checks = deploy_contract(CHECKS_CONTRACT_PATH, w3)
    erc721_data, tx_receipt_erc721 = deploy_contract(DOCK_PLASMA_CONTRACT_PATH, w3)
    plasma_data, tx_receipt_plasma = deploy_contract(PLASMA_CONTRACT_PATH, w3)

    erc20_instance = w3.eth.contract(
        address=tx_receipt_ERC20.contractAddress,
        abi=erc_data['abi'],
    )

    plasma_instance = w3.eth.contract(
        address=tx_receipt_plasma.contractAddress,
        abi=plasma_data['abi'],
    )

    erc721_instance = w3.eth.contract(
        address=tx_receipt_erc721.contractAddress,
        abi=erc721_data['abi'],
    )

    checks_instance = w3.eth.contract(
        address=tx_receipt_checks.contractAddress,
        abi=do_checks_data['abi'],
    )

    # load address to ERC721 contract
    args = (tx_receipt_plasma.contractAddress,)
    kwargs = {'from': account}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_load = erc721_instance.functions.loadPlasmaAddress(*args)
    kwargs['gas'] = fn_load.estimateGas(kwargs)
    tx_hash = fn_load.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # set Bond and Maturity params
    args = (CHALLENGE_PARAMS['bond-to-wei'],
            CHALLENGE_PARAMS['maturity-period'],
            CHALLENGE_PARAMS['challenge-window']
            )
    kwargs = {'from': account}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_set_params = plasma_instance.functions.setMaturityAndBond(*args)
    kwargs['gas'] = fn_set_params.estimateGas(kwargs)
    tx_hash = fn_set_params.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # set contract addresses
    args = (erc20_instance.address,
            erc721_instance.address,
            checks_instance.address)
    kwargs = {'from': account}
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_set_addrs = plasma_instance.functions.setAddresses(*args)
    kwargs['gas'] = fn_set_addrs.estimateGas(kwargs)
    tx_hash = fn_set_addrs.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status

    # checking if bond is set
    assert plasma_instance.functions.bond_amount().call() == CHALLENGE_PARAMS['bond-to-wei']

    # checking if plasma address is set
    assert tx_receipt_plasma.contractAddress == erc721_instance.functions.plasmaAddress().call()

    deployed_contracts = AttributeDict(
        {
            "erc20_instance": erc20_instance,
            "plasma_instance": plasma_instance,
            "erc721_instance": erc721_instance,
            "checks_instance": checks_instance
        }
    )

    return deployed_contracts
