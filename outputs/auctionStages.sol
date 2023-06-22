// SPDX-License-Identifier: GPL-3.0
pragma solidity >=0.8.2 <0.9.0;

contract AuctionStages {
    address payable public beneficiary;  //拍卖者
    uint public reservePrice;
    bool public delivery;
    address public owner;

    uint public publicBiddingDeposit;   //公开竞标保证金 （拍卖者发布）,防止拍卖者无故终止拍卖流程
    uint public auctionEndTime;  //拍卖截止时间
    mapping(address => uint) public publicBiddingDepositReturns; //公开竞标保证金退回金钱的地址和金额映射（拍卖成功后，退回给拍卖者）
    bool public auction_started; //拍卖有两个状态一个是开始一个是结束
    uint public auctionDurationMinutes;
    event auctionDepolyed(address beneficiary,uint publicBiddingDeposit,uint auctionEndTime);
    event auctionEnd();
   //初始状态
    constructor(uint _reservePrice, uint _publicBiddingDeposit, uint _auctionDurationMinutes) {

         //实例化一个拍卖标的物
        beneficiary = payable(msg.sender);
        owner = beneficiary;
        reservePrice = _reservePrice;
        delivery = false;
        publicBiddingDeposit = _publicBiddingDeposit;
        publicBiddingDepositReturns[beneficiary]=publicBiddingDeposit;
        auctionEndTime = block.timestamp + (_auctionDurationMinutes * 1 minutes);
        auction_started = true;
        emit auctionDepolyed(beneficiary,publicBiddingDeposit,auctionEndTime);

    }

}