import sys
import os
import json
import shutil
import re
import platform
import subprocess
import glob
import webbrowser

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QListWidget, QListWidgetItem, QLabel, 
                             QPushButton, QCheckBox, QFrame, QFileDialog, 
                             QMessageBox, QComboBox, QAbstractButton)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QRectF, pyqtProperty, pyqtSignal, QPoint
from PyQt6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor, QPen, QBrush

# --- 引入外部语言包 ---
try:
    import lang_config
except ImportError:
    class MockLang:
        def get_lang(self, l): return {}
        LANGUAGES = {"English": "en"}
    lang_config = MockLang()

# --- 路径与常量 ---
def get_app_data_path():
    home = os.path.expanduser("~")
    app_data_dir = os.path.join(home, ".moho_tool_manager")
    if not os.path.exists(app_data_dir):
        try: os.makedirs(app_data_dir)
        except: return home
    return app_data_dir

APP_DATA_DIR = get_app_data_path()
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
URL_SCRIPTS = "https://mohoscripts.com/"
URL_NOTION = "https://moeu33.notion.site/Moho-a49ca9864920461ab9bef0763d47ca21"
SORT_MODES = ["name_asc", "name_desc", "date_desc"]

# --- 字体设置 ---
if platform.system() == "Windows":
    SYSTEM_FONT = "Microsoft YaHei UI"
    BASE_FONT_SIZE = 10
elif platform.system() == "Darwin":
    SYSTEM_FONT = ".AppleSystemUIFont"
    BASE_FONT_SIZE = 12
else:
    SYSTEM_FONT = "Arial"
    BASE_FONT_SIZE = 10

# ==========================================
#  🎨 [配置区] 颜色与样式配置
# ==========================================
THEME_CONFIG = {
    "Light": {
        "bg_main": "#ffffff",
        "bg_sidebar": "#f5f5f5",
        "text_main": "#333333",
        "text_sub": "#888888",
        
        "list_bg": "#ffffff",
        "list_alt": "#fafafa",
        "list_border": "#e0e0e0",
        
        "icon_bg": "#e0e0e0", 

        # --- 按钮通用配置 ---
        "btn_border_width": "2px",
        # [背景, 文字, 边框, 按下背景(深一点)]
        "btn_normal":    ["#4dabf7", "#333333", "#495057", "#e6e6e6"], 
        "btn_normal_hover": "#eeeeee",

        "btn_import":    ["#2CC985", "#333333", "#229A65", "#1FA86E"], # 按下变深绿
        "btn_refresh":   ["#3B8ED0", "#333333", "#36719F", "#2A6695"], # 按下变深蓝
        "btn_del":       ["#FF5555", "#333333", "#CC0000", "#B30000"], # 按下变深红
        "btn_sort":      ["#ffffff", "#333333", "#495057", "#e6e6e6"],

        # --- 勾选框配置 ---
        "check_border_width": "2px",
        "check_border": "#495057",       
        "check_bg_checked": "#2CC985",   
        "check_border_checked": "#229A65",
    },
    "Dark": {
        "bg_main": "#2b2b2b",
        "bg_sidebar": "#202020",
        "text_main": "#ffffff",
        "text_sub": "#aaaaaa",
        
        "list_bg": "#2b2b2b",
        "list_alt": "#323232",
        "list_border": "#444444",
        
        "icon_bg": "#505050",
        
        "btn_border_width": "2px",
        # [背景, 文字, 边框, 按下背景]
        "btn_normal":    ["#3a3a3a", "#ffffff", "#f8f9fa", "#222222"],
        "btn_normal_hover": "#4a4a4a",

        "btn_import":    ["#2CC985", "#ffffff", "#2CC985", "#1FA86E"], 
        "btn_refresh":   ["#3B8ED0", "#ffffff", "#3B8ED0", "#2A6695"],
        "btn_del":       ["#FF5555", "#ffffff", "#FF5555", "#B30000"],
        "btn_sort":      ["#3a3a3a", "#ffffff", "#f8f9fa", "#222222"],

        "check_border_width": "2px",
        "check_border": "#f1f3f5",
        "check_bg_checked": "#2CC985",
        "check_border_checked": "none",
    }
}
# ==========================================
#  🧩 自定义控件：SwitchButton (滑块开关)
# ==========================================
class SwitchButton(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(46, 26)
        self._track_radius = 13
        self._thumb_radius = 10
        self._margin = 3
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        track_color = QColor("#e0e0e0")
        if self.isChecked():
            track_color = QColor("#b197fc") 
        
        p.setBrush(track_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), self._track_radius, self._track_radius)
        
        p.setBrush(Qt.GlobalColor.white)
        if self.isChecked():
            p.drawEllipse(self.width() - self._thumb_radius * 2 - self._margin, self._margin, self._thumb_radius * 2, self._thumb_radius * 2)
        else:
            p.drawEllipse(self._margin, self._margin, self._thumb_radius * 2, self._thumb_radius * 2)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        self.update()

# ==========================================
#  🧩 自定义控件：列表项
# ==========================================
class ScriptItemWidget(QWidget):
    def __init__(self, filename, full_path, meta, png_path, parent_list, theme_key="Light"):
        super().__init__()
        self.filename = filename
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)

        self.checkbox = QCheckBox()
        self.checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.checkbox)

        self.icon_container = QLabel()
        self.icon_container.setFixedSize(34, 34)
        self.icon_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_container.setStyleSheet("border-radius: 4px;") 
        
        if os.path.exists(png_path):
            pixmap = QPixmap(png_path)
            scaled_pix = pixmap.scaled(24, 20, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.icon_container.setPixmap(scaled_pix)
        else:
            self.icon_container.setText("📄") 
            self.icon_container.setFont(QFont("Segoe UI Emoji", 14))
        
        layout.addWidget(self.icon_container)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        
        title_txt = meta.get("name") if meta.get("name") else filename
        self.lbl_title = QLabel(title_txt)
        self.lbl_title.setFont(QFont(SYSTEM_FONT, BASE_FONT_SIZE + 1, QFont.Weight.Bold))
        self.lbl_title.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        text_layout.addWidget(self.lbl_title)

        meta_parts = []
        if meta.get("version"): meta_parts.append(f"v{meta['version']}")
        if meta.get("creator"): meta_parts.append(f"@{meta['creator']}")
        meta_str = "  |  ".join(meta_parts)
        if not meta_str: meta_str = filename
        
        self.lbl_meta = QLabel(meta_str)
        self.lbl_meta.setFont(QFont(SYSTEM_FONT, BASE_FONT_SIZE - 1))
        self.lbl_meta.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        text_layout.addWidget(self.lbl_meta)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        self.apply_theme_colors(theme_key)

    def apply_theme_colors(self, theme_key):
        cfg = THEME_CONFIG[theme_key]
        if not self.icon_container.pixmap():
             self.icon_container.setStyleSheet(f"background-color: {cfg['icon_bg']}; border-radius: 4px; color: {cfg['text_main']};")
        else:
             self.icon_container.setStyleSheet(f"background-color: {cfg['icon_bg']}; border-radius: 4px;")
        
        self.lbl_title.setStyleSheet(f"color: {cfg['text_main']}; background-color: transparent;")
        self.lbl_meta.setStyleSheet(f"color: {cfg['text_sub']}; background-color: transparent;")

# ==========================================
#  🖥️ 主窗口
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.current_lang = self.config.get("language", "English")
        self.sort_mode = self.config.get("sort_mode", "name_asc")
        self.current_theme = self.config.get("theme", "Light")
        self.txt = lang_config.get_lang(self.current_lang)

        self.setWindowTitle(self.txt.get("title", "Moho Scripts Manager"))
        self.resize(900, 750)
        if os.path.exists("icon.ico"): self.setWindowIcon(QIcon("icon.ico"))

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === 侧边栏 ===
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setObjectName("sidebar")
        
        sb_layout = QVBoxLayout(self.sidebar)
        sb_layout.setContentsMargins(15, 20, 15, 20)
        sb_layout.setSpacing(10)
        main_layout.addWidget(self.sidebar)

        def mk_btn(text, func, obj_name):
            btn = QPushButton(text)
            btn.clicked.connect(func)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont(SYSTEM_FONT, BASE_FONT_SIZE))
            btn.setObjectName(obj_name) 
            return btn

        self.btn_select = mk_btn("Select Folder", self.select_folder, "btn_normal")
        self.btn_open = mk_btn("Open Folder", self.open_in_explorer, "btn_normal")
        self.btn_import = mk_btn("Import", self.import_folder_dialog, "btn_import")
        self.btn_sort = mk_btn("Sort", self.toggle_sort_mode, "btn_sort")
        self.btn_refresh = mk_btn("Refresh", self.load_files_list, "btn_refresh")
        
        sb_layout.addWidget(self.btn_select)
        sb_layout.addWidget(self.btn_open)
        sb_layout.addWidget(self.btn_import)
        sb_layout.addWidget(self.btn_sort)
        sb_layout.addWidget(self.btn_refresh)
        
        sb_layout.addSpacing(25)
        
        self.btn_all = mk_btn("Select All", self.toggle_select_all, "btn_normal")
        self.btn_del = mk_btn("Delete", self.delete_selected_scripts, "btn_del")
        sb_layout.addWidget(self.btn_all)
        sb_layout.addWidget(self.btn_del)
        
        sb_layout.addStretch()

        # 主题开关
        theme_row = QHBoxLayout()
        self.theme_icon = QLabel("☀")
        self.theme_icon.setFont(QFont("Segoe UI Emoji", 16))
        self.switch_theme = SwitchButton()
        self.switch_theme.toggled.connect(self.toggle_theme_switch)
        
        theme_row.addWidget(self.theme_icon)
        theme_row.addWidget(self.switch_theme)
        theme_row.addStretch()
        sb_layout.addLayout(theme_row)

        self.combo_lang = QComboBox()
        self.combo_lang.addItems(list(lang_config.LANGUAGES.keys()))
        self.combo_lang.setCurrentText(self.current_lang)
        self.combo_lang.currentTextChanged.connect(self.change_language)
        sb_layout.addWidget(self.combo_lang)
        
        sb_layout.addSpacing(20)

        # 链接
        link_style = "QPushButton { text-align: left; background: transparent; border: none; color: gray; } QPushButton:hover { color: #FF5555; }"
        
        b_link1 = QPushButton("📜 MohoScripts.com")
        b_link1.setStyleSheet(link_style)
        b_link1.setCursor(Qt.CursorShape.PointingHandCursor)
        b_link1.clicked.connect(lambda: webbrowser.open(URL_SCRIPTS))
        
        b_link2 = QPushButton("📓 Moho 脚本整理")
        b_link2.setStyleSheet(link_style)
        b_link2.setCursor(Qt.CursorShape.PointingHandCursor)
        b_link2.clicked.connect(lambda: webbrowser.open(URL_NOTION))
        
        sb_layout.addWidget(b_link1)
        sb_layout.addWidget(b_link2)
        
        self.lbl_author = QLabel("")
        self.lbl_author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_author.setStyleSheet("color: gray; background: transparent;")
        sb_layout.addWidget(self.lbl_author)

        # === 列表 ===
        self.list_widget = QListWidget()
        self.list_widget.setFrameShape(QFrame.Shape.NoFrame)
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        main_layout.addWidget(self.list_widget)

        self.all_selected_flag = False
        self.switch_theme.setChecked(True if self.current_theme == "Dark" else False)
        
        self.apply_theme_style()
        self.change_language(self.current_lang)

        last_folder = self.config.get("last_folder")
        if last_folder and os.path.exists(last_folder):
             if os.path.basename(last_folder).lower() == "scripts":
                self.current_scripts_folder = last_folder
                self.load_files_list()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding='utf-8') as f: return json.load(f)
            except: pass
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False)

    def toggle_theme_switch(self, checked):
        self.current_theme = "Dark" if checked else "Light"
        self.config["theme"] = self.current_theme
        self.save_config()
        self.apply_theme_style()

    def apply_theme_style(self):
        t = self.current_theme
        cfg = THEME_CONFIG[t]
        
        self.theme_icon.setText("🌙" if t == "Dark" else "☀")
        self.theme_icon.setStyleSheet(f"color: {cfg['text_main']}; background: transparent;")

        def btn_style(obj_id, color_list):
            return f"""
                QPushButton#{obj_id} {{
                    text-align: left; 
                    padding: 8px 15px; 
                    border-radius: 6px; 
                    border-style: solid;
                    border-width: {cfg['btn_border_width']};
                    background-color: {color_list[0]}; 
                    color: {color_list[1]}; 
                    border-color: {color_list[2]};
                }}
                QPushButton#{obj_id}:pressed {{
                    background-color: {color_list[3]};
                }}
            """

        qss = f"""
            QMainWindow, QWidget {{ background-color: {cfg['bg_main']}; color: {cfg['text_main']}; }}
            
            QWidget#sidebar {{ background-color: {cfg['bg_sidebar']}; }}
            
            QListWidget {{ 
                background-color: {cfg['list_bg']}; 
                border-left: 1px solid {cfg['list_border']};
                outline: none;
            }}
            QListWidget::item {{ 
                border-bottom: 1px solid {cfg['list_alt']}; 
                padding: 2px;
            }}
            QListWidget::item:alternate {{ background-color: {cfg['list_alt']}; }}
            
            QPushButton:hover {{ opacity: 0.85; }}
            QPushButton#btn_normal:hover, QPushButton#btn_sort:hover {{ background-color: {cfg.get('btn_normal_hover', '#eeeeee')}; }}

            {btn_style("btn_normal", cfg['btn_normal'])}
            {btn_style("btn_import", cfg['btn_import'])}
            {btn_style("btn_refresh", cfg['btn_refresh'])}
            {btn_style("btn_del",    cfg['btn_del'])}
            {btn_style("btn_sort",   cfg['btn_sort'])}

            QCheckBox::indicator {{
                width: 18px; 
                height: 18px;
                border-radius: 4px;
                border-style: solid;
                border-width: {cfg['check_border_width']};
                border-color: {cfg['check_border']};
                background-color: transparent;
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: {cfg['check_bg_checked']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {cfg['check_bg_checked']};
                border-color: {cfg['check_border_checked']};
                image: url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIzIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwb2x5bGluZSBwb2ludHM9IjIwIDYgOSAxNyA0IDEyIi8+PC9zdmc+');
            }}
            QCheckBox::indicator:pressed {{
                background-color: {cfg.get('btn_normal_hover', '#eee')};
            }}
            
            QComboBox {{ 
                padding: 5px; 
                border-style: solid;
                border-width: {cfg['btn_border_width']};
                border-color: {cfg['btn_normal'][2]}; 
                border-radius: 4px; 
                background-color: {cfg['btn_normal'][0]}; 
                color: {cfg['text_main']}; 
            }}
            QCheckBox {{ color: {cfg['text_main']}; spacing: 5px; }}
        """
        self.setStyleSheet(qss)
        self.sidebar.setStyleSheet(f"background-color: {cfg['bg_sidebar']};")

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget: widget.apply_theme_colors(t)

    def change_language(self, choice):
        self.current_lang = choice
        self.config["language"] = choice
        self.save_config()
        self.txt = lang_config.get_lang(choice)
        
        self.setWindowTitle(self.txt.get("title", "Manager"))
        self.btn_select.setText(self.txt.get("select_folder", "Select Folder"))
        self.btn_open.setText(self.txt.get("open_folder", "Open Folder"))
        self.btn_import.setText(self.txt.get("add_folder", "Import"))
        self.btn_refresh.setText(self.txt.get("refresh", "Refresh"))
        self.btn_del.setText(self.txt.get("del_selected", "Delete"))
        self.lbl_author.setText(self.txt.get("author", ""))
        self.btn_sort.setText(self.get_sort_text())
        
        self.btn_all.setText(self.txt.get("deselect_all", "Unselect All") if self.all_selected_flag else self.txt.get("select_all", "Select All"))

    def get_sort_text(self):
        if self.sort_mode == "name_asc": return self.txt.get("sort_az", "A-Z")
        elif self.sort_mode == "name_desc": return self.txt.get("sort_za", "Z-A")
        elif self.sort_mode == "date_desc": return self.txt.get("sort_time", "Date")
        return "Sort"

    def toggle_sort_mode(self):
        try:
            idx = SORT_MODES.index(self.sort_mode)
            self.sort_mode = SORT_MODES[(idx + 1) % len(SORT_MODES)]
        except: self.sort_mode = SORT_MODES[0]
        self.config["sort_mode"] = self.sort_mode
        self.save_config()
        self.btn_sort.setText(self.get_sort_text())
        self.load_files_list()

    # --- 修复后补上的 3 个核心函数 ---
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.txt.get("select_folder", "Select Folder"))
        if not folder: return
        if os.path.basename(folder).lower() != "scripts":
            QMessageBox.critical(self, "Error", self.txt.get("error_folder_msg", "Please select 'Scripts' folder.").format(path=os.path.basename(folder)))
            return
        self.current_scripts_folder = folder
        self.config["last_folder"] = folder
        self.save_config()
        self.load_files_list()

    def open_in_explorer(self):
        if not self.current_scripts_folder: return
        try:
            if platform.system() == "Windows": os.startfile(self.current_scripts_folder)
            elif platform.system() == "Darwin": subprocess.call(["open", self.current_scripts_folder])
            else: subprocess.call(["xdg-open", self.current_scripts_folder])
        except: pass

    def toggle_select_all(self):
        self.all_selected_flag = not self.all_selected_flag
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if widget: widget.checkbox.setChecked(self.all_selected_flag)
        
        self.btn_all.setText(self.txt.get("deselect_all", "Unselect All") if self.all_selected_flag else self.txt.get("select_all", "Select All"))

    # --- End of fixed methods ---

    def load_files_list(self):
        self.list_widget.clear()
        self.all_selected_flag = False
        self.btn_all.setText(self.txt.get("select_all", "Select All"))
        
        if not self.current_scripts_folder: return
        tool_folder = os.path.join(self.current_scripts_folder, "Tool")
        if not os.path.exists(tool_folder): return

        try:
            files = os.listdir(tool_folder)
            lua_files = [f for f in files if f.lower().endswith('.lua')]

            if self.sort_mode == "name_asc": lua_files.sort(key=str.lower)
            elif self.sort_mode == "name_desc": lua_files.sort(key=str.lower, reverse=True)
            elif self.sort_mode == "date_desc": lua_files.sort(key=lambda f: os.path.getmtime(os.path.join(tool_folder, f)), reverse=True)
            
            for f in lua_files: self.add_list_item(f, tool_folder)
            
        except Exception as e: print(e)

    def add_list_item(self, filename, folder):
        file_path = os.path.join(folder, filename)
        base_name = os.path.splitext(filename)[0]
        png_path = os.path.join(folder, base_name + ".png")
        meta = self.parse_lua_metadata(file_path)
        
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(0, 64)) 
        
        widget = ScriptItemWidget(filename, file_path, meta, png_path, self.list_widget, self.current_theme)
        self.list_widget.setItemWidget(item, widget)

    def parse_lua_metadata(self, file_path):
        meta = {"name": "", "version": "", "creator": ""}
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                auth_match = re.search(r'function\s+[\w\.:_]+:Creator\(\)\s*return\s*["\'](.*?)["\']', content)
                if not auth_match: auth_match = re.search(r'--\s*(?:Author|Creator|By):\s*(.*)', content, re.IGNORECASE)
                if auth_match: meta["creator"] = auth_match.group(1).strip()
                
                ver_match = re.search(r'function\s+[\w\.:_]+:Version\(\)\s*return\s*["\'](.*?)["\']', content)
                if not ver_match: ver_match = re.search(r'(?:--\s*Version:|Version\s*=|v)\s*["\']?([0-9\.]+(?:\s*RC\s*\d+)?)', content, re.IGNORECASE)
                if ver_match: meta["version"] = ver_match.group(1).strip()
                
                name_match = re.search(r'function\s+[\w\.:_]+:(?:Name|UILabel)\(\)\s*return\s*["\'](.*?)["\']', content)
                if not name_match: name_match = re.search(r'(?:\[["\']UILabel["\']\]|UILabel)\s*=\s*["\'](.*?)["\']', content, re.IGNORECASE)
                if not name_match: name_match = re.search(r'(?:script\.Name|UILabel)\s*=\s*["\'](.*?)["\']', content)
                if name_match: meta["name"] = name_match.group(1).strip()
        except: pass
        return meta

    def scan_resources_for_script(self, file_path):
        candidates = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # 1. 常规扫描 (ScriptResources/文件夹)
                matches = re.findall(r'["\'](ScriptResources[\\/][^"\']+)["\']', content, re.IGNORECASE)
                folder_map, direct = {}, []
                for m in matches:
                    parts = m.replace("\\", os.sep).replace("/", os.sep).split(os.sep)
                    if len(parts) > 2:
                        full = os.path.join(self.current_scripts_folder, "ScriptResources", parts[1])
                        folder_map.setdefault(full, set()).add(parts[2])
                    elif len(parts) == 2:
                        full = os.path.join(self.current_scripts_folder, m)
                        if os.path.exists(full): direct.append(full)
                        elif os.path.exists(full+".lua"): direct.append(full+".lua")

                # 2. DoLayout 扫描
                dolayout_match = re.search(r'function\s+[\w\.:_]+:DoLayout\(\)\s*return\s*["\'](.*?)["\']', content, re.IGNORECASE)
                if dolayout_match:
                    layout_name = dolayout_match.group(1).strip()
                    base_res = os.path.join(self.current_scripts_folder, "ScriptResources", layout_name)
                    if os.path.exists(base_res): direct.append(base_res)
                    elif os.path.exists(base_res + ".lua"): direct.append(base_res + ".lua")
                    elif os.path.exists(base_res + ".png"): direct.append(base_res + ".png")

                # 处理文件夹内的碎片
                for folder, refs in folder_map.items():
                    if not os.path.exists(folder): continue
                    to_del, has_alien = [], False
                    for f in os.listdir(folder):
                        if f.lower() in [".ds_store", "thumbs.db", "desktop.ini"]: continue
                        name = os.path.splitext(f)[0]
                        if f in refs or name in refs or any(name.startswith(r+"_") for r in refs): to_del.append(os.path.join(folder, f))
                        else: has_alien = True
                    candidates.extend([folder] if not has_alien else to_del)
                
                candidates.extend(direct)
        except: pass
        return candidates

    def delete_selected_scripts(self):
        selected_files = []
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if widget and widget.checkbox.isChecked(): selected_files.append(widget.filename)

        if not selected_files:
            QMessageBox.information(self, "Info", self.txt.get("del_no_selection", "No script selected."))
            return

        all_files, all_res = [], []
        tool_folder = os.path.join(self.current_scripts_folder, "Tool")

        for filename in selected_files:
            file_path = os.path.join(tool_folder, filename)
            base_name = os.path.splitext(filename)[0]
            all_files.append(file_path)
            for p in glob.glob(os.path.join(tool_folder, "*.png")):
                if os.path.basename(p).startswith(base_name): all_files.append(p)
            all_res.extend(self.scan_resources_for_script(file_path))

        all_files, all_res = list(set(all_files)), list(set(all_res))

        if not all_res:
            self.execute_batch_delete(all_files, len(selected_files))
        else:
            msg = "\n".join([f"• {os.path.basename(p)}" for p in all_res[:8]]) + ("\n..." if len(all_res)>8 else "")
            reply = QMessageBox.question(self, "Confirm", self.txt.get("confirm_del_msg", "Delete?").format(count=len(selected_files), deps=msg), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes: self.execute_batch_delete(all_files + all_res, len(selected_files))

    def execute_batch_delete(self, paths, count):
        for p in paths:
            if os.path.isfile(p): os.remove(p)
            elif os.path.isdir(p): shutil.rmtree(p, ignore_errors=True)
        self.load_files_list()
        QMessageBox.information(self, "Success", self.txt.get("delete_success_msg", "Deleted.").format(count=count))

    def import_folder_dialog(self):
        src = QFileDialog.getExistingDirectory(self, self.txt.get("add_folder", "Import"))
        if not src or not self.current_scripts_folder: return
        
        target_map = {"tool":"Tool", "scriptresources":"ScriptResources", "utility":"Utility", "menu":"Menu", "tool_pro": "Tool_pro"}
        
        imported_tool_count = 0
        has_valid_content = False 
        
        for current_root, dirs, files in os.walk(src):
            for dirname in dirs:
                dir_lower = dirname.lower()
                if dir_lower in target_map:
                    has_valid_content = True
                    standard_name = target_map[dir_lower]
                    
                    src_dir_full = os.path.join(current_root, dirname)
                    dst_dir_full = os.path.join(self.current_scripts_folder, standard_name)
                    try:
                        self.copy_tree_merge(src_dir_full, dst_dir_full)
                        if standard_name == "Tool":
                            imported_tool_count += 1
                    except Exception as e:
                        print(f"Merge error: {e}")

        if has_valid_content:
            QMessageBox.information(self, "Success", self.txt.get("import_success_msg", "Imported").format(count=imported_tool_count))
            self.load_files_list()
        else:
            QMessageBox.warning(self, "Error", self.txt.get("import_err", "No valid folders found"))

    def copy_tree_merge(self, src, dst):
        if not os.path.exists(dst): os.makedirs(dst)
        for item in os.listdir(src):
            s, d = os.path.join(src, item), os.path.join(dst, item)
            if os.path.isdir(s): self.copy_tree_merge(s, d)
            else: shutil.copy2(s, d)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont(SYSTEM_FONT, BASE_FONT_SIZE))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())