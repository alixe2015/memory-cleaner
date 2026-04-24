"""
内存急救包 - 专为 SolidWorks 用户优化
快速释放后台进程内存，让 SolidWorks 运行更流畅
v2.0 - 加入进程分类、风险评分、悬停说明
"""

import tkinter as tk
from tkinter import ttk, messagebox
import psutil
import threading
import time
from datetime import datetime

# ─── 进程知识库 ────────────────────────────────────────────────────────────
# 格式: name -> { friendly, category, risk, description, effect }
# category: "work"=工作软件, "comm"=通讯, "browser"=浏览器, "media"=媒体,
#           "cloud"=云盘, "game"=游戏, "dev"=开发, "tool"=工具, "sys_extra"=系统附加
# risk: "safe"=安全关闭, "caution"=注意(有副作用), "danger"=不建议关闭

PROCESS_DB = {
    # ── 浏览器 ──────────────────────────────────────────────────────
    "chrome.exe": {
        "friendly": "Google Chrome",
        "category": "browser",
        "risk": "caution",
        "description": "谷歌浏览器，内存占用大户，每个标签页都是独立进程",
        "effect": "关闭后所有网页标签丢失，未保存的表单数据会丢失",
    },
    "msedge.exe": {
        "friendly": "Microsoft Edge",
        "category": "browser",
        "risk": "caution",
        "description": "Windows 自带浏览器，基于 Chromium 内核",
        "effect": "关闭后所有网页标签丢失",
    },
    "firefox.exe": {
        "friendly": "Firefox 浏览器",
        "category": "browser",
        "risk": "caution",
        "description": "火狐浏览器",
        "effect": "关闭后所有网页标签丢失，可恢复上次会话",
    },
    "opera.exe": {
        "friendly": "Opera 浏览器",
        "category": "browser",
        "risk": "caution",
        "description": "Opera 浏览器，内置 VPN",
        "effect": "关闭后所有网页标签丢失",
    },
    "brave.exe": {
        "friendly": "Brave 浏览器",
        "category": "browser",
        "risk": "caution",
        "description": "注重隐私的浏览器",
        "effect": "关闭后所有网页标签丢失",
    },
    # ── 通讯软件 ────────────────────────────────────────────────────
    "wechat.exe": {
        "friendly": "微信",
        "category": "comm",
        "risk": "caution",
        "description": "微信电脑版，聊天记录本地保存",
        "effect": "关闭后无法接收消息，重新登录即可恢复",
    },
    "weixin.exe": {
        "friendly": "微信",
        "category": "comm",
        "risk": "caution",
        "description": "微信电脑版（新版）",
        "effect": "关闭后无法接收消息，重新登录即可恢复",
    },
    "dingtalk.exe": {
        "friendly": "钉钉",
        "category": "comm",
        "risk": "caution",
        "description": "阿里巴巴办公通讯软件",
        "effect": "关闭后无法接收工作消息和会议通知",
    },
    "feishu.exe": {
        "friendly": "飞书",
        "category": "comm",
        "risk": "caution",
        "description": "字节跳动办公协作平台",
        "effect": "关闭后无法接收飞书消息和日程提醒",
    },
    "lark.exe": {
        "friendly": "飞书（国际版）",
        "category": "comm",
        "risk": "caution",
        "description": "飞书国际版 Lark",
        "effect": "关闭后无法接收消息",
    },
    "qqwork.exe": {
        "friendly": "企业微信",
        "category": "comm",
        "risk": "caution",
        "description": "腾讯企业微信",
        "effect": "关闭后无法接收企业消息",
    },
    "wework.exe": {
        "friendly": "企业微信",
        "category": "comm",
        "risk": "caution",
        "description": "企业微信（新版）",
        "effect": "关闭后无法接收企业消息",
    },
    "qq.exe": {
        "friendly": "QQ",
        "category": "comm",
        "risk": "safe",
        "description": "腾讯 QQ 聊天软件",
        "effect": "关闭后无法接收消息，重新登录恢复",
    },
    "tim.exe": {
        "friendly": "TIM",
        "category": "comm",
        "risk": "safe",
        "description": "腾讯 TIM，QQ 办公版",
        "effect": "关闭后无法接收消息，重新登录恢复",
    },
    "teams.exe": {
        "friendly": "Microsoft Teams",
        "category": "comm",
        "risk": "caution",
        "description": "微软团队协作工具",
        "effect": "关闭后无法接收 Teams 消息和会议邀请",
    },
    "slack.exe": {
        "friendly": "Slack",
        "category": "comm",
        "risk": "safe",
        "description": "团队通讯工具 Slack",
        "effect": "关闭后无法接收频道消息",
    },
    "discord.exe": {
        "friendly": "Discord",
        "category": "comm",
        "risk": "safe",
        "description": "Discord 语音/文字聊天",
        "effect": "关闭后断开语音频道，无法接收消息",
    },
    # ── 媒体播放 ────────────────────────────────────────────────────
    "spotify.exe": {
        "friendly": "Spotify",
        "category": "media",
        "risk": "safe",
        "description": "Spotify 音乐播放器",
        "effect": "关闭后停止播放音乐，无其他影响",
    },
    "neteasemusic.exe": {
        "friendly": "网易云音乐",
        "category": "media",
        "risk": "safe",
        "description": "网易云音乐桌面版",
        "effect": "关闭后停止播放音乐，无其他影响",
    },
    "qqmusic.exe": {
        "friendly": "QQ音乐",
        "category": "media",
        "risk": "safe",
        "description": "QQ音乐桌面版",
        "effect": "关闭后停止播放音乐，无其他影响",
    },
    "kugou.exe": {
        "friendly": "酷狗音乐",
        "category": "media",
        "risk": "safe",
        "description": "酷狗音乐播放器",
        "effect": "关闭后停止播放音乐，无其他影响",
    },
    "vlc.exe": {
        "friendly": "VLC 播放器",
        "category": "media",
        "risk": "safe",
        "description": "VLC 开源视频播放器",
        "effect": "关闭后停止播放，无其他影响",
    },
    "potplayer.exe": {
        "friendly": "PotPlayer",
        "category": "media",
        "risk": "safe",
        "description": "PotPlayer 视频播放器",
        "effect": "关闭后停止播放，无其他影响",
    },
    # ── 游戏平台 ────────────────────────────────────────────────────
    "steam.exe": {
        "friendly": "Steam",
        "category": "game",
        "risk": "safe",
        "description": "Valve 游戏平台，常驻后台",
        "effect": "关闭后无法接收游戏更新和好友消息，游戏不受影响",
    },
    "epicgameslauncher.exe": {
        "friendly": "Epic Games",
        "category": "game",
        "risk": "safe",
        "description": "Epic 游戏启动器",
        "effect": "关闭后无法启动 Epic 游戏，无其他影响",
    },
    "origin.exe": {
        "friendly": "Origin",
        "category": "game",
        "risk": "safe",
        "description": "EA 游戏平台",
        "effect": "关闭后无法启动 EA 游戏",
    },
    "upc.exe": {
        "friendly": "Ubisoft Connect",
        "category": "game",
        "risk": "safe",
        "description": "育碧游戏平台",
        "effect": "关闭后无法启动育碧游戏",
    },
    # ── 云盘同步 ────────────────────────────────────────────────────
    "baiduyunguanjia.exe": {
        "friendly": "百度网盘",
        "category": "cloud",
        "risk": "safe",
        "description": "百度网盘客户端，后台持续同步",
        "effect": "关闭后暂停文件同步，下次打开继续",
    },
    "baidunetdisk.exe": {
        "friendly": "百度网盘",
        "category": "cloud",
        "risk": "safe",
        "description": "百度网盘客户端（新版）",
        "effect": "关闭后暂停文件同步，下次打开继续",
    },
    "onedrive.exe": {
        "friendly": "OneDrive",
        "category": "cloud",
        "risk": "safe",
        "description": "微软云盘，持续后台同步文件",
        "effect": "关闭后暂停文件同步，下次打开继续",
    },
    "dropbox.exe": {
        "friendly": "Dropbox",
        "category": "cloud",
        "risk": "safe",
        "description": "Dropbox 云盘客户端",
        "effect": "关闭后暂停文件同步",
    },
    # ── 开发工具 ────────────────────────────────────────────────────
    "code.exe": {
        "friendly": "VS Code",
        "category": "dev",
        "risk": "caution",
        "description": "Visual Studio Code 代码编辑器",
        "effect": "关闭后未保存的代码文件可能丢失（通常有自动保存）",
    },
    "cursor.exe": {
        "friendly": "Cursor",
        "category": "dev",
        "risk": "caution",
        "description": "Cursor AI 代码编辑器",
        "effect": "关闭后未保存的文件可能丢失",
    },
    "devenv.exe": {
        "friendly": "Visual Studio",
        "category": "dev",
        "risk": "caution",
        "description": "Visual Studio IDE",
        "effect": "关闭后未保存的项目可能丢失",
    },
    # ── 设计/办公软件 ───────────────────────────────────────────────
    "photoshop.exe": {
        "friendly": "Photoshop",
        "category": "work",
        "risk": "caution",
        "description": "Adobe Photoshop 图像处理",
        "effect": "关闭后未保存的PSD文件丢失",
    },
    "illustrator.exe": {
        "friendly": "Illustrator",
        "category": "work",
        "risk": "caution",
        "description": "Adobe Illustrator 矢量设计",
        "effect": "关闭后未保存的AI文件丢失",
    },
    "premiere.exe": {
        "friendly": "Premiere Pro",
        "category": "work",
        "risk": "caution",
        "description": "Adobe Premiere 视频剪辑",
        "effect": "关闭后未保存的项目丢失",
    },
    "afterfx.exe": {
        "friendly": "After Effects",
        "category": "work",
        "risk": "caution",
        "description": "Adobe After Effects 特效合成",
        "effect": "关闭后未保存的项目丢失",
    },
    "acrobat.exe": {
        "friendly": "Adobe Acrobat",
        "category": "work",
        "risk": "safe",
        "description": "Adobe PDF 阅读器/编辑器",
        "effect": "关闭后未保存的标注丢失",
    },
    "wps.exe": {
        "friendly": "WPS Office",
        "category": "work",
        "risk": "caution",
        "description": "WPS 办公套件（文档/表格/演示）",
        "effect": "关闭后未保存的文档丢失",
    },
    "et.exe": {
        "friendly": "WPS 表格",
        "category": "work",
        "risk": "caution",
        "description": "WPS 表格组件",
        "effect": "关闭后未保存的表格丢失",
    },
    "wpp.exe": {
        "friendly": "WPS 演示",
        "category": "work",
        "risk": "caution",
        "description": "WPS 演示文稿组件",
        "effect": "关闭后未保存的PPT丢失",
    },
    "excel.exe": {
        "friendly": "Excel",
        "category": "work",
        "risk": "caution",
        "description": "Microsoft Excel 电子表格",
        "effect": "关闭后未保存的数据丢失",
    },
    "winword.exe": {
        "friendly": "Word",
        "category": "work",
        "risk": "caution",
        "description": "Microsoft Word 文字处理",
        "effect": "关闭后未保存的文档丢失",
    },
    "powerpnt.exe": {
        "friendly": "PowerPoint",
        "category": "work",
        "risk": "caution",
        "description": "Microsoft PowerPoint 演示文稿",
        "effect": "关闭后未保存的PPT丢失",
    },
    "notion.exe": {
        "friendly": "Notion",
        "category": "work",
        "risk": "safe",
        "description": "Notion 笔记与协作工具（云端保存）",
        "effect": "关闭后无影响，数据已同步到云端",
    },
    "obsidian.exe": {
        "friendly": "Obsidian",
        "category": "work",
        "risk": "safe",
        "description": "Obsidian 本地笔记工具（自动保存）",
        "effect": "关闭后无影响，数据自动保存在本地",
    },
    # ── 下载工具 ────────────────────────────────────────────────────
    "thunder.exe": {
        "friendly": "迅雷",
        "category": "tool",
        "risk": "safe",
        "description": "迅雷下载工具，常驻后台占用内存",
        "effect": "关闭后正在下载的任务暂停",
    },
    "xunlei.exe": {
        "friendly": "迅雷",
        "category": "tool",
        "risk": "safe",
        "description": "迅雷下载工具（新版）",
        "effect": "关闭后正在下载的任务暂停",
    },
    # ── 会议/远程 ──────────────────────────────────────────────────
    "zoom.exe": {
        "friendly": "Zoom",
        "category": "comm",
        "risk": "safe",
        "description": "Zoom 视频会议",
        "effect": "关闭后断开当前会议",
    },
    "todesk.exe": {
        "friendly": "ToDesk",
        "category": "tool",
        "risk": "safe",
        "description": "ToDesk 远程桌面工具",
        "effect": "关闭后无法被远程连接",
    },
    "sunloginclient.exe": {
        "friendly": "向日葵远程",
        "category": "tool",
        "risk": "safe",
        "description": "向日葵远程控制客户端",
        "effect": "关闭后无法被远程连接",
    },
    # ── Windows 附加/系统相关 ───────────────────────────────────────
    "searchui.exe": {
        "friendly": "Windows 搜索",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Windows 搜索索引服务，占内存较高",
        "effect": "关闭后搜索功能暂时不可用，会自动重启",
    },
    "searchhost.exe": {
        "friendly": "Windows 搜索",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Windows 搜索服务",
        "effect": "关闭后搜索功能暂时不可用",
    },
    "runtimebroker.exe": {
        "friendly": "运行时代理",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Windows UWP 应用运行时代理",
        "effect": "关闭后部分应用可能异常，会自动重启",
    },
    "shellexperiencehost.exe": {
        "friendly": "Shell 体验",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Windows Shell 体验宿主",
        "effect": "关闭后开始菜单等可能暂时异常，会自动重启",
    },
    "microsoft.notes.exe": {
        "friendly": "便签",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Windows 便签（Sticky Notes）",
        "effect": "关闭后便签内容已保存，无影响",
    },
    "yourphone.exe": {
        "friendly": "手机连接",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Windows 手机连接（Your Phone）",
        "effect": "关闭后手机与电脑断开连接",
    },
    "widgetservice.exe": {
        "friendly": "Windows 小组件",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Windows 小组件服务",
        "effect": "关闭后小组件面板不可用",
    },
    "microsoftedgeupdate.exe": {
        "friendly": "Edge 更新服务",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Edge 浏览器自动更新程序",
        "effect": "关闭后仅暂停更新检查，无影响",
    },
    "googleupdate.exe": {
        "friendly": "Chrome 更新服务",
        "category": "sys_extra",
        "risk": "safe",
        "description": "Chrome 自动更新程序",
        "effect": "关闭后仅暂停更新检查，无影响",
    },
    # ── 输入法 ──────────────────────────────────────────────────────
    "sogoucloud.exe": {
        "friendly": "搜狗输入法云服务",
        "category": "sys_extra",
        "risk": "safe",
        "description": "搜狗输入法云计算服务，占内存较高",
        "effect": "关闭后输入法基本功能正常，云联想暂时不可用",
    },
    "soghelper.exe": {
        "friendly": "搜狗输入法助手",
        "category": "sys_extra",
        "risk": "safe",
        "description": "搜狗输入法辅助程序",
        "effect": "关闭后输入法基本功能正常",
    },
    # ── 其他常见进程 ────────────────────────────────────────────────
    "wallpaper64.exe": {
        "friendly": "Wallpaper Engine",
        "category": "tool",
        "risk": "safe",
        "description": "壁纸引擎，持续渲染动态壁纸",
        "effect": "关闭后壁纸恢复为静态",
    },
    "rainmeter.exe": {
        "friendly": "Rainmeter",
        "category": "tool",
        "risk": "safe",
        "description": "桌面美化工具",
        "effect": "关闭后桌面小组件消失",
    },
    "autohotkey.exe": {
        "friendly": "AutoHotkey",
        "category": "tool",
        "risk": "caution",
        "description": "AutoHotkey 自动化脚本引擎",
        "effect": "关闭后所有热键和自动化脚本失效",
    },
    "everything.exe": {
        "friendly": "Everything",
        "category": "tool",
        "risk": "safe",
        "description": "文件快速搜索工具",
        "effect": "关闭后无法快速搜索文件，重新打开即可",
    },
    "wox.exe": {
        "friendly": "Wox",
        "category": "tool",
        "risk": "safe",
        "description": "Wox 启动器",
        "effect": "关闭后快捷启动不可用",
    },
    "poweriso.exe": {
        "friendly": "PowerISO",
        "category": "tool",
        "risk": "safe",
        "description": "虚拟光驱工具",
        "effect": "关闭后虚拟光驱可能断开",
    },
    "traymonitor.exe": {
        "friendly": "系统托盘监控",
        "category": "sys_extra",
        "risk": "safe",
        "description": "系统托盘监控程序",
        "effect": "关闭后无显著影响",
    },
    # ── WorkBuddy / AI 工具 ────────────────────────────────────────
    "codebuddy.exe": {
        "friendly": "WorkBuddy",
        "category": "dev",
        "risk": "caution",
        "description": "WorkBuddy AI 编程助手",
        "effect": "关闭后 AI 助手不可用，需重新启动",
    },
}

# ─── 保护名单（绝对不关闭的进程）───────────────────────────────────────────
PROTECTED_PROCESSES = {
    # SolidWorks 相关（全部保护）
    "sldworks.exe", "sldworkscommandmanager.exe", "swspmanager.exe",
    "swdocumentmgr.exe", "sldshellshellext.exe", "edrawings.exe",
    # 系统核心
    "explorer.exe", "svchost.exe", "system", "system idle process",
    "registry", "smss.exe", "csrss.exe", "wininit.exe", "winlogon.exe",
    "services.exe", "lsass.exe", "fontdrvhost.exe", "dwm.exe",
    "taskmgr.exe", "conhost.exe", "cmd.exe", "powershell.exe",
    "memory_cleaner.exe", "python.exe", "pythonw.exe",
    # 安全软件
    "360tray.exe", "360sd.exe", "msmpeng.exe", "avp.exe",
    "hipsdaemon.exe", "hwscc3.exe", " ZhuDongFangYu.exe",
    # 硬件驱动
    "nvcplui.exe", "igfxem.exe", "igfxtray.exe", "radeonsoftware.exe",
    "realtekhdaudioservice.exe", "audiodg.exe",
}

# ─── 分类配置 ──────────────────────────────────────────────────────────────
CATEGORY_CONFIG = {
    "browser":   {"label": "🌐 浏览器",   "color": "#64b5f6", "sort": 0},
    "comm":      {"label": "💬 通讯",     "color": "#ffb74d", "sort": 1},
    "media":     {"label": "🎵 媒体",     "color": "#ce93d8", "sort": 2},
    "cloud":     {"label": "☁️ 云盘",     "color": "#80cbc4", "sort": 3},
    "game":      {"label": "🎮 游戏",     "color": "#ef9a9a", "sort": 4},
    "tool":      {"label": "🔧 工具",     "color": "#a5d6a7", "sort": 5},
    "dev":       {"label": "💻 开发",     "color": "#90caf9", "sort": 6},
    "work":      {"label": "📝 办公",     "color": "#fff59d", "sort": 7},
    "sys_extra": {"label": "⚙️ 系统附加", "color": "#b0bec5", "sort": 8},
    "unknown":   {"label": "❓ 未知",     "color": "#78909c", "sort": 9},
}

RISK_CONFIG = {
    "safe":    {"label": "🟢 安全", "color": "#4ecca3", "default_check": True,
                "desc": "可以放心关闭，没有副作用"},
    "caution": {"label": "🟡 注意", "color": "#f5a623", "default_check": False,
                "desc": "关闭后有影响，请确认当前不需要"},
    "danger":  {"label": "🔴 危险", "color": "#e94560", "default_check": False,
                "desc": "不建议关闭，可能丢失数据"},
}

# 颜色主题
COLORS = {
    "bg": "#1a1a2e",
    "card": "#16213e",
    "accent": "#0f3460",
    "btn_danger": "#e94560",
    "btn_safe": "#4ecca3",
    "btn_warn": "#f5a623",
    "text": "#e0e0e0",
    "text_dim": "#888888",
    "green": "#4ecca3",
    "yellow": "#f5a623",
    "red": "#e94560",
    "protected": "#4a4a6a",
    "tooltip_bg": "#2d2d4a",
}


class ToolTip:
    """鼠标悬停提示框"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)

        frame = tk.Frame(tw, bg=COLORS["tooltip_bg"], bd=1,
                         relief="solid", padx=12, pady=8)
        frame.pack()

        for line in self.text.split("\n"):
            tk.Label(frame, text=line, font=("微软雅黑", 9),
                     bg=COLORS["tooltip_bg"], fg=COLORS["text"],
                     wraplength=320, justify="left").pack(anchor="w")

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class MemoryCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("内存急救包 · SolidWorks 优化版 v2.0")
        self.root.geometry("800x680")
        self.root.minsize(760, 580)
        self.root.configure(bg=COLORS["bg"])

        self.user_protected = set()
        self.process_vars = {}  # pid -> BooleanVar
        self.process_data = []

        # 分类筛选
        self.filter_category = "all"

        self._build_ui()
        self._start_monitor()
        self._scan_processes()

    # ─── 构建界面 ─────────────────────────────────────────────────────────
    def _build_ui(self):
        # 顶部标题栏
        header = tk.Frame(self.root, bg=COLORS["accent"], pady=10)
        header.pack(fill="x")

        tk.Label(header, text="🧹 内存急救包",
                 font=("微软雅黑", 16, "bold"),
                 bg=COLORS["accent"], fg=COLORS["btn_safe"]).pack(side="left", padx=20)

        tk.Label(header, text="专为 SolidWorks 用户优化 · 智能识别安全关闭",
                 font=("微软雅黑", 9),
                 bg=COLORS["accent"], fg=COLORS["text_dim"]).pack(side="left")

        # 内存状态栏
        status_frame = tk.Frame(self.root, bg=COLORS["card"], pady=12)
        status_frame.pack(fill="x")

        inner = tk.Frame(status_frame, bg=COLORS["card"])
        inner.pack(padx=20)

        self.mem_label = tk.Label(inner, text="内存使用: 计算中...",
                                   font=("微软雅黑", 11, "bold"),
                                   bg=COLORS["card"], fg=COLORS["text"])
        self.mem_label.pack(side="left", padx=(0, 20))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Mem.Horizontal.TProgressbar",
                         troughcolor=COLORS["bg"],
                         background=COLORS["green"],
                         thickness=16)
        self.mem_bar = ttk.Progressbar(inner, style="Mem.Horizontal.TProgressbar",
                                        length=180, maximum=100)
        self.mem_bar.pack(side="left", padx=(0, 15))

        self.sw_status = tk.Label(inner, text="",
                                   font=("微软雅黑", 9),
                                   bg=COLORS["card"], fg=COLORS["green"])
        self.sw_status.pack(side="left", padx=(0, 15))

        # 风险图例
        legend = tk.Frame(inner, bg=COLORS["card"])
        legend.pack(side="right")
        for risk_key, risk_cfg in RISK_CONFIG.items():
            tk.Label(legend, text=risk_cfg["label"],
                     font=("微软雅黑", 8),
                     bg=COLORS["card"], fg=risk_cfg["color"]).pack(side="left", padx=4)

        # 分类筛选栏 + 工具栏
        filter_frame = tk.Frame(self.root, bg=COLORS["bg"], pady=4)
        filter_frame.pack(fill="x", padx=20)

        tk.Label(filter_frame, text="分类:", font=("微软雅黑", 9),
                 bg=COLORS["bg"], fg=COLORS["text_dim"]).pack(side="left", padx=(0, 6))

        self.filter_btns = {}
        all_btn = tk.Button(filter_frame, text="全部", font=("微软雅黑", 8),
                             bg=COLORS["accent"], fg=COLORS["text"],
                             relief="flat", padx=8, pady=2, cursor="hand2",
                             command=lambda: self._set_filter("all"))
        all_btn.pack(side="left", padx=2)
        self.filter_btns["all"] = all_btn

        for cat_key, cat_cfg in sorted(CATEGORY_CONFIG.items(),
                                        key=lambda x: x[1]["sort"]):
            btn = tk.Button(filter_frame, text=cat_cfg["label"],
                             font=("微软雅黑", 8),
                             bg=COLORS["bg"], fg=cat_cfg["color"],
                             relief="flat", padx=6, pady=2, cursor="hand2",
                             command=lambda k=cat_key: self._set_filter(k))
            btn.pack(side="left", padx=2)
            self.filter_btns[cat_key] = btn

        # 工具栏
        toolbar = tk.Frame(self.root, bg=COLORS["bg"], pady=6)
        toolbar.pack(fill="x", padx=20)

        tk.Button(toolbar, text="🔄 刷新扫描",
                  command=self._scan_processes,
                  bg=COLORS["accent"], fg=COLORS["text"],
                  font=("微软雅黑", 9), relief="flat",
                  padx=12, pady=4, cursor="hand2").pack(side="left", padx=(0, 8))

        tk.Button(toolbar, text="☑ 全选安全",
                  command=self._select_safe,
                  bg=COLORS["accent"], fg=COLORS["text"],
                  font=("微软雅黑", 9), relief="flat",
                  padx=12, pady=4, cursor="hand2").pack(side="left", padx=(0, 8))

        tk.Button(toolbar, text="☐ 取消全选",
                  command=self._deselect_all,
                  bg=COLORS["accent"], fg=COLORS["text"],
                  font=("微软雅黑", 9), relief="flat",
                  padx=12, pady=4, cursor="hand2").pack(side="left", padx=(0, 8))

        self.estimate_label = tk.Label(toolbar, text="",
                                        font=("微软雅黑", 9, "bold"),
                                        bg=COLORS["bg"], fg=COLORS["yellow"])
        self.estimate_label.pack(side="right")

        # 进程列表
        list_frame = tk.Frame(self.root, bg=COLORS["bg"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        # 表头
        header_row = tk.Frame(list_frame, bg=COLORS["accent"], pady=4)
        header_row.pack(fill="x")

        tk.Label(header_row, text="  选择", width=5,
                 font=("微软雅黑", 9, "bold"),
                 bg=COLORS["accent"], fg=COLORS["text_dim"]).pack(side="left")
        tk.Label(header_row, text="应用名称", width=18,
                 font=("微软雅黑", 9, "bold"),
                 bg=COLORS["accent"], fg=COLORS["text_dim"]).pack(side="left")
        tk.Label(header_row, text="分类", width=10,
                 font=("微软雅黑", 9, "bold"),
                 bg=COLORS["accent"], fg=COLORS["text_dim"]).pack(side="left")
        tk.Label(header_row, text="内存", width=10,
                 font=("微软雅黑", 9, "bold"),
                 bg=COLORS["accent"], fg=COLORS["text_dim"]).pack(side="left")
        tk.Label(header_row, text="风险", width=10,
                 font=("微软雅黑", 9, "bold"),
                 bg=COLORS["accent"], fg=COLORS["text_dim"]).pack(side="left")
        tk.Label(header_row, text="关闭影响",
                 font=("微软雅黑", 9, "bold"),
                 bg=COLORS["accent"], fg=COLORS["text_dim"]).pack(side="left", padx=(0, 20))

        # 滚动列表区域
        canvas_frame = tk.Frame(list_frame, bg=COLORS["bg"])
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=COLORS["bg"],
                                 highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical",
                                   command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=COLORS["bg"])

        self.scroll_frame.bind("<Configure>",
                                lambda e: self.canvas.configure(
                                    scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮
        self.canvas.bind_all("<MouseWheel>",
                              lambda e: self.canvas.yview_scroll(
                                  -1 * (e.delta // 120), "units"))

        # 底部操作栏
        bottom = tk.Frame(self.root, bg=COLORS["accent"], pady=12)
        bottom.pack(fill="x")

        self.kill_btn = tk.Button(bottom, text="🚀  一键释放选中进程",
                                   command=self._kill_selected,
                                   bg=COLORS["btn_danger"], fg="white",
                                   font=("微软雅黑", 11, "bold"),
                                   relief="flat", padx=24, pady=8,
                                   cursor="hand2")
        self.kill_btn.pack(side="left", padx=20)

        self.result_label = tk.Label(bottom, text="",
                                      font=("微软雅黑", 10),
                                      bg=COLORS["accent"], fg=COLORS["green"])
        self.result_label.pack(side="left")

        tk.Label(bottom, text="🛡️ SolidWorks 及系统核心进程已自动保护  |  悬停查看详情",
                 font=("微软雅黑", 8),
                 bg=COLORS["accent"], fg=COLORS["text_dim"]).pack(side="right", padx=20)

    # ─── 分类筛选 ─────────────────────────────────────────────────────────
    def _set_filter(self, category):
        self.filter_category = category
        # 更新按钮样式
        for key, btn in self.filter_btns.items():
            if key == category:
                btn.config(bg=COLORS["accent"])
            else:
                btn.config(bg=COLORS["bg"])
        self._render_list(self.process_data)

    # ─── 扫描进程 ─────────────────────────────────────────────────────────
    def _scan_processes(self):
        self.result_label.config(text="扫描中...")
        threading.Thread(target=self._do_scan, daemon=True).start()

    def _do_scan(self):
        procs = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'status']):
            try:
                pname = proc.info['name'].lower()
                if pname in PROTECTED_PROCESSES:
                    continue
                if pname in self.user_protected:
                    continue
                mem_mb = proc.info['memory_info'].rss / (1024 * 1024)
                if mem_mb < 20:  # 低于 20MB 的不显示
                    continue

                # 查询知识库
                db_info = PROCESS_DB.get(pname)
                if db_info:
                    friendly = db_info["friendly"]
                    category = db_info["category"]
                    risk = db_info["risk"]
                    description = db_info["description"]
                    effect = db_info["effect"]
                else:
                    friendly = proc.info['name']
                    category = "unknown"
                    risk = "caution"  # 未知进程默认为"注意"
                    description = f"未在知识库中的进程：{proc.info['name']}"
                    effect = "不确定关闭后的影响，建议谨慎操作"

                procs.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "friendly": friendly,
                    "mem_mb": mem_mb,
                    "status": proc.info['status'],
                    "category": category,
                    "risk": risk,
                    "description": description,
                    "effect": effect,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # 按分类排序，同类按内存降序
        cat_sort = {k: v["sort"] for k, v in CATEGORY_CONFIG.items()}
        procs.sort(key=lambda x: (cat_sort.get(x["category"], 99), -x["mem_mb"]))

        self.root.after(0, lambda: self._render_list(procs))

    def _render_list(self, procs):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.process_vars.clear()
        self.process_data = procs

        # 筛选
        if self.filter_category != "all":
            display_procs = [p for p in procs if p["category"] == self.filter_category]
        else:
            display_procs = procs

        for i, p in enumerate(display_procs):
            row_bg = COLORS["card"] if i % 2 == 0 else COLORS["bg"]
            row = tk.Frame(self.scroll_frame, bg=row_bg, pady=5)
            row.pack(fill="x")

            # 复选框
            risk_cfg = RISK_CONFIG[p["risk"]]
            var = tk.BooleanVar(value=risk_cfg["default_check"])
            self.process_vars[p["pid"]] = var
            cb = tk.Checkbutton(row, variable=var,
                                 bg=row_bg, activebackground=row_bg,
                                 selectcolor=COLORS["bg"],
                                 command=self._update_estimate)
            cb.pack(side="left", padx=6)

            # 应用名
            name_label = tk.Label(row, text=p["friendly"][:20], width=18,
                                   font=("微软雅黑", 9),
                                   bg=row_bg, fg=COLORS["text"],
                                   anchor="w")
            name_label.pack(side="left")

            # 分类标签
            cat_cfg = CATEGORY_CONFIG.get(p["category"], CATEGORY_CONFIG["unknown"])
            tk.Label(row, text=cat_cfg["label"], width=10,
                     font=("微软雅黑", 8),
                     bg=row_bg, fg=cat_cfg["color"]).pack(side="left")

            # 内存
            mem_color = COLORS["red"] if p["mem_mb"] > 500 else \
                        COLORS["yellow"] if p["mem_mb"] > 200 else COLORS["text"]
            tk.Label(row, text=f"{p['mem_mb']:.0f} MB", width=10,
                     font=("微软雅黑", 9, "bold"),
                     bg=row_bg, fg=mem_color).pack(side="left")

            # 风险等级
            tk.Label(row, text=risk_cfg["label"], width=10,
                     font=("微软雅黑", 8, "bold"),
                     bg=row_bg, fg=risk_cfg["color"]).pack(side="left")

            # 关闭影响（截断显示）
            effect_short = p["effect"][:16] + "..." if len(p["effect"]) > 16 else p["effect"]
            effect_label = tk.Label(row, text=effect_short,
                                     font=("微软雅黑", 8),
                                     bg=row_bg, fg=COLORS["text_dim"])
            effect_label.pack(side="left", padx=(0, 10))

            # ─── 悬停提示 ────────────────────────────────────────────
            cat_label = CATEGORY_CONFIG.get(p["category"], CATEGORY_CONFIG["unknown"])["label"]
            tooltip_text = (
                f"📁 进程名: {p['name']}\n"
                f"📋 分类: {cat_label}\n"
                f"📝 说明: {p['description']}\n"
                f"{risk_cfg['label']} 关闭风险\n"
                f"⚠️ 关闭影响: {p['effect']}\n"
                f"💾 占用内存: {p['mem_mb']:.0f} MB"
            )
            # 给整行和各标签都绑定 tooltip
            for widget in [row, name_label, effect_label]:
                ToolTip(widget, tooltip_text)

        self._update_estimate()
        self.result_label.config(
            text=f"共 {len(procs)} 个进程" +
                 (f"，当前显示 {len(display_procs)} 个" if self.filter_category != "all" else ""))

    # ─── 全选安全 / 取消 ─────────────────────────────────────────────────
    def _select_safe(self):
        for p in self.process_data:
            if p["pid"] in self.process_vars:
                self.process_vars[p["pid"]].set(p["risk"] == "safe")
        self._update_estimate()

    def _deselect_all(self):
        for var in self.process_vars.values():
            var.set(False)
        self._update_estimate()

    # ─── 估算可释放内存 ───────────────────────────────────────────────────
    def _update_estimate(self):
        total = sum(
            p["mem_mb"] for p in self.process_data
            if p["pid"] in self.process_vars and self.process_vars[p["pid"]].get()
        )
        if total > 0:
            self.estimate_label.config(text=f"预计释放: {total:.0f} MB ({total/1024:.1f} GB)")
        else:
            self.estimate_label.config(text="")

    # ─── 执行关闭 ─────────────────────────────────────────────────────────
    def _kill_selected(self):
        selected = [
            p for p in self.process_data
            if p["pid"] in self.process_vars and self.process_vars[p["pid"]].get()
        ]
        if not selected:
            messagebox.showinfo("提示", "请先勾选要关闭的进程")
            return

        # 按风险分组显示
        safe_list = [p for p in selected if p["risk"] == "safe"]
        caution_list = [p for p in selected if p["risk"] == "caution"]
        danger_list = [p for p in selected if p["risk"] == "danger"]

        msg_parts = []
        if safe_list:
            names = "\n".join(f"  🟢 {p['friendly']} ({p['mem_mb']:.0f} MB)" for p in safe_list[:8])
            msg_parts.append(f"【安全关闭】\n{names}")
        if caution_list:
            names = "\n".join(f"  🟡 {p['friendly']} ({p['mem_mb']:.0f} MB) - {p['effect']}" for p in caution_list[:8])
            msg_parts.append(f"【需注意】\n{names}")
        if danger_list:
            names = "\n".join(f"  🔴 {p['friendly']} ({p['mem_mb']:.0f} MB)" for p in danger_list)
            msg_parts.append(f"【⚠ 不建议关闭】\n{names}")

        total_procs = len(selected)
        msg = "\n\n".join(msg_parts)
        if total_procs > 10:
            msg += f"\n\n...共 {total_procs} 个"

        # 如果选了危险进程，额外警告
        warn_extra = ""
        if danger_list:
            warn_extra = "\n\n⚠️ 你选择了「危险」进程，关闭可能导致数据丢失！"

        confirm = messagebox.askyesno(
            "确认操作",
            f"即将关闭 {total_procs} 个进程：\n\n{msg}{warn_extra}\n\n"
            f"🛡️ SolidWorks 不会受到影响\n\n确认执行？"
        )
        if not confirm:
            return

        killed, failed, freed = 0, 0, 0
        for p in selected:
            try:
                proc = psutil.Process(p["pid"])
                freed += proc.memory_info().rss / (1024 * 1024)
                proc.terminate()
                killed += 1
            except Exception:
                failed += 1

        msg = f"✅ 已关闭 {killed} 个进程，释放约 {freed:.0f} MB"
        if failed:
            msg += f"  (⚠ {failed} 个失败)"
        self.result_label.config(text=msg)
        self.root.after(1500, self._scan_processes)

    # ─── 实时监控内存 ─────────────────────────────────────────────────────
    def _start_monitor(self):
        def monitor():
            while True:
                try:
                    mem = psutil.virtual_memory()
                    pct = mem.percent
                    used_gb = mem.used / (1024 ** 3)
                    total_gb = mem.total / (1024 ** 3)

                    style = ttk.Style()
                    if pct >= 85:
                        bar_color = COLORS["red"]
                        status_txt = f"⚠️ 内存紧张！ {used_gb:.1f}/{total_gb:.0f}GB ({pct:.0f}%)"
                    elif pct >= 70:
                        bar_color = COLORS["yellow"]
                        status_txt = f"内存使用: {used_gb:.1f}/{total_gb:.0f}GB ({pct:.0f}%)"
                    else:
                        bar_color = COLORS["green"]
                        status_txt = f"内存使用: {used_gb:.1f}/{total_gb:.0f}GB ({pct:.0f}%)"

                    sw_running = any(
                        p.info['name'] and p.info['name'].lower() == "sldworks.exe"
                        for p in psutil.process_iter(['name'])
                    )

                    self.root.after(0, lambda s=status_txt, p=pct, c=bar_color,
                                    sw=sw_running: self._update_status(s, p, c, sw))
                except Exception:
                    pass
                time.sleep(2)

        threading.Thread(target=monitor, daemon=True).start()

    def _update_status(self, status_txt, pct, bar_color, sw_running):
        self.mem_label.config(text=status_txt)
        self.mem_bar["value"] = pct
        style = ttk.Style()
        style.configure("Mem.Horizontal.TProgressbar", background=bar_color)

        if sw_running:
            self.sw_status.config(text="● SolidWorks 运行中（已保护）",
                                   fg=COLORS["green"])
        else:
            self.sw_status.config(text="○ SolidWorks 未运行",
                                   fg=COLORS["text_dim"])


def main():
    root = tk.Tk()
    app = MemoryCleanerApp(root)
    try:
        root.iconbitmap(default="icon.ico")
    except Exception:
        pass
    root.mainloop()


if __name__ == "__main__":
    main()
