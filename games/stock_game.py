import tkinter as tk
from tkinter import ttk
import random
import time
import threading
from datetime import datetime


class Stock:
    """股票类"""
    def __init__(self, code, name, industry, base_price, risk_level, trend_bias):
        self.code = code          # 股票代码
        self.name = name          # 股票名称
        self.industry = industry  # 所属行业
        self.price = base_price   # 当前价格
        self.base_price = base_price  # 基准价格（用于均值回归）
        self.risk_level = risk_level  # 风险等级 1-5
        self.trend_bias = trend_bias  # 趋势偏好（正=倾向于上涨，负=倾向于下跌）
        self.volatility = risk_level * 0.3  # 基础波动率
        self.price_history = [base_price]  # 价格历史
        self.consecutive_up = 0   # 连续上涨天数
        self.consecutive_down = 0  # 连续下跌天数
        self.market_cycle = 0     # 市场周期（正=牛市，负=熊市）
        self.last_change = 0      # 上次变化率
        self.shares = 0           # 持有股数
        self.total_cost = 0       # 总成本


class StockGame:
    def __init__(self, root):
        self.root = root
        self.root.title("股票大冒险 Stock Rush")
        self.root.geometry("1000x1000")
        self.root.minsize(900, 900)
        self.root.configure(bg="#1a1a2e")

        # 游戏状态
        self.cash = 10000         # 初始资金 - 已减少
        self.day = 1
        self.is_running = False
        self.volatility_level = 3
        self.selected_stock_index = 0
        self.game_seconds = 0  # 游戏已运行秒数

        # 卖出冷却时间
        self.sell_cooldown = 0        # 卖出冷却剩余秒数
        self.sell_cooldown_max = 10  # 冷却时间10秒
        self.last_buy_time = 0       # 上次购买时间

        # 杠杆系统 - 扩展为多倍率
        self.leverage = 1            # 当前杠杆倍数
        self.leverage_options = [1, 2, 3, 5, 10]  # 杠杆选项
        self.leverage_index = 0       # 当前选项索引
        self.leverage_cost = 500     # 杠杆使用费
        self.leverage_available = True

        # 彩票系统 - 已移除冷却限制
        self.lottery_cost = 100      # 彩票价格
        self.lottery_last_result = ""  # 上次彩票结果

        # 自动打工机系统
        self.work_level = 1          # 打工等级
        self.work_income = 10        # 每次收入
        self.work_upgrade_cost = 200 # 升级费用
        self.auto_work_count = 0      # 自动打工机数量
        self.auto_work_cost = 500    # 自动打工机价格

        # 消费系统
        self.vip_level = 0           # VIP等级
        self.vip_cost = 1000        # VIP升级费用
        self.car_level = 0           # 车辆等级
        self.car_cost = 2000         # 车辆价格
        self.house_level = 0         # 房产等级
        self.house_cost = 5000       # 房产价格

        # 初始化多只股票
        self.stocks = self.init_stocks()

        # 市场整体状态
        self.market_sentiment = 0  # 市场情绪 -1到1
        self.market_cycle_days = 0 # 市场周期持续天数

        self.setup_ui()
        self.start_game()

    def init_stocks(self):
        """初始化多只股票"""
        return [
            # 股票代码, 名称, 行业, 基准价, 风险等级, 趋势偏好
            Stock("SH600519", "贵州茅台", "白酒", 1800, 2, 0.1),
            Stock("SH000001", "上证指数", "大盘指数", 3200, 3, 0.05),
            Stock("SZ000858", "五粮液", "白酒", 150, 2, 0.08),
            Stock("SH600036", "招商银行", "银行", 35, 2, 0.05),
            Stock("SZ300750", "宁德时代", "新能源", 200, 4, 0.15),
            Stock("SH601318", "中国平安", "保险", 45, 3, 0.02),
            Stock("SZ002475", "立讯精密", "电子", 35, 4, 0.1),
            Stock("SH600900", "长江电力", "电力", 22, 1, 0.03),
            Stock("SH688981", "中芯国际", "芯片", 45, 5, 0.12),
            Stock("SZ000002", "万科A", "房地产", 8, 4, -0.05),
            # 比特币 - 极高风险
            Stock("BTC", "比特币", "加密货币", 50000, 5, 0.2),
        ]

    def setup_ui(self):
        # 标题
        title_label = tk.Label(
            self.root,
            text="股票大冒险",
            font=("Microsoft YaHei", 24, "bold"),
            bg="#1a1a2e",
            fg="#eaeaea"
        )
        title_label.pack(pady=10)

        # 股票选择栏
        stock_select_frame = tk.Frame(self.root, bg="#16213e", padx=20, pady=5)
        stock_select_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(stock_select_frame, text="选择股票:",
                font=("Microsoft YaHei", 12), bg="#16213e", fg="#eaeaea").pack(side=tk.LEFT)

        self.stock_buttons = []
        btn_frame = tk.Frame(stock_select_frame, bg="#16213e")
        btn_frame.pack(side=tk.LEFT, padx=10)

        for i, stock in enumerate(self.stocks):
            btn = tk.Button(
                btn_frame,
                text=f"{stock.name[:4]}",
                font=("Microsoft YaHei", 9),
                bg="#4a4eff" if i == 0 else "#333333",
                fg="white",
                relief=tk.FLAT,
                width=8,
                command=lambda idx=i: self.select_stock(idx)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.stock_buttons.append(btn)

        # 状态栏
        status_frame = tk.Frame(self.root, bg="#16213e", padx=20, pady=10)
        status_frame.pack(fill=tk.X, padx=20, pady=5)

        self.cash_label = tk.Label(
            status_frame,
            text=f"资金: ¥{self.cash:,.2f}",
            font=("Microsoft YaHei", 14),
            bg="#16213e",
            fg="#00ff88"
        )
        self.cash_label.pack(side=tk.LEFT)

        self.date_label = tk.Label(
            status_frame,
            text=f"第 {self.day} 天",
            font=("Microsoft YaHei", 14),
            bg="#16213e",
            fg="#eaeaea"
        )
        self.date_label.pack(side=tk.RIGHT)

        # K线图表区域
        chart_frame = tk.Frame(self.root, bg="#16213e", padx=20, pady=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.canvas = tk.Canvas(
            chart_frame,
            bg="#16213e",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 价格信息
        price_frame = tk.Frame(self.root, bg="#1a1a2e", padx=20, pady=5)
        price_frame.pack(fill=tk.X)

        self.stock_name_label = tk.Label(
            price_frame,
            text=f"贵州茅台 (白酒)",
            font=("Microsoft YaHei", 14),
            bg="#1a1a2e",
            fg="#888888"
        )
        self.stock_name_label.pack(side=tk.LEFT)

        self.price_label = tk.Label(
            price_frame,
            text=f"¥1800.00",
            font=("Consolas", 18, "bold"),
            bg="#1a1a2e",
            fg="#eaeaea"
        )
        self.price_label.pack(side=tk.LEFT, padx=20)

        self.change_label = tk.Label(
            price_frame,
            text="+0.00%",
            font=("Consolas", 14),
            bg="#1a1a2e",
            fg="#eaeaea"
        )
        self.change_label.pack(side=tk.RIGHT)

        # ===== 交易区域 =====
        trade_frame = tk.Frame(self.root, bg="#1a1a2e", padx=20, pady=10)
        trade_frame.pack(fill=tk.X)

        # 杠杆显示
        leverage_frame = tk.Frame(trade_frame, bg="#1a1a2e")
        leverage_frame.pack(side=tk.LEFT, padx=5)

        tk.Label(leverage_frame, text="杠杆", font=("Microsoft YaHei", 11, "bold"),
                bg="#1a1a2e", fg="#ff6b00").pack()

        self.leverage_btn = tk.Button(
            leverage_frame,
            text=f"×{self.leverage}",
            font=("Microsoft YaHei", 12, "bold"),
            bg="#ff6b00",
            fg="white",
            relief=tk.RAISED,
            width=4,
            command=self.toggle_leverage
        )
        self.leverage_btn.pack(pady=3)

        self.leverage_label = tk.Label(
            leverage_frame,
            text=f"费用: ¥{self.leverage_cost}",
            font=("Microsoft YaHei", 9),
            bg="#1a1a2e",
            fg="#888888"
        )
        self.leverage_label.pack()

        buy_frame = tk.Frame(trade_frame, bg="#1a1a2e")
        buy_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(buy_frame, text="买入", font=("Microsoft YaHei", 12, "bold"),
                bg="#1a1a2e", fg="#00ff88").pack()

        self.btn_buy_100 = tk.Button(buy_frame, text="买入100股", font=("Microsoft YaHei", 11),
                                bg="#4a4eff", fg="white", relief=tk.FLAT,
                                command=lambda: self.buy_stock(100),
                                activebackground="#6c6cff", width=14)
        self.btn_buy_100.pack(pady=3)

        self.btn_buy_500 = tk.Button(buy_frame, text="买入500股", font=("Microsoft YaHei", 11),
                                bg="#4a4eff", fg="white", relief=tk.FLAT,
                                command=lambda: self.buy_stock(500),
                                activebackground="#6c6cff", width=14)
        self.btn_buy_500.pack(pady=3)

        self.btn_buy_all = tk.Button(buy_frame, text="全部买入", font=("Microsoft YaHei", 11),
                                bg="#4a4eff", fg="white", relief=tk.FLAT,
                                command=lambda: self.buy_stock(self.get_max_shares()),
                                activebackground="#6c6cff", width=14)
        self.btn_buy_all.pack(pady=3)

        sell_frame = tk.Frame(trade_frame, bg="#1a1a2e")
        sell_frame.pack(side=tk.RIGHT, padx=10)

        tk.Label(sell_frame, text="卖出", font=("Microsoft YaHei", 12, "bold"),
                bg="#1a1a2e", fg="#ff4757").pack()

        # 冷却时间显示
        self.cooldown_label = tk.Label(
            sell_frame,
            text="",
            font=("Microsoft YaHei", 10),
            bg="#1a1a2e",
            fg="#ff6b00"
        )
        self.cooldown_label.pack(pady=2)

        self.btn_sell_100 = tk.Button(sell_frame, text="卖出100股", font=("Microsoft YaHei", 11),
                                bg="#ff4757", fg="white", relief=tk.FLAT,
                                command=lambda: self.sell_stock(100),
                                activebackground="#ff6b7a", width=14)
        self.btn_sell_100.pack(pady=3)

        self.btn_sell_500 = tk.Button(sell_frame, text="卖出500股", font=("Microsoft YaHei", 11),
                                bg="#ff4757", fg="white", relief=tk.FLAT,
                                command=lambda: self.sell_stock(500),
                                activebackground="#ff6b7a", width=14)
        self.btn_sell_500.pack(pady=3)

        self.btn_sell_all = tk.Button(sell_frame, text="全部卖出", font=("Microsoft YaHei", 11),
                                bg="#ff4757", fg="white", relief=tk.FLAT,
                                command=lambda: self.sell_stock(self.stocks[self.selected_stock_index].shares),
                                activebackground="#ff6b7a", width=14)
        self.btn_sell_all.pack(pady=3)

        # 持仓信息
        position_frame = tk.Frame(self.root, bg="#16213e", padx=20, pady=10)
        position_frame.pack(fill=tk.X, padx=20, pady=5)

        self.position_label = tk.Label(
            position_frame,
            text="持仓: 0股  |  成本: ¥0.00  |  盈亏: ¥0.00 (0.00%)",
            font=("Microsoft YaHei", 12),
            bg="#16213e",
            fg="#eaeaea"
        )
        self.position_label.pack()

        # ===== 自动打工机系统 =====
        work_panel = tk.Frame(self.root, bg="#16213e", padx=20, pady=10)
        work_panel.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(work_panel, text="自动打工机",
                font=("Microsoft YaHei", 11, "bold"),
                bg="#16213e", fg="#00bcd4").pack(side=tk.LEFT, padx=10)

        # 自动打工机数量显示
        self.auto_work_count_label = tk.Label(
            work_panel,
            text=f"数量: {self.auto_work_count}台",
            font=("Microsoft YaHei", 11),
            bg="#16213e",
            fg="#eaeaea"
        )
        self.auto_work_count_label.pack(side=tk.LEFT, padx=5)

        # 打工升级按钮
        self.work_upgrade_btn = tk.Button(
            work_panel,
            text=f"升级 (¥{self.work_upgrade_cost})",
            font=("Microsoft YaHei", 10),
            bg="#ff9800",
            fg="white",
            relief=tk.RAISED,
            width=15,
            command=self.upgrade_work
        )
        self.work_upgrade_btn.pack(side=tk.LEFT, padx=5)

        # 购买自动打工机按钮
        self.auto_work_btn = tk.Button(
            work_panel,
            text=f"购买 (¥{self.auto_work_cost})",
            font=("Microsoft YaHei", 10),
            bg="#9c27b0",
            fg="white",
            relief=tk.RAISED,
            width=15,
            command=self.buy_auto_work
        )
        self.auto_work_btn.pack(side=tk.LEFT, padx=5)

        # ===== 彩票系统 =====
        lottery_panel = tk.Frame(self.root, bg="#16213e", padx=20, pady=10)
        lottery_panel.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(lottery_panel, text="彩票 (¥100/张)",
                font=("Microsoft YaHei", 11, "bold"),
                bg="#16213e", fg="#ff6b6b").pack(side=tk.LEFT, padx=10)

        self.lottery_btn = tk.Button(
            lottery_panel,
            text="购买彩票",
            font=("Microsoft YaHei", 11),
            bg="#ff6b6b",
            fg="white",
            relief=tk.RAISED,
            width=12,
            command=self.buy_lottery
        )
        self.lottery_btn.pack(side=tk.LEFT, padx=5)

        self.lottery_result_label = tk.Label(
            lottery_panel,
            text="",
            font=("Microsoft YaHei", 10),
            bg="#16213e",
            fg="#ffd700"
        )
        self.lottery_result_label.pack(side=tk.LEFT, padx=10)

        # ===== 消费商店 =====
        shop_panel = tk.Frame(self.root, bg="#16213e", padx=20, pady=10)
        shop_panel.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(shop_panel, text="消费商店",
                font=("Microsoft YaHei", 11, "bold"),
                bg="#16213e", fg="#e91e63").pack(side=tk.LEFT, padx=10)

        # VIP会员
        self.vip_btn = tk.Button(
            shop_panel,
            text=f"VIP会员 Lv.{self.vip_level}",
            font=("Microsoft YaHei", 10),
            bg="#ffd700",
            fg="black",
            relief=tk.RAISED,
            width=15,
            command=self.buy_vip
        )
        self.vip_btn.pack(side=tk.LEFT, padx=5)

        # 车辆
        self.car_btn = tk.Button(
            shop_panel,
            text=f"购车 (Lv.{self.car_level})",
            font=("Microsoft YaHei", 10),
            bg="#607d8b",
            fg="white",
            relief=tk.RAISED,
            width=12,
            command=self.buy_car
        )
        self.car_btn.pack(side=tk.LEFT, padx=5)

        # 房产
        self.house_btn = tk.Button(
            shop_panel,
            text=f"买房 (Lv.{self.house_level})",
            font=("Microsoft YaHei", 10),
            bg="#795548",
            fg="white",
            relief=tk.RAISED,
            width=12,
            command=self.buy_house
        )
        self.house_btn.pack(side=tk.LEFT, padx=5)

        # 控制面板
        control_frame = tk.Frame(self.root, bg="#1a1a2e", padx=20, pady=10)
        control_frame.pack(fill=tk.X)

        btn_start = tk.Button(control_frame, text="暂停/继续", font=("Microsoft YaHei", 11),
                              bg="#4a4eff", fg="white", relief=tk.FLAT,
                              command=self.toggle_pause,
                              activebackground="#6c6cff", width=12)
        btn_start.pack(side=tk.LEFT, padx=5)

        btn_reset = tk.Button(control_frame, text="重置游戏", font=("Microsoft YaHei", 11),
                              bg="#666666", fg="white", relief=tk.FLAT,
                              command=self.reset_game,
                              activebackground="#888888", width=12)
        btn_reset.pack(side=tk.LEFT, padx=5)

        # 波动剧烈度
        tk.Label(control_frame, text="波动剧烈度:",
                font=("Microsoft YaHei", 11), bg="#1a1a2e", fg="#eaeaea").pack(side=tk.LEFT, padx=(30, 10))

        self.volatility_frame = tk.Frame(control_frame, bg="#1a1a2e")
        self.volatility_frame.pack(side=tk.LEFT)

        self.volatility_buttons = []
        for i in range(5):
            btn = tk.Button(
                self.volatility_frame,
                text="●",
                font=("Microsoft YaHei", 12),
                bg="#4a4eff" if i < self.volatility_level else "#333333",
                fg="white" if i < self.volatility_level else "#666666",
                relief=tk.FLAT,
                width=2,
                command=lambda idx=i: self.set_volatility(idx + 1)
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.volatility_buttons.append(btn)

    # ===== 打工系统功能 =====
    def upgrade_work(self):
        """升级打工技能"""
        if self.cash >= self.work_upgrade_cost:
            self.cash -= self.work_upgrade_cost
            self.work_level += 1
            self.work_income = 10 * self.work_level
            self.work_upgrade_cost = int(self.work_upgrade_cost * 1.5)

            self.work_upgrade_btn.configure(text=f"升级 (¥{self.work_upgrade_cost})")
            self.update_ui()

    def buy_auto_work(self):
        """购买自动打工机"""
        if self.cash >= self.auto_work_cost:
            self.cash -= self.auto_work_cost
            self.auto_work_count += 1
            self.auto_work_cost = int(self.auto_work_cost * 1.3)

            self.auto_work_count_label.configure(text=f"数量: {self.auto_work_count}台")
            self.auto_work_btn.configure(text=f"购买 (¥{self.auto_work_cost})")
            self.update_ui()

    # ===== 消费系统功能 =====
    def buy_vip(self):
        """购买VIP会员"""
        cost = self.vip_cost * (self.vip_level + 1)
        if self.cash >= cost:
            self.cash -= cost
            self.vip_level += 1

            self.vip_btn.configure(text=f"VIP会员 Lv.{self.vip_level}")
            self.update_ui()

    def buy_car(self):
        """购买车辆"""
        if self.cash >= self.car_cost:
            self.cash -= self.car_cost
            self.car_level += 1
            self.car_cost = int(self.car_cost * 1.5)

            self.car_btn.configure(text=f"购车 (Lv.{self.car_level})")
            self.update_ui()

    def buy_house(self):
        """购买房产"""
        if self.cash >= self.house_cost:
            self.cash -= self.house_cost
            self.house_level += 1
            self.house_cost = int(self.house_cost * 1.8)

            self.house_btn.configure(text=f"买房 (Lv.{self.house_level})")
            self.update_ui()

    # ===== 彩票系统 =====
    def buy_lottery(self):
        """购买彩票 - 可无限购买"""
        if self.cash < self.lottery_cost:
            self.lottery_result_label.configure(text="资金不足!", fg="#ff4757")
            return

        self.cash -= self.lottery_cost

        # 抽奖逻辑
        rand = random.random()

        if rand < 0.01:  # 1% 中大奖
            prize = 10000
            result = f"恭喜! 中大奖 ¥{prize}!"
            color = "#00ff88"
        elif rand < 0.05:  # 4% 中小奖
            prize = 500
            result = f"中奖! ¥{prize}"
            color = "#00ff88"
        elif rand < 0.15:  # 10% 安慰奖
            prize = 150
            result = f"安慰奖 ¥{prize}"
            color = "#ffd700"
        else:  # 85% 不中奖
            prize = 0
            result = "谢谢参与"
            color = "#888888"

        self.cash += prize
        self.lottery_last_result = result
        self.lottery_result_label.configure(text=result, fg=color)

        # 显示3秒后消失
        self.root.after(3000, lambda: self.lottery_result_label.configure(text=""))

        self.update_ui()

    def select_stock(self, index):
        """选择股票"""
        # 切换选中的股票
        self.selected_stock_index = index
        current_stock = self.stocks[index]

        # 更新按钮状态，显示持股数量
        for i, btn in enumerate(self.stock_buttons):
            stock = self.stocks[i]
            if i == index:
                btn.configure(bg="#4a4eff")
            else:
                btn.configure(bg="#333333")
            # 更新按钮文本显示持股
            if stock.shares > 0:
                btn.configure(text=f"{stock.name[:4]}({stock.shares})")
            else:
                btn.configure(text=f"{stock.name[:4]}")

        # 更新UI显示新股票信息
        self.stock_name_label.configure(text=f"{current_stock.name} ({current_stock.industry})")
        self.update_ui()
        self.draw_chart()

    def set_volatility(self, level):
        self.volatility_level = level
        for i, btn in enumerate(self.volatility_buttons):
            if i < self.volatility_level:
                btn.configure(bg="#4a4eff", fg="white")
            else:
                btn.configure(bg="#333333", fg="#666666")

    def get_max_shares(self):
        current_price = self.stocks[self.selected_stock_index].price
        return int(self.cash // current_price)

    def buy_stock(self, amount):
        if amount <= 0:
            return
        current_stock = self.stocks[self.selected_stock_index]
        cost = amount * current_stock.price * self.leverage

        if cost > self.cash:
            # 资金不足，自动调整为可买入的最大数量
            amount = int(self.cash // (current_stock.price * self.leverage))
            cost = amount * current_stock.price * self.leverage

        if amount > 0:
            self.cash -= cost
            current_stock.shares += amount * self.leverage
            current_stock.total_cost += cost

            # 开启杠杆后，需要扣除杠杆使用费
            if self.leverage > 1:
                self.cash -= self.leverage_cost

            # 购买后设置卖出冷却时间
            self.sell_cooldown = self.sell_cooldown_max
            self.update_sell_button()
            self.update_ui()

    def sell_stock(self, amount):
        # 检查冷却时间
        if self.sell_cooldown > 0:
            return

        current_stock = self.stocks[self.selected_stock_index]

        if amount <= 0:
            return
        if amount > current_stock.shares:
            amount = current_stock.shares

        if amount > 0:
            revenue = amount * current_stock.price
            self.cash += revenue
            current_stock.shares -= amount

            # 更新成本
            if current_stock.shares > 0:
                avg_cost = current_stock.total_cost / (current_stock.shares + amount)
                current_stock.total_cost = avg_cost * current_stock.shares
            else:
                current_stock.total_cost = 0

            self.update_ui()

    def update_sell_button(self):
        """更新卖出按钮状态"""
        if self.sell_cooldown > 0:
            # 禁用卖出按钮
            self.btn_sell_100.configure(state=tk.DISABLED, bg="#555555")
            self.btn_sell_500.configure(state=tk.DISABLED, bg="#555555")
            self.btn_sell_all.configure(state=tk.DISABLED, bg="#555555")
            self.cooldown_label.configure(text=f"冷却中: {self.sell_cooldown}秒")
        else:
            # 启用卖出按钮
            self.btn_sell_100.configure(state=tk.NORMAL, bg="#ff4757")
            self.btn_sell_500.configure(state=tk.NORMAL, bg="#ff4757")
            self.btn_sell_all.configure(state=tk.NORMAL, bg="#ff4757")
            self.cooldown_label.configure(text="")

    def toggle_leverage(self):
        """切换杠杆倍数 - 扩展版本"""
        self.leverage_index = (self.leverage_index + 1) % len(self.leverage_options)
        new_leverage = self.leverage_options[self.leverage_index]

        old_leverage = self.leverage

        # 如果从×1切换到更高杠杆，收取费用
        if old_leverage == 1 and new_leverage > 1:
            if self.cash >= self.leverage_cost:
                self.cash -= self.leverage_cost
                self.leverage = new_leverage
            else:
                # 资金不足，恢复原状态
                self.leverage_index = (self.leverage_index - 1) % len(self.leverage_options)
                self.leverage_label.configure(fg="#ff4757", text=f"费用不足 ¥{self.leverage_cost}")
                self.root.after(1000, lambda: self.leverage_label.configure(fg="#888888", text=f"费用: ¥{self.leverage_cost}"))
                return
        # 如果从高杠杆切换到×1，不退还费用，直接切换
        elif old_leverage > 1 and new_leverage == 1:
            self.leverage = new_leverage
        # 如果在高杠杆之间切换，不额外收费
        elif old_leverage > 1 and new_leverage > 1:
            self.leverage = new_leverage
        else:
            self.leverage = new_leverage

        self.leverage_btn.configure(bg="#ff3300" if self.leverage > 1 else "#ff6b00", text=f"×{self.leverage}")
        self.leverage_label.configure(text=f"费用: ¥{self.leverage_cost}")
        self.update_ui()

    def toggle_pause(self):
        self.is_running = not self.is_running

    def reset_game(self):
        self.cash = 10000  # 初始资金
        self.day = 1
        self.game_seconds = 0
        self.market_sentiment = 0
        self.market_cycle_days = 0

        # 重置所有股票
        self.stocks = self.init_stocks()
        self.selected_stock_index = 0

        # 重置杠杆
        self.leverage = 1
        self.leverage_index = 0
        self.leverage_btn.configure(bg="#ff6b00", text="×1")
        self.leverage_label.configure(text=f"费用: ¥{self.leverage_cost}")

        # 重置打工系统
        self.work_level = 1
        self.work_income = 10
        self.work_upgrade_cost = 200
        self.auto_work_count = 0
        self.auto_work_cost = 500
        self.auto_work_count_label.configure(text=f"数量: {self.auto_work_count}台")
        self.work_upgrade_btn.configure(text=f"升级 (¥{self.work_upgrade_cost})")
        self.auto_work_btn.configure(text=f"购买 (¥{self.auto_work_cost})")

        # 重置消费系统
        self.vip_level = 0
        self.car_level = 0
        self.house_level = 0
        self.vip_btn.configure(text=f"VIP会员 Lv.{self.vip_level}")
        self.car_btn.configure(text=f"购车 (Lv.{self.car_level})")
        self.house_btn.configure(text=f"买房 (Lv.{self.house_level})")

        # 更新按钮状态
        for i, btn in enumerate(self.stock_buttons):
            btn.configure(bg="#4a4eff" if i == 0 else "#333333", text=f"{self.stocks[i].name[:4]}")

        # 重置冷却时间
        self.sell_cooldown = 0
        self.update_sell_button()

        # 重置彩票
        self.lottery_result_label.configure(text="")

        self.stock_name_label.configure(text=f"{self.stocks[0].name} ({self.stocks[0].industry})")
        self.update_ui()
        self.draw_chart()

    def calculate_change(self):
        current_stock = self.stocks[self.selected_stock_index]
        if len(current_stock.price_history) > 1:
            old_price = current_stock.price_history[-2]
            change = (current_stock.price - old_price) / old_price * 100
            return change
        return 0

    def update_market_sentiment(self):
        """更新市场情绪和周期"""
        # 市场周期转换
        self.market_cycle_days += 1

        # 每30-60天转换一次市场周期
        if self.market_cycle_days > random.randint(30, 60):
            self.market_cycle_days = 0
            # 30%概率转换市场周期
            if random.random() < 0.3:
                self.market_cycle = random.choice([-1, 0, 0, 1])  # 偏向于稳定或牛市

        # 市场情绪波动
        self.market_sentiment += random.uniform(-0.05, 0.05)
        self.market_sentiment = max(-1, min(1, self.market_sentiment))

    def update_price_realistic(self, stock):
        """更真实的价格更新算法"""
        volatility_multiplier = self.volatility_level / 3

        # 基础波动率（基于风险等级）
        base_volatility = stock.volatility * volatility_multiplier

        # 比特币特殊处理 - 极高波动
        if stock.code == "BTC":
            base_volatility *= 3  # 3倍波动率
            # 比特币黑天鹅概率更高
            black_swan_chance = 0.03  # 3%概率
        else:
            black_swan_chance = 0.01  # 1%概率

        # 1. 趋势跟踪因子 - 股价倾向于延续当前趋势
        trend_factor = 0
        if stock.consecutive_up >= 2:
            trend_factor = base_volatility * 0.5  # 上涨趋势延续
        elif stock.consecutive_down >= 2:
            trend_factor = -base_volatility * 0.5  # 下跌趋势延续

        # 2. 波动聚集性 - 大波动后往往继续大波动
        volatility_clustering = 0
        if abs(stock.last_change) > base_volatility * 3:
            volatility_clustering = stock.last_change * 0.3  # 延续之前的波动方向

        # 3. 均值回归 - 价格不会偏离基准太远
        deviation = (stock.price - stock.base_price) / stock.base_price
        mean_reversion = -deviation * base_volatility * 2

        # 4. 市场周期影响
        market_cycle_impact = self.market_cycle * base_volatility * 0.5

        # 5. 市场情绪影响
        sentiment_impact = self.market_sentiment * base_volatility * 0.3

        # 6. 行业趋势偏好
        trend_bias_impact = stock.trend_bias * base_volatility * 0.3

        # 7. 黑天鹅事件（罕见但剧烈）
        black_swan = 0
        if random.random() < black_swan_chance:
            black_swan = random.choice([-1, 1]) * base_volatility * random.uniform(5, 10)
            # 触发黑天鹅后，市场情绪会受到影响
            self.market_sentiment += black_swan * 0.1
            self.market_sentiment = max(-1, min(1, self.market_sentiment))

        # 计算总变化率
        change_percent = (
            random.uniform(-base_volatility, base_volatility) +  # 随机波动
            trend_factor +
            volatility_clustering +
            mean_reversion +
            market_cycle_impact +
            sentiment_impact +
            trend_bias_impact +
            black_swan
        )

        # 限制极端波动
        change_percent = max(-15, min(15, change_percent))

        # 更新价格
        stock.price = max(1, stock.price * (1 + change_percent / 100))
        stock.price_history.append(stock.price)

        # 更新连续涨跌计数
        if change_percent > 0.5:
            stock.consecutive_up += 1
            stock.consecutive_down = 0
        elif change_percent < -0.5:
            stock.consecutive_down += 1
            stock.consecutive_up = 0
        else:
            stock.consecutive_up = max(0, stock.consecutive_up - 1)
            stock.consecutive_down = max(0, stock.consecutive_down - 1)

        stock.last_change = change_percent

        # 限制历史记录长度
        if len(stock.price_history) > 200:
            stock.price_history = stock.price_history[-200:]

    def update_price(self):
        """更新所有股票价格"""
        self.update_market_sentiment()

        # 更新每只股票的价格
        for stock in self.stocks:
            self.update_price_realistic(stock)

    def update_ui(self):
        current_stock = self.stocks[self.selected_stock_index]

        self.cash_label.configure(text=f"资金: ¥{self.cash:,.2f}")
        self.date_label.configure(text=f"第 {self.day} 天")
        self.price_label.configure(text=f"¥{current_stock.price:.2f}")

        # 计算涨跌
        change = self.calculate_change()
        if change >= 0:
            self.change_label.configure(
                text=f"+{change:.2f}%",
                fg="#00ff88"
            )
            self.price_label.configure(fg="#00ff88")
        else:
            self.change_label.configure(
                text=f"{change:.2f}%",
                fg="#ff4757"
            )
            self.price_label.configure(fg="#ff4757")

        # 计算盈亏（使用当前股票的持仓）
        if current_stock.shares > 0:
            current_value = current_stock.shares * current_stock.price
            profit = current_value - current_stock.total_cost
            profit_percent = (profit / current_stock.total_cost * 100) if current_stock.total_cost > 0 else 0

            if profit >= 0:
                self.position_label.configure(
                    text=f"持仓: {current_stock.shares}股  |  成本: ¥{current_stock.total_cost:,.2f}  |  盈亏: +¥{profit:,.2f} (+{profit_percent:.2f}%)",
                    fg="#00ff88"
                )
            else:
                self.position_label.configure(
                    text=f"持仓: {current_stock.shares}股  |  成本: ¥{current_stock.total_cost:,.2f}  |  盈亏: -¥{abs(profit):,.2f} ({profit_percent:.2f}%)",
                    fg="#ff4757"
                )
        else:
            self.position_label.configure(
                text="持仓: 0股  |  成本: ¥0.00  |  盈亏: ¥0.00 (0.00%)",
                fg="#eaeaea"
            )

    def draw_chart(self):
        self.canvas.delete("all")

        current_stock = self.stocks[self.selected_stock_index]

        if not current_stock.price_history:
            return

        # 获取画布大小
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1:
            canvas_width = 800
            canvas_height = 300

        # 计算价格范围
        min_price = min(current_stock.price_history)
        max_price = max(current_stock.price_history)
        price_range = max_price - min_price

        if price_range == 0:
            price_range = 1

        # 边距
        margin_left = 50
        margin_right = 20
        margin_top = 20
        margin_bottom = 30

        chart_width = canvas_width - margin_left - margin_right
        chart_height = canvas_height - margin_top - margin_bottom

        # 绘制背景网格
        for i in range(5):
            y = margin_top + (chart_height / 4) * i
            self.canvas.create_line(
                margin_left, y, canvas_width - margin_right, y,
                fill="#2a2a4a", dash=(2, 4)
            )

        # 绘制价格线
        points = []
        history_len = len(current_stock.price_history)
        for i, price in enumerate(current_stock.price_history):
            if history_len > 1:
                x = margin_left + (i / (history_len - 1)) * chart_width
            else:
                x = margin_left
            y = margin_top + chart_height - ((price - min_price) / price_range) * chart_height
            points.append((x, y))

        # 绘制渐变填充
        if len(points) > 1:
            fill_points = [(margin_left, margin_top + chart_height)]
            fill_points.extend(points)
            last_x = margin_left + chart_width
            fill_points.append((last_x, margin_top + chart_height))

            self.canvas.create_polygon(
                fill_points,
                fill="#2a2a5a",
                outline=""
            )

            # 绘制价格线
            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]

                if current_stock.price_history[i + 1] >= current_stock.price_history[i]:
                    color = "#00ff88"
                else:
                    color = "#ff4757"

                self.canvas.create_line(
                    x1, y1, x2, y2,
                    fill=color,
                    width=2
                )

        # 绘制价格标签
        price_labels = [max_price, (max_price + min_price) / 2, min_price]
        for i, price in enumerate(price_labels):
            y = margin_top + (chart_height / 2) * i
            self.canvas.create_text(
                margin_left - 8, y,
                text=f"¥{price:.1f}",
                fill="#888888",
                font=("Consolas", 9),
                anchor=tk.E
            )

        # 绘制当前价格标记
        if points:
            last_x, last_y = points[-1]
            current_color = "#00ff88" if current_stock.price >= current_stock.price_history[0] else "#ff4757"
            self.canvas.create_oval(
                last_x - 5, last_y - 5,
                last_x + 5, last_y + 5,
                fill=current_color,
                outline="white",
                width=2
            )

    def game_loop(self):
        """游戏主循环 - 使用线程安全的方式更新"""
        while True:
            try:
                if self.is_running:
                    self.game_seconds += 1

                    # 每10秒增加一天（游戏内一天 = 现实10秒）
                    if self.game_seconds % 10 == 0:
                        self.day += 1

                    # 更新卖出冷却时间
                    if self.sell_cooldown > 0:
                        self.sell_cooldown -= 1
                        self.root.after(0, self.update_sell_button)

                    # 自动打工机收入（每秒）
                    if self.auto_work_count > 0:
                        auto_income = self.auto_work_count * self.work_income
                        # 计算总加成系数
                        bonus_multiplier = 1 + self.vip_level * 0.2 + self.car_level * 0.1 + self.house_level * 0.15
                        auto_income = auto_income * bonus_multiplier

                        self.cash += int(auto_income)

                    self.update_price()
                    # 使用after方法更新UI，确保线程安全
                    self.root.after(0, self.update_ui)
                    self.root.after(0, self.draw_chart)
                time.sleep(1)
            except Exception as e:
                # 忽略错误，继续运行
                pass

    def start_game(self):
        self.is_running = True
        # 启动游戏循环线程
        game_thread = threading.Thread(target=self.game_loop)
        game_thread.daemon = False
        game_thread.start()


def main():
    root = tk.Tk()

    # 设置窗口居中
    window_width = 1000
    window_height = 1000
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    try:
        root.iconbitmap(default="")
    except:
        pass

    app = StockGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
