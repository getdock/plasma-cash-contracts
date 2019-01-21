from helpers.web3Provider import w3
from helpers import instances, estimate_gas

pwd = 'passw0rd'

# transfer function to handle erc20 transfers to users
# address: the address where tokens are being transafered.
# amount: the amount that we want to trasnfer
def transfer(address, amount):

    # getting erc20Instance set by deployer
    erc20Instance = instances.erc20_instance

    # estimating function gas cost
    gas = estimate_gas.erc20Transfer(address, amount)

    # unlocking account so we can call functions
    w3.personal.unlockAccount(w3.eth.accounts[0], '')

    # calling transfer function on erc20 contract.
    transfer1 = erc20Instance.functions.transfer(
        address, amount).transact({'from': w3.eth.accounts[0], 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(transfer1).status == 1

    # checking if amount transfered is correct
    balance = erc20Instance.functions.balanceOf(address).call()
    assert balance == amount

    # returning the bilance of address
    return balance

# approve function to handle approves on erc20 contract
# approveAddress : the address we want to approve
# address : approver(owner of erc20 tokens)
# amount: amount to approve
def approve(approveAddress, address, amount):

    # getting erc20Instance set by deployer
    erc20Instance = instances.erc20_instance

    # estimating function gas cost
    gas = estimate_gas.erc20Approve(approveAddress, address, amount)

    # unlocking account so we can call functions
    w3.personal.unlockAccount(address, pwd)

    # calling approve function on erc20 contract.
    approve1 = erc20Instance.functions.approve(
        approveAddress, amount).transact({'from': address, 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(approve1).status == 1

    # checking if amount was approved correctly.
    allowance = erc20Instance.functions.allowance(address, approveAddress).call()
    assert allowance == amount

    # returning amount approved
    return allowance
