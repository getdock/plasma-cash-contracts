import json
from typing import Tuple, Dict

from web3.datastructures import AttributeDict

from fixtures.const import w3, PLASMA_CONTRACT_PATH, ERC20_CONTRACT_PATH, DOCK_PLASMA_CONTRACT_PATH, \
    CHECKS_CONTRACT_PATH, DEFAULT_FROM

"""
    deployer.py
        Used to deploy all contracts needed to make this whole poc work.
        Also deployer handles linking all contracts together.
"""


def deploy_contract(compiled_contract_path: str, account: str) -> Tuple[Dict, AttributeDict]:
    """
    Deploy the given compiled contract using the given account.
    
    :param compiled_contract_path: path to the compiled contract in json format
    :param account: account to use
    :return: transaction receipt
    """
    with open(compiled_contract_path) as f:
        contract_data = json.load(f)

    contract_to_deploy = w3.eth.contract(
        abi=contract_data['abi'],
        bytecode=contract_data['bytecode']
    )

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = contract_to_deploy.constructor().estimateGas({'from': account})

    # unlocking account so we can call constructor of contract.
    w3.personal.unlockAccount(account, '')

    # calling contract constructor which will deploy our contract to TestRPC.
    tx_hash_contract = contract_to_deploy.constructor().transact(
        {'from': account, 'gas': gas})

    # tx_receipt_contract is the transaction response we get from TestRPC.
    tx_receipt_contract = w3.eth.waitForTransactionReceipt(tx_hash_contract)

    # asserting the status of response to check if transaction is completed successfully
    assert tx_receipt_contract.status == 1

    return contract_data, tx_receipt_contract


def deploy_all_contracts(account: str) -> AttributeDict:
    """
    Deploy all contracts needed in this POC.

    :param account: account to use
    :return: AttributeDict with web3.utils.datatypes.Contract instances of the deployed contracts
    """
    erc_data, tx_receipt_ERC20 = deploy_contract(ERC20_CONTRACT_PATH, account)
    do_checks_data, tx_receipt_checks = deploy_contract(CHECKS_CONTRACT_PATH, account)
    erc721_data, tx_receipt_erc721 = deploy_contract(DOCK_PLASMA_CONTRACT_PATH, account)
    plasma_data, tx_receipt_plasma = deploy_contract(PLASMA_CONTRACT_PATH, account)

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

    deployed_contracts = AttributeDict(
        {
            "erc20_instance": erc20_instance,
            "plasma_instance": plasma_instance,
            "erc721_instance": erc721_instance,
            "checks_instance": checks_instance
        }
    )

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = erc721_instance.functions.loadPlasmaAddress(tx_receipt_plasma.contractAddress).estimateGas(DEFAULT_FROM)

    # unlocking account so we can call contract function.
    w3.personal.unlockAccount(account, '')

    # loading PlasmaContract address to erc721 contract since functions on erc721
    # are only callable from PlasmaContract.
    loadAddressOnERC721 = erc721_instance.functions.loadPlasmaAddress(
        tx_receipt_plasma.contractAddress).transact({'from': account, 'gas': gas})

    # asserting the status of response to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(loadAddressOnERC721).status == 1

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = plasma_instance.functions.setMaturityAndBond(w3.toWei(0.1, 'ether'), 2, 1).estimateGas(DEFAULT_FROM)

    # setting the maturity and bond on plasma contract where :
    # maturity : is the time that an exit needs to mature in order to be finalized.
    # bond: is the amount of bond(stake) user needs to put in order to start/challenge
    # and exit.
    setBondValue = plasma_instance.functions.setMaturityAndBond(w3.toWei(
        0.1, 'ether'), 2, 1).transact({'from': account, 'gas': gas})

    # asserting the status of response to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(setBondValue).status == 1

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    gas = deployed_contracts.plasma_instance.functions.setAddresses(
        deployed_contracts.erc20_instance.address,
        deployed_contracts.erc721_instance.address,
        deployed_contracts.checks_instance.address
    ).estimateGas(
        DEFAULT_FROM
    )

    # setting addresses on PlasmaContract which will be used to :
    # erc20: transfer coins from participant to PlasmaContract and vice versa if
    # PlasmaCoin is withdrawn.
    # erc721: to mint a new coin when user participates
    #         to trasnfer erc721 token when coin is exited
    #         to burn erc721 tokens when coin is withdrawn
    #         to get the amount user ownes
    tx = plasma_instance.functions.setAddresses(
        tx_receipt_ERC20.contractAddress,
        tx_receipt_erc721.contractAddress,
        tx_receipt_checks.contractAddress).transact(
        {
            'from': account,
            'gas': gas})

    # asserting the status of response to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(tx).status == 1

    # checking if bond is set as expected.
    assert plasma_instance.functions.bond_amount().call() == w3.toWei(0.1, 'ether')

    # checking if plasma address is set as expected in erc721.
    assert tx_receipt_plasma.contractAddress == erc721_instance.functions.plasmaAddress().call()

    return deployed_contracts
