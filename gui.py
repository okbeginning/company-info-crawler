import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import json
from datetime import datetime
import threading
import subprocess
import platform
import os
import re
from crawler import StockCrawler, ReportType
import requests

class StockCrawlerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("股票财务报告下载器")
        self.root.geometry("1200x800")  # 增加窗口大小
        
        # 加载股票代码
        try:
            with open('stock_codes.json', 'r', encoding='utf-8') as f:
                self.stock_codes = json.load(f)
        except FileNotFoundError:
            self.stock_codes = {}
            messagebox.showwarning("警告", "未找到股票代码文件，请先运行update_stock_list.py更新股票列表")
        
        # 创建爬虫实例
        self.crawler = None
        self.is_crawling = False
        
        # 创建主框架
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建左侧和右侧框架
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建文件列表选项卡
        self.file_list_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.file_list_tab, text="可下载文件列表")
        
        # 创建进度日志选项卡
        self.progress_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.progress_tab, text="爬取进度")
        
        # 股票代码搜索框架
        self.create_stock_search_frame(self.left_frame)
        
        # 年份选择框架
        self.create_year_selection_frame(self.left_frame)
        
        # 报告类型选择框架
        self.create_report_type_selection_frame(self.left_frame)
        
        # 控制按钮框架
        self.create_control_buttons_frame(self.left_frame)
        
        # 文件列表框架（放在文件列表选项卡中）
        self.create_file_list_frame(self.file_list_tab)
        
        # 进度显示框架（放在进度日志选项卡中）
        self.create_progress_frame(self.progress_tab)
        
        # 配置主框架的网格权重
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        
        # 绑定关闭窗口事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_stock_search_frame(self, parent):
        # 股票输入框
        ttk.Label(parent, text="股票名称或代码:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.stock_entry = ttk.Entry(parent, width=30)
        self.stock_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.stock_entry.bind('<KeyRelease>', self.on_stock_input)
        
        # 股票列表
        self.stock_listbox = tk.Listbox(parent, height=5)
        self.stock_listbox.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        self.stock_listbox.bind('<<ListboxSelect>>', self.on_stock_select)
        
    def create_year_selection_frame(self, parent):
        # 年份选择框架
        year_frame = ttk.LabelFrame(parent, text="选择年份", padding="5")
        year_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 年份全选按钮
        self.year_select_all_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(year_frame, text="全选", variable=self.year_select_all_var, 
                       command=self.toggle_all_years).grid(row=0, column=0, padx=5, pady=2)
        
        # 创建年份复选框
        self.year_vars = {}
        current_year = datetime.now().year
        for i, year in enumerate(range(2015, current_year + 1)):
            self.year_vars[year] = tk.BooleanVar()
            ttk.Checkbutton(year_frame, text=str(year), variable=self.year_vars[year],
                          command=self.check_year_selection).grid(
                row=(i+1)//5, column=(i+1)%5, padx=5, pady=2
            )
            
    def create_report_type_selection_frame(self, parent):
        # 报告类型选择框架
        type_frame = ttk.LabelFrame(parent, text="选择报告类型", padding="5")
        type_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # 报告类型全选按钮
        self.type_select_all_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(type_frame, text="全选", variable=self.type_select_all_var,
                       command=self.toggle_all_types).grid(row=0, column=0, padx=5, pady=2)
        
        # 创建报告类型复选框
        report_types = [
            ReportType.ANNUAL.report_name,
            ReportType.SEMI_ANNUAL.report_name,
            ReportType.Q1.report_name,
            ReportType.Q3.report_name,
            ReportType.IPO_PROSPECTUS.report_name,
            ReportType.IPO_INQUIRY.report_name,
            ReportType.INTERNAL.report_name,
            ReportType.ESG.report_name,
            ReportType.SUSTAINABLE.report_name,
            ReportType.SOCIAL.report_name
        ]
        self.type_vars = {}
        for i, report_type in enumerate(report_types):
            self.type_vars[report_type] = tk.BooleanVar(value=True)
            ttk.Checkbutton(type_frame, text=report_type, variable=self.type_vars[report_type],
                          command=self.check_type_selection).grid(
                row=(i+1)//3, column=(i+1)%3, padx=5, pady=2, sticky=tk.W
            )
            
    def create_control_buttons_frame(self, parent):
        """创建控制按钮框架"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)  # 移到报告类型选择框架下方
        
        # 开始爬取按钮
        self.start_button = ttk.Button(button_frame, text="开始爬取", command=self.start_crawling)
        self.start_button.grid(row=0, column=0, padx=5)
        
        # 暂停/继续按钮
        self.pause_button = ttk.Button(button_frame, text="暂停", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        # 下载选中文件按钮
        self.download_button = ttk.Button(button_frame, text="下载选中文件", command=self.download_selected_files, state=tk.DISABLED)
        self.download_button.grid(row=0, column=2, padx=5)
        
    def create_file_list_frame(self, parent):
        """创建文件列表框架"""
        # 创建文件列表框架
        file_list_frame = ttk.Frame(parent)
        file_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建文件列表
        columns = ('title', 'date', 'type', 'size', 'status')
        self.file_list = ttk.Treeview(file_list_frame, columns=columns, show='headings')
        
        # 设置列标题
        self.file_list.heading('title', text='标题', command=lambda: self.sort_file_list('title'))
        self.file_list.heading('date', text='发布日期', command=lambda: self.sort_file_list('date'))
        self.file_list.heading('type', text='类型', command=lambda: self.sort_file_list('type'))
        self.file_list.heading('size', text='大小', command=lambda: self.sort_file_list('size'))
        self.file_list.heading('status', text='状态')
        
        # 设置列宽
        self.file_list.column('title', width=400, minwidth=200)
        self.file_list.column('date', width=100, minwidth=100)
        self.file_list.column('type', width=100, minwidth=100)
        self.file_list.column('size', width=80, minwidth=80)
        self.file_list.column('status', width=80, minwidth=80)
        
        # 创建滚动条
        scrollbar = ttk.Scrollbar(file_list_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.file_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 配置网格权重
        file_list_frame.grid_columnconfigure(0, weight=1)
        file_list_frame.grid_rowconfigure(0, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # 绑定右键菜单
        self.file_list.bind('<Button-3>', self.show_file_list_menu)
        
        # 创建右键菜单
        self.file_list_menu = tk.Menu(self.root, tearoff=0)
        self.file_list_menu.add_command(label="复制标题", command=self.copy_file_title)
        self.file_list_menu.add_command(label="复制日期", command=self.copy_file_date)
        self.file_list_menu.add_separator()
        self.file_list_menu.add_command(label="选择相同类型", command=self.select_same_type)
        self.file_list_menu.add_command(label="选择相同年份", command=self.select_same_year)
        
        # 创建搜索框架
        search_frame = ttk.Frame(file_list_frame)
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 创建搜索输入框
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.filter_file_list)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
    def create_progress_frame(self, parent):
        """创建进度显示框架"""
        # 工具栏框架
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 日志级别选择
        level_frame = ttk.Frame(toolbar_frame)
        level_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(level_frame, text="日志级别:").pack(side=tk.LEFT)
        self.log_level_var = tk.StringVar(value="ALL")
        log_level_combo = ttk.Combobox(level_frame, textvariable=self.log_level_var, 
                                     values=["ALL", "INFO", "WARNING", "ERROR"], 
                                     width=8, state="readonly")
        log_level_combo.pack(side=tk.LEFT, padx=2)
        log_level_combo.bind('<<ComboboxSelected>>', self.filter_log)
        
        # 自动滚动开关
        scroll_frame = ttk.Frame(toolbar_frame)
        scroll_frame.pack(side=tk.LEFT, padx=10)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(scroll_frame, text="自动滚动", 
                       variable=self.auto_scroll_var).pack(side=tk.LEFT)
        
        # 清空按钮
        ttk.Button(toolbar_frame, text="清空日志", 
                  command=self.clear_progress_log).pack(side=tk.RIGHT, padx=5)
        
        # 导出日志按钮
        ttk.Button(toolbar_frame, text="导出日志",
                  command=self.export_log).pack(side=tk.RIGHT, padx=5)
        
        # 进度显示文本框
        text_frame = ttk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.progress_text = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.progress_text.yview)
        
        self.progress_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.progress_text.configure(yscrollcommand=scrollbar.set)
        
        # 为不同级别的日志设置标签
        self.progress_text.tag_configure("INFO", foreground="black")
        self.progress_text.tag_configure("WARNING", foreground="orange")
        self.progress_text.tag_configure("ERROR", foreground="red")
        self.progress_text.tag_configure("SUCCESS", foreground="green")
        
    def select_all_files(self):
        """全选文件列表"""
        for item in self.file_list.get_children():
            self.file_list.selection_add(item)
            
    def deselect_all_files(self):
        """取消全选文件列表"""
        self.file_list.selection_remove(*self.file_list.get_children())
        
    def toggle_pause(self):
        """切换暂停/继续状态"""
        if self.crawler:
            if self.crawler.is_paused:
                self.crawler.resume()
                self.pause_button.configure(text="暂停")
                self.update_progress("爬虫已继续运行")
            else:
                self.crawler.pause()
                self.pause_button.configure(text="继续")
                self.update_progress("爬虫已暂停")
                
    def start_crawling(self):
        """开始爬取流程"""
        if not hasattr(self, 'selected_stock'):
            messagebox.showwarning("警告", "请先选择股票")
            return
        
        # 获取选中的年份和报告类型
        selected_years = []
        selected_types = []
        
        # 获取选中的报告类型
        for type_name, var in self.type_vars.items():
            if var.get():
                selected_types.append(type_name)
        
        # 检查是否有选中的报告类型
        if not selected_types:
            messagebox.showwarning("警告", "请至少选择一个报告类型")
            return
        
        # 检查是否只选择了 IPO 相关报告
        ipo_types = [ReportType.IPO_PROSPECTUS.report_name, ReportType.IPO_INQUIRY.report_name]
        only_ipo = all(t in ipo_types for t in selected_types)
        
        # 如果不是只选择了 IPO 相关报告，则需要选择年份
        if not only_ipo:
            for year, var in self.year_vars.items():
                if var.get():
                    selected_years.append(year)
                    
            # 检查是否有选中的年份
            if not selected_years:
                messagebox.showwarning("警告", "请至少选择一个年份")
                return
        
        # 清空文件列表
        for item in self.file_list.get_children():
            self.file_list.delete(item)
        
        # 禁用按钮，防止重复点击
        self.start_button.configure(state=tk.DISABLED)
        self.download_button.configure(state=tk.DISABLED)
        self.pause_button.configure(state=tk.DISABLED)
        
        # 切换到进度日志选项卡
        self.notebook.select(self.progress_tab)
        
        def crawl_thread():
            try:
                # 创建爬虫实例
                self.crawler = StockCrawler(self.selected_stock['code'], self.update_progress)
                
                # 获取可下载的文件列表
                self.update_progress("正在获取可下载文件列表...")
                available_files = self.crawler.get_available_files(
                    years=selected_years if not only_ipo else None,
                    selected_types=selected_types,
                    stock_name=self.selected_stock['name']
                )
                
                if not available_files:
                    self.root.after(0, lambda: self.update_progress("未找到任何可下载的文件", "WARNING"))
                    self.root.after(0, lambda: messagebox.showwarning("提示", "未找到任何可下载的文件"))
                    self.root.after(0, lambda: self.start_button.configure(state=tk.NORMAL))
                    return
                
                def update_gui():
                    try:
                        # 清空现有的文件列表
                        for item in self.file_list.get_children():
                            self.file_list.delete(item)
                            
                        # 显示文件列表
                        for file_info in available_files:
                            values = (
                                file_info['title'],
                                file_info['date'].strftime('%Y-%m-%d'),
                                file_info['type'],
                                file_info['size'],
                                '未下载'
                            )
                            self.file_list.insert('', 'end', values=values)
                            
                        self.update_progress(f"找到 {len(available_files)} 个可下载文件")
                        
                        # 更新按钮状态
                        self.start_button.configure(state=tk.NORMAL)
                        self.download_button.configure(state=tk.NORMAL)
                        self.pause_button.configure(state=tk.NORMAL)
                        
                        # 切换到文件列表选项卡
                        self.notebook.select(self.file_list_tab)
                        
                    except Exception as e:
                        self.update_progress(f"更新界面时出错: {str(e)}", "ERROR")
                        messagebox.showerror("错误", f"更新界面失败: {str(e)}")
                
                # 在主线程中更新GUI
                self.root.after(0, update_gui)
                
            except Exception as e:
                self.root.after(0, lambda: self.update_progress(f"错误: {str(e)}", "ERROR"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"获取文件列表失败: {str(e)}"))
                self.root.after(0, lambda: self.start_button.configure(state=tk.NORMAL))
        
        # 启动爬虫线程
        threading.Thread(target=crawl_thread, daemon=True).start()
        
    def download_selected_files(self):
        """下载选中的文件"""
        selected_items = self.file_list.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择要下载的文件")
            return
            
        total_files = len(selected_items)
        success_count = 0
        
        for item in selected_items:
            file_info = self.file_list.item(item)['values']
            # 查找对应的完整文件信息
            full_file_info = next(
                (f for f in self.crawler.available_files if f['title'] == file_info[0]),
                None
            )
            
            if full_file_info:
                if self.crawler.download_file(full_file_info):
                    success_count += 1
                    
        # 显示下载完成的消息框，并询问是否打开下载文件夹
        if success_count > 0:
            if messagebox.askyesno("下载完成", 
                                 f"成功下载 {success_count}/{total_files} 个文件。\n是否打开下载文件夹？"):
                # 在 macOS 上使用 open 命令打开文件夹
                import subprocess
                subprocess.run(['open', self.crawler.download_dir])
        else:
            messagebox.showwarning("下载失败", f"下载失败！成功下载 {success_count}/{total_files} 个文件。")
            
    def toggle_all_years(self):
        """切换所有年份的选择状态"""
        state = self.year_select_all_var.get()
        for var in self.year_vars.values():
            var.set(state)
            
    def toggle_all_types(self):
        """切换所有报告类型的选择状态"""
        state = self.type_select_all_var.get()
        for var in self.type_vars.values():
            var.set(state)
            
    def check_year_selection(self):
        """检查年份选择状态，更新全选按钮"""
        all_selected = all(var.get() for var in self.year_vars.values())
        self.year_select_all_var.set(all_selected)
        
    def check_type_selection(self):
        """检查报告类型选择状态，更新全选按钮"""
        all_selected = all(var.get() for var in self.type_vars.values())
        self.type_select_all_var.set(all_selected)
        
    def on_stock_input(self, event):
        """处理股票输入事件"""
        search_text = self.stock_entry.get().strip()
        self.stock_listbox.delete(0, tk.END)
        
        if search_text:
            # 搜索匹配的股票
            matches = []
            for name, code in self.stock_codes.items():
                if search_text in name or search_text in code:
                    matches.append(f"{name} ({code})")
                if len(matches) >= 10:  # 限制显示数量
                    break
            
            for match in matches:
                self.stock_listbox.insert(tk.END, match)
                
    def on_stock_select(self, event):
        """处理股票选择事件"""
        selection = self.stock_listbox.curselection()
        if selection:
            selected = self.stock_listbox.get(selection[0])
            self.stock_entry.delete(0, tk.END)
            self.stock_entry.insert(0, selected)
            self.selected_stock = {
                'name': selected.split('(')[0].strip(),
                'code': selected.split('(')[1].split(')')[0]
            }
            
    def update_progress(self, message, level="INFO"):
        """更新进度显示"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # 如果当前日志级别符合筛选条件
        if self.log_level_var.get() == "ALL" or level == self.log_level_var.get():
            self.progress_text.insert(tk.END, log_entry, level)
            if self.auto_scroll_var.get():
                self.progress_text.see(tk.END)
                
    def clear_progress_log(self):
        """清空进度日志"""
        self.progress_text.delete(1.0, tk.END)
        
    def filter_log(self, event=None):
        """根据日志级别筛选显示"""
        # 保存当前内容
        content = self.progress_text.get(1.0, tk.END)
        lines = content.split('\n')
        self.progress_text.delete(1.0, tk.END)
        
        selected_level = self.log_level_var.get()
        for line in lines:
            if line.strip():
                if selected_level == "ALL" or f"[{selected_level}]" in line:
                    level = "INFO"
                    if "[WARNING]" in line:
                        level = "WARNING"
                    elif "[ERROR]" in line:
                        level = "ERROR"
                    self.progress_text.insert(tk.END, line + '\n', level)
                    
    def sort_file_list(self, column):
        """排序文件列表"""
        items = [(self.file_list.set(child, column), child) for child in self.file_list.get_children()]
        
        # 如果是第一次点击，按升序排序；再次点击同一列，按降序排序
        reverse = False
        if hasattr(self, '_sort_column') and self._sort_column == column:
            reverse = not getattr(self, '_sort_reverse', False)
        self._sort_column = column
        self._sort_reverse = reverse
        
        # 特殊处理日期和大小列
        if column == 'date':
            items.sort(key=lambda x: datetime.strptime(x[0], '%Y-%m-%d'), reverse=reverse)
        elif column == 'size':
            def size_to_bytes(size_str):
                if size_str == '未知':
                    return -1
                try:
                    number = float(size_str.replace('MB', ''))
                    return number
                except ValueError:
                    return -1
            items.sort(key=lambda x: size_to_bytes(x[0]), reverse=reverse)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=reverse)
        
        # 重新排列项目
        for index, (_, child) in enumerate(items):
            self.file_list.move(child, '', index)
            
    def filter_file_list(self, *args):
        """过滤文件列表"""
        search_text = self.search_var.get().lower()
        children = self.file_list.get_children()
        
        # 如果搜索框为空，显示所有项目
        if not search_text:
            for child in children:
                self.file_list.reattach(child, '', 'end')
            return
        
        # 否则，只显示匹配的项目
        for child in children:
            values = [
                self.file_list.set(child, col).lower()
                for col in ('title', 'type', 'date')
            ]
            if any(search_text in value for value in values):
                self.file_list.reattach(child, '', 'end')
            else:
                self.file_list.detach(child)
                
    def show_file_list_menu(self, event):
        """显示文件列表右键菜单"""
        try:
            self.file_list_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.file_list_menu.grab_release()
            
    def copy_file_title(self):
        """复制选中文件的标题"""
        selection = self.file_list.selection()
        if selection:
            title = self.file_list.item(selection[0])['values'][0]
            self.root.clipboard_clear()
            self.root.clipboard_append(title)
            
    def copy_file_date(self):
        """复制选中文件的发布日期"""
        selection = self.file_list.selection()
        if selection:
            date = self.file_list.item(selection[0])['values'][1]
            self.root.clipboard_clear()
            self.root.clipboard_append(date)
            
    def open_excel_file(self, file_path):
        """打开Excel文件"""
        if platform.system() == 'Darwin':  # macOS
            subprocess.run(['open', file_path])
        elif platform.system() == 'Windows':  # Windows
            os.startfile(file_path)
        else:  # Linux
            subprocess.run(['xdg-open', file_path])
            
    def on_closing(self):
        """关闭窗口事件处理"""
        if messagebox.askokcancel("退出", "是否退出程序？"):
            self.root.destroy()
            
    def select_same_type(self):
        """选择相同类型的报告"""
        selection = self.file_list.selection()
        if selection:
            selected_type = self.file_list.item(selection[0])['values'][2]
            self.file_list.selection_remove(*self.file_list.selection())
            for item in self.file_list.get_children():
                if self.file_list.item(item)['values'][2] == selected_type:
                    self.file_list.selection_add(item)

    def select_same_year(self):
        """选择相同年份的报告"""
        selection = self.file_list.selection()
        if selection:
            selected_date = self.file_list.item(selection[0])['values'][1]
            selected_year = selected_date.split('-')[0]
            self.file_list.selection_remove(*self.file_list.selection())
            for item in self.file_list.get_children():
                item_date = self.file_list.item(item)['values'][1]
                if item_date.startswith(selected_year):
                    self.file_list.selection_add(item)

    def export_log(self):
        """导出日志到文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"crawler_log_{timestamp}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.progress_text.get(1.0, tk.END))
            self.update_progress(f"日志已导出到: {filename}", "SUCCESS")
            if messagebox.askyesno("完成", "日志导出成功，是否打开日志文件？"):
                self.open_excel_file(filename)
        except Exception as e:
            self.update_progress(f"导出日志失败: {str(e)}", "ERROR")
            
if __name__ == "__main__":
    root = tk.Tk()
    app = StockCrawlerGUI(root)
    root.mainloop()
