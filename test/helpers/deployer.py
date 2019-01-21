from helpers.web3Provider import w3
import json
from helpers import instances, estimate_gas

'''
    deployer.py
        Used to deploy all contracts needed to make this whole poc work.
        Also deployer handles linking all contracts together.
'''

# reading compiled PlasmaContract.
with open('test/json/contracts/PlasmaContract.json') as f:
    plasmadata = json.load(f)
# reading compiled ERC20DockToken.sol contract.
with open('test/json/contracts/ERC20DockToken.json') as f:
    ercdata = json.load(f)
# reading compiled DockPlasmaToken.sol contract.
with open('test/json/contracts/DockPlasmaToken.json') as f:
    erc721Data = json.load(f)
# reading compiled DoChecks.sol contract.
with open('test/json/contracts/DoChecks.json') as f:
    doChecksData = json.load(f)

# deployContracts function used to deploy all contracts needed in this POC.
def deployContracts():

    # creating the contract object.
    ERC20 = w3.eth.contract(
        # contract abi
        abi=ercdata['abi'],
        # bytecode of compiled contract.
        bytecode=ercdata['bytecode']
    )

    # getting gas cost of constructor using estimateGas script.
    gas = estimate_gas.ERC20(ercdata)

    # unlocking account so we can call constructor of contract.
    w3.personal.unlockAccount(w3.eth.accounts[0], '')

    # calling contract constructor which will deploy our contract to TestRPC.
    tx_hash_ERC20 = ERC20.constructor().transact(
        {'from': w3.eth.accounts[0], 'gas': gas})

    # tx_receipt_ERC20 is the transaction respond we get from TestRPC.
    tx_receipt_ERC20 = w3.eth.waitForTransactionReceipt(tx_hash_ERC20)

    # asserting the status of respond to check if transaction is completed successfully
    assert tx_receipt_ERC20.status == 1

    # --------------------------------------------------------------------------

    # creating the contract object.
    DoChecks = w3.eth.contract(
        # abi of contract
        abi=doChecksData['abi'],
        # bytecode of compiled contract
        bytecode=doChecksData['bytecode']
    )

    # getting gas cost of constructor using estimateGas script.
    gas = estimate_gas.DoChecks(doChecksData)

    # unlocking account so we call constructor of contract
    w3.personal.unlockAccount(w3.eth.accounts[0], '')

    # calling constructor which will deploy our contract to TestRPC.
    tx_hash_checks = DoChecks.constructor().transact(
        {'from': w3.eth.accounts[0], 'gas': gas})

    # tx_receipt_ERC20 is the transaction respond we get from TestRPC.
    tx_receipt_checks = w3.eth.waitForTransactionReceipt(tx_hash_checks)

    # asserting the status of respond to check if transaction is completed successfully
    assert tx_receipt_checks.status == 1

    # --------------------------------------------------------------------------

    # creating the contract object.
    PlasmaTokenERC721 = w3.eth.contract(
        # contract abi
        abi=erc721Data['abi'],
        # compiled contract bytecode
        bytecode=erc721Data['bytecode']
    )

    # getting gas cost of constructor using estimateGas script.
    gas = estimate_gas.PlasmaTokenERC721(erc721Data)

    # unlocking account so we call constructor of contract.
    w3.personal.unlockAccount(w3.eth.accounts[0], '')

    # calling constructor which will deploy our contract to TestRPC.
    tx_hash_erc721 = PlasmaTokenERC721.constructor().transact(
        {'from': w3.eth.accounts[0], 'gas': gas})

    # tx_receipt_ERC20 is the transaction respond we get from TestRPC.
    tx_receipt_erc721 = w3.eth.waitForTransactionReceipt(tx_hash_erc721)

    # asserting the status of respond to check if transaction is completed successfully
    assert tx_receipt_erc721.status == 1

    # --------------------------------------------------------------------------

    # creating the contract object.
    Plasma = w3.eth.contract(
        # contract abi
        abi=plasmadata['abi'],
        # compiled contract bytecode
        bytecode=plasmadata['bytecode']
    )

    # getting gas cost of constructor using estimateGas script.
    gas = estimate_gas.PlasmaContract(plasmadata)

    # unlocking account so we call constructor of contract.
    w3.personal.unlockAccount(w3.eth.accounts[0], '')

    # calling constructor which will deploy our contract to TestRPC.
    tx_hash_Plasma = Plasma.constructor().transact(
        {'from': w3.eth.accounts[0], 'gas': gas})

    # tx_receipt_ERC20 is the transaction respond we get from TestRPC.
    tx_receipt_Plasma = w3.eth.waitForTransactionReceipt(tx_hash_Plasma)

    # asserting the status of respond to check if transaction is completed successfully
    assert tx_receipt_Plasma.status == 1

    # --------------------------------------------------------------------------

    # creating contract instance
    erc20Instance = w3.eth.contract(
        # erc20 contract address deployed to TestRPC.
        address=tx_receipt_ERC20.contractAddress,
        # deployed contract abi.
        abi=ercdata['abi'],
    )

    # creating contract instance
    plasma_instance = w3.eth.contract(
        # Plasma contract address deployed to TestRPC.
        address=tx_receipt_Plasma.contractAddress,
        # deployed contract abi.
        abi=plasmadata['abi'],
    )

    # creating contract instance
    erc721Instance = w3.eth.contract(
        # erc721 contract address deployed to TestRPC
        address=tx_receipt_erc721.contractAddress,
        # deployed contract abi.
        abi=erc721Data['abi'],
    )

    # creating contract instance
    checksInstance = w3.eth.contract(
        # DoChecks contract address deployed to TestRPC
        address=tx_receipt_checks.contractAddress,
        # deployed contract abi.
        abi=doChecksData['abi'],
    )

    # setting contract instances as global variables so we can call them in other
    # scripts without needing to create new ones.
    instances.setInstances(
        erc20Instance,
        plasma_instance,
        erc721Instance,
        checksInstance
    )

    # getting gas cost of loadAddress function using estimateGas script.
    gas = estimate_gas.loadAddress(tx_receipt_Plasma.contractAddress)

    # unlocking account so we can call contract function.
    w3.personal.unlockAccount(w3.eth.accounts[0], '')

    # loading PlasmaContract address to erc721 contract since functions on erc721
    # are only callable from PlasmaContract.
    loadAddressOnERC721 = erc721Instance.functions.loadPlasmaAddress(
        tx_receipt_Plasma.contractAddress).transact({'from': w3.eth.accounts[0], 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(loadAddressOnERC721).status == 1

    # getting gas cost of setMaturityAndBond function using estimateGas script.
    gas = estimate_gas.setMaturityAndBond()

    # unlocking account so we can call contract function.
    w3.personal.unlockAccount(w3.eth.accounts[0], '')

    # setting the maturity and bond on plasma contract where :
    # maturity : is the time that an exit needs to mature in order to be finalized.
    # bond: is the amount of bond(stake) user needs to put in order to start/challenge
    # and exit.
    setBondValue = plasma_instance.functions.setMaturityAndBond(w3.toWei(
        0.1, 'ether'), 2, 1).transact({'from': w3.eth.accounts[0], 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(setBondValue).status == 1

    # getting gas cost of loadAddressesOnPlasma function using estimateGas script.
    gas = estimate_gas.loadAddressesOnPlasma(
        tx_receipt_ERC20.contractAddress,
        tx_receipt_erc721.contractAddress,
        tx_receipt_checks.contractAddress)
    w3.personal.unlockAccount(w3.eth.accounts[0], '')

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
            'from': w3.eth.accounts[0],
            'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(tx).status == 1

    # checking if bond is set as expected.
    assert plasma_instance.functions.bond_amount().call() == w3.toWei(0.1, 'ether')

    # checking if plasma address is set as expected in erc721.
    assert tx_receipt_Plasma.contractAddress == erc721Instance.functions.plasmaAddress().call()

    return erc20Instance, plasma_instance, erc721Instance, checksInstance
