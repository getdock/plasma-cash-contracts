import time

import rlp

from fixtures.const import DEFAULT_PASSWORD, ETHER_NAME, w3, DEFAULT_BOND

"""
    challenges.py
        Used to initiate challenge functions of PlasmaContract and check
        if the challenge process is happening successfully.
"""


# challenge_before calling PlasmaContract challenge_before function.
# token_id : the token_id which user wants to challenge.
# tx_bytes: the transaction bytes of the transaction that user is challenging with.
# tx_inclusion_proof : transaction SparseMerkleTree proof.
# signature: signature of the transaction that user is challenging with.
# block_number: block_number of the transaction that user is challenging with.
# address: the challenger address
# tx_hash: needed to get the challenge set on PlasmaContract.
def challenge_before(
        plasma_instance,
        token_id,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        block_number,
        address,
        tx_hash):
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


# finishChallengeExit used to finalize an exited coin
# token_id: token_id of the token that user wants to finalize
# address: the initiater of finalizeExit function.
def finish_challenge_exit(plasma_instance, token_id, address):
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


# respondchallenge_before calling PlasmaContract respondchallenge_before function.
# token_id : the token_id which user wants to challenge.
# challengetx_hash: tx_hash of the tx that has challenged the exit
# respondingblock_number: block number of respond trasnaction
# respondingTransaction: the trasnaction which user responds to a challenge
# proof: proof of the respondingTransaction
# signature: signature of the respondingTransaction
# address: the responder address.
def respond_challenge_before(
        plasma_instance,
        token_id,
        challengingtx_hash,
        respondingblock_number,
        respondingTransaction,
        proof,
        signature,
        address):
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


# challengeAfter calling PlasmaContract challengeAfter function.
# token_id : the token_id which user wants to challenge.
# challengingblock_number: challenge trasnaction block number
# challengingTransaction: challenge trasnaction bytes
# proof: proof of challengingTransaction.
# signature: signature of challengingTransaction.
# address: challenger address
def challenge_after(
        plasma_instance,
        token_id,
        challengingblock_number,
        challengingTransaction,
        proof,
        signature,
        address):
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


# challengeBetween calling PlasmaContract challengeBetween function.
# token_id : the token_id which user wants to challenge.
# block_number: challenge tx block number
# tx_bytes: challenge tx bytes
# tx_inclusion_proof: smt proof of challenge tx
# signature: challenge tx signature
# address: challenger address
def challenge_between(
        plasma_instance,
        token_id,
        block_number,
        tx_bytes,
        tx_inclusion_proof,
        signature,
        address):
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


# function to check whether challenge was set as expected
def assert_challenge(
        challenge,
        owner,
        challenger,
        tx_hash,
        challengingblock_number):
    assert bytes.fromhex(challenge[0][2:]) == owner
    assert challenge[1] == challenger
    assert challenge[2] == tx_hash
    assert challenge[3] == challengingblock_number


# function to check if exit is deleted when a challenge is successfull.
def assert_non_existing_exit(exitObj):
    assert exitObj[0] == '0x0000000000000000000000000000000000000000'
    assert exitObj[1] == 0
    assert exitObj[2] == 0
    assert exitObj[3] == 0


# function to check balance of challenger if challenge was successfull
def assert_successful_challenge(plasma_instance, address):
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


# function to check whether coin was deleted properly
def assert_deleted_coin(coin):
    assert coin[0] == '0x0000000000000000000000000000000000000000'
    assert coin[1] == 0
    assert coin[2] == 0
    assert coin[4] == 0
