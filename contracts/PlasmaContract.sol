// Copyright Loom Network 2018 - All rights reserved, Dual licensed on GPLV3
// Learn more about Loom DappChains at https://loomx.io
// All derivitive works of this code must incluse this copyright header on every file

pragma solidity ^0.4.24;


// ERC721
import "./DockPlasmaToken.sol";

// ERC20
import "./ERC20.sol";

// Lib deps
import "./SafeMath.sol";
import "./ChallengeLib.sol";
import "./Transaction.sol";

// Inclusion checks
import "./DoChecks.sol";


contract PlasmaContract {

    /**
     * Event for coin deposit logging.
     * @notice The Deposit event indicates that a deposit block has been added
     *         to the Plasma chain
     * @param slot Plasma slot, a unique identifier, assigned to the deposit
     * @param blockNumber The index of the block in which a deposit transaction
     *                    is included
     * @param denomination Quantity of a particular coin deposited
     * @param from The address of the depositor
     */
    event Deposit(uint64 indexed slot, uint256 blockNumber, uint256 denomination,
                  address indexed from);

    /**
     * Event for block submission logging
     * @notice The event indicates the addition of a new Plasma block
     * @param blockNumber The block number of the submitted block
     * @param root The root hash of the Merkle tree containing all of a block's
     *             transactions.
     * @param timestamp The time when a block was added to the Plasma chain
     */
    event SubmittedBlock(uint256 blockNumber, bytes32 root, uint256 timestamp);

    /**
     * Event for logging exit starts
     * @param slot The slot of the coin being exited
     * @param owner The user who claims to own the coin being exited
     */
    event StartedExit(uint64 indexed slot, address indexed owner);

    /**
     * Event for exit challenge logging
     * @notice This event only fires if `challengeBefore` is called.
     * @param slot The slot of the coin whose exit was challenged
     * @param txHash The hash of the tx used for the challenge
     */
    event ChallengedExit(uint64 indexed slot, bytes32 txHash, uint256 challengingBlockNumber);

    /**
     * Event for exit response logging
     * @notice This only logs responses to `challengeBefore`
     * @param slot The slot of the coin whose challenge was responded to
     */
    event RespondedExitChallenge(uint64 indexed slot);

    /**
     * Event for logging when an exit was successfully challenged
     * @param slot The slot of the coin being reset to NOT_EXITING
     * @param owner The owner of the coin
     */
    event CoinReset(uint64 indexed slot, address indexed owner);

    /**
     * Event for exit finalization logging
     * @param slot The slot of the coin whose exit has been finalized
     * @param owner The owner of the coin whose exit has been finalized
     */
    event FinalizedExit(uint64 indexed slot, address owner);

    /**
     * Event to log the freeing of a bond
     * @param from The address of the user whose bonds have been freed
     * @param amount The bond amount which can now be withdrawn
     */
    event FreedBond(address indexed from, uint256 amount);

    /**
     * Event to log the slashing of a bond
     * @param from The address of the user whose bonds have been slashed
     * @param to The recipient of the slashed bonds
     * @param amount The bound amount which has been forfeited
     */
    event SlashedBond(address indexed from, address indexed to, uint256 amount);

    /**
     * Event to log the withdrawal of a bond
     * @param from The address of the user who withdrew bonds
     * @param amount The bond amount which has been withdrawn
     */
    event WithdrewBonds(address indexed from, uint256 amount);

    /**
     * Event to log the withdrawal of a coin
     * @param owner The address of the user who withdrew bonds
     * @param slot the slot of the coin that was exited
     * @param uid The uid of the coin being withdrawn if ERC721, else 0
     * @param denomination The denomination of the coin which has been withdrawn (=1 for ERC721)
     */
    event Withdrew(address indexed owner, uint64 indexed slot, uint uid, uint denomination);

    using SafeMath for uint256;
    using Transaction for bytes;
    using ChallengeLib for ChallengeLib.Challenge[];

    uint256 public bond_amount;
    // An exit can be finalized after it has matured,
    // after T2 = T0 + maturity_period
    // An exit can be challenged in the first window
    // between T0 and T1 ( T1 = T0 + challenge_window)
    // A challenge can be responded to in the second window
    // between T1 and T2
    uint256 maturity_period;
    uint256 challenge_window;
    bool paused;

    address validator;
    address erc20_DOCK_addr;
    address erc721_DPT_addr;
    address do_checks_addr;

    /*
     * Modifiers
     */
    modifier isValidator() {
        require(msg.sender == validator);
        _;
    }

    modifier isBonded() {
        require(msg.value == bond_amount);
        // Save challenger's bond
        balances[msg.sender].bonded = balances[msg.sender].bonded.add(msg.value);
        _;
    }

    modifier isState(uint64 slot, State state) {
        require(coins[slot].state == state, "Wrong state");
        _;
    }

    struct Balance {
        uint256 bonded;
        uint256 withdrawable;
    }
    mapping (address => Balance) public balances;

    // Each exit can only be challenged by a single challenger at a time
    struct Exit {
        address prevOwner; // previous owner of coin
        address owner;
        uint256 createdAt;
        uint256 bond;
        uint256 prevBlock;
        uint256 exitBlock;
    }
    enum State {
        NOT_EXITING,
        EXITING,
        EXITED
    }

    // Track owners of txs that are pending a response
    struct Challenge {
        address owner;
        uint256 blockNumber;
    }
    mapping (uint64 => ChallengeLib.Challenge[]) private challenges;

    uint256 public numCoins = 0;
    mapping (uint64 => Coin) private coins;
    struct Coin {
        State state;
        address owner; // who owns that nft
        Exit exit;
        uint256 uid;
        uint256 denomination;
        uint256 depositBlock;
    }

    // child chain
    uint256 public childBlockInterval = 1000;
    uint256 public currentBlock = 0;
    struct ChildBlock {
        bytes32 root;
        uint256 createdAt;
    }
    mapping(uint256 => ChildBlock) public childChain;

    constructor () public {
        validator = msg.sender;
    }

    /// @dev called by a Validator to append a Plasma block to the Plasma chain
    /// @param root The transaction root hash of the Plasma block being added
    function submitBlock(uint256 blockNumber, bytes32 root)
        public
        isValidator
    {
        // rounding to next whole `childBlockInterval`
        require(blockNumber >= currentBlock);
        currentBlock = blockNumber;

        childChain[currentBlock] = ChildBlock({
            root: root,
            createdAt: block.timestamp
        });

        emit SubmittedBlock(currentBlock, root, block.timestamp);
    }

    /// @dev Allows anyone to deposit funds into the Plasma chain, called when
    //       contract receives ERC721
    /// @notice Appends a deposit block to the Plasma chain
    ///            identifier allocated by the ERC721 token contract; it is not
    ///            related to `slot`. If the coin is ETH or ERC20 the uid is 0
    /// @param denomination The quantity of a particular coin being deposited
    function deposit(uint256 denomination)
        private
    {
        require(!paused, "Contract is not accepting more deposits!");

        uint64 slot = uint64(bytes8(keccak256(abi.encodePacked(numCoins, msg.sender, block.timestamp, block.number))));
        //mint a new token for the depositor
        DockPlasmaToken(erc721_DPT_addr).mint(msg.sender, slot);

        currentBlock = currentBlock.add(1);
        address from = msg.sender;

        // Update state. Leave `exit` empty
        Coin storage coin = coins[slot];
        coin.uid = slot;
        coin.denomination = denomination;
        coin.depositBlock = currentBlock;
        coin.owner = from;
        coin.state = State.NOT_EXITING;

        childChain[currentBlock] = ChildBlock({
            // save signed transaction hash as root
            // hash for deposit transactions is the hash of its slot
            root: keccak256(abi.encodePacked(slot)),
            createdAt: block.timestamp
        });

        // create a utxo at `slot`
        emit Deposit(
            slot,
            currentBlock,
            denomination,
            from
        );

        numCoins = numCoins.add(1);
    }

    // Approve and Deposit function for 2-step deposits without having to approve the token by the validators
    // Requires first to have called `approve` on the specified ERC20 contract
    function participate(uint256 amount) external {
        require(ERC20(erc20_DOCK_addr).transferFrom(msg.sender, address(this), amount), "Transfer failed");
        deposit(amount);

    }

    /******************** EXIT RELATED ********************/

    function startExit(
        uint64 slot,
        bytes prevTxBytes, bytes exitingTxBytes,
        bytes prevTxInclusionProof, bytes exitingTxInclusionProof,
        bytes signature,
        uint256[2] blocks)
        external
        payable isBonded
        isState(slot, State.NOT_EXITING)
    {
        require(msg.sender == exitingTxBytes.getOwner());
        doInclusionChecks(
            prevTxBytes, exitingTxBytes,
            prevTxInclusionProof, exitingTxInclusionProof,
            signature,
            blocks
        );

        pushExit(slot, prevTxBytes.getOwner(), blocks);
    }

    /// @dev Verifies that consecutive two transaction involving the same coin
    ///      are valid
    /// @notice If exitingTxBytes corresponds to a deposit transaction,
    ///         prevTxBytes cannot have a meaningul value and thus it is ignored.
    /// @param prevTxBytes The RLP-encoded transaction involving a particular
    ///        coin which took place directly before exitingTxBytes
    /// @param exitingTxBytes The RLP-encoded transaction involving a particular
    ///        coin which an exiting owner of the coin claims to be the latest
    /// @param prevTxInclusionProof An inclusion proof of prevTx
    /// @param exitingTxInclusionProof An inclusion proof of exitingTx
    /// @param signature The signature of the exitingTxBytes by the coin
    ///        owner indicated in prevTx
    /// @param blocks An array of two block numbers, at index 0, the block
    ///        containing the prevTx and at index 1, the block containing
    ///        the exitingTx
    function doInclusionChecks(
        bytes prevTxBytes, bytes exitingTxBytes,
        bytes prevTxInclusionProof, bytes exitingTxInclusionProof,
        bytes signature,
        uint256[2] blocks)
        private
        view
    {
        if (blocks[1] % childBlockInterval != 0) {
            DoChecks(do_checks_addr).checkIncludedAndSigned(
                exitingTxBytes,
                exitingTxInclusionProof,
                signature,
                childChain[blocks[1]].root,
                blocks[1]
            );
        } else {
            DoChecks(do_checks_addr).checkBothIncludedAndSigned(
                prevTxBytes, exitingTxBytes, prevTxInclusionProof,
                exitingTxInclusionProof, signature,
                childChain[blocks[0]].root, childChain[blocks[1]].root,
                blocks
            );
        }
    }

    // Needed to bypass stack limit errors
    function pushExit(
        uint64 slot,
        address prevOwner,
        uint256[2] blocks)
        private
    {
        // Create exit
        Coin storage c = coins[slot];
        c.exit = Exit({
            prevOwner: prevOwner,
            owner: msg.sender,
            createdAt: block.timestamp,
            bond: msg.value,
            prevBlock: blocks[0],
            exitBlock: blocks[1]
        });

        // Update coin state
        c.state = State.EXITING;
        emit StartedExit(slot, msg.sender);
    }

    /// @dev Finalizes an exit, i.e. puts the exiting coin into the EXITED
    ///      state which will allow it to be withdrawn, provided the exit has
    ///      matured and has not been successfully challenged
    function finalizeExit(uint64 slot) public {
        Coin storage coin = coins[slot];

        // If a coin is not under exit/challenge, then ignore it
        if (coin.state != State.EXITING)
            return;

        // If an exit is not matured, ignore it
        if ((block.timestamp - coin.exit.createdAt) <= maturity_period)
            return;

        // Check if there are any pending challenges for the coin.
        // `checkPendingChallenges` will also penalize
        // for each challenge that has not been responded to
        bool hasChallenges = checkPendingChallenges(slot);

        if (!hasChallenges) {

            address prevOwner = coin.owner;
            // Update coin's owner
            coin.owner = coin.exit.owner;
            coin.state = State.EXITED;

            DockPlasmaToken(erc721_DPT_addr).transferFrom(prevOwner, coin.owner, slot);
            // Allow the exitor to withdraw their bond
            freeBond(coin.owner);

            emit FinalizedExit(slot, coin.owner);
        } else {
            // Reset coin state since it was challenged
            coin.state = State.NOT_EXITING;
            emit CoinReset(slot, coin.owner);
        }

        delete coins[slot].exit;
    }

    function checkPendingChallenges(uint64 slot) private returns (bool hasChallenges) {
        uint256 length = challenges[slot].length;
        bool slashed;
        for (uint i = 0; i < length; i++) {
            if (challenges[slot][i].txHash != 0x0) {
                // Penalize the exitor and reward the first valid challenger.
                if (!slashed) {
                    slashBond(coins[slot].exit.owner, challenges[slot][i].challenger);
                    slashed = true;
                }
                // Also free the bond of the challenger.
                freeBond(challenges[slot][i].challenger);

                // Challenge resolved, delete it
                delete challenges[slot][i];
                hasChallenges = true;
            }
        }
    }

    /// @dev Iterates through all of the initiated exits and finalizes those
    ///      which have matured without being successfully challenged
    function finalizeExits(uint64[] slots) external {
        uint256 slotsLength = slots.length;
        for (uint256 i = 0; i < slotsLength; i++) {
            finalizeExit(slots[i]);
        }
    }

    function cancelExit(uint64 slot) public {
        require(coins[slot].exit.owner == msg.sender, "Unauthorized user");
        delete coins[slot].exit;
        coins[slot].state = State.NOT_EXITING;
        freeBond(msg.sender);
        emit CoinReset(slot, coins[slot].owner);
    }

    /*
        NOTE :
            removed function cancelExits() so we wont extend block
            gas limit on deployment.
    */

    /// @dev Withdraw a UTXO that has been exited
    /// @param slot The slot of the coin being withdrawn
    function withdraw(uint64 slot) external isState(slot, State.EXITED) {
        require(coins[slot].owner == msg.sender, "You do not own that UTXO");
        uint256 uid = coins[slot].uid;
        uint256 denomination = coins[slot].denomination;

        // Delete the coin that is being withdrawn
        Coin memory c = coins[slot];
        delete coins[slot];

        ERC20(erc20_DOCK_addr).transfer(msg.sender, c.denomination);
        DockPlasmaToken(erc721_DPT_addr).burn(slot);

        numCoins = numCoins.sub(1);

        emit Withdrew(
            msg.sender,
            slot,
            uid,
            denomination
        );

    }

    /******************** CHALLENGES ********************/

    /// @dev Submits proof of a transaction before prevTx as an exit challenge
    /// @notice Exitor has to call respondChallengeBefore and submit a
    ///         transaction before prevTx or prevTx itself.
    /// @param slot The slot corresponding to the coin whose exit is being challenged
    /// @param txBytes The RLP-encoded transaction involving a particular
    ///        coin which an exiting owner of the coin claims to be the latest
    /// @param txInclusionProof An inclusion proof of exitingTx
    /// @param signature The signature of the txBytes by the coin
    ///        owner indicated in prevTx
    /// @param blockNumber The block containing the exitingTx
    function challengeBefore(
        uint64 slot,
        bytes txBytes,
        bytes txInclusionProof,
        bytes signature,
        uint256 blockNumber)
        external
        payable isBonded
        isState(slot, State.EXITING)
    {

        checkBefore(
            slot,
            txBytes,
            blockNumber,
            signature,
            txInclusionProof
        );

        setChallenged(
            slot,
            txBytes.getOwner(),
            blockNumber,
            txBytes.getHash()
        );

    }

    function checkBefore(
        uint64 slot,
        bytes txBytes,
        uint blockNumber,
        bytes signature,
        bytes txInclusionProof
    )
        private
        view
    {
        uint exitPrevBlock = coins[slot].exit.prevBlock;

        DoChecks(do_checks_addr).checkBefore(
            slot,
            txBytes,
            blockNumber,
            exitPrevBlock,
            signature,
            txInclusionProof,
            childChain[blockNumber].root
        );

    }

    /// @dev Submits proof of a later transaction that corresponds to a challenge
    /// @notice Can only be called in the second window of the exit period.
    /// @param slot The slot corresponding to the coin whose exit is being challenged
    /// @param challengingTxHash The hash of the transaction
    ///        corresponding to the challenge we're responding to
    /// @param respondingBlockNumber The block number which included the transaction
    ///        we are responding with
    /// @param respondingTransaction The RLP-encoded transaction involving a particular
    ///        coin which took place directly after challengingTransaction
    /// @param proof An inclusion proof of respondingTransaction
    /// @param signature The signature which proves a direct spend from the challenger
    function respondChallengeBefore(
        uint64 slot,
        bytes32 challengingTxHash,
        uint256 respondingBlockNumber,
        bytes respondingTransaction,
        bytes proof,
        bytes signature
    )
        external
    {
        // Check that the transaction being challenged exists
        require(challenges[slot].contains(challengingTxHash), "Responding to non existing challenge");

        // Get index of challenge in the challenges array
        uint256 index = uint256(challenges[slot].indexOf(challengingTxHash));

        checkResponse(
            slot,
            respondingBlockNumber,
            index,
            respondingTransaction,
            proof,
            signature
        );

        // If the exit was actually challenged and responded, penalize the challenger and award the responder
        slashBond(challenges[slot][index].challenger, msg.sender);

        // Put coin back to the exiting state
        coins[slot].state = State.EXITING;

        challenges[slot].remove(challengingTxHash);
        emit RespondedExitChallenge(slot);
    }

    function checkResponse(
        uint64 slot,
        uint256 respondingBlockNumber,
        uint256 index,
        bytes respondingTransaction,
        bytes proof,
        bytes signature
    )
        private
        view
    {

        DoChecks(do_checks_addr).checkResponse(
            slot,
            respondingBlockNumber,
            coins[slot].exit.exitBlock,
            challenges[slot][index].challengingBlockNumber,
            challenges[slot][index].owner,
            childChain[respondingBlockNumber].root,
            respondingTransaction,
            signature,
            proof
        );

    }

    function challengeBetween(
        uint64 slot,
        uint256 challengingBlockNumber,
        bytes challengingTransaction,
        bytes proof,
        bytes signature
    )
        external
        isState(slot, State.EXITING)
    {

        checkBetween(
            slot,
            challengingBlockNumber,
            challengingTransaction,
            proof,
            signature
        );
        applyPenalties(slot);
    }

    function checkBetween(
        uint64 slot,
        uint256 challengingBlockNumber,
        bytes challengingTransaction,
        bytes proof,
        bytes signature
    )
        private
        view
    {

        DoChecks(do_checks_addr).checkBetween(
            slot,
            coins[slot].exit.exitBlock,
            coins[slot].exit.prevBlock,
            challengingTransaction,
            challengingBlockNumber,
            coins[slot].exit.prevOwner,
            childChain[challengingBlockNumber].root,
            signature,
            proof
        );

    }

    function challengeAfter(
        uint64 slot,
        uint256 challengingBlockNumber,
        bytes challengingTransaction,
        bytes proof,
        bytes signature)
        external
        isState(slot, State.EXITING)
    {
        checkAfter(slot, challengingTransaction, challengingBlockNumber, signature, proof);
        applyPenalties(slot);
    }

    function checkAfter(
        uint64 slot,
        bytes challengingTransaction,
        uint256 challengingBlockNumber,
        bytes proof,
        bytes signature
    )
        private
        view
    {

        DoChecks(do_checks_addr).checkAfter(
            slot,
            challengingTransaction,
            coins[slot].exit.exitBlock,
            coins[slot].exit.owner,
            challengingBlockNumber,
            childChain[challengingBlockNumber].root,
            proof,
            signature
        );
    }

    function applyPenalties(uint64 slot) private {
        // Apply penalties and change state
        slashBond(coins[slot].exit.owner, msg.sender);
        coins[slot].state = State.NOT_EXITING;
        delete coins[slot].exit;
        emit CoinReset(slot, coins[slot].owner);
    }

    /// @param slot The slot of the coin being challenged
    /// @param owner The user claimed to be the true owner of the coin
    function setChallenged(uint64 slot, address owner, uint256 challengingBlockNumber, bytes32 txHash) private {
        // Require that the challenge is in the first half of the challenge window
        require(block.timestamp <= coins[slot].exit.createdAt + challenge_window);

        require(!challenges[slot].contains(txHash),
                "Transaction used for challenge already");

        // Need to save the exiting transaction's owner, to verify
        // that the response is valid
        challenges[slot].push(
            ChallengeLib.Challenge({
                owner: owner,
                challenger: msg.sender,
                txHash: txHash,
                challengingBlockNumber: challengingBlockNumber
            })
        );

        emit ChallengedExit(slot, txHash, challengingBlockNumber);
    }


    /******************** BOND RELATED ********************/

    function freeBond(address from) private {
        balances[from].bonded = balances[from].bonded.sub(bond_amount);
        balances[from].withdrawable = balances[from].withdrawable.add(bond_amount);
        emit FreedBond(from, bond_amount);
    }

    function withdrawBonds() external {
        // Can only withdraw bond if the msg.sender
        uint256 amount = balances[msg.sender].withdrawable;
        balances[msg.sender].withdrawable = 0; // no reentrancy!

        msg.sender.transfer(amount);
        emit WithdrewBonds(msg.sender, amount);
    }

    function slashBond(address from, address to) private {
        balances[from].bonded = balances[from].bonded.sub(bond_amount);
        balances[to].withdrawable = balances[to].withdrawable.add(bond_amount);
        emit SlashedBond(from, to, bond_amount);
    }

    /*********************  Sets ***************************/

    // @dev Called by validator/owner of the contract in order to update
    //      mautrity wainting time and bond.
    // @param amount The amount to update bond.
    // @param _maturity_period The value to update maturity period time.
    // @param _challenge_window The value to update challenge window time.
    function setMaturityAndBond(
        uint256 amount,
        uint256 _maturity_period,
        uint256 _challenge_window
    )
        public
        isValidator
    {
        maturity_period = _maturity_period;
        challenge_window = _challenge_window;
        bond_amount = amount;
    }

    // @dev Called by validator/owner of the contract in order to pause Plasma
    // @param _pause Boolean to update paused to true or false.
    function pause(bool _pause) public isValidator{
        paused = _pause;
    }

    // @dev Called by validator/owner of the contract to link all needed
    //      contracts together.
    // @param _erc20_DOCK_addr The Erc20 deployed address.
    // @param _erc721_DPT_addr The DockPlasmaToken deployed address.
    // @param _do_checks_addr The DoChecks deployed address.
    function setAddresses(
        address _erc20_DOCK_addr,
        address _erc721_DPT_addr,
        address _do_checks_addr
    )
        public
        isValidator
    {
        erc20_DOCK_addr = _erc20_DOCK_addr;
        erc721_DPT_addr = _erc721_DPT_addr;
        do_checks_addr = _do_checks_addr;
    }

    /******************** HELPERS ********************/

    function getMaturityAndBond() public view returns(uint256, uint256, uint256){
        return (maturity_period, challenge_window, bond_amount);
    }

    function getPlasmaCoin(uint64 slot) external view returns(uint256, uint256, uint256, address, State) {
        Coin memory c = coins[slot];
        return (c.uid, c.depositBlock, c.denomination, c.owner, c.state);
    }

    function getChallenge(uint64 slot, bytes32 txHash)
        external
        view
        returns(address, address, bytes32, uint256)
    {
        uint256 index = uint256(challenges[slot].indexOf(txHash));
        ChallengeLib.Challenge memory c = challenges[slot][index];
        return (c.owner, c.challenger, c.txHash, c.challengingBlockNumber);
    }

    function getExit(uint64 slot) external view returns(address, uint256, uint256, State, uint256) {
        Exit memory e = coins[slot].exit;
        return (e.owner, e.prevBlock, e.exitBlock, coins[slot].state, e.createdAt);
    }

}
