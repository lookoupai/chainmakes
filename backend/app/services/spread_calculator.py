"""
价差计算服务
"""
from decimal import Decimal
from typing import Tuple
from datetime import datetime

from app.utils.logger import setup_logger

logger = setup_logger('spread_calculator')


class SpreadCalculator:
    """
    价差计算器
    
    负责计算两个市场之间的涨跌幅差异(价差)
    """
    
    @staticmethod
    def calculate_price_change_percentage(
        current_price: Decimal,
        start_price: Decimal
    ) -> Decimal:
        """
        计算价格变化百分比
        
        Args:
            current_price: 当前价格
            start_price: 起始价格
            
        Returns:
            涨跌幅百分比
        """
        if start_price == 0:
            logger.warning("起始价格为0,无法计算涨跌幅")
            return Decimal('0')
        
        change = (current_price / start_price - 1) * 100
        return change
    
    @staticmethod
    def calculate_spread(
        market1_current: Decimal,
        market1_start: Decimal,
        market2_current: Decimal,
        market2_start: Decimal
    ) -> Decimal:
        """
        计算两个市场之间的价差
        
        公式: (market1_current/market1_start - 1) - (market2_current/market2_start - 1)
        
        Args:
            market1_current: 市场1当前价格
            market1_start: 市场1起始价格
            market2_current: 市场2当前价格
            market2_start: 市场2起始价格
            
        Returns:
            价差百分比
        """
        change1 = SpreadCalculator.calculate_price_change_percentage(
            market1_current, market1_start
        )
        change2 = SpreadCalculator.calculate_price_change_percentage(
            market2_current, market2_start
        )
        
        spread = change1 - change2
        
        logger.debug(
            f"市场1涨跌: {change1:.4f}%, "
            f"市场2涨跌: {change2:.4f}%, "
            f"价差: {spread:.4f}%"
        )
        
        return spread
    
    @staticmethod
    def calculate_spread_from_last_trade(
        current_spread: Decimal,
        last_trade_spread: Decimal
    ) -> Decimal:
        """
        计算相对上次成交的价差变化
        
        Args:
            current_spread: 当前绝对价差
            last_trade_spread: 上次成交时的价差
            
        Returns:
            相对上次成交的价差变化
        """
        return current_spread - last_trade_spread
    
    @staticmethod
    def determine_trading_direction(
        market1_change: Decimal,
        market2_change: Decimal
    ) -> Tuple[str, str]:
        """
        根据涨跌幅确定交易方向
        
        涨幅高的做空,涨幅低的做多
        
        Args:
            market1_change: 市场1涨跌幅
            market2_change: 市场2涨跌幅
            
        Returns:
            (market1_side, market2_side) - 交易方向元组
            可能的值: ('sell', 'buy') 或 ('buy', 'sell')
        """
        if market1_change > market2_change:
            # 市场1涨幅更高,做空市场1,做多市场2
            return ('sell', 'buy')
        else:
            # 市场2涨幅更高,做多市场1,做空市场2
            return ('buy', 'sell')
    
    @staticmethod
    def calculate_position_profit_ratio(
        market1_pnl: Decimal,
        market2_pnl: Decimal,
        total_investment: Decimal
    ) -> Decimal:
        """
        计算仓位盈利比例
        
        Args:
            market1_pnl: 市场1浮盈
            market2_pnl: 市场2浮盈
            total_investment: 总投资额
            
        Returns:
            盈利比例(%)
        """
        if total_investment == 0:
            return Decimal('0')
        
        total_pnl = market1_pnl + market2_pnl
        profit_ratio = (total_pnl / total_investment) * 100
        
        return profit_ratio
    
    @staticmethod
    def should_take_profit_regression(
        current_spread: Decimal,
        first_trade_spread: Decimal,
        profit_ratio_target: Decimal
    ) -> bool:
        """
        判断是否应该回归止盈
        
        Args:
            current_spread: 当前价差
            first_trade_spread: 第一次开仓时的价差
            profit_ratio_target: 目标止盈比例
            
        Returns:
            是否应该止盈
        """
        spread_diff = abs(first_trade_spread - current_spread)
        return spread_diff >= profit_ratio_target
    
    @staticmethod
    def should_take_profit_position(
        total_pnl: Decimal,
        total_investment: Decimal,
        profit_ratio_target: Decimal
    ) -> bool:
        """
        判断是否应该仓位止盈
        
        Args:
            total_pnl: 总浮盈
            total_investment: 总投资额
            profit_ratio_target: 目标止盈比例(%)
            
        Returns:
            是否应该止盈
        """
        if total_investment == 0:
            return False
        
        profit_ratio = (total_pnl / total_investment) * 100
        return profit_ratio >= profit_ratio_target
    
    @staticmethod
    def should_stop_loss(
        total_pnl: Decimal,
        total_investment: Decimal,
        stop_loss_ratio: Decimal
    ) -> bool:
        """
        判断是否应该止损

        Args:
            total_pnl: 总浮盈(负数表示亏损)
            total_investment: 总投资额
            stop_loss_ratio: 止损比例(%)，设置为 0 或负数时禁用止损

        Returns:
            是否应该止损
        """
        # 如果止损比例 <= 0，禁用止损功能
        if stop_loss_ratio <= 0:
            return False

        if total_investment == 0:
            return False

        loss_ratio = abs(total_pnl / total_investment) * 100
        return total_pnl < 0 and loss_ratio >= stop_loss_ratio