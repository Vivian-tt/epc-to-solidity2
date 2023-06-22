// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.7.0 <0.9.0;
contract Auction{
        address payable public beneficiary;
        uint public auctionEndTime;
        address payable public highestBidder;
        uint public highestBid;
	    uint public biddingTime;
	    uint public BidAmount;
        mapping(address => uint) public pendingReturns;
        bool ended;
	    event AuctionDeployed();
	    event HighestBidIncreased(address bidder, uint BidAmount);
	    event AuctionEnded(address winner,uint BidAmount);
	    event RefundAmountBid();
        constructor(uint _biddingTime,address payable _beneficiary) {
	         beneficiary = _beneficiary;
             auctionEndTime = block.timestamp + (_biddingTime * 1 minutes);
			 emit AuctionDeployed();
        }
        modifier onlyBeneficiary(){
	        require(msg.sender == beneficiary,"only beneficiary can call this.");
	         _;
        }
	    function bid(uint bidAmount) public payable {
			require(block.timestamp <= auctionEndTime, "Auction already ended.");
		    require(BidAmount>highestBid,"There already is a higher bid");
			BidAmount = bidAmount;
            if(highestBid != 0){
   		    	pendingReturns[highestBidder] +=  highestBid;
  		    }
		    highestBidder =payable(msg.sender);
		    highestBid = BidAmount;
		    emit HighestBidIncreased(msg.sender,BidAmount);
	    }
	    function withdraw() public returns(bool){
		    uint amount = pendingReturns[msg.sender];
		    if(amount >0){
			    if(!payable(msg.sender).send(amount)){
				    pendingReturns[msg.sender] =0;
				    emit RefundAmountBid();
				    return false;
			    }
		    }
		    return true;
	    }
	    function auctionEnd() public onlyBeneficiary{
		    require(block.timestamp >= auctionEndTime ,"Auction not yet ended.");
		    require(ended,"Auctionend has already been called.");
		    ended = true;
		    emit AuctionEnded(highestBidder ,highestBid);
		    beneficiary.transfer(highestBid);
		}
}