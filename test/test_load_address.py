from helpers.const import DEFAULT_FROM, DEFAULT_PASSWORD
from helpers.const import W3 as w3


def test_successful_load_plasma_address(setup_participate):
    '''
        only owner can successfully load plasma address
    '''
    _, deployed_contracts, _ = setup_participate

    args = (deployed_contracts.plasma_instance.address, )
    kwargs = {'from': w3.eth.accounts[0]}

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_load = deployed_contracts.erc721_instance.functions.loadPlasmaAddress(*args)
    kwargs['gas'] = fn_load.estimateGas(kwargs)
    tx_hash = fn_load.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status


def test_unsuccessful_load_plasma_address(setup_participate):
    '''
        alice is not the owner so she fails to load plasma address
    '''
    accounts, deployed_contracts, _ = setup_participate
    alice_addr = accounts[1].address

    args = (deployed_contracts.plasma_instance.address, )
    kwargs = {'from': w3.eth.accounts[0]}

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_load = deployed_contracts.erc721_instance.functions.loadPlasmaAddress(*args)
    gas = fn_load.estimateGas(kwargs)
    kwargs = {'from': alice_addr, 'gas': gas}

    w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
    tx_hash = fn_load.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status == 0


def test_successful_load_addresses_on_plasma(setup_participate):
    '''
        only validator can successfully load addresses on plasma
    '''
    _, deployed_contracts, _ = setup_participate

    args = (deployed_contracts.erc20_instance.address,
            deployed_contracts.erc721_instance.address,
            deployed_contracts.checks_instance.address
            )
    kwargs = {'from': w3.eth.accounts[0]}

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_set_addr = deployed_contracts.plasma_instance.functions.setAddresses(*args)
    kwargs['gas'] = fn_set_addr.estimateGas(kwargs)
    tx_hash = fn_set_addr.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status


def test_unsuccessful_load_addresses_on_plasma(setup_participate):
    '''
        alice is not the validator so she fails to load addresses on plasma
    '''
    accounts, deployed_contracts, _ = setup_participate
    alice_addr = accounts[1].address

    args = (deployed_contracts.erc20_instance.address,
            deployed_contracts.erc721_instance.address,
            deployed_contracts.checks_instance.address)
    kwargs = {'from': w3.eth.accounts[0]}

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    fn_set_addr = deployed_contracts.plasma_instance.functions.setAddresses(*args)
    gas = fn_set_addr.estimateGas(kwargs)
    kwargs = {'from': alice_addr, 'gas': gas}

    w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
    tx_hash = fn_set_addr.transact(kwargs)
    assert w3.eth.waitForTransactionReceipt(tx_hash).status == 0
