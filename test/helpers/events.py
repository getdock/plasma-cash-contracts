import time

import rlp

from helpers.const import w3, DEFAULT_PASSWORD, DEFAULT_BOND, ETHER_NAME


# startExit calling PlasmaContract startExit function.
# coin_id: ID of the coin which user wants to exit.
# prevtx_bytes: the previous transaction bytes that happend right before exiting transaction.
# exitingtx_bytes: the transaction bytes of the transaction that user is starting exit with.
# prevtx_inclusion_proof: the previous transaction SparseMerkleTree proof.
# exitingtx_inclusion_proof: the exiting transaction SparseMerkleTree proof.
# signature: signature of the exiting transaction.
# blocks: block number of prevTx and exitTx.
# addr: address of the exiter.
def start_exit(
        plasma_instance,
        coin_id,
        prevtx_bytes,
        exitingtx_bytes,
        prevtx_inclusion_proof,
        exitingtx_inclusion_proof,
        signature,
        blocks,
        addr):
    # unlocking account so we can call startExit function
    w3.personal.unlockAccount(addr, DEFAULT_PASSWORD)
    # getting the gas cost of startExit function.
    gas = plasma_instance.functions.startExit(
        coin_id,
        prevtx_bytes,
        exitingtx_bytes,
        prevtx_inclusion_proof,
        exitingtx_inclusion_proof,
        signature,
        blocks
    ).estimateGas({'from': addr, 'value': w3.toWei(0.1, 'ether')})

    # unlocking account so we can call startExit function.
    w3.personal.unlockAccount(addr, DEFAULT_PASSWORD)
    # calling startExit function on PlasmaContract.
    t = plasma_instance.functions.startExit(
        coin_id,
        prevtx_bytes,
        exitingtx_bytes,
        prevtx_inclusion_proof,
        exitingtx_inclusion_proof,
        signature,
        blocks
    ).transact({'from': addr, 'value': w3.toWei(0.1, 'ether')})

    # asserting the status of respond to check if transaction is completed
    # successfully
    assert w3.eth.waitForTransactionReceipt(t).status == 1

    # getting exit struct from PlasmaContract.
    exitObj = plasma_instance.functions.getExit(coin_id).call()
    # asserting the state of the coin, in this case 1 means coin is EXITING
    assert exitObj[3] == 1


# finishExit calling PlasmaContract finalizeExit function.
# coinI_i : ID of the coin that user wants to finish exit.
# address : address of the user that finishes exit.
def finish_exit(deployed_contracts, coin_id, address):
    # getting the erc20_instance set by deployer.
    erc20_instance = deployed_contracts.erc20_instance
    # getting the erc721_instance set by deployer.
    erc721_instance = deployed_contracts.erc721_instance

    # time required to wait for MATURITY_PERIOD(on mainnet = 1 week / 5 days)
    time.sleep(3)

    """
    Note :
        estimateGas is not working as it should in the case of calling finalizeExit() function.
    """

    # unlocking account so we can call finalizeExit function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling finalizeExit function on PlasmaContract.
    final = deployed_contracts.plasma_instance.functions.finalizeExit(
        coin_id).transact({'from': address, 'gas': 500000})

    # asserting the status of respond to check if transaction is completed
    # successfully.
    assert w3.eth.waitForTransactionReceipt(final).status == 1

    # calling ownerOfToken function on DockPlasmaToken.
    newOwner = erc721_instance.functions.ownerOfToken(coin_id).call()

    # owner of the coin has to be the one who fulfills the requirements to execute finalizeExit.
    # asserting the owner of the coin, newOwner address is equal with address.
    assert newOwner == address

    # calling the exit function on PlasmaContract.
    exitObj = deployed_contracts.plasma_instance.functions.getExit(coin_id).call()

    # asserting the none existing exit
    assertNonExistingExit(exitObj)

    # calling balances instance of Balance struct on PlasmaContract.
    balance = deployed_contracts.plasma_instance.functions.balances(address).call()
    expected = w3.toWei(0.1, 'ether')

    # asseting balance[0] which represent bonded value, after finalizeExit is
    # executed successfully bonded value is equal with zero.
    assert balance[0] == 0

    # asserting balance[1] which represent withdrawable value, the user who
    # finalizes exit successfully can withdraw the withdrawable bond,
    assert balance[1] == expected

    # unlocking account so we can find how much gas is used by withdrawBonds
    # function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # getting the gas cost of withdrawBonds function.
    gas = deployed_contracts.plasma_instance.functions.withdrawBonds().estimateGas({
        'from': address})

    # unlocking account so we can call withdrawBonds function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling withdrawBonds function on PlasmaContract.
    t = deployed_contracts.plasma_instance.functions.withdrawBonds().transact(
        {'from': address, 'gas': gas})
    w3.eth.waitForTransactionReceipt(t)

    # calling balances instance of Balance struct on PlasmaContract.
    balance = deployed_contracts.plasma_instance.functions.balances(address).call()
    expected = w3.toWei(0, 'ether')

    # asseting balance[0] which represent bonded value, after finalizeExit is
    # executed successfully bonded value is equal with zero.
    assert balance[0] == 0
    # asserting balance[1] which represent withdrawable value, after
    # withdrawBonds function is executed this value has to be equal with zero
    assert balance[1] == expected

    # calling  balanceOf ERC20DockToken contract.
    balanceBefore = erc20_instance.functions.balanceOf(address).call()

    # unlocking account so we can call withdraw function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # getting the gas cost of withdraw function.
    gas = deployed_contracts.plasma_instance.functions.withdraw(
        coin_id).estimateGas({'from': address})

    # unlocking account so we can call withdraw function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling withdraw function on PlasmaContract.
    t = deployed_contracts.plasma_instance.functions.withdraw(
        coin_id).transact({'from': address, 'gas': gas})
    w3.eth.waitForTransactionReceipt(t)

    # calling  balanceOf ERC20DockToken contract.
    balance = erc20_instance.functions.balanceOf(address).call()

    # asserting balance of the user that withdraws the coin, current balance
    # has to be equal with balance before calling withdrawn function  and the
    # denomination of the coin.
    assert balance == balanceBefore + w3.toWei(5000, 'ether')


def finish_exits(plasma_instance, tokens, address):
    # time required to wait for MATURITY_PERIOD(on mainnet = 1 week / 5 days)
    time.sleep(3)

    # unlocking account so we can call finalizeExit function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling finalizeExit function on PlasmaContract.
    t = plasma_instance.functions.finalizeExits(
        tokens).transact({'from': address, 'gas': 8000000})

    # asserting the status of respond to check if transaction is completed
    # successfully
    assert w3.eth.waitForTransactionReceipt(t).status == 1


def cancel_exit(plasma_instance, coin_id, address):
    # unlocking account so we can find how much gas is used by cancelExit
    # function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # getting the gas cost of withdraw function.
    gas = plasma_instance.functions.cancelExit(
        coin_id).estimateGas({'from': address})

    # unlocking account so we can call cancelExit function.
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling cancelExit function on PlasmaContract.
    cancelExit = plasma_instance.functions.cancelExit(
        coin_id).transact({'from': address, 'gas': gas})

    # asserting the status of respond to check if transaction is completed
    # successfully.
    assert w3.eth.waitForTransactionReceipt(cancelExit).status == 1

    # calling getExit function to check if an instance of Exit struct is deleted
    # coinI_i : ID of the coin that is exiting.
    exitObj = plasma_instance.functions.getExit(coin_id).call()

    # asserting deleted struct of an exit that is canceled.
    assert exitObj[0] == '0x0000000000000000000000000000000000000000'
    assert exitObj[1] == 0
    assert exitObj[2] == 0
    assert exitObj[3] == 0


def assertNonExistingExit(exitObj):
    # asserting deleted struct of an Exit that is finalized.
    assert exitObj[0] == '0x0000000000000000000000000000000000000000'
    assert exitObj[1] == 0
    assert exitObj[2] == 0
    assert exitObj[3] == 2


def challenge_before(
        plasma_instance,
        token_id,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        block_number,
        address,
        tx_hash):
    # challenge_before calling PlasmaContract challenge_before function.
    # token_id : the token_id which user wants to challenge.
    # tx_bytes: the transaction bytes of the transaction that user is challenging with.
    # tx_inclusion_proof : transaction SparseMerkleTree proof.
    # signature: signature of the transaction that user is challenging with.
    # block_number: block_number of the transaction that user is challenging with.
    # address: the challenger address
    # tx_hash: needed to get the challenge set on PlasmaContract.
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    gas = plasma_instance.functions.challengeBefore(
        token_id,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        block_number
    ).estimateGas({'from': address, 'value': DEFAULT_BOND})

    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    ch = plasma_instance.functions.challengeBefore(
        token_id,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        block_number
    ).transact({'from': address, 'value': DEFAULT_BOND, 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(ch).status == 1

    # building(decoding) tx from tx_bytes
    tx = rlp.decode(tx_bytes)

    # getting challenge from PlasmaContract.
    challengeObj = plasma_instance.functions.getChallenge(
        token_id, tx_hash).call()

    # asserting challengeObj to check whether the challenge initiated successfully.
    assert_challenge(challengeObj, tx[3], address, tx_hash, block_number)


def finish_challenge_exit(plasma_instance, token_id, address):
    # finishChallengeExit used to finalize an exited coin
    # token_id: token_id of the token that user wants to finalize
    # address: the initiater of finalizeExit function.

    # using time.sleep to stop thread for some time in order to let token be matured
    # testing : 3 seconds
    # real world : 1 week or less.
    time.sleep(3)

    # unlocking account so we can call function
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling finalizeExit function on PlasmaContract.
    final = plasma_instance.functions.finalizeExit(
        token_id).transact({'from': address, 'gas': 500000})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(final).status == 1

    # getting the balance of challenger after finalizeExit is finished
    # where balance is the bond provided by exiter/challenger.
    balances = plasma_instance.functions.balances(address).call()

    # asserting the expected values from balance.
    # balance[0] is the bonded amount.
    # in this case it should be 0 since challenger is successfully challenging.
    assert balances[0] == 0
    # balance[0] is the withdrawable amount.
    # in this case it should be 0.2 :
    # bond of challenger provided + bond of exiter provided
    assert balances[1] == w3.toWei(0.2, ETHER_NAME)

    # getting exit struct from plasma_instance
    exitObj = plasma_instance.functions.getExit(token_id).call()
    # asserting the deleted exit since challenge was successfull.
    assert_non_existing_exit(exitObj)

    # unlocking account so we can call function
    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    # calling the WithdrawBonds function to get the woned bond(stake).
    t = plasma_instance.functions.withdrawBonds().transact({'from': address})
    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(t).status == 1

    # getting the balance of exiter after withdrawBonds is called
    balances = plasma_instance.functions.balances(address).call()

    # asserting the expected value of balance
    # balances[1](withdrawable) should equal 0 since user has withdrawn it.
    assert balances[1] == 0


def respond_challenge_before(
        plasma_instance,
        token_id,
        challengingtx_hash,
        respondingblock_number,
        respondingTransaction,
        proof,
        signature,
        address):
    # respondchallenge_before calling PlasmaContract respondchallenge_before function.
    # token_id : the token_id which user wants to challenge.
    # challengetx_hash: tx_hash of the tx that has challenged the exit
    # respondingblock_number: block number of respond trasnaction
    # respondingTransaction: the trasnaction which user responds to a challenge
    # proof: proof of the respondingTransaction
    # signature: signature of the respondingTransaction
    # address: the responder address.
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    gas = plasma_instance.functions.respondChallengeBefore(
        token_id,
        challengingtx_hash,
        respondingblock_number,
        respondingTransaction,
        proof,
        signature
    ).estimateGas({'from': address})

    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)

    # calling respondchallenge_before function on PlasmaContract
    res = plasma_instance.functions.respondChallengeBefore(
        token_id,
        challengingtx_hash,
        respondingblock_number,
        respondingTransaction,
        proof,
        signature
    ).transact({'from': address, 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(res).status == 1


def challenge_after(
        plasma_instance,
        token_id,
        challengingblock_number,
        challengingTransaction,
        proof,
        signature,
        address):
    # challengeAfter calling PlasmaContract challengeAfter function.
    # token_id : the token_id which user wants to challenge.
    # challengingblock_number: challenge trasnaction block number
    # challengingTransaction: challenge trasnaction bytes
    # proof: proof of challengingTransaction.
    # signature: signature of challengingTransaction.
    # address: challenger address
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    gas = plasma_instance.functions.challengeAfter(
        token_id,
        challengingblock_number,
        challengingTransaction,
        proof,
        signature
    ).estimateGas({'from': address})

    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    ch = plasma_instance.functions.challengeAfter(
        token_id,
        challengingblock_number,
        challengingTransaction,
        proof,
        signature
    ).transact({'from': address, 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(ch).status == 1

    # asserting successfull challenge
    assert_successful_challenge(plasma_instance, address)

    # getting exit obj
    exitObj = plasma_instance.functions.getExit(token_id).call()

    # assert deleted exit since the challenge was successfull.
    assert_non_existing_exit(exitObj)


def challenge_between(
        plasma_instance,
        token_id,
        block_number,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        address):
    # challengeBetween calling PlasmaContract challengeBetween function.
    # token_id : the token_id which user wants to challenge.
    # block_number: challenge tx block number
    # tx_bytes: challenge tx bytes
    # tx_inclusion_proof: smt proof of challenge tx
    # signature: challenge tx signature
    # address: challenger address
    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    gas = plasma_instance.functions.challengeBetween(
        token_id,
        block_number,
        tx_bytes,
        tx_inclusion_proof,
        signature
    ).estimateGas({'from': address})

    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    ch = plasma_instance.functions.challengeBetween(
        token_id,
        block_number,
        tx_bytes,
        tx_inclusion_proof,
        signature
    ).transact({'from': address, 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(ch).status == 1

    # asserting successfull challenge
    assert_successful_challenge(plasma_instance, address)

    # getting exit struct from PlasmaContract
    exitObj = plasma_instance.functions.getExit(token_id).call()

    # assert deleted exit since challenge was successfull.
    assert_non_existing_exit(exitObj)


def assert_challenge(
        challenge,
        owner,
        challenger,
        tx_hash,
        challengingblock_number):
    # function to check whether challenge was set as expected

    assert bytes.fromhex(challenge[0][2:]) == owner
    assert challenge[1] == challenger
    assert challenge[2] == tx_hash
    assert challenge[3] == challengingblock_number


def assert_non_existing_exit(exitObj):
    # function to check if exit is deleted when a challenge is successfull.
    assert exitObj[0] == '0x0000000000000000000000000000000000000000'
    assert exitObj[1] == 0
    assert exitObj[2] == 0
    assert exitObj[3] == 0


def assert_successful_challenge(plasma_instance, address):
    # function to check balance of challenger if challenge was successfull
    # getting the balance of challenger
    balances = plasma_instance.functions.balances(address).call()

    # balances[0]: bonded amount should be 0
    assert balances[0] == 0
    # balances[1]: withdrawable bond should be 0.1 since challenge was successfull
    assert balances[1] == DEFAULT_BOND

    w3.personal.unlockAccount(w3.eth.defaultAccount, '')
    gas = plasma_instance.functions.withdrawBonds().estimateGas({'from': address})

    w3.personal.unlockAccount(address, DEFAULT_PASSWORD)
    t = plasma_instance.functions.withdrawBonds().transact(
        {'from': address, 'gas': gas})

    # asserting the status of respond to check if transaction is completed successfully
    assert w3.eth.waitForTransactionReceipt(t).status == 1

    # getting the balance of challenger
    balances = plasma_instance.functions.balances(address).call()

    # bonded : should be 0
    assert balances[0] == 0
    # withdrawable should be 0 since user has withdrawn it.
    assert balances[1] == 0


def assert_deleted_coin(coin):
    # function to check whether coin was deleted properly
    assert coin[0] == '0x0000000000000000000000000000000000000000'
    assert coin[1] == 0
    assert coin[2] == 0
    assert coin[4] == 0