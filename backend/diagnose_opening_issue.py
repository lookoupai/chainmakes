# -*- coding: utf-8 -*-
"""
诊断机器人未开仓问题
"""
import sqlite3
import json
from decimal import Decimal
import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("交易机器人开仓问题诊断")
print("=" * 80)

conn = sqlite3.connect('trading_bot.db')
cursor = conn.cursor()

# 获取正在运行的机器人
cursor.execute('''
    SELECT id, bot_name, market1_symbol, market2_symbol, 
           investment_per_order, dca_config, current_dca_count,
           last_trade_spread, first_trade_spread
    FROM bot_instances 
    WHERE status = 'running'
''')

running_bots = cursor.fetchall()

if not running_bots:
    print("\n❌ 没有正在运行的机器人！")
    conn.close()
    exit()

for bot in running_bots:
    bot_id = bot[0]
    bot_name = bot[1]
    market1 = bot[2]
    market2 = bot[3]
    investment = bot[4]
    dca_config = json.loads(bot[5])
    current_dca = bot[6]
    last_trade_spread = bot[7]
    
    print(f"\n{'=' * 80}")
    print(f"机器人: {bot_name} (ID: {bot_id})")
    print(f"{'=' * 80}")
    print(f"市场1: {market1}")
    print(f"市场2: {market2}")
    print(f"投资金额: {investment} USDT")
    print(f"当前DCA次数: {current_dca}")
    print(f"上次交易价差: {last_trade_spread}")
    
    # 获取最近的价差
    cursor.execute('''
        SELECT spread_percentage, recorded_at
        FROM spread_history
        WHERE bot_instance_id = ?
        ORDER BY recorded_at DESC
        LIMIT 1
    ''', (bot_id,))
    
    latest_spread = cursor.fetchone()
    
    if latest_spread:
        current_spread = float(latest_spread[0])
        print(f"\n当前价差: {current_spread:.4f}%")
        print(f"记录时间: {latest_spread[1]}")
        
        # 分析开仓条件
        print(f"\n{'─' * 80}")
        print("开仓条件分析:")
        print(f"{'─' * 80}")
        
        # 检查DCA配置
        if current_dca >= len(dca_config):
            print(f"[X] 问题1: 已达到最大DCA次数 ({current_dca}/{len(dca_config)})")
        else:
            dca_level = current_dca
            target_config = dca_config[dca_level]
            target_spread = target_config['spread']
            multiplier = target_config['multiplier']
            
            print(f"[OK] DCA等级: {dca_level + 1}/{len(dca_config)}")
            print(f"[OK] 目标价差阈值: {target_spread}%")
            print(f"[OK] 倍投系数: {multiplier}x")
            
            # 计算实际投资金额
            actual_investment = investment * multiplier
            print(f"[OK] 本次投资金额: {actual_investment} USDT")
            
            # 检查开仓条件
            print(f"\n开仓条件判断:")
            
            if last_trade_spread is None:
                # 首次开仓
                print(f"  模式: 首次开仓")
                print(f"  需要: |当前价差| >= {target_spread}%")
                print(f"  实际: |{current_spread:.4f}%| = {abs(current_spread):.4f}%")
                
                if abs(current_spread) >= target_spread:
                    print(f"  [YES] 满足开仓条件！")
                    print(f"\n[!!!] 机器人应该开仓但未开仓，可能的原因：")
                    print(f"     1. 交易所API连接问题")
                    print(f"     2. 账户余额不足 (需要至少 {actual_investment} USDT)")
                    print(f"     3. 最小下单数量限制")
                    print(f"     4. 代码执行异常（检查日志）")
                else:
                    print(f"  [NO] 未满足开仓条件")
                    print(f"     当前价差 {abs(current_spread):.4f}% < 目标 {target_spread}%")
                    print(f"     还需要 {target_spread - abs(current_spread):.4f}% 的价差")
            else:
                # 加仓模式
                print(f"  模式: 加仓 (第 {current_dca + 1} 次)")
                print(f"  上次价差: {last_trade_spread:.4f}%")
                spread_diff = abs(current_spread - last_trade_spread)
                print(f"  需要: |当前价差 - 上次价差| >= {target_spread}%")
                print(f"  实际: |{current_spread:.4f}% - {last_trade_spread:.4f}%| = {spread_diff:.4f}%")
                
                if spread_diff >= target_spread:
                    print(f"  [YES] 满足加仓条件！")
                    print(f"\n[!!!] 机器人应该加仓但未加仓，可能的原因：")
                    print(f"     1. 交易所API连接问题")
                    print(f"     2. 账户余额不足 (需要至少 {actual_investment} USDT)")
                    print(f"     3. 最小下单数量限制")
                    print(f"     4. 代码执行异常（检查日志）")
                else:
                    print(f"  [NO] 未满足加仓条件")
                    print(f"     价差变化 {spread_diff:.4f}% < 目标 {target_spread}%")
                    print(f"     还需要 {target_spread - spread_diff:.4f}% 的价差变化")
    else:
        print("\n[X] 没有价差历史记录，机器人可能未正常运行")
    
    print(f"\n{'=' * 80}\n")

conn.close()

print("\n建议的检查步骤:")
print("1. 检查 logs/app.log 中的详细错误信息")
print("2. 确认交易所API配置正确 (backend/.env)")
print("3. 检查交易所账户余额是否足够")
print("4. 验证网络代理设置是否正确")
print("5. 查看最小交易数量限制")