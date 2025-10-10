"""
模拟交易所测试
"""
import pytest
from app.exchanges.mock_exchange import MockExchange


@pytest.fixture
async def mock_exchange():
    """创建模拟交易所实例"""
    return MockExchange(
        name="Test Mock Exchange",
        api_key="test_api_key",
        api_secret="test_api_secret",
        passphrase="test_passphrase",
        sandbox=True
    )


@pytest.mark.asyncio
async def test_mock_exchange_get_ticker(mock_exchange):
    """测试获取行情数据"""
    symbol = "BTC/USDT"
    ticker = await mock_exchange.get_ticker(symbol)
    
    assert "symbol" in ticker
    assert ticker["symbol"] == symbol
    assert "bid" in ticker
    assert "ask" in ticker
    assert "last" in ticker
    assert "timestamp" in ticker
    assert ticker["bid"] > 0
    assert ticker["ask"] > 0
    assert ticker["last"] > 0
    assert ticker["ask"] > ticker["bid"]  # 卖价应该高于买价


@pytest.mark.asyncio
async def test_mock_exchange_get_orderbook(mock_exchange):
    """测试获取订单簿"""
    symbol = "BTC/USDT"
    orderbook = await mock_exchange.get_orderbook(symbol, limit=10)
    
    assert "symbol" in orderbook
    assert orderbook["symbol"] == symbol
    assert "bids" in orderbook
    assert "asks" in orderbook
    assert "timestamp" in orderbook
    assert len(orderbook["bids"]) > 0
    assert len(orderbook["asks"]) > 0
    
    # 验证订单簿格式
    for bid in orderbook["bids"]:
        assert len(bid) == 2  # [price, amount]
        assert bid[0] > 0
        assert bid[1] > 0
    
    for ask in orderbook["asks"]:
        assert len(ask) == 2  # [price, amount]
        assert ask[0] > 0
        assert ask[1] > 0
    
    # 验证买价排序（从高到低）
    for i in range(len(orderbook["bids"]) - 1):
        assert orderbook["bids"][i][0] >= orderbook["bids"][i+1][0]
    
    # 验证卖价排序（从低到高）
    for i in range(len(orderbook["asks"]) - 1):
        assert orderbook["asks"][i][0] <= orderbook["asks"][i+1][0]


@pytest.mark.asyncio
async def test_mock_exchange_create_market_order(mock_exchange):
    """测试创建市价单"""
    symbol = "BTC/USDT"
    side = "buy"
    amount = 0.001
    
    order = await mock_exchange.create_market_order(symbol, side, amount)
    
    assert "id" in order
    assert order["symbol"] == symbol
    assert order["type"] == "market"
    assert order["side"] == side
    assert order["amount"] == amount
    assert order["filled"] == amount  # 市价单应该完全成交
    assert order["remaining"] == 0
    assert order["status"] == "closed"
    assert "price" in order
    assert order["price"] > 0
    assert "timestamp" in order


@pytest.mark.asyncio
async def test_mock_exchange_create_limit_order(mock_exchange):
    """测试创建限价单"""
    symbol = "BTC/USDT"
    side = "buy"
    amount = 0.001
    price = 50000.0
    
    order = await mock_exchange.create_limit_order(symbol, side, amount, price)
    
    assert "id" in order
    assert order["symbol"] == symbol
    assert order["type"] == "limit"
    assert order["side"] == side
    assert order["amount"] == amount
    assert order["price"] == price
    assert order["status"] in ["open", "closed", "partially_filled"]
    assert "filled" in order
    assert "remaining" in order
    assert "timestamp" in order


@pytest.mark.asyncio
async def test_mock_exchange_cancel_order(mock_exchange):
    """测试取消订单"""
    # 先创建一个订单
    symbol = "BTC/USDT"
    side = "buy"
    amount = 0.001
    price = 50000.0
    
    order = await mock_exchange.create_limit_order(symbol, side, amount, price)
    order_id = order["id"]
    
    # 然后取消订单
    result = await mock_exchange.cancel_order(order_id, symbol)
    
    assert result["id"] == order_id
    assert result["status"] == "canceled"


@pytest.mark.asyncio
async def test_mock_exchange_get_order(mock_exchange):
    """测试获取订单"""
    # 先创建一个订单
    symbol = "BTC/USDT"
    side = "buy"
    amount = 0.001
    
    order = await mock_exchange.create_market_order(symbol, side, amount)
    order_id = order["id"]
    
    # 然后获取订单
    retrieved_order = await mock_exchange.get_order(order_id, symbol)
    
    assert retrieved_order["id"] == order_id
    assert retrieved_order["symbol"] == symbol
    assert retrieved_order["type"] == order["type"]
    assert retrieved_order["side"] == side
    assert retrieved_order["amount"] == amount


@pytest.mark.asyncio
async def test_mock_exchange_get_orders(mock_exchange):
    """测试获取订单列表"""
    symbol = "BTC/USDT"
    
    # 创建几个订单
    await mock_exchange.create_market_order(symbol, "buy", 0.001)
    await mock_exchange.create_market_order(symbol, "sell", 0.002)
    await mock_exchange.create_limit_order(symbol, "buy", 0.001, 50000.0)
    
    # 获取订单列表
    orders = await mock_exchange.get_orders(symbol, limit=10)
    
    assert isinstance(orders, list)
    assert len(orders) >= 3
    
    for order in orders:
        assert "id" in order
        assert "symbol" in order
        assert "type" in order
        assert "side" in order
        assert "amount" in order


@pytest.mark.asyncio
async def test_mock_exchange_get_open_orders(mock_exchange):
    """测试获取未成交订单"""
    symbol = "BTC/USDT"
    
    # 创建一个限价单（可能未成交）
    await mock_exchange.create_limit_order(symbol, "buy", 0.001, 30000.0)  # 价格很低，不会成交
    
    # 获取未成交订单
    open_orders = await mock_exchange.get_open_orders(symbol)
    
    assert isinstance(open_orders, list)
    
    for order in open_orders:
        assert order["status"] in ["open", "partially_filled"]


@pytest.mark.asyncio
async def test_mock_exchange_get_balance(mock_exchange):
    """测试获取账户余额"""
    balance = await mock_exchange.get_balance()
    
    assert isinstance(balance, dict)
    assert "USD" in balance
    assert "BTC" in balance
    assert "free" in balance["USD"]
    assert "used" in balance["USD"]
    assert "total" in balance["USD"]
    assert balance["USD"]["free"] >= 0
    assert balance["USD"]["used"] >= 0
    assert balance["USD"]["total"] >= 0
    assert balance["USD"]["total"] == balance["USD"]["free"] + balance["USD"]["used"]


@pytest.mark.asyncio
async def test_mock_exchange_get_position(mock_exchange):
    """测试获取持仓"""
    symbol = "BTC/USDT"
    
    # 先创建一些交易来产生持仓
    await mock_exchange.create_market_order(symbol, "buy", 0.001)
    
    position = await mock_exchange.get_position(symbol)
    
    if position is not None:  # 可能没有持仓
        assert "symbol" in position
        assert position["symbol"] == symbol
        assert "side" in position
        assert "size" in position
        assert "entry_price" in position
        assert "mark_price" in position
        assert "unrealized_pnl" in position
        assert "percentage" in position


@pytest.mark.asyncio
async def test_mock_exchange_get_all_positions(mock_exchange):
    """测试获取所有持仓"""
    # 先创建一些交易
    await mock_exchange.create_market_order("BTC/USDT", "buy", 0.001)
    await mock_exchange.create_market_order("ETH/USDT", "buy", 0.01)
    
    positions = await mock_exchange.get_all_positions()
    
    assert isinstance(positions, list)
    
    for position in positions:
        assert "symbol" in position
        assert "side" in position
        assert "size" in position
        assert "entry_price" in position
        assert "mark_price" in position
        assert "unrealized_pnl" in position
        assert "percentage" in position


@pytest.mark.asyncio
async def test_mock_exchange_close_position(mock_exchange):
    """测试平仓"""
    symbol = "BTC/USDT"
    
    # 先创建一个持仓
    await mock_exchange.create_market_order(symbol, "buy", 0.001)
    
    # 然后平仓
    result = await mock_exchange.close_position(symbol)
    
    assert result is True  # 平仓成功
    
    # 验证持仓已平掉
    position = await mock_exchange.get_position(symbol)
    assert position is None or position["size"] == 0


@pytest.mark.asyncio
async def test_mock_exchange_get_symbols(mock_exchange):
    """测试获取交易对列表"""
    symbols = await mock_exchange.get_symbols()
    
    assert isinstance(symbols, list)
    assert len(symbols) > 0
    assert "BTC/USDT" in symbols
    assert "ETH/USDT" in symbols


@pytest.mark.asyncio
async def test_mock_exchange_get_fees(mock_exchange):
    """测试获取手续费"""
    symbol = "BTC/USDT"
    
    fees = await mock_exchange.get_fees(symbol)
    
    assert isinstance(fees, dict)
    assert "maker" in fees
    assert "taker" in fees
    assert fees["maker"] >= 0
    assert fees["taker"] >= 0


@pytest.mark.asyncio
async def test_mock_exchange_invalid_symbol(mock_exchange):
    """测试无效交易对"""
    invalid_symbol = "INVALID/PAIR"
    
    # 测试获取无效交易对的行情
    with pytest.raises(Exception):
        await mock_exchange.get_ticker(invalid_symbol)
    
    # 测试创建无效交易对的订单
    with pytest.raises(Exception):
        await mock_exchange.create_market_order(invalid_symbol, "buy", 0.001)


@pytest.mark.asyncio
async def test_mock_exchange_invalid_order(mock_exchange):
    """测试无效订单"""
    symbol = "BTC/USDT"
    
    # 测试取消不存在的订单
    with pytest.raises(Exception):
        await mock_exchange.cancel_order("invalid_order_id", symbol)
    
    # 测试获取不存在的订单
    with pytest.raises(Exception):
        await mock_exchange.get_order("invalid_order_id", symbol)