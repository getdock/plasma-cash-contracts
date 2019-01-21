from fixtures.const import DEFAULT_PASSWORD
from helpers import instances, estimate_gas
from helpers.web3Provider import w3


# only owner can successfully load plasma address
def test_successful_load_plasma_address(setup_participate):
    gas = estimate_gas.loadAddress(instances.plasma_instance.address)

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    load_address_on_ERC721 = instances.erc721_instance.functions.loadPlasmaAddress(
        instances.plasma_instance.address).transact(
        {'from': w3.eth.accounts[0], 'gas': gas}
    )
    tx_receipt = w3.eth.waitForTransactionReceipt(load_address_on_ERC721)

    assert tx_receipt.status == 1


# alice is not the owner so she fails to load plasma address
def test_unsuccessful_load_plasma_address(setup_participate):
    accounts, coins = setup_participate
    alice_addr = accounts[1].address

    gas = estimate_gas.loadAddress(instances.plasma_instance.address)

    w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
    load_address_on_ERC721 = instances.erc721_instance.functions.loadPlasmaAddress(
        instances.plasma_instance.address).transact(
        {'from': alice_addr, 'gas': gas}
    )
    tx_receipt = w3.eth.waitForTransactionReceipt(load_address_on_ERC721)

    assert tx_receipt.status == 0


# only validator can successfully load addresses on plasma
def test_successful_load_addresses_on_plasma(setup_participate):
    gas = estimate_gas.loadAddressesOnPlasma(
        instances.erc20_instance.address,
        instances.erc721_instance.address,
        instances.checksInstance.address
    )

    w3.personal.unlockAccount(w3.eth.accounts[0], '')
    tx = instances.plasma_instance.functions.setAddresses(
        instances.erc20_instance.address,
        instances.erc721_instance.address,
        instances.checksInstance.address
    ).transact(
        {'from': w3.eth.accounts[0], 'gas': gas}
    )
    tx_receipt = w3.eth.waitForTransactionReceipt(tx)

    assert tx_receipt.status == 1


# alice is not the validator so she fails to load addresses on plasma
def test_unsuccessful_load_addresses_on_plasma(setup_participate):
    accounts, coins = setup_participate
    alice_addr = accounts[1].address

    gas = estimate_gas.loadAddressesOnPlasma(
        instances.erc20_instance.address,
        instances.erc721_instance.address,
        instances.checksInstance.address
    )

    w3.personal.unlockAccount(alice_addr, DEFAULT_PASSWORD)
    tx = instances.plasma_instance.functions.setAddresses(
        instances.erc20_instance.address,
        instances.erc721_instance.address,
        instances.checksInstance.address
    ).transact(
        {'from': alice_addr, 'gas': gas}
    )
    tx_receipt = w3.eth.waitForTransactionReceipt(tx)

    assert tx_receipt.status == 0
