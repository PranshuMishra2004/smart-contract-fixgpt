// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract VulnerableAuth {
    address public owner;
    address public beneficiary;

    constructor() {
        owner = msg.sender;
        beneficiary = msg.sender;
    }

    function changeBeneficiary(
        address newBeneficiary
    ) external {
        require(
            tx.origin == owner,
            "Not owner"
        );

        require(
            newBeneficiary != address(0),
            "Invalid beneficiary"
        );

        beneficiary = newBeneficiary;
    }
}