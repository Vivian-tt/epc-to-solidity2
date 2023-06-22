pragma solidity ^0.8.0;

contract Auction {

	address payable public beneficiary;
	address payable public highestBidder;
	uint public highestBid;
	uint public BidAmount;
	mapping (address=>int)public BiddingReturns;
	uint public auctionEndTime;
	uint public biddingTime;
	bool  ended;
	event AuctionDeployed();
	event HighestBidIncreased(address highestBidder, uint BidAmount);
	event RefundAmountBid();
	event AuctionEnded();
	constructor(uint auctionEndTime,address beneficiary) { 
		emit AuctionDeployed();
	}

	function bid (uint BidAmount) public payable { 
		emit HighestBidIncreased();
	}

	function withdraw () public returns(bool) {
		emit RefundAmountBid();
	}

	modifier onlybeneficiary (){
		require(msg.sender == beneficiary,'only beneficiary can call this.');
		_;
	}
	function auctionEnd () public onlybeneficiary {
		emit AuctionEnded();
	}

}