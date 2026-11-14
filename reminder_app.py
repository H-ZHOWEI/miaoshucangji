import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import shutil
from tkinter import ttk, messagebox, font, filedialog
from datetime import datetime
import csv
import os
import re


class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("喵数仓记 - 仓库库存管理系统")
        self.root.geometry("1200x700")
        self.root.configure(bg="#f0f2f5")

        try:
            self.root.iconbitmap("application-note.ico")
        except:
            pass

        # 创建自定义字体
        self.title_font = font.Font(family="微软雅黑", size=24, weight="bold")
        self.subtitle_font = font.Font(family="微软雅黑", size=12)
        self.button_font = font.Font(family="微软雅黑", size=12, weight="bold")
        self.label_font = font.Font(family="微软雅黑", size=11)
        self.entry_font = font.Font(family="微软雅黑", size=12)
        self.stat_font = font.Font(family="微软雅黑", size=24, weight="bold")
        self.stat_label_font = font.Font(family="微软雅黑", size=12)
        self.table_header_font = font.Font(family="微软雅黑", size=12, weight="bold")
        self.table_font = font.Font(family="微软雅黑", size=11)

        # 初始化数据
        self.inventory = []
        self.records = []
        self.grouped_inventory = []  # 用于存储分组后的数据
        self.load_data()
        self.group_items()  # 初始分组

        # 创建UI
        self.create_header()
        self.create_stats()
        self.create_inventory_table()
        self.create_footer()

        self.update_stats()

    def load_data(self):
        """加载库存和记录数据"""
        # 尝试从CSV文件加载库存
        if os.path.exists("inventory.csv"):
            with open("inventory.csv", "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 转换数量为整数
                    row["quantity"] = int(row["quantity"])
                    # 检查是否存在规格字段，如果没有则添加空字符串
                    if "spec" not in row:
                        row["spec"] = ""
                    # 检查是否存在物品编码字段，如果没有则添加空字符串
                    if "code" not in row:
                        row["code"] = ""
                    # 添加类别字段，默认为非月度采购物品
                    if "category" not in row:
                        row["category"] = "非月度采购物品"
                    # 添加购买链接字段，默认为空字符串
                    if "purchase_link" not in row:
                        row["purchase_link"] = ""
                    self.inventory.append(row)

        # 尝试从CSV文件加载记录
        if os.path.exists("records.csv"):
            with open("records.csv", "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 转换数量为整数
                    row["quantity"] = int(row["quantity"])

                    # 兼容旧数据：如果没有operation_date字段，则使用date字段的值
                    if "operation_date" not in row:
                        row["operation_date"] = row["date"]

                    # 兼容旧数据：如果没有image_path字段，则添加空字符串
                    if "image_path" not in row:
                        row["image_path"] = ""

                    # 兼容旧数据：如果没有code字段，则添加空字符串
                    if "code" not in row:
                        row["code"] = ""

                    self.records.append(row)

            # 将记录按操作日期倒序排列（最新的在最上面）
            self.records.sort(key=lambda x: datetime.strptime(x["operation_date"], "%Y-%m-%d"), reverse=True)

    def group_items(self):
        """按物品名称分组库存"""
        self.grouped_inventory = []
        grouped_dict = {}

        for item in self.inventory:
            key = f"{item['name']}"
            if key not in grouped_dict:
                grouped_dict[key] = {
                    "key": key,
                    "name": item["name"],
                    "quantity": 0,
                    "last_updated": "0000-00-00",
                    "items": []
                }

            grouped_dict[key]["quantity"] += item["quantity"]

            if item.get("last_updated", "0000-00-00") > grouped_dict[key]["last_updated"]:
                grouped_dict[key]["last_updated"] = item["last_updated"]

            grouped_dict[key]["items"].append(item)

        self.grouped_inventory = list(grouped_dict.values())
        self.grouped_inventory.sort(key=lambda x: x["last_updated"], reverse=True)

        # 修改状态逻辑 - 现在状态仅用于分组显示，不影响统计
        for group in self.grouped_inventory:
            # 检查组内是否有月度采购物品且数量<2
            has_low_monthly = any(
                item["quantity"] < 2 and item["category"] == "月度采购物品"
                for item in group["items"]
            )

            # 检查组内是否有任何物品数量<2（无论类别）
            has_any_low = any(item["quantity"] < 2 for item in group["items"])

            # 状态逻辑：
            # 1. 如果有月度采购物品且数量<2 -> 需补货
            # 2. 否则 -> 库存充足（即使有非月度采购物品数量<2）
            if has_low_monthly:
                group["status"] = "需补货"
            else:
                group["status"] = "库存充足"

    def save_inventory(self):
        """保存库存数据到CSV文件"""
        if not self.inventory:
            return

        with open("inventory.csv", "w", newline="", encoding="utf-8") as f:
            # 确保包含category和purchase_link字段
            fieldnames = ["id", "code", "name", "spec", "quantity", "company", "last_updated", "category",
                          "purchase_link"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.inventory)

    def save_records(self):
        """保存记录数据到CSV文件"""
        if not self.records:
            return

        # 确保所有记录字典都有相同的键
        # 获取所有可能的字段名
        fieldnames = set()
        for record in self.records:
            fieldnames.update(record.keys())

        # 转换为列表并确保有固定的顺序
        fieldnames = ["id", "type", "item_id", "code", "name", "spec", "quantity",
                      "company", "department", "recipient", "date", "operation_date", "notes", "image_path"]

        with open("records.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.records)

    def create_header(self):
        """创建页面头部"""
        header_frame = tk.Frame(self.root, bg="#4e73df", height=100)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        # 左侧logo和标题
        logo_frame = tk.Frame(header_frame, bg="#4e73df")
        logo_frame.pack(side=tk.LEFT, padx=20)

        self.logo_label = tk.Label(
            logo_frame,
            text="",
            font=("Arial", 28),
            bg="#4e73df",
            fg="white"
        )
        self.logo_label.pack(side=tk.LEFT, padx=(0, 10))

        title_frame = tk.Frame(logo_frame, bg="#4e73df")
        title_frame.pack(side=tk.LEFT)

        self.title_label = tk.Label(
            title_frame,
            text="喵数仓记",
            font=self.title_font,
            bg="#4e73df",
            fg="white"
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = tk.Label(
            title_frame,
            text="智能仓库库存管理系统",
            font=self.subtitle_font,
            bg="#4e73df",
            fg="#e6e6ff"
        )
        self.subtitle_label.pack(anchor="w")

        # 右侧控制按钮
        controls_frame = tk.Frame(header_frame, bg="#4e73df")
        controls_frame.pack(side=tk.RIGHT, padx=20)

        self.add_btn = tk.Button(
            controls_frame,
            text="新增物品",
            bg="#1cc88a",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            bd=0,
            command=self.open_add_dialog
        )
        self.add_btn.pack(side=tk.LEFT, padx=5)

        # 新增修改信息按钮
        self.edit_btn = tk.Button(
            controls_frame,
            text="修改信息",
            bg="#36b9cc",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            bd=0,
            command=self.open_edit_dialog
        )
        self.edit_btn.pack(side=tk.LEFT, padx=5)

        # 新增入库按钮
        self.restock_btn = tk.Button(
            controls_frame,
            text="入库",
            bg="#4e73df",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            bd=0,
            command=self.open_restock_dialog
        )
        self.restock_btn.pack(side=tk.LEFT, padx=5)

        # 将变更库存按钮改为出库按钮
        self.update_btn = tk.Button(
            controls_frame,
            text="出库",
            bg="#f6c23e",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            bd=0,
            command=self.open_update_dialog
        )
        self.update_btn.pack(side=tk.LEFT, padx=5)

        self.history_btn = tk.Button(
            controls_frame,
            text="操作记录",
            bg="#e74a3b",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            bd=0,
            command=self.open_history_dialog
        )
        self.history_btn.pack(side=tk.LEFT, padx=5)

    def create_stats(self):
        """创建统计信息卡片（圆角设计）"""
        stats_frame = tk.Frame(self.root, bg="#f0f2f5")
        stats_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        # 库存物品总数（圆角卡片）
        stat1 = tk.Frame(stats_frame, bg="white", relief=tk.RAISED, bd=1)
        stat1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10), ipadx=15, ipady=10)

        # 使用Canvas创建圆角矩形
        canvas1 = tk.Canvas(stat1, width=60, height=60, bg="white", highlightthickness=0)
        canvas1.pack(side=tk.LEFT, padx=(10, 0))
        canvas1.create_oval(5, 5, 55, 55, fill="#4e73df", outline="#4e73df")
        canvas1.create_text(30, 30, text="📦", font=("Arial", 24), fill="white")

        text_frame1 = tk.Frame(stat1, bg="white")
        text_frame1.pack(side=tk.LEFT, padx=10, pady=10)

        # 计算唯一物品数量（按名称+规格）
        unique_items = set()
        for item in self.inventory:
            key = f"{item['name']}_{item['spec']}"
            unique_items.add(key)

        self.total_items = tk.Label(
            text_frame1,
            text=str(len(unique_items)),
            font=self.stat_font,
            bg="white",
            fg="#4e73df"
        )
        self.total_items.pack(anchor="w", padx=(20, 0))

        tk.Label(
            text_frame1,
            text="库存物品总数",
            font=self.stat_label_font,
            bg="white",
            fg="#6c757d"
        ).pack(anchor="w", padx=(20, 0))

        # 库存总量（圆角卡片）
        stat2 = tk.Frame(stats_frame, bg="white", relief=tk.RAISED, bd=1)
        stat2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, ipadx=15, ipady=10)

        canvas2 = tk.Canvas(stat2, width=60, height=60, bg="white", highlightthickness=0)
        canvas2.pack(side=tk.LEFT, padx=(10, 0))
        canvas2.create_oval(5, 5, 55, 55, fill="#1cc88a", outline="#1cc88a")
        canvas2.create_text(30, 27, text="📊", font=("Arial", 24), fill="white")

        text_frame2 = tk.Frame(stat2, bg="white")
        text_frame2.pack(side=tk.LEFT, padx=10, pady=10)

        total_qty = sum(item["quantity"] for item in self.inventory)
        self.total_quantity = tk.Label(
            text_frame2,
            text=str(total_qty),
            font=self.stat_font,
            bg="white",
            fg="#1cc88a"
        )
        self.total_quantity.pack(anchor="w", padx=(20, 0))

        tk.Label(
            text_frame2,
            text="库存总量",
            font=self.stat_label_font,
            bg="white",
            fg="#6c757d"
        ).pack(anchor="w", padx=(20, 0))

        # 低库存物品（圆角卡片）
        stat3 = tk.Frame(stats_frame, bg="white", relief=tk.RAISED, bd=1)
        stat3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), ipadx=15, ipady=10)

        canvas3 = tk.Canvas(stat3, width=60, height=60, bg="white", highlightthickness=0)
        canvas3.pack(side=tk.LEFT, padx=(10, 0))
        canvas3.create_oval(5, 5, 55, 55, fill="#f6c23e", outline="#f6c23e")
        canvas3.create_text(53, 30, text="⚠️", font=("Arial", 24), fill="white")

        text_frame3 = tk.Frame(stat3, bg="white")
        text_frame3.pack(side=tk.LEFT, padx=10, pady=10)

        low_stock = sum(1 for item in self.inventory if item["quantity"] < 2)
        self.low_stock_items = tk.Label(
            text_frame3,
            text=str(low_stock),
            font=self.stat_font,
            bg="white",
            fg="#f6c23e"
        )
        self.low_stock_items.pack(anchor="w", padx=(20, 0))

        tk.Label(
            text_frame3,
            text="低库存物品",
            font=self.stat_label_font,
            bg="white",
            fg="#6c757d"
        ).pack(anchor="w", padx=(20, 0))

    def create_inventory_table(self):
        """创建库存表格"""
        table_frame = tk.Frame(self.root, bg="#f0f2f5")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # 表格标题
        header = tk.Frame(table_frame, bg="#4e73df")
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="库存物品清单",
            font=self.table_header_font,
            fg="white",
            bg="#4e73df",
            padx=15,
            pady=10
        ).pack(side=tk.LEFT)

        # 搜索框
        search_frame = tk.Frame(header, bg="#4e73df")
        search_frame.pack(side=tk.RIGHT, padx=15)

        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=self.entry_font,
            width=30
        )
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind("<KeyRelease>", self.filter_table)

        tk.Button(
            search_frame,
            text="搜索",
            bg="#1cc88a",
            fg="white",
            font=self.button_font,
            padx=10,
            command=self.filter_table
        ).pack(side=tk.LEFT)

        # 表格
        table_container = tk.Frame(table_frame, bg="white", relief=tk.SUNKEN, bd=1)
        table_container.pack(fill=tk.BOTH, expand=True)

        # 创建带滚动条的表格容器
        table_wrapper = tk.Frame(table_container)
        table_wrapper.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建表格 - 只显示四列
        columns = ("name", "quantity", "last_updated", "status")
        self.tree = ttk.Treeview(
            table_wrapper,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Custom.Treeview"
        )

        # 自定义表格样式
        style = ttk.Style()
        style.configure("Custom.Treeview", font=self.table_font, rowheight=30)
        style.configure("Custom.Treeview.Heading", font=self.table_header_font)
        style.map("Custom.Treeview", background=[("selected", "#4e73df")])

        # 设置列标题（居中显示）
        self.tree.heading("name", text="物品名称", anchor=tk.CENTER)
        self.tree.heading("quantity", text="当前库存", anchor=tk.CENTER)
        self.tree.heading("last_updated", text="最近操作日期", anchor=tk.CENTER)
        self.tree.heading("status", text="状态", anchor=tk.CENTER)

        # 设置列宽（居中显示）
        self.tree.column("name", width=300, anchor=tk.CENTER)
        self.tree.column("quantity", width=150, anchor=tk.CENTER)
        self.tree.column("last_updated", width=200, anchor=tk.CENTER)
        self.tree.column("status", width=150, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_wrapper, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # 绑定双击事件查看明细
        self.tree.bind("<Double-1>", self.show_item_details)

        # 填充数据
        self.update_table()

    def update_table(self):
        """更新表格数据"""
        # 重新分组数据
        self.group_items()

        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 添加分组后的数据
        for group in self.grouped_inventory:
            tags = ("red_font",) if group["status"] == "需补货" else ()
            self.tree.insert("", tk.END, values=(
                group["name"],
                group["quantity"],
                group["last_updated"],
                group["status"]
            ), tags=tags)

        # 配置红色字体标签
        self.tree.tag_configure("red_font", foreground="red")

    def filter_table(self, event=None):
        """根据搜索词过滤表格"""
        search_term = self.search_var.get().lower()

        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 添加过滤后的数据
        for group in self.grouped_inventory:
            if search_term in group["name"].lower():
                tags = ("red_font",) if group["status"] == "需补货" else ()
                self.tree.insert("", tk.END, values=(
                    group["name"],
                    group["quantity"],
                    group["last_updated"],
                    group["status"]
                ), tags=tags)

    def create_footer(self):
        """创建页脚"""
        footer_frame = tk.Frame(self.root, bg="#f0f2f5", height=30)
        footer_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        tk.Label(
            footer_frame,
            text="© 2025 喵数仓记仓库管理系统 | 设计：爱吃蟹黄先生 | 版本 v1.0",
            font=self.label_font,
            fg="#6c757d",
            bg="#f0f2f5"
        ).pack(pady=5)

    def open_add_dialog(self):
        """打开新增物品对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("新增物品")
        dialog.geometry("400x900")  # 增加高度以容纳新字段
        dialog.resizable(False, False)
        dialog.transient(self.root)
        # dialog.grab_set()

        # 设置对话框背景
        dialog.configure(bg="#f0f2f5")

        # 对话框标题
        tk.Label(
            dialog,
            text="新增物品",
            font=self.title_font,
            bg="#4e73df",
            fg="white",
            padx=15,
            pady=10
        ).pack(fill=tk.X)

        # 表单容器（增加滚动条）
        form_container = tk.Frame(dialog, bg="#f0f2f5")
        form_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建Canvas和滚动条
        canvas = tk.Canvas(form_container, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f2f5")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 表单内容
        form_frame = tk.Frame(scrollable_frame, bg="#f0f2f5", padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 物品编码
        tk.Label(form_frame, text="物品编码 *", bg="#f0f2f5", font=self.label_font).grid(row=0, column=0, sticky="w",
                                                                                         pady=(0, 5))
        code_var = tk.StringVar()
        code_entry = tk.Entry(form_frame, textvariable=code_var, font=self.entry_font, width=30)
        code_entry.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # 物品名称
        tk.Label(form_frame, text="物品名称 *", bg="#f0f2f5", font=self.label_font).grid(row=2, column=0, sticky="w",
                                                                                         pady=(0, 5))
        name_var = tk.StringVar()
        name_entry = tk.Entry(form_frame, textvariable=name_var, font=self.entry_font, width=30)
        name_entry.grid(row=3, column=0, sticky="ew", pady=(0, 15))

        # 物品规格
        tk.Label(form_frame, text="物品规格 *", bg="#f0f2f5", font=self.label_font).grid(row=4, column=0, sticky="w",
                                                                                         pady=(0, 5))
        spec_var = tk.StringVar()
        spec_entry = tk.Entry(form_frame, textvariable=spec_var, font=self.entry_font, width=30)
        spec_entry.grid(row=5, column=0, sticky="ew", pady=(0, 15))

        # 数量
        tk.Label(form_frame, text="数量 *", bg="#f0f2f5", font=self.label_font).grid(row=6, column=0, sticky="w",
                                                                                     pady=(0, 5))
        qty_var = tk.StringVar()
        qty_entry = tk.Entry(form_frame, textvariable=qty_var, font=self.entry_font, width=30)
        qty_entry.grid(row=7, column=0, sticky="ew", pady=(0, 15))

        # 申请公司
        tk.Label(form_frame, text="申请公司", bg="#f0f2f5", font=self.label_font).grid(row=8, column=0, sticky="w",
                                                                                       pady=(0, 5))
        company_var = tk.StringVar()
        company_entry = tk.Entry(form_frame, textvariable=company_var, font=self.entry_font, width=30)
        company_entry.grid(row=9, column=0, sticky="ew", pady=(0, 15))

        # 领取部门
        tk.Label(form_frame, text="领取部门", bg="#f0f2f5", font=self.label_font).grid(row=10, column=0, sticky="w",
                                                                                       pady=(0, 5))
        dept_var = tk.StringVar()
        dept_entry = tk.Entry(form_frame, textvariable=dept_var, font=self.entry_font, width=30)
        dept_entry.grid(row=11, column=0, sticky="ew", pady=(0, 15))

        # 领取人
        tk.Label(form_frame, text="领取人", bg="#f0f2f5", font=self.label_font).grid(row=12, column=0, sticky="w",
                                                                                     pady=(0, 5))
        recipient_var = tk.StringVar()
        recipient_entry = tk.Entry(form_frame, textvariable=recipient_var, font=self.entry_font, width=30)
        recipient_entry.grid(row=13, column=0, sticky="ew", pady=(0, 15))

        # 新增时间（物品入库时间）
        tk.Label(form_frame, text="新增时间（物品入库时间）*", bg="#f0f2f5", font=self.label_font).grid(row=14, column=0,
                                                                                                      sticky="w",
                                                                                                      pady=(0, 5))
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(form_frame, textvariable=date_var, font=self.entry_font, width=30)
        date_entry.grid(row=15, column=0, sticky="ew", pady=(0, 15))

        # 操作时间（系统自动记录）
        tk.Label(form_frame, text="操作时间（系统自动记录）", bg="#f0f2f5", font=self.label_font).grid(row=16, column=0,
                                                                                                     sticky="w",
                                                                                                     pady=(0, 5))
        operation_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        operation_date_entry = tk.Entry(form_frame, textvariable=operation_date_var, font=self.entry_font, width=30,
                                        state="readonly")
        operation_date_entry.grid(row=17, column=0, sticky="ew", pady=(0, 15))

        # 在表单内容中添加类别选择（放在备注前面）
        tk.Label(form_frame, text="物品类别 *", bg="#f0f2f5", font=self.label_font).grid(row=18, column=0, sticky="w",
                                                                                         pady=(0, 5))
        category_var = tk.StringVar(value="非月度采购物品")
        category_frame = tk.Frame(form_frame, bg="#f0f2f5")
        category_frame.grid(row=19, column=0, sticky="w", pady=(0, 15))

        tk.Radiobutton(
            category_frame,
            text="非月度采购物品",
            variable=category_var,
            value="非月度采购物品",
            bg="#f0f2f5",
            font=self.label_font
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            category_frame,
            text="月度采购物品",
            variable=category_var,
            value="月度采购物品",
            bg="#f0f2f5",
            font=self.label_font
        ).pack(side=tk.LEFT)

        # 调整备注的行号
        tk.Label(form_frame, text="备注", bg="#f0f2f5", font=self.label_font).grid(row=20, column=0, sticky="w",
                                                                                   pady=(0, 5))
        notes_var = tk.StringVar()
        notes_entry = tk.Entry(form_frame, textvariable=notes_var, font=self.entry_font, width=30)
        notes_entry.grid(row=21, column=0, sticky="ew", pady=(0, 20))

        # 在备注字段后面添加购买链接字段
        tk.Label(form_frame, text="购买链接", bg="#f0f2f5", font=self.label_font).grid(row=22, column=0, sticky="w",
                                                                                       pady=(0, 5))
        purchase_link_var = tk.StringVar()
        purchase_link_entry = tk.Entry(form_frame, textvariable=purchase_link_var, font=self.entry_font, width=30)
        purchase_link_entry.grid(row=23, column=0, sticky="ew", pady=(0, 20))

        # 按钮（确保在可见区域）
        btn_frame = tk.Frame(form_frame, bg="#f0f2f5")
        btn_frame.grid(row=24, column=0, sticky="e", pady=(10, 0))

        def submit():
            """提交新增表单"""
            code = code_var.get().strip()
            name = name_var.get().strip()
            spec = spec_var.get().strip()
            qty = qty_var.get().strip()
            company = company_var.get().strip()
            dept = dept_var.get().strip()
            recipient = recipient_var.get().strip()
            date = date_var.get().strip()
            operation_date = operation_date_var.get().strip()
            notes = notes_var.get().strip()
            purchase_link = purchase_link_var.get().strip()  # 获取购买链接

            # 验证输入
            if not code or not name or not qty or not spec:
                messagebox.showerror("错误", "物品编码、名称、规格和数量是必填项！")
                return

            try:
                qty = int(qty)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("错误", "数量必须是正整数！")
                return

            # 查找是否已存在该物品的相同规格
            existing_item = next((item for item in self.inventory
                                  if item["name"].lower().strip() == name.lower().strip()
                                  and item.get("spec", "").lower().strip() == spec.lower().strip()
                                  and item.get("company", "").lower().strip() == company.lower().strip()), None)

            # 在创建新物品时添加category字段和purchase_link字段
            if existing_item:
                # 更新现有物品
                existing_item["quantity"] += qty
                existing_item["last_updated"] = date
                # 只有在新增时才更新类别和购买链接
                if "category" not in existing_item:
                    existing_item["category"] = category_var.get()
                if "purchase_link" not in existing_item or not existing_item["purchase_link"]:
                    existing_item["purchase_link"] = purchase_link
            else:
                # 创建新物品
                new_id = max(int(item["id"]) for item in self.inventory) + 1 if self.inventory else 1
                self.inventory.append({
                    "id": str(new_id),
                    "code": code,
                    "name": name,
                    "spec": spec,
                    "quantity": qty,
                    "company": company,
                    "last_updated": date,
                    "category": category_var.get(),  # 添加类别字段
                    "purchase_link": purchase_link  # 添加购买链接字段
                })

            # 记录操作（添加到记录列表开头，确保最新记录在最上面）
            if self.records:
                record_id = max(int(record["id"]) for record in self.records) + 1
            else:
                record_id = 1

            # 将新记录插入到列表开头（确保最新记录在最上面）
            new_record = {
                "id": str(record_id),  # 保存为字符串以保持一致性
                "type": "add",
                "item_id": existing_item["id"] if existing_item else new_id,
                "code": code,
                "name": name,
                "spec": spec,
                "quantity": qty,
                "company": company,
                "department": dept,
                "recipient": recipient,
                "date": date,  # 物品新增时间
                "operation_date": operation_date,  # 操作时间
                "notes": notes
            }
            self.records.insert(0, new_record)

            # 保存数据
            self.save_inventory()
            self.save_records()

            # 更新UI
            self.update_table()
            self.update_stats()

            messagebox.showinfo("成功", "物品添加成功！")
            dialog.destroy()

        def cancel():
            """取消操作"""
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="取消",
            bg="#6c757d",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=cancel
        ).pack(side=tk.LEFT, padx=5)

        submit_btn = tk.Button(
            btn_frame,
            text="保存",
            bg="#4e73df",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=submit
        )
        submit_btn.pack(side=tk.LEFT, padx=5)

        # 确保滚动到顶部
        canvas.yview_moveto(0)

    def open_edit_dialog(self):
        """打开修改物品名称对话框"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showinfo("提示", "请先在表格中选择一个物品！")
            return

        # 获取选中的物品名称
        item_values = self.tree.item(selected_item)["values"]
        old_name = item_values[0]

        dialog = tk.Toplevel(self.root)
        dialog.title("修改物品名称")
        dialog.geometry("410x250")
        dialog.transient(self.root)
        # dialog.grab_set()

        # 设置对话框背景
        dialog.configure(bg="#f0f2f5")

        # 对话框标题
        tk.Label(
            dialog,
            text="修改物品名称",
            font=self.title_font,
            bg="#36b9cc",
            fg="white",
            padx=15,
            pady=10
        ).pack(fill=tk.X)

        # 表单容器
        form_frame = tk.Frame(dialog, bg="#f0f2f5", padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 原物品名称
        tk.Label(form_frame, text="原物品名称", bg="#f0f2f5", font=self.label_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            form_frame,
            text=old_name,
            bg="#f0f2f5",
            font=self.entry_font,
            padx=5,
            pady=5
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        # 新物品名称
        tk.Label(form_frame, text="新物品名称 *", bg="#f0f2f5", font=self.label_font).grid(row=1, column=0, sticky="w",
                                                                                           pady=(10, 0))
        new_name_var = tk.StringVar()
        new_name_entry = tk.Entry(form_frame, textvariable=new_name_var, font=self.entry_font, width=30)
        new_name_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(10, 0))

        # 按钮
        btn_frame = tk.Frame(form_frame, bg="#f0f2f5")
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="e", pady=(20, 0))

        def submit():
            """提交修改"""
            new_name = new_name_var.get().strip()
            if not new_name:
                messagebox.showerror("错误", "新物品名称不能为空！")
                return

            # 更新所有相关物品记录
            for item in self.inventory:
                if item["name"] == old_name:
                    item["name"] = new_name

            # 保存数据
            self.save_inventory()

            # 更新UI
            self.update_table()
            self.update_stats()

            messagebox.showinfo("成功", "物品名称修改成功！")
            dialog.destroy()

        def cancel():
            """取消操作"""
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="取消",
            bg="#6c757d",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=cancel
        ).pack(side=tk.LEFT, padx=5)

        submit_btn = tk.Button(
            btn_frame,
            text="保存",
            bg="#36b9cc",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=submit
        )
        submit_btn.pack(side=tk.LEFT, padx=5)

    def open_restock_dialog(self):
        """打开入库对话框"""
        if not self.inventory:
            messagebox.showinfo("提示", "库存中没有物品，请先添加物品！")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("物品入库")
        dialog.geometry("450x700")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        # dialog.grab_set()

        # 设置对话框背景
        dialog.configure(bg="#f0f2f5")

        # 对话框标题
        tk.Label(
            dialog,
            text="物品入库",
            font=self.title_font,
            bg="#4e73df",
            fg="white",
            padx=15,
            pady=10
        ).pack(fill=tk.X)

        # 创建主框架
        main_frame = tk.Frame(dialog, bg="#f0f2f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建Canvas和滚动条
        canvas = tk.Canvas(main_frame, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f2f5")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 表单内容
        form_frame = tk.Frame(scrollable_frame, bg="#f0f2f5", padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 选择公司
        tk.Label(form_frame, text="选择公司 *", bg="#f0f2f5", font=self.label_font).grid(row=0, column=0, sticky="w",
                                                                                         pady=(0, 5))
        company_var = tk.StringVar()
        company_combobox = ttk.Combobox(
            form_frame,
            textvariable=company_var,
            font=self.entry_font,
            width=28,
            state="readonly"
        )

        # 获取所有公司名称（去重）
        companies = sorted(list(set(item.get('company', '') for item in self.inventory if item.get('company'))))
        company_combobox["values"] = companies
        if companies:
            company_combobox.current(0)
        company_combobox.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # 当公司选择变化时更新物品列表
        def update_items_list(event=None):
            selected_company = company_var.get()
            items = []

            for item in self.inventory:
                # 如果选择了特定公司，只显示该公司的物品
                if selected_company and item.get('company', '') != selected_company:
                    continue

                spec = item.get('spec', '')
                display_text = f"{item['name']}"
                if spec:
                    display_text += f" ({spec})"
                display_text += f" - 库存: {item['quantity']}"
                items.append(display_text)

            item_combobox["values"] = items
            if items:
                item_combobox.current(0)
            else:
                item_combobox.set("")
                item_var.set("")

        # 选择物品
        tk.Label(form_frame, text="选择物品 *", bg="#f0f2f5", font=self.label_font).grid(row=2, column=0, sticky="w",
                                                                                         pady=(0, 5))
        item_var = tk.StringVar()
        item_combobox = ttk.Combobox(
            form_frame,
            textvariable=item_var,
            font=self.entry_font,
            width=28,
            state="readonly"
        )
        item_combobox.grid(row=3, column=0, sticky="ew", pady=(0, 15))

        # 初始更新物品列表
        update_items_list()

        # 绑定公司选择变化事件
        company_var.trace_add("write", lambda *args: update_items_list())

        # 入库数量
        tk.Label(form_frame, text="入库数量 *", bg="#f0f2f5", font=self.label_font).grid(row=4, column=0, sticky="w",
                                                                                         pady=(0, 5))
        qty_var = tk.StringVar()
        qty_entry = tk.Entry(form_frame, textvariable=qty_var, font=self.entry_font, width=30)
        qty_entry.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        tk.Label(
            form_frame,
            text="注意：入库操作会增加库存数量",
            bg="#f0f2f5",
            fg="#1cc88a",
            font=self.label_font
        ).grid(row=6, column=0, sticky="w", pady=(0, 10))

        # 入库时间
        tk.Label(form_frame, text="入库时间 *", bg="#f0f2f5", font=self.label_font).grid(row=7, column=0, sticky="w",
                                                                                         pady=(0, 5))
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(form_frame, textvariable=date_var, font=self.entry_font, width=30)
        date_entry.grid(row=8, column=0, sticky="ew", pady=(0, 15))

        # 操作时间
        tk.Label(form_frame, text="操作时间（系统自动记录）", bg="#f0f2f5", font=self.label_font).grid(row=9, column=0,
                                                                                                     sticky="w",
                                                                                                     pady=(0, 5))
        operation_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        operation_date_entry = tk.Entry(form_frame, textvariable=operation_date_var, font=self.entry_font, width=30,
                                        state="readonly")
        operation_date_entry.grid(row=10, column=0, sticky="ew", pady=(0, 15))

        # 备注
        tk.Label(form_frame, text="备注", bg="#f0f2f5", font=self.label_font).grid(row=11, column=0, sticky="w",
                                                                                   pady=(0, 5))
        notes_var = tk.StringVar()
        notes_entry = tk.Entry(form_frame, textvariable=notes_var, font=self.entry_font, width=30)
        notes_entry.grid(row=12, column=0, sticky="ew", pady=(0, 15))

        # 按钮
        btn_frame = tk.Frame(form_frame, bg="#f0f2f5")
        btn_frame.grid(row=13, column=0, sticky="e", pady=(20, 0))

        def submit():
            """提交入库表单"""
            # 禁用提交按钮，防止重复提交
            submit_btn.config(state="disabled")

            selected_company = company_var.get()
            selected_item = item_var.get()
            qty = qty_var.get().strip()
            date = date_var.get().strip()
            operation_date = operation_date_var.get().strip()
            notes = notes_var.get().strip()

            # 验证输入
            if not selected_item or not qty:
                messagebox.showerror("错误", "请选择物品并输入数量！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return

            try:
                qty = int(qty)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("错误", "数量必须是正整数！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return

            # 获取物品名称和规格
            parts = selected_item.split(" - ")
            name_spec = parts[0].split(" (")
            item_name = name_spec[0].strip()
            item_spec = name_spec[1].replace(")", "").strip() if len(name_spec) > 1 else ""

            # 查找物品
            item = next((i for i in self.inventory
                         if i["name"] == item_name
                         and i.get("spec", "") == item_spec
                         and (not selected_company or i.get("company", "") == selected_company)), None)
            if not item:
                messagebox.showerror("错误", "未找到所选物品！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return

            # 更新库存
            item["quantity"] += qty
            item["last_updated"] = date

            # 记录操作（添加到记录列表开头，确保最新记录在最上面）
            if self.records:
                record_id = max(int(record["id"]) for record in self.records) + 1
            else:
                record_id = 1

            # 将新记录插入到列表开头（确保最新记录在最上面）
            new_record = {
                "id": str(record_id),  # 保存为字符串以保持一致性
                "type": "restock",  # 入库类型
                "item_id": item["id"],
                "code": item.get("code", ""),
                "name": item["name"],
                "spec": item.get("spec", ""),
                "quantity": qty,
                "company": item.get("company", ""),
                "department": "",  # 入库不需要部门
                "recipient": "",  # 入库不需要领取人
                "date": date,  # 物品入库时间
                "operation_date": operation_date,  # 操作时间
                "notes": notes,
                "image_path": ""  # 入库不需要图片
            }
            self.records.insert(0, new_record)

            # 保存数据
            self.save_inventory()
            self.save_records()

            # 更新UI
            self.update_table()
            self.update_stats()

            messagebox.showinfo("成功", "物品入库成功！")
            dialog.destroy()

        def cancel():
            """取消操作"""
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="取消",
            bg="#6c757d",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=cancel
        ).pack(side=tk.LEFT, padx=5)

        submit_btn = tk.Button(
            btn_frame,
            text="确认入库",
            bg="#4e73df",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=submit
        )
        submit_btn.pack(side=tk.LEFT, padx=5)

        # 确保滚动到顶部
        canvas.yview_moveto(0)
        # 更新滚动区域
        canvas.configure(scrollregion=canvas.bbox("all"))

    def open_update_dialog(self):
        """打开出库对话框"""
        if not self.inventory:
            messagebox.showinfo("提示", "库存中没有物品，请先添加物品！")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("物品出库")
        dialog.geometry("450x950")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        # dialog.grab_set()

        # 设置对话框背景
        dialog.configure(bg="#f0f2f5")

        # 对话框标题
        tk.Label(
            dialog,
            text="物品出库",
            font=self.title_font,
            bg="#f6c23e",
            fg="white",
            padx=15,
            pady=10
        ).pack(fill=tk.X)

        # 创建主框架
        main_frame = tk.Frame(dialog, bg="#f0f2f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建Canvas和滚动条
        canvas = tk.Canvas(main_frame, bg="#f0f2f5", highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f2f5")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # 表单内容
        form_frame = tk.Frame(scrollable_frame, bg="#f0f2f5", padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 选择公司
        tk.Label(form_frame, text="选择公司 *", bg="#f0f2f5", font=self.label_font).grid(row=0, column=0, sticky="w",
                                                                                         pady=(0, 5))
        company_var = tk.StringVar()
        company_combobox = ttk.Combobox(
            form_frame,
            textvariable=company_var,
            font=self.entry_font,
            width=28,
            state="readonly"
        )

        # 获取所有公司名称（去重）
        companies = sorted(list(set(item.get('company', '') for item in self.inventory if item.get('company'))))
        # companies.insert(0, "全部公司")  # 添加"全部公司"选项
        company_combobox["values"] = companies
        company_combobox.current(0)
        company_combobox.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # 当公司选择变化时更新物品列表
        def update_items_list(event=None):
            selected_company = company_var.get()
            items = []

            for item in self.inventory:
                # 如果选择了特定公司，只显示该公司的物品
                if selected_company != "全部公司" and item.get('company', '') != selected_company:
                    continue

                # 只显示库存大于1的物品
                if item["quantity"] > 0:
                    spec = item.get('spec', '')
                    display_text = f"{item['name']}"
                    if spec:
                        display_text += f" ({spec})"
                    display_text += f" - 库存: {item['quantity']}"
                    items.append(display_text)

            item_combobox["values"] = items
            if items:
                item_combobox.current(0)
            else:
                item_combobox.set("")
                item_var.set("")

        # 选择物品
        tk.Label(form_frame, text="选择物品 *", bg="#f0f2f5", font=self.label_font).grid(row=2, column=0, sticky="w",
                                                                                         pady=(0, 5))
        item_var = tk.StringVar()
        item_combobox = ttk.Combobox(
            form_frame,
            textvariable=item_var,
            font=self.entry_font,
            width=28,
            state="readonly"
        )
        item_combobox.grid(row=3, column=0, sticky="ew", pady=(0, 15))

        # 初始更新物品列表
        update_items_list()

        # 绑定公司选择变化事件
        company_var.trace_add("write", lambda *args: update_items_list())

        # 领取数量
        tk.Label(form_frame, text="领取数量 *", bg="#f0f2f5", font=self.label_font).grid(row=4, column=0, sticky="w",
                                                                                         pady=(0, 5))
        qty_var = tk.StringVar()
        qty_entry = tk.Entry(form_frame, textvariable=qty_var, font=self.entry_font, width=30)
        qty_entry.grid(row=5, column=0, sticky="ew", pady=(0, 15))
        tk.Label(
            form_frame,
            text="注意：出库操作会减少库存数量",
            bg="#f0f2f5",
            fg="#e74a3b",
            font=self.label_font
        ).grid(row=6, column=0, sticky="w", pady=(0, 10))

        # 领取部门
        tk.Label(form_frame, text="领取部门 *", bg="#f0f2f5", font=self.label_font).grid(row=7, column=0, sticky="w",
                                                                                         pady=(0, 5))
        dept_var = tk.StringVar()
        dept_entry = tk.Entry(form_frame, textvariable=dept_var, font=self.entry_font, width=30)
        dept_entry.grid(row=8, column=0, sticky="ew", pady=(0, 15))

        # 领取人
        tk.Label(form_frame, text="领取人 *", bg="#f0f2f5", font=self.label_font).grid(row=9, column=0, sticky="w",
                                                                                       pady=(0, 5))
        recipient_var = tk.StringVar()
        recipient_entry = tk.Entry(form_frame, textvariable=recipient_var, font=self.entry_font, width=30)
        recipient_entry.grid(row=10, column=0, sticky="ew", pady=(0, 15))

        # 领取时间
        tk.Label(form_frame, text="领取时间（物品领取时间）*", bg="#f0f2f5", font=self.label_font).grid(row=11, column=0,
                                                                                                      sticky="w",
                                                                                                      pady=(0, 5))
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(form_frame, textvariable=date_var, font=self.entry_font, width=30)
        date_entry.grid(row=12, column=0, sticky="ew", pady=(0, 15))

        # 操作时间
        tk.Label(form_frame, text="操作时间（系统自动记录）", bg="#f0f2f5", font=self.label_font).grid(row=13, column=0,
                                                                                                     sticky="w",
                                                                                                     pady=(0, 5))
        operation_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        operation_date_entry = tk.Entry(form_frame, textvariable=operation_date_var, font=self.entry_font, width=30,
                                        state="readonly")
        operation_date_entry.grid(row=14, column=0, sticky="ew", pady=(0, 15))

        # 备注
        tk.Label(form_frame, text="备注", bg="#f0f2f5", font=self.label_font).grid(row=15, column=0, sticky="w",
                                                                                   pady=(0, 5))
        notes_var = tk.StringVar()
        notes_entry = tk.Entry(form_frame, textvariable=notes_var, font=self.entry_font, width=30)
        notes_entry.grid(row=16, column=0, sticky="ew", pady=(0, 15))

        # 添加图片上传控件
        tk.Label(form_frame, text="上传图片 *", bg="#f0f2f5", font=self.label_font).grid(row=17, column=0, sticky="w",
                                                                                         pady=(0, 5))

        # 图片路径变量
        image_path_var = tk.StringVar()

        # 创建图片预览和路径显示的垂直布局框架
        image_container = tk.Frame(form_frame, bg="#f0f2f5")
        image_container.grid(row=18, column=0, sticky="ew", pady=(0, 10))

        # 图片预览标签
        image_label = tk.Label(image_container, bg="#f0f2f5")
        image_label.pack(side=tk.TOP, pady=(0, 5))

        # 图片路径显示
        image_path_display = tk.Label(
            image_container,
            textvariable=image_path_var,
            bg="#f0f2f5",
            font=self.label_font,
            wraplength=300
        )
        image_path_display.pack(side=tk.TOP, fill=tk.X)

        # 图片上传按钮
        def upload_image():
            file_path = filedialog.askopenfilename(
                title="选择图片",
                filetypes=[("图片文件", "*.jpg;*.jpeg;*.png;*.bmp")]
            )
            if file_path:
                try:
                    # 验证文件大小（限制为5MB以内）
                    if os.path.getsize(file_path) > 5 * 1024 * 1024:
                        messagebox.showerror("错误", "图片文件太大，请选择小于5MB的图片！")
                        return

                    # 验证图片格式
                    try:
                        img = Image.open(file_path)
                        img.verify()  # 验证图片完整性
                        img = Image.open(file_path)  # 重新打开已验证的图片
                    except Exception as e:
                        messagebox.showerror("错误", f"图片文件损坏或不支持: {str(e)}")
                        return

                    # 限制图片大小，防止过大
                    max_size = (300, 300)
                    img.thumbnail(max_size, Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    image_label.configure(image=photo)
                    image_label.image = photo

                    # 显示文件名
                    image_path_var.set(os.path.basename(file_path))
                    # 保存完整路径
                    image_path_var.full_path = file_path

                    # 更新滚动区域
                    canvas.configure(scrollregion=canvas.bbox("all"))
                except Exception as e:
                    messagebox.showerror("错误", f"无法加载图片: {str(e)}")

        upload_btn = tk.Button(
            form_frame,
            text="浏览图片...",
            command=upload_image,
            bg="#4e73df",
            fg="white",
            font=self.button_font,
            padx=10
        )
        upload_btn.grid(row=19, column=0, sticky="w", pady=(0, 20))

        # 按钮框架
        btn_frame = tk.Frame(form_frame, bg="#f0f2f5")
        btn_frame.grid(row=20, column=0, sticky="e", pady=(10, 0))

        def submit():
            """提交变更表单"""
            # 禁用提交按钮，防止重复提交
            submit_btn.config(state="disabled")

            selected_company = company_var.get()
            selected_item = item_var.get()
            qty = qty_var.get().strip()
            dept = dept_var.get().strip()
            recipient = recipient_var.get().strip()
            date = date_var.get().strip()
            operation_date = operation_date_var.get().strip()
            notes = notes_var.get().strip()

            # 新增必填验证
            if not dept:
                messagebox.showerror("错误", "领取部门是必填项！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return
            if not recipient:
                messagebox.showerror("错误", "领取人是必填项！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return
            if not hasattr(image_path_var, 'full_path') or not image_path_var.full_path:
                messagebox.showerror("错误", "请上传领料单图片！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return

            # 验证输入
            if not selected_item or not qty:
                messagebox.showerror("错误", "请选择物品并输入数量！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return

            try:
                qty = int(qty)
                if qty <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("错误", "数量必须是正整数！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return

            # 获取物品名称和规格
            parts = selected_item.split(" - ")
            name_spec = parts[0].split(" (")
            item_name = name_spec[0].strip()
            item_spec = name_spec[1].replace(")", "").strip() if len(name_spec) > 1 else ""

            # 查找物品
            item = next((i for i in self.inventory
                         if i["name"] == item_name
                         and i.get("spec", "") == item_spec
                         and (selected_company == "全部公司" or i.get("company", "") == selected_company)), None)
            if not item:
                messagebox.showerror("错误", "未找到所选物品！")
                submit_btn.config(state="normal")  # 重新启用按钮
                return

            # 检查库存是否足够
            if item["quantity"] < qty:
                messagebox.showerror("错误", f"库存不足！当前库存：{item['quantity']}")
                submit_btn.config(state="normal")  # 重新启用按钮
                return

            # 更新库存
            item["quantity"] -= qty
            item["last_updated"] = date

            # 记录操作（添加到记录列表开头，确保最新记录在最上面）
            if self.records:
                record_id = max(int(record["id"]) for record in self.records) + 1
            else:
                record_id = 1

            # 处理图片路径
            image_path = ""
            if hasattr(image_path_var, 'full_path') and image_path_var.full_path:
                # 创建图片保存目录（使用相对路径）
                img_dir = os.path.join("record_images", datetime.now().strftime("%Y%m"))
                os.makedirs(img_dir, exist_ok=True)

                # 生成唯一文件名
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                ext = os.path.splitext(image_path_var.full_path)[1].lower()

                # 只允许特定扩展名
                if ext not in ['.jpg', '.jpeg', '.png', '.bmp']:
                    messagebox.showerror("错误", "不支持的图片格式！")
                    submit_btn.config(state="normal")  # 重新启用按钮
                    return

                # 使用物品名称和规格创建文件名（清理非法字符）
                safe_name = re.sub(r'[\\/*?:"<>|]', "", f"{item_name}_{item_spec}_{timestamp}{ext}")
                dest_path = os.path.join(img_dir, safe_name)

                try:
                    # 复制图片到目标位置
                    shutil.copyfile(image_path_var.full_path, dest_path)
                    # 存储相对路径
                    image_path = os.path.join("record_images", datetime.now().strftime("%Y%m"), safe_name)
                except Exception as e:
                    messagebox.showerror("错误", f"无法保存图片: {str(e)}")
                    submit_btn.config(state="normal")  # 重新启用按钮
                    return

            # 将新记录插入到列表开头（确保最新记录在最上面）
            new_record = {
                "id": str(record_id),  # 保存为字符串以保持一致性
                "type": "update",
                "item_id": item["id"],
                "code": item.get("code", ""),  # 添加编码信息
                "name": item["name"],
                "spec": item.get("spec", ""),
                "quantity": qty,
                "company": "",  # 不再记录申请公司
                "department": dept,
                "recipient": recipient,
                "date": date,  # 物品领取时间
                "operation_date": operation_date,  # 操作时间
                "notes": notes,
                "image_path": image_path  # 添加图片路径
            }
            self.records.insert(0, new_record)

            # 保存数据
            self.save_inventory()
            self.save_records()

            # 更新UI
            self.update_table()
            self.update_stats()

            messagebox.showinfo("成功", "物品出库成功！")
            dialog.destroy()

        def cancel():
            """取消操作"""
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="取消",
            bg="#6c757d",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=cancel
        ).pack(side=tk.LEFT, padx=5)

        submit_btn = tk.Button(
            btn_frame,
            text="确认出库",
            bg="#f6c23e",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=submit
        )
        submit_btn.pack(side=tk.LEFT, padx=5)

        # 确保滚动到顶部
        canvas.yview_moveto(0)
        # 更新滚动区域
        canvas.configure(scrollregion=canvas.bbox("all"))

    def open_history_dialog(self):
        """打开操作记录对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("操作记录")
        dialog.geometry("1200x600")
        dialog.transient(self.root)

        # 设置对话框背景
        dialog.configure(bg="#f0f2f5")

        # 对话框标题
        tk.Label(
            dialog,
            text="操作记录",
            font=self.title_font,
            bg="#36b9cc",
            fg="white",
            padx=15,
            pady=10
        ).pack(fill=tk.X)

        # 标签页
        tab_control = ttk.Notebook(dialog)

        # 全部记录标签页
        all_tab = ttk.Frame(tab_control)
        tab_control.add(all_tab, text="全部记录")

        # 新增记录标签页
        add_tab = ttk.Frame(tab_control)
        tab_control.add(add_tab, text="新增记录")

        # 变更记录标签页（修改标题为"变更/删除记录"）
        update_tab = ttk.Frame(tab_control)
        tab_control.add(update_tab, text="变更/删除记录")

        # 入库记录标签页
        restock_tab = ttk.Frame(tab_control)
        tab_control.add(restock_tab, text="入库记录")

        tab_control.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 填充全部记录
        self.fill_records_table(all_tab, self.records, "物品时间")

        # 填充新增记录
        add_records = [r for r in self.records if r["type"] == "add"]
        self.fill_records_table(add_tab, add_records, "新增时间")

        # 填充变更记录（包含update和delete类型的记录）
        update_records = [r for r in self.records if r["type"] in ("update", "delete")]
        self.fill_records_table(update_tab, update_records, "变更时间")

        # 填充入库记录
        restock_records = [r for r in self.records if r["type"] == "restock"]
        self.fill_records_table(restock_tab, restock_records, "入库时间")

    def fill_records_table(self, parent, records, item_date_label):
        """填充记录表格"""
        if not records:
            tk.Label(
                parent,
                text="没有操作记录",
                font=self.label_font,
                fg="#6c757d",
                pady=50
            ).pack(fill=tk.BOTH, expand=True)
            return

        # 创建带滚动条的表格容器
        container = tk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建水平和垂直滚动条
        tree_frame = tk.Frame(container)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 水平滚动条
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal")  # 这里修改为ttk
        h_scrollbar.pack(side="bottom", fill="x")

        # 垂直滚动条
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side="right", fill="y")

        # 创建表格
        columns = (
            "type", "operation_date", "item_date", "code", "name", "spec", "qty", "dept", "recipient", "notes", "image")
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            xscrollcommand=h_scrollbar.set,
            yscrollcommand=v_scrollbar.set
        )
        tree.pack(fill=tk.BOTH, expand=True)

        # 配置滚动条
        h_scrollbar.config(command=tree.xview)
        v_scrollbar.config(command=tree.yview)

        # 设置列标题
        tree.heading("type", text="操作类型", anchor=tk.CENTER)
        tree.heading("operation_date", text="操作时间", anchor=tk.CENTER)
        tree.heading("item_date", text=item_date_label, anchor=tk.CENTER)
        tree.heading("code", text="物品编码", anchor=tk.CENTER)
        tree.heading("name", text="物品名称", anchor=tk.CENTER)
        tree.heading("spec", text="规格", anchor=tk.CENTER)
        tree.heading("qty", text="数量", anchor=tk.CENTER)
        tree.heading("dept", text="领取部门", anchor=tk.CENTER)
        tree.heading("recipient", text="领取人", anchor=tk.CENTER)
        tree.heading("notes", text="备注", anchor=tk.CENTER)
        tree.heading("image", text="图片", anchor=tk.CENTER)

        # 设置列宽
        tree.column("type", width=100, anchor=tk.CENTER)  # 增加宽度以显示完整操作类型
        tree.column("operation_date", width=120, anchor=tk.CENTER)
        tree.column("item_date", width=120, anchor=tk.CENTER)
        tree.column("code", width=100, anchor=tk.CENTER)
        tree.column("name", width=150, anchor=tk.CENTER)
        tree.column("spec", width=100, anchor=tk.CENTER)
        tree.column("qty", width=60, anchor=tk.CENTER)
        tree.column("dept", width=100, anchor=tk.CENTER)
        tree.column("recipient", width=100, anchor=tk.CENTER)
        tree.column("notes", width=150, anchor=tk.CENTER)
        tree.column("image", width=80, anchor=tk.CENTER)

        # 填充数据
        for record in records:
            op_type = "新增" if record["type"] == "add" else "变更" if record["type"] == "update" else "删除" if record[
                                                                                                                     "type"] == "delete" else "入库"
            image_text = "有" if record.get("image_path") else "无"

            tree.insert("", tk.END, values=(
                op_type,
                record["operation_date"],
                record["date"],
                record.get("code", "-"),
                record["name"],
                record.get("spec", "-"),
                record["quantity"],
                record.get("department", "-"),
                record.get("recipient", "-"),
                record.get("notes", "-"),
                image_text
            ), tags=(record.get("image_path", ""),))

        # 绑定双击事件查看图片
        def view_image(event):
            item = tree.identify_row(event.y)
            if not item:
                return

            # 获取图片路径
            tags = tree.item(item, "tags")
            if tags and tags[0]:  # 第一个tag是图片路径
                self.show_image(tags[0])

        tree.bind("<Double-1>", view_image)

        # 调整列宽以适应内容
        for col in columns:
            tree.column(col, width=font.Font().measure(col) + 20)

    def show_image(self, image_path):
        """显示图片预览（添加关闭按钮和键盘事件）"""
        # 如果是相对路径，转换为绝对路径
        if not os.path.isabs(image_path):
            image_path = os.path.join(os.getcwd(), image_path)

        if not os.path.exists(image_path):
            messagebox.showerror("错误", "图片文件不存在！")
            return

        image_dialog = tk.Toplevel(self.root)
        image_dialog.title("图片预览")
        image_dialog.geometry("500x550")
        image_dialog.resizable(True, True)

        # # 设置窗口为模态（阻止操作记录窗口的操作）
        # image_dialog.grab_set()

        # 绑定窗口关闭事件
        def on_closing():
            image_dialog.grab_release()  # 释放模态
            image_dialog.destroy()

        image_dialog.protocol("WM_DELETE_WINDOW", on_closing)

        # 绑定ESC键关闭窗口
        def close_dialog(event=None):
            on_closing()

        image_dialog.bind("<Escape>", close_dialog)

        try:
            img = Image.open(image_path)
            # 调整图片大小以适应窗口
            max_size = (480, 480)
            img.thumbnail(max_size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            # 创建图片容器
            img_container = tk.Frame(image_dialog)
            img_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            img_label = tk.Label(img_container, image=photo)
            img_label.image = photo  # 保持引用
            img_label.pack(fill=tk.BOTH, expand=True)

            # 添加关闭按钮
            btn_frame = tk.Frame(image_dialog)
            btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

            tk.Button(
                btn_frame,
                text="关闭 (ESC)",
                command=close_dialog,
                bg="#4e73df",
                fg="white",
                font=self.button_font,
                padx=10,
                pady=5
            ).pack(pady=5)

            # 添加图片路径信息
            tk.Label(
                btn_frame,
                text=f"图片路径: {image_path}",
                font=self.label_font,
                wraplength=480
            ).pack(pady=5)

        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")
            image_dialog.destroy()

    def update_stats(self):
        """更新统计信息"""
        # 更新库存物品总数 - 统计唯一物品名称+规格的组合数量
        unique_items = set()
        for item in self.inventory:
            key = f"{item['name']}_{item['spec']}"  # 使用名称和规格组合作为唯一标识
            unique_items.add(key)
        self.total_items.config(text=str(len(unique_items)))

        # 更新库存总量
        total_qty = sum(item["quantity"] for item in self.inventory)
        self.total_quantity.config(text=str(total_qty))

        # 更新低库存物品数量 - 只统计状态为"需补货"的物品明细
        # 修改为统计所有库存数量<2且类别为"月度采购物品"的物品明细
        low_stock_items = [
            item for item in self.inventory
            if item["quantity"] < 2 and item["category"] == "月度采购物品"
        ]
        # 统计唯一物品名称+规格的组合数量（避免重复计算相同物品的不同公司）
        low_stock_unique = set(f"{item['name']}_{item['spec']}" for item in low_stock_items)
        self.low_stock_items.config(text=str(len(low_stock_unique)))

    def show_item_details(self, event):
        """显示物品明细"""
        selected_item = self.tree.selection()
        if not selected_item:
            return

        # 获取选中的物品名称
        item_values = self.tree.item(selected_item)["values"]
        item_name = item_values[0]

        # 查找分组数据
        group = next((g for g in self.grouped_inventory if g["name"] == item_name), None)
        if not group or not group["items"]:
            return

        # 打开明细对话框
        self.open_item_details_dialog(item_name, group["items"])

    def open_item_details_dialog(self, item_name, items):
        """打开物品明细对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"物品明细: {item_name}")
        dialog.geometry("900x550")  # 增加高度以容纳按钮
        dialog.resizable(True, True)
        dialog.transient(self.root)

        # 设置对话框背景
        dialog.configure(bg="#f0f2f5")

        # 对话框标题
        tk.Label(
            dialog,
            text=f"物品明细: {item_name}",
            font=self.title_font,
            bg="#4e73df",
            fg="white",
            padx=15,
            pady=10
        ).pack(fill=tk.X)

        # 创建表格 - 添加购买链接列
        columns = ("code", "spec", "company", "category", "quantity", "last_updated", "status", "purchase_link")
        tree = ttk.Treeview(dialog, columns=columns, show="headings")

        # 设置列标题
        tree.heading("code", text="物品编码", anchor=tk.CENTER)
        tree.heading("spec", text="规格", anchor=tk.CENTER)
        tree.heading("company", text="申请公司", anchor=tk.CENTER)
        tree.heading("category", text="物品类别", anchor=tk.CENTER)
        tree.heading("quantity", text="库存数量", anchor=tk.CENTER)
        tree.heading("last_updated", text="最近操作日期", anchor=tk.CENTER)
        tree.heading("status", text="状态", anchor=tk.CENTER)
        tree.heading("purchase_link", text="购买链接", anchor=tk.CENTER)

        # 设置列宽
        tree.column("code", width=120, anchor=tk.CENTER)
        tree.column("spec", width=120, anchor=tk.CENTER)
        tree.column("company", width=120, anchor=tk.CENTER)
        tree.column("category", width=120, anchor=tk.CENTER)
        tree.column("quantity", width=80, anchor=tk.CENTER)
        tree.column("last_updated", width=120, anchor=tk.CENTER)
        tree.column("status", width=80, anchor=tk.CENTER)
        tree.column("purchase_link", width=150, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        # 按钮框架 - 添加复制购买链接按钮
        btn_frame = tk.Frame(dialog, bg="#f0f2f5")
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # 复制购买链接按钮
        copy_link_btn = tk.Button(
            btn_frame,
            text="复制选中物品购买链接",
            bg="#1cc88a",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=lambda: self.copy_purchase_link(tree)
        )
        copy_link_btn.pack(side=tk.LEFT, padx=5)

        # 删除按钮
        delete_btn = tk.Button(
            btn_frame,
            text="删除选中物品",
            bg="#e74a3b",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=lambda: self.delete_detail_item(tree, items, dialog)
        )
        delete_btn.pack(side=tk.LEFT, padx=5)

        # 关闭按钮
        close_btn = tk.Button(
            btn_frame,
            text="关闭",
            bg="#6c757d",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=dialog.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

        # 填充数据
        for item in items:
            status = "需补货" if item["quantity"] < 2 and item["category"] == "月度采购物品" else "库存充足"
            purchase_link = item.get("purchase_link", "")
            # 如果购买链接太长，显示简略版本
            display_link = purchase_link if len(purchase_link) <= 20 else purchase_link[:20] + "..."

            tree.insert("", tk.END, values=(
                item.get("code", "-"),
                item.get("spec", "-"),
                item.get("company", "-"),
                item.get("category", "-"),
                item["quantity"],
                item.get("last_updated", "-"),
                status,
                display_link
            ), tags=(item["id"],))  # 使用物品ID作为标签

        # 绑定双击事件编辑明细
        tree.bind("<Double-1>", lambda e: self.edit_detail_item(tree, items))

    def copy_purchase_link(self, tree):
        """复制选中物品的购买链接"""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择一个物品！")
            return

        # 获取选中的物品ID
        tags = tree.item(selected_item, "tags")
        if not tags:
            return

        item_id = tags[0]

        # 根据物品ID在库存中查找购买链接
        purchase_link = ""
        for item in self.inventory:
            if item["id"] == item_id:
                purchase_link = item.get("purchase_link", "")
                break

        if not purchase_link:
            messagebox.showinfo("提示", "该物品没有购买链接！")
            return

        # 复制到剪贴板
        self.root.clipboard_clear()
        self.root.clipboard_append(purchase_link)
        self.root.update()  # 保持剪贴板内容
        messagebox.showinfo("成功", "购买链接已复制到剪贴板！")

    def delete_detail_item(self, tree, items, dialog):
        """删除选中的明细物品"""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择要删除的物品明细！")
            return

        # 获取选中的物品ID
        tags = tree.item(selected_item, "tags")
        if not tags:
            return

        item_id = tags[0]

        # 确认删除
        if not messagebox.askyesno("确认删除", "确定要删除这个物品明细吗？此操作不可恢复！"):
            return

        # 从库存中删除物品
        self.inventory = [item for item in self.inventory if item["id"] != item_id]

        # 添加删除记录
        if self.records:
            record_id = max(int(record["id"]) for record in self.records) + 1
            record_id = max(record_id, max(int(item["id"]) for item in self.inventory) + 1) if self.inventory else 1
        else:
            record_id = 1

        # 查找被删除的物品信息
        deleted_item = next((item for item in items if item["id"] == item_id), None)
        if deleted_item:
            # 添加删除记录（插入到列表开头）
            delete_record = {
                "id": str(record_id),
                "type": "delete",
                "item_id": item_id,
                "code": deleted_item.get("code", ""),
                "name": deleted_item["name"],
                "spec": deleted_item.get("spec", ""),
                "quantity": 0,
                "company": deleted_item.get("company", ""),
                "department": "",
                "recipient": "",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "operation_date": datetime.now().strftime("%Y-%m-%d"),
                "notes": "删除物品明细",
                "image_path": ""
            }
            self.records.insert(0, delete_record)

        # 保存数据
        self.save_inventory()
        self.save_records()

        # 更新UI
        self.update_table()
        self.update_stats()

        # 关闭对话框
        dialog.destroy()
        messagebox.showinfo("成功", "物品明细删除成功！")

    def edit_detail_item(self, tree, items):
        """编辑明细物品"""
        selected_item = tree.selection()
        if not selected_item:
            return

        # 获取选中的物品ID
        tags = tree.item(selected_item, "tags")
        if not tags:
            return

        item_id = tags[0]

        # 查找物品
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return

        # 打开编辑对话框
        self.open_edit_detail_dialog(item)

    def open_edit_detail_dialog(self, item):
        """打开编辑明细对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑物品明细")
        dialog.geometry("500x500")
        dialog.transient(self.root)
        # dialog.grab_set()

        # 设置对话框背景
        dialog.configure(bg="#f0f2f5")

        # 对话框标题
        tk.Label(
            dialog,
            text="编辑物品明细",
            font=self.title_font,
            bg="#36b9cc",
            fg="white",
            padx=15,
            pady=10
        ).pack(fill=tk.X)

        # 表单容器
        form_frame = tk.Frame(dialog, bg="#f0f2f5", padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)

        # 物品名称（不可编辑）
        tk.Label(form_frame, text="物品名称", bg="#f0f2f5", font=self.label_font).grid(row=0, column=0, sticky="w")
        tk.Label(
            form_frame,
            text=item["name"],
            bg="#f0f2f5",
            font=self.entry_font,
            padx=5,
            pady=5
        ).grid(row=0, column=1, sticky="w", padx=(10, 0))

        # 规格
        tk.Label(form_frame, text="规格 *", bg="#f0f2f5", font=self.label_font).grid(row=1, column=0, sticky="w",
                                                                                     pady=(10, 0))
        spec_var = tk.StringVar(value=item.get("spec", ""))
        spec_entry = tk.Entry(form_frame, textvariable=spec_var, font=self.entry_font, width=30)
        spec_entry.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=(10, 0))

        # 在表单内容中添加类别选择（放在规格后面）
        tk.Label(form_frame, text="物品类别 *", bg="#f0f2f5", font=self.label_font).grid(row=2, column=0, sticky="w",
                                                                                         pady=(10, 0))
        category_var = tk.StringVar(value=item.get("category", "非月度采购物品"))
        category_frame = tk.Frame(form_frame, bg="#f0f2f5")
        category_frame.grid(row=2, column=1, sticky="w", pady=(10, 0))

        tk.Radiobutton(
            category_frame,
            text="非月度采购物品",
            variable=category_var,
            value="非月度采购物品",
            bg="#f0f2f5",
            font=self.label_font
        ).pack(side=tk.LEFT, padx=(0, 20))

        tk.Radiobutton(
            category_frame,
            text="月度采购物品",
            variable=category_var,
            value="月度采购物品",
            bg="#f0f2f5",
            font=self.label_font
        ).pack(side=tk.LEFT)

        # 调整后续组件的行号（公司、编码等）
        # 申请公司
        tk.Label(form_frame, text="申请公司", bg="#f0f2f5", font=self.label_font).grid(row=3, column=0, sticky="w",
                                                                                       pady=(10, 0))
        company_var = tk.StringVar(value=item.get("company", ""))
        company_entry = tk.Entry(form_frame, textvariable=company_var, font=self.entry_font, width=30)
        company_entry.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=(10, 0))

        # 物品编码
        tk.Label(form_frame, text="物品编码 *", bg="#f0f2f5", font=self.label_font).grid(row=4, column=0, sticky="w",
                                                                                         pady=(10, 0))
        code_var = tk.StringVar(value=item.get("code", ""))
        code_entry = tk.Entry(form_frame, textvariable=code_var, font=self.entry_font, width=30)
        code_entry.grid(row=4, column=1, sticky="ew", padx=(10, 0), pady=(10, 0))

        # 在物品编码后面添加购买链接字段
        tk.Label(form_frame, text="购买链接", bg="#f0f2f5", font=self.label_font).grid(row=5, column=0, sticky="w",
                                                                                       pady=(10, 0))
        purchase_link_var = tk.StringVar(value=item.get("purchase_link", ""))
        purchase_link_entry = tk.Entry(form_frame, textvariable=purchase_link_var, font=self.entry_font, width=30)
        purchase_link_entry.grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=(10, 0))

        # 按钮
        btn_frame = tk.Frame(form_frame, bg="#f0f2f5")
        btn_frame.grid(row=5, column=0, columnspan=2, sticky="e", pady=(20, 0))

        def submit():
            """提交修改"""
            # 验证输入
            if not spec_var.get().strip():
                messagebox.showerror("错误", "规格不能为空！")
                return

            # 获取原始物品编码和新物品编码
            old_code = item.get("code", "")
            new_code = code_var.get().strip()


            # 更新物品信息
            item["spec"] = spec_var.get().strip()  # 规格
            item["company"] = company_var.get().strip()  # 公司
            item["code"] = code_var.get().strip()
            item["category"] = category_var.get()  # 更新类别
            item["purchase_link"] = purchase_link_var.get().strip()  # 更新购买链接

            # 更新相关的操作记录
            for record in self.records:
                if record.get("code", "") == old_code and record.get("item_id", "") == item["id"]:
                    record["code"] = new_code

            # 记录操作（添加到记录列表开头，确保最新记录在最上面）
            if self.records:
                record_id = max(int(record["id"]) for record in self.records) + 1
            else:
                record_id = 1

            # 将新记录插入到列表开头（确保最新记录在最上面）
            new_record = {
                "id": str(record_id),  # 保存为字符串以保持一致性
                "type": "update",
                "item_id": item["id"],
                "code": new_code,
                "name": item["name"],
                "spec": item.get("spec", ""),
                "quantity": 0,  # 编辑操作不改变数量
                "company": item.get("company", ""),
                "department": "",  # 编辑操作不涉及部门
                "recipient": "",  # 编辑操作不涉及领取人
                "date": datetime.now().strftime("%Y-%m-%d"),  # 物品编辑时间
                "operation_date": datetime.now().strftime("%Y-%m-%d"),  # 操作时间
                "notes": "编辑物品明细",
                "image_path": ""  # 编辑操作不涉及图片
            }
            self.records.insert(0, new_record)

            # 保存数据
            self.save_inventory()
            self.save_records()

            # 更新UI
            self.update_table()
            self.update_stats()

            messagebox.showinfo("成功", "物品明细修改成功！")
            dialog.destroy()

        def cancel():
            """取消操作"""
            dialog.destroy()

        tk.Button(
            btn_frame,
            text="取消",
            bg="#6c757d",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=cancel
        ).pack(side=tk.LEFT, padx=5)

        submit_btn = tk.Button(
            btn_frame,
            text="保存",
            bg="#36b9cc",
            fg="white",
            font=self.button_font,
            padx=15,
            pady=5,
            command=submit
        )
        submit_btn.pack(side=tk.LEFT, padx=5)


def main():
    # 确保图片目录存在
    os.makedirs("record_images", exist_ok=True)

    root = tk.Tk()
    try:
        root.iconbitmap("application-note.ico")
    except Exception as e:
        print(f"无法加载图标文件: {e}")

    app = InventoryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()