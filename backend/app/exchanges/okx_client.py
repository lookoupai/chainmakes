"""
OKX 交易所 API 客户端
文档: https://www.okx.com/docs-v5/zh/
"""
import hmac
import base64
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import httpx
from app.utils.logger import setup_logger

logger = setup_logger('okx_client')


class OKXClient:
    """OKX 交易所 API 客户端"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str,
        is_demo: bool = True  # 默认使用模拟盘
    ):
        """
        初始化 OKX 客户端

        Args:
            api_key: API Key
            api_secret: API Secret
            passphrase: API Passphrase
            is_demo: 是否使用模拟盘 (默认 True)
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.is_demo = is_demo

        # API 端点
        if is_demo:
            self.base_url = "https://www.okx.com"  # 模拟盘使用相同端点,通过 header 区分
        else:
            self.base_url = "https://www.okx.com"

        self.client = httpx.AsyncClient(timeout=30.0)

    def _generate_signature(
        self, timestamp: str, method: str, request_path: str, body: str = ""
    ) -> str:
        """
        生成请求签名

        Args:
            timestamp: 时间戳
            method: HTTP 方法
            request_path: 请求路径
            body: 请求体

        Returns:
            签名字符串
        """
        # 签名规则: timestamp + method + requestPath + body
        message = timestamp + method.upper() + request_path + body
        mac = hmac.new(
            bytes(self.api_secret, encoding="utf8"),
            bytes(message, encoding="utf-8"),
            digestmod="sha256",
        )
        signature = base64.b64encode(mac.digest()).decode()
        return signature

    def _get_headers(
        self, method: str, request_path: str, body: str = ""
    ) -> Dict[str, str]:
        """
        生成请求头

        Args:
            method: HTTP 方法
            request_path: 请求路径
            body: 请求体

        Returns:
            请求头字典
        """
        timestamp = datetime.utcnow().isoformat(timespec="milliseconds") + "Z"
        signature = self._generate_signature(timestamp, method, request_path, body)

        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }

        # 模拟盘标识
        if self.is_demo:
            headers["x-simulated-trading"] = "1"

        return headers

    async def _request(
        self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            params: 查询参数
            data: 请求体数据

        Returns:
            响应数据

        Raises:
            Exception: 请求失败时抛出异常
        """
        url = self.base_url + endpoint
        body = json.dumps(data) if data else ""
        headers = self._get_headers(method, endpoint, body)

        try:
            if method.upper() == "GET":
                response = await self.client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await self.client.post(url, headers=headers, json=data)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            response.raise_for_status()
            result = response.json()

            # 检查 OKX API 返回的状态码
            if result.get("code") != "0":
                error_msg = result.get("msg", "未知错误")
                logger.error(f"OKX API 错误: {error_msg}, 完整响应: {result}")
                raise Exception(f"OKX API 错误: {error_msg}")

            return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP 请求失败: {str(e)}")
            raise Exception(f"HTTP 请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"请求异常: {str(e)}")
            raise

    # ==================== 行情数据 API ====================

    async def get_ticker(self, inst_id: str) -> Dict[str, Any]:
        """
        获取单个产品行情数据

        Args:
            inst_id: 产品ID (如 BTC-USDT)

        Returns:
            行情数据
        """
        endpoint = "/api/v5/market/ticker"
        params = {"instId": inst_id}
        result = await self._request("GET", endpoint, params=params)
        return result["data"][0] if result.get("data") else {}

    async def get_tickers(self, inst_type: str = "SPOT") -> List[Dict[str, Any]]:
        """
        获取所有产品行情数据

        Args:
            inst_type: 产品类型 (SPOT, SWAP, FUTURES, OPTION)

        Returns:
            行情数据列表
        """
        endpoint = "/api/v5/market/tickers"
        params = {"instType": inst_type}
        result = await self._request("GET", endpoint, params=params)
        return result.get("data", [])

    # ==================== 账户 API ====================

    async def get_account_balance(self, ccy: Optional[str] = None) -> Dict[str, Any]:
        """
        获取账户余额

        Args:
            ccy: 币种 (如 USDT, 为空则返回所有)

        Returns:
            账户余额数据
        """
        endpoint = "/api/v5/account/balance"
        params = {"ccy": ccy} if ccy else {}
        result = await self._request("GET", endpoint, params=params)
        return result.get("data", [])[0] if result.get("data") else {}

    async def get_positions(
        self, inst_type: Optional[str] = None, inst_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取持仓信息

        Args:
            inst_type: 产品类型
            inst_id: 产品ID

        Returns:
            持仓列表
        """
        endpoint = "/api/v5/account/positions"
        params = {}
        if inst_type:
            params["instType"] = inst_type
        if inst_id:
            params["instId"] = inst_id

        result = await self._request("GET", endpoint, params=params)
        return result.get("data", [])

    # ==================== 交易 API ====================

    async def place_order(
        self,
        inst_id: str,
        td_mode: str,  # 交易模式: cash(非保证金), cross(全仓), isolated(逐仓)
        side: str,  # 订单方向: buy, sell
        ord_type: str,  # 订单类型: market, limit, post_only, fok, ioc
        sz: str,  # 数量
        px: Optional[str] = None,  # 价格 (限价单必填)
        pos_side: Optional[str] = None,  # 持仓方向: long, short (双向持仓必填)
        ccy: Optional[str] = None,  # 保证金币种
        cl_ord_id: Optional[str] = None,  # 客户自定义订单ID
    ) -> Dict[str, Any]:
        """
        下单

        Args:
            inst_id: 产品ID
            td_mode: 交易模式
            side: 订单方向
            ord_type: 订单类型
            sz: 数量
            px: 价格
            pos_side: 持仓方向
            ccy: 保证金币种
            cl_ord_id: 客户自定义订单ID

        Returns:
            订单信息
        """
        endpoint = "/api/v5/trade/order"
        data = {
            "instId": inst_id,
            "tdMode": td_mode,
            "side": side,
            "ordType": ord_type,
            "sz": sz,
        }

        if px:
            data["px"] = px
        if pos_side:
            data["posSide"] = pos_side
        if ccy:
            data["ccy"] = ccy
        if cl_ord_id:
            data["clOrdId"] = cl_ord_id

        result = await self._request("POST", endpoint, data=data)
        return result.get("data", [])[0] if result.get("data") else {}

    async def cancel_order(
        self, inst_id: str, ord_id: Optional[str] = None, cl_ord_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        撤单

        Args:
            inst_id: 产品ID
            ord_id: 订单ID
            cl_ord_id: 客户自定义订单ID

        Returns:
            撤单结果
        """
        endpoint = "/api/v5/trade/cancel-order"
        data = {"instId": inst_id}

        if ord_id:
            data["ordId"] = ord_id
        elif cl_ord_id:
            data["clOrdId"] = cl_ord_id
        else:
            raise ValueError("必须提供 ord_id 或 cl_ord_id")

        result = await self._request("POST", endpoint, data=data)
        return result.get("data", [])[0] if result.get("data") else {}

    async def get_order_detail(
        self, inst_id: str, ord_id: Optional[str] = None, cl_ord_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取订单详情

        Args:
            inst_id: 产品ID
            ord_id: 订单ID
            cl_ord_id: 客户自定义订单ID

        Returns:
            订单详情
        """
        endpoint = "/api/v5/trade/order"
        params = {"instId": inst_id}

        if ord_id:
            params["ordId"] = ord_id
        elif cl_ord_id:
            params["clOrdId"] = cl_ord_id
        else:
            raise ValueError("必须提供 ord_id 或 cl_ord_id")

        result = await self._request("GET", endpoint, params=params)
        return result.get("data", [])[0] if result.get("data") else {}

    async def close_position(
        self,
        inst_id: str,
        mgnMode: str,  # 保证金模式: cross, isolated
        pos_side: Optional[str] = None,  # 持仓方向: long, short
        ccy: Optional[str] = None,  # 保证金币种
    ) -> Dict[str, Any]:
        """
        市价平仓

        Args:
            inst_id: 产品ID
            mgnMode: 保证金模式
            pos_side: 持仓方向
            ccy: 保证金币种

        Returns:
            平仓结果
        """
        endpoint = "/api/v5/trade/close-position"
        data = {
            "instId": inst_id,
            "mgnMode": mgnMode,
        }

        if pos_side:
            data["posSide"] = pos_side
        if ccy:
            data["ccy"] = ccy

        result = await self._request("POST", endpoint, data=data)
        return result.get("data", [])[0] if result.get("data") else {}

    # ==================== 工具方法 ====================

    async def test_connection(self) -> bool:
        """
        测试连接是否正常

        Returns:
            连接是否成功
        """
        try:
            # 获取服务器时间
            endpoint = "/api/v5/public/time"
            await self._request("GET", endpoint)
            logger.info("OKX API 连接测试成功")
            return True
        except Exception as e:
            logger.error(f"OKX API 连接测试失败: {str(e)}")
            return False

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()
