// Copyright Loom Network 2018 - All rights reserved, Dual licensed on GPLV3
// Learn more about Loom DappChains at https://loomx.io
// All derivitive works of this code must incluse this copyright header on every file

pragma solidity ^0.4.24;


import "./Transaction.sol";
import "./SparseMerkleTree.sol";
import "./ECVerify.sol";


contract DoChecks {

    uint256 public childBlockInterval = 1000;
    SparseMerkleTree smt;

    constructor() public {
        smt = new SparseMerkleTree();
    }

    using Transaction for bytes;
    using ECVerify for bytes32;

    /******************** PROOF CHECKING ********************/

    function checkIncludedAndSigned(
        bytes exitingTxBytes,
        bytes exitingTxInclusionProof,
        bytes signature,
        bytes32 blockRoot,
        uint256 blk)
        public
        view
    {
        Transaction.TX memory txData = exitingTxBytes.getTx();

        // Deposit transactions need to be signed by their owners
        // e.g. Alice signs a transaction to Alice
        require(txData.hash.ecverify(signature, txData.owner), "Invalid signature");
        checkTxIncluded(txData.slot, txData.hash, blockRoot, blk, exitingTxInclusionProof);
    }

    function checkBothIncludedAndSigned(
        bytes prevTxBytes, bytes exitingTxBytes,
        bytes prevTxInclusionProof, bytes exitingTxInclusionProof,
        bytes signature,
        bytes32 block0root, bytes32 block1root,
        uint256[2] blocks)
        public
        view
    {
        require(blocks[0] < blocks[1]);

        Transaction.TX memory exitingTxData = exitingTxBytes.getTx();
        Transaction.TX memory prevTxData = prevTxBytes.getTx();

        // Both transactions need to be referring to the same slot
        require(exitingTxData.slot == prevTxData.slot);

        // The exiting transaction must be signed by the previous transaciton's owner
        require(exitingTxData.hash.ecverify(signature, prevTxData.owner), "Invalid signature");

        // Both transactions must be included in their respective blocks
        checkTxIncluded(prevTxData.slot, prevTxData.hash, block0root, blocks[0], prevTxInclusionProof);
        checkTxIncluded(exitingTxData.slot, exitingTxData.hash, block1root, blocks[1], exitingTxInclusionProof);
    }

    function checkTxIncluded(
        uint64 slot,
        bytes32 txHash,
        bytes32 root,
        uint256 blockNumber,
        bytes proof
    )
        public
        view
    {

        if (blockNumber % childBlockInterval != 0) {
            // Check against block root for deposit block numbers
            require(txHash == root);
        } else {
            // Check against merkle tree for all other block numbers
            require(
                checkMembership(
                    txHash,
                    root,
                    slot,
                    proof
            ),
            "Tx not included in claimed block"
            );
        }
    }

    /******************** CHALLENGES ********************/

    // Must challenge with a tx in between
    function checkBefore(
        uint64 slot,
        bytes txBytes,
        uint blockNumber,
        uint exitPrevBlock,
        bytes signature,
        bytes proof,
        bytes32 root

    )
        public
        view
    {
        require(
            blockNumber <= exitPrevBlock,
            "Tx should be before the exit's parent block"
        );

        Transaction.TX memory txData = txBytes.getTx();
        require(txData.hash.recover(signature) != address(0x0), "Invalid signature");
        require(txData.slot == slot, "Tx is referencing another slot");
        checkTxIncluded(slot, txData.hash, root, blockNumber, proof);
    }

    function checkResponse(
        uint64 slot,
        uint256 blockNumber,
        uint256 exitBlock,
        uint256 challengingBlockNumber,
        address challengeOwner,
        bytes32 root,
        bytes txBytes,
        bytes signature,
        bytes proof
    )
        public
        view
    {
        Transaction.TX memory txData = txBytes.getTx();
        require(txData.hash.ecverify(signature, challengeOwner), "Invalid signature");
        require(txData.slot == slot, "Tx is referencing another slot");
        require(blockNumber > challengingBlockNumber, "Must be after the chalenge");
        require(blockNumber <= exitBlock, "Cannot respond with a tx after the exit");
        checkTxIncluded(txData.slot, txData.hash, root, blockNumber, proof);
    }

    function checkBetween(
        uint64 slot,
        uint256 exitBlock,
        uint256 prevBlock,
        bytes txBytes,
        uint blockNumber,
        address prevOwner,
        bytes32 root,
        bytes signature,
        bytes proof
    )
        public
        view
    {
        require(
            exitBlock > blockNumber &&
            prevBlock < blockNumber,
            "Tx should be between the exit's blocks"
        );

        Transaction.TX memory txData = txBytes.getTx();
        require(txData.hash.ecverify(signature, prevOwner), "Invalid signature");
        require(txData.slot == slot, "Tx is referencing another slot");
        checkTxIncluded(slot, txData.hash, root, blockNumber, proof);
    }

    function checkAfter(
        uint64 slot,
        bytes txBytes,
        uint exitBlockNumber,
        address exitOwner,
        uint blockNumber,
        bytes32 root,
        bytes signature,
        bytes proof
    )
        public
        view
    {

        require(
            exitBlockNumber < blockNumber,
            "Tx should be after the exitBlock"
        );

        Transaction.TX memory txData = txBytes.getTx();
        require(txData.hash.ecverify(signature, exitOwner), "Invalid signature");
        require(txData.slot == slot, "Tx is referencing another slot");
        require(txData.prevBlock == exitBlockNumber, "Not a direct spend");
        checkTxIncluded(slot, txData.hash, root, blockNumber, proof);
    }

    /******************** HELPERS ********************/

    function checkMembership(
        bytes32 txHash,
        bytes32 root,
        uint64 slot,
        bytes proof) public view returns (bool)
    {
        return smt.checkMembership(
            txHash,
            root,
            slot,
            proof);
    }

}
