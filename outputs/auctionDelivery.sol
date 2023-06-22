// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.2 <0.9.0;

import "./auctionBidding.sol";
import "./auctionStages.sol";

contract AuctionDelivery is AuctionStages,AuctionBidding {

    uint public transactionDeposit;  //交易保证金
    event Deliver(address highestBidder, bool delivery);
    event ConfirmDelivery(address highestBidder, address owner);

   constructor(uint _transactionDeposit,
    uint _reservePrice, uint _publicBiddingDeposit, uint _auctionDurationMinutes
    ,uint _biddingTime
    )
    AuctionBidding(_biddingTime,_reservePrice,_publicBiddingDeposit,_auctionDurationMinutes)
    {
        transactionDeposit = _transactionDeposit;

    }


     modifier onlyHighestBidder(){
        require(msg.sender == highestBidder,"only beneficiary can call this");
        _;
    }

    function deliver() public onlyBeneficiary  {

        require(!auction_started); //拍卖还没结束
        require(highestBidder != address(0), "Auction is not ended or no bids were made");
        require(delivery == false );
        delivery = true;
        emit Deliver(highestBidder, delivery);
    }

    function confirmDelivery() public onlyHighestBidder {
        require(delivery == true, "Item not yet delivered");
        payable(beneficiary).transfer(transactionDeposit);
        payable(beneficiary).transfer(highestBid);
        owner = highestBidder;
        emit ConfirmDelivery(highestBidder, owner);
        emit auctionEnd();
    }


}
