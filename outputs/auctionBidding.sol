// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.2 <0.9.0;

import "./auctionStages.sol";

contract AuctionBidding is AuctionStages {

    address[] bidders;  //存放了所有的竞买者的地址
    uint public highestBid;  //定义最高竞价的价格

    address payable public highestBidder; //定义最高竞价者=买受者
   // event auctionEnd();
    mapping(address => uint) public pendingReturns;
//用来记录每个竞拍者的出价，它的 key 是地址类型的，value 是出价的 uint 类型。在拍卖过程中，每个竞拍者可以调用 bid 函数提交自己的出价，出价会被记录在这个 mapping 中
    uint public endBiddingTime;//竞标的结束时间

    constructor(uint _biddingTime, uint _reservePrice, uint _publicBiddingDeposit, uint _auctionDurationMinutes) AuctionStages(_reservePrice, _publicBiddingDeposit, _auctionDurationMinutes) {
        endBiddingTime = block.timestamp + (_biddingTime * 1 minutes);
    }

    event BidPlaced(address highestBidder, uint amount); //竞标者发布竞价
    event BidingCompleted(address highestBidder, uint highestBid); //竞标结束，选出了最高竞价者
  //  event AuctionCanceled(); //取消了拍卖

    modifier onlyBeneficiary(){
        require(msg.sender == beneficiary,"only beneficiary can call this");
        _;
    }


    function placeBid(uint bidAmount) public payable {
        require(auction_started, "Auction not yet started."); //竞拍需要在拍卖程序开始后
        require(block.timestamp < endBiddingTime, "Bidding has ended.");
        require(bidAmount > reservePrice, "Bid not high enough.");
        require(bidAmount > highestBid, "Bid not high enough.");

    //    require(msg.sender != beneficiary,"The beneficiary cannot bidding");

        bidders.push(msg.sender);

        if (highestBidder != address(0)) {
            uint amount = pendingReturns[msg.sender];
            if (amount>0){
                payable(highestBidder).transfer(highestBid);  //退回给竞标者价格
                pendingReturns[highestBidder] = 0;
            }
        }
        highestBidder = payable(msg.sender);
        highestBid = bidAmount;
        pendingReturns[highestBidder] = highestBid;
        emit BidPlaced(msg.sender, bidAmount);
        //这个过程结束后，只有highestBidder的出价还在池中，其他人的出价都已退回。
    }


    //在竞标过程结束后，选出买受者，并把公开竞标保证金退回给beneficiary
     function selectWinner() public onlyBeneficiary payable{
         require(block.timestamp > endBiddingTime, "Bidding has not ended.");
         require(auction_started,"auction has canceled");//代表拍卖没有取消也没有被结束
         require(highestBidder != address(0), "No bids received.");
        // 竞标成功，将公开竞标保证金退回beneficiary
         payable(beneficiary).transfer(publicBiddingDeposit);
         emit BidingCompleted(highestBidder, highestBid);
    }

    //如果拍卖者无故取消拍卖，则将所有竞买者的出价退回，并将拍卖者的公开竞价保证金全部给所有竞买者作为补偿
      function cancelAuction() public onlyBeneficiary payable {
           require(auction_started,"auction has not start");
        // Split auction deposit among bidders
           uint refundAmount = publicBiddingDeposit / bidders.length;
        // Refund all bidders 检查一下将所有竞买者的出价退回
         for (uint i = 0; i < bidders.length; i++) {
            address payable bidderAddress = payable(bidders[i]);
            pendingReturns[bidderAddress] += refundAmount;
            uint amount= pendingReturns[bidderAddress];
            if (amount >0 ){
                payable(bidderAddress).transfer(amount);
                pendingReturns[bidderAddress] = 0;
            }

        }

        publicBiddingDeposit = 0;
        highestBidder = payable(address(0));
        highestBid = 0;
        auction_started=false;
        emit AuctionStages.auctionEnd();
    }
}
