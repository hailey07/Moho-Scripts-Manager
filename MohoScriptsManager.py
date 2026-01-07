import customtkinter as ctk
import os
import shutil
import json
import platform
import subprocess
import re
import webbrowser
from tkinter import filedialog, messagebox
from PIL import Image

# --- 获取路径 ---
def get_app_data_path():
    """获取跨平台的数据存储路径 (用户主目录)"""
    home = os.path.expanduser("~")
    # 在用户主目录下创建一个 .moho_manager 文件夹来存配置
    app_data_dir = os.path.join(home, ".moho_tool_manager")
    
    if not os.path.exists(app_data_dir):
        try:
            os.makedirs(app_data_dir)
        except Exception as e:
            print(f"无法创建配置文件夹: {e}")
            return home # 如果失败，回退到主目录
            
    return app_data_dir

# --- 配置与常量 ---
APP_DATA_DIR = get_app_data_path()
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json") # 配置文件存到用户目录
PLACEHOLDER_ICON = "❓"
BTN_WIDTH = 180

# 图标颜色配置 (支持十六进制颜色代码)
COLOR_SUN = "#F9A825"  # 太阳：深黄色
COLOR_MOON = "#9575CD" # 月亮：淡紫色
ICON_SUN = "☀︎"
ICON_MOON = "☪"

# --- 多语言字典 ---
LANGUAGES = {
    "English": {
        "title": "Moho Scripts Manager",
        "select_folder": "📂 Select Tool Folder",
        "open_folder": "👀 Open Folder",
        "add_file": "➕ Add Files",
        "sort_az": "🔄 Name (A-Z)",
        "sort_za": "🔄 Name (Z-A)",
        "sort_time": "🔄 Date (Newest)",
        "list_label": "Script List",
        "delete": "Delete",
        "no_folder": "Select 'Tool' folder...",
        "confirm_del_title": "Delete File",
        "res_del_title": "Associated Resource",
        "res_del_msg": "Resource file found:\n'{res_path}'\n\nDelete this resource as well?",
        "res_del_yes": "Delete Resource",
        "res_del_no": "Keep Resource",
        "add_check_title": "Association Detected",
        "add_check_msg": "Script contains 'ScriptResources' or 'utility'.\nOpen parent folder to add dependencies?",
        "link_scripts": "📜 Moho Scripts",
        "author": "by MoeU33",
        "error": "Error"
    },
    "中文": {
        "title": "Moho 脚本管理器",
        "select_folder": "📂 选择 Tool 文件夹",
        "open_folder": "👀 打开 Tool 文件夹",
        "add_file": "➕ 添加文件",
        "sort_az": "🔄 文件名 (A-Z)",
        "sort_za": "🔄 文件名 (Z-A)",
        "sort_time": "🔄 修改时间 (最新)",
        "list_label": "脚本列表",
        "delete": "删除",
        "no_folder": "请先选择 'Tool' 文件夹...",
        "confirm_del_title": "确认删除",
        "res_del_title": "发现关联资源",
        "res_del_msg": "发现关联资源文件：\n'{res_path}'\n\n是否连同资源文件一起删除？",
        "res_del_yes": "删除关联资源",
        "res_del_no": "保留关联资源",
        "add_check_title": "关联检测",
        "add_check_msg": "脚本包含 'ScriptResources' 或 'utility' 引用。\n是否打开上一级文件夹以便添加关联文件？",
        "link_scripts": "📜 Moho Scripts",
        "author": "by 萌酥33",
        "error": "错误"
    },
    "Русский": {
        "title": "Менеджер скриптов Moho",
        "select_folder": "📂 Папка Tool",
        "open_folder": "👀 Открыть папку",
        "add_file": "➕ Добавить",
        "sort_az": "🔄 Имя (A-Z)",
        "sort_za": "🔄 Имя (Z-A)",
        "sort_time": "🔄 Дата (Новые)",
        "list_label": "Список",
        "delete": "Удалить",
        "no_folder": "Выберите папку 'Tool'...",
        "confirm_del_title": "Удаление",
        "res_del_title": "Ресурс найден",
        "res_del_msg": "Найден ресурс:\n'{res_path}'\n\nУдалить его тоже?",
        "res_del_yes": "Удалить",
        "res_del_no": "Оставить",
        "add_check_title": "Связь",
        "add_check_msg": "Есть ссылки 'ScriptResources'. Открыть родительскую папку?",
        "link_scripts": "📜 Moho Scripts",
        "author": "by MoeU33",
        "error": "Ошибка"
    },
    "日本語": {
        "title": "Moho スクリプトマネージャー",
        "select_folder": "📂 フォルダ選択",
        "open_folder": "👀 開く",
        "add_file": "➕ 追加",
        "sort_az": "🔄 名前 (A-Z)",
        "sort_za": "🔄 名前 (Z-A)",
        "sort_time": "🔄 日付 (新しい順)",
        "list_label": "リスト",
        "delete": "削除",
        "no_folder": "'Tool'フォルダを選択...",
        "confirm_del_title": "削除",
        "res_del_title": "関連リソース",
        "res_del_msg": "リソースが見つかりました：\n'{res_path}'\n\nこれも削除しますか？",
        "res_del_yes": "削除",
        "res_del_no": "保持",
        "add_check_title": "確認",
        "add_check_msg": "'ScriptResources'が含まれています。親フォルダを開きますか？",
        "link_scripts": "📜 Moho Scripts",
        "author": "by MoeU33",
        "error": "エラー"
    },
    "한국어": {
        "title": "Moho 스크립트 관리자",
        "select_folder": "📂 폴더 선택",
        "open_folder": "👀 폴더 열기",
        "add_file": "➕ 추가",
        "sort_az": "🔄 이름 (A-Z)",
        "sort_za": "🔄 이름 (Z-A)",
        "sort_time": "🔄 날짜 (최신순)",
        "list_label": "목록",
        "delete": "삭제",
        "no_folder": "'Tool' 폴더 선택...",
        "confirm_del_title": "삭제",
        "res_del_title": "리소스 발견",
        "res_del_msg": "리소스가 발견되었습니다:\n'{res_path}'\n\n함께 삭제하시겠습니까?",
        "res_del_yes": "삭제",
        "res_del_no": "유지",
        "add_check_title": "확인",
        "add_check_msg": "'ScriptResources'가 포함됨. 상위 폴더를 여시겠습니까?",
        "link_scripts": "📜 Moho Scripts",
        "author": "by MoeU33",
        "error": "오류"
    },
    "Español": {
        "title": "Gestor de Scripts Moho",
        "select_folder": "📂 Carpeta Tool",
        "open_folder": "👀 Abrir carpeta",
        "add_file": "➕ Añadir",
        "sort_az": "🔄 Nombre (A-Z)",
        "sort_za": "🔄 Nombre (Z-A)",
        "sort_time": "🔄 Fecha (Reciente)",
        "list_label": "Lista",
        "delete": "Borrar",
        "no_folder": "Seleccione 'Tool'...",
        "confirm_del_title": "Borrar",
        "res_del_title": "Recurso",
        "res_del_msg": "Recurso encontrado:\n'{res_path}'\n\n¿Borrar también?",
        "res_del_yes": "Borrar",
        "res_del_no": "Mantener",
        "add_check_title": "Asociación",
        "add_check_msg": "Contiene 'ScriptResources'. ¿Abrir carpeta principal?",
        "link_scripts": "📜 Moho Scripts",
        "author": "by MoeU33",
        "error": "Error"
    }
}
SORT_MODES = ["name_asc", "name_desc", "date_desc"]
URL_SCRIPTS = "https://mohoscripts.com/"
URL_NOTION = "https://moeu33.notion.site/Moho-a49ca9864920461ab9bef0763d47ca21"

class ScriptManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # --- 初始化数据 ---
        self.config = self.load_config()
        self.current_lang = self.config.get("language", "English")
        self.sort_mode = self.config.get("sort_mode", "name_asc")
        self.current_folder = ""
        self.txt = LANGUAGES[self.current_lang]

        # 窗口设置
        self.title(self.txt["title"])
        self.geometry("700x750")
        self.set_theme(self.config.get("theme", "System"))

        # --- 布局 ---
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # 1. 左侧边栏
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        # 上部按钮区
        self.sidebar_frame.grid_rowconfigure(0, minsize=20) 
        
        # 核心功能按钮
        self.btn_select_folder = ctk.CTkButton(self.sidebar_frame, width=BTN_WIDTH, command=self.select_folder)
        self.btn_select_folder.grid(row=1, column=0, padx=20, pady=(10, 5))

        self.btn_open_folder = ctk.CTkButton(self.sidebar_frame, width=BTN_WIDTH, command=self.open_in_explorer)
        self.btn_open_folder.grid(row=2, column=0, padx=20, pady=5)
        
        self.btn_add_file = ctk.CTkButton(self.sidebar_frame, width=BTN_WIDTH, fg_color="#2CC985", hover_color="#229A65", command=self.add_files_dialog)
        self.btn_add_file.grid(row=3, column=0, padx=20, pady=5)
        
        self.btn_sort = ctk.CTkButton(self.sidebar_frame, width=BTN_WIDTH, command=self.toggle_sort_mode)
        self.btn_sort.grid(row=4, column=0, padx=20, pady=5)

        # === 布局核心：弹簧 ===
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        # === 设置区域 (左对齐) ===
        
        # 6. 日夜切换 (图标 + 开关)
        self.theme_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.theme_frame.grid(row=6, column=0, padx=20, pady=(0, 5), sticky="w") 
        
        # 图标 Label
        self.lbl_theme_icon = ctk.CTkLabel(self.theme_frame, text=ICON_SUN, font=("Arial", 24), text_color=COLOR_SUN)
        self.lbl_theme_icon.pack(side="left", padx=(5, 10)) 
        
        # 开关
        self.switch_mode = ctk.CTkSwitch(self.theme_frame, text="", width=40, command=self.toggle_mode)
        self.switch_mode.pack(side="left")
        
        # 初始化开关状态
        if self.config.get("theme") == "Dark":
            self.switch_mode.select()
            self.lbl_theme_icon.configure(text=ICON_MOON, text_color=COLOR_MOON)
        else:
            self.lbl_theme_icon.configure(text=ICON_SUN, text_color=COLOR_SUN)

        # 7. 语言选择
        self.option_lang = ctk.CTkOptionMenu(self.sidebar_frame, width=BTN_WIDTH, values=list(LANGUAGES.keys()), command=self.change_language)
        self.option_lang.set(self.current_lang)
        self.option_lang.grid(row=7, column=0, padx=20, pady=(5, 45)) 

        # 8. 链接区域
        self.link_scripts = ctk.CTkButton(self.sidebar_frame, text="", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w", hover_color=("gray70", "gray30"), command=lambda: webbrowser.open(URL_SCRIPTS))
        self.link_scripts.grid(row=8, column=0, padx=20, pady=1, sticky="ew")

        self.link_notion = ctk.CTkButton(self.sidebar_frame, text="📓 Moho 脚本整理", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w", hover_color=("gray70", "gray30"), command=lambda: webbrowser.open(URL_NOTION))
        self.link_notion.grid(row=9, column=0, padx=20, pady=(1, 10), sticky="ew")

        # 9. 作者信息
        self.lbl_author = ctk.CTkLabel(self.sidebar_frame, text="", font=("Arial", 12), text_color="gray50")
        self.lbl_author.grid(row=10, column=0, padx=20, pady=(0, 20))

        # 2. 右侧主区域
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # --- 初始化 ---
        self.update_ui_text()
        
        if self.config.get("last_folder") and os.path.exists(self.config.get("last_folder")):
            self.current_folder = self.config.get("last_folder")
            self.load_files_list()

    # --- 逻辑 ---
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding='utf-8') as f: return json.load(f)
            except: return {}
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False)

    def get_sort_text(self):
        if self.sort_mode == "name_asc": return self.txt["sort_az"]
        elif self.sort_mode == "name_desc": return self.txt["sort_za"]
        elif self.sort_mode == "date_desc": return self.txt["sort_time"]
        return self.txt["sort_az"]

    def update_ui_text(self):
        self.txt = LANGUAGES[self.current_lang]
        self.title(self.txt["title"])
        
        self.btn_select_folder.configure(text=self.txt["select_folder"])
        self.btn_open_folder.configure(text=self.txt["open_folder"])
        self.btn_add_file.configure(text=self.txt["add_file"])
        self.btn_sort.configure(text=self.get_sort_text())
        
        if self.current_folder:
             self.main_frame.configure(label_text=f"{self.txt['list_label']}: {os.path.basename(self.current_folder)}")
        else:
             self.main_frame.configure(label_text=self.txt["no_folder"])

        self.link_scripts.configure(text=self.txt["link_scripts"])
        self.lbl_author.configure(text=self.txt["author"])
        
        # --- 修复：重新加载列表以更新“删除”按钮的文字 ---
        self.load_files_list()

    def change_language(self, choice):
        self.current_lang = choice
        self.config["language"] = choice
        self.save_config()
        self.update_ui_text()

    def set_theme(self, mode):
        if mode == "Dark":
            ctk.set_appearance_mode("Dark")
            self.config["theme"] = "Dark"
        else:
            ctk.set_appearance_mode("Light")
            self.config["theme"] = "Light"
        self.save_config()

    def toggle_mode(self):
        if self.switch_mode.get() == 1:
            self.set_theme("Dark")
            self.lbl_theme_icon.configure(text=ICON_MOON, text_color=COLOR_MOON)
        else:
            self.set_theme("Light")
            self.lbl_theme_icon.configure(text=ICON_SUN, text_color=COLOR_SUN)

    def toggle_sort_mode(self):
        try:
            current_index = SORT_MODES.index(self.sort_mode)
            next_index = (current_index + 1) % len(SORT_MODES)
            self.sort_mode = SORT_MODES[next_index]
        except:
            self.sort_mode = SORT_MODES[0]

        self.config["sort_mode"] = self.sort_mode
        self.save_config()
        self.btn_sort.configure(text=self.get_sort_text())
        self.load_files_list()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.config["last_folder"] = folder
            self.save_config()
            self.load_files_list()

    def open_in_explorer(self, target_path=None):
        path_to_open = target_path if target_path else self.current_folder
        if not path_to_open or not os.path.exists(path_to_open):
            messagebox.showwarning(self.txt["error"], self.txt["no_folder"])
            return
        
        system_name = platform.system()
        try:
            if system_name == "Windows": os.startfile(path_to_open)
            elif system_name == "Darwin": subprocess.call(["open", path_to_open])
            else: subprocess.call(["xdg-open", path_to_open])
        except: pass

    def load_files_list(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()

        if not self.current_folder:
            self.main_frame.configure(label_text=self.txt["no_folder"])
            return
        
        self.main_frame.configure(label_text=f"{self.txt['list_label']}: {os.path.basename(self.current_folder)}")

        try:
            files = os.listdir(self.current_folder)
            lua_files = [f for f in files if f.lower().endswith('.lua')]
            
            if self.sort_mode == "name_asc":
                lua_files.sort(key=str.lower)
            elif self.sort_mode == "name_desc":
                lua_files.sort(key=str.lower, reverse=True)
            elif self.sort_mode == "date_desc":
                lua_files.sort(key=lambda f: os.path.getmtime(os.path.join(self.current_folder, f)), reverse=True)
            else:
                lua_files.sort()
            
            for f in lua_files: self.create_file_item(f)
        except Exception: return

    def create_file_item(self, lua_filename):
        base_name = os.path.splitext(lua_filename)[0]
        png_filename = base_name + ".png"
        png_path = os.path.join(self.current_folder, png_filename)
        
        card = ctk.CTkFrame(self.main_frame)
        card.pack(fill="x", padx=5, pady=5)
        
        if os.path.exists(png_path):
            try:
                img = Image.open(png_path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(24, 24))
                icon_label = ctk.CTkLabel(card, text="", image=ctk_img)
            except: icon_label = ctk.CTkLabel(card, text=PLACEHOLDER_ICON, font=("Arial", 16))
        else:
            icon_label = ctk.CTkLabel(card, text=PLACEHOLDER_ICON, font=("Arial", 16))
        
        icon_label.pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(card, text=lua_filename, font=("Arial", 14)).pack(side="left", padx=10)
        ctk.CTkButton(card, text=self.txt["delete"], fg_color="#FF5555", hover_color="#CC0000", width=60,
                      command=lambda f=lua_filename: self.delete_script(f)).pack(side="right", padx=10, pady=8)

    def delete_script(self, filename):
        file_path = os.path.join(self.current_folder, filename)
        base_name = os.path.splitext(filename)[0]
        png_path = os.path.join(self.current_folder, base_name + ".png")
        resource_path_relative = None
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                match = re.search(r'["\'](ScriptResources[\\/][^"\']+)["\']', content)
                if match: resource_path_relative = match.group(1)
        except: pass
        
        if not resource_path_relative:
            self.execute_delete(file_path, png_path, None)
            return

        parent_dir = os.path.dirname(self.current_folder) 
        clean_rel_path = resource_path_relative.replace("\\", os.sep).replace("/", os.sep)
        full_res_path = os.path.join(parent_dir, clean_rel_path)
        if not os.path.exists(full_res_path): full_res_path = os.path.join(self.current_folder, clean_rel_path)

        dialog = ctk.CTkToplevel(self)
        dialog.title(self.txt["res_del_title"])
        dialog.geometry("400x250")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text=self.txt["res_del_msg"].format(res_path=resource_path_relative), wraplength=350).pack(pady=20, padx=20)
        
        ctk.CTkButton(dialog, text=self.txt["res_del_yes"], fg_color="#FF5555", hover_color="#CC0000", 
                      command=lambda: [dialog.destroy(), self.execute_delete(file_path, png_path, full_res_path)]).pack(pady=5)
        ctk.CTkButton(dialog, text=self.txt["res_del_no"], fg_color="gray", hover_color="darkgray", 
                      command=lambda: [dialog.destroy(), self.execute_delete(file_path, png_path, None)]).pack(pady=5)
        dialog.wait_window()

    def execute_delete(self, lua_path, png_path, res_path):
        try:
            if os.path.exists(lua_path): os.remove(lua_path)
            if os.path.exists(png_path): os.remove(png_path)
            if res_path and os.path.exists(res_path):
                if os.path.isfile(res_path): os.remove(res_path)
                elif os.path.isdir(res_path): shutil.rmtree(res_path) 
            self.load_files_list()
        except Exception as e: messagebox.showerror(self.txt["error"], str(e))

    def add_files_dialog(self):
        if not self.current_folder:
            messagebox.showwarning(self.txt["error"], self.txt["no_folder"])
            return
        file_paths = filedialog.askopenfilenames(title=self.txt["add_file"])
        if not file_paths: return

        warnings = False
        for src_path in file_paths:
            if not os.path.exists(src_path): continue
            filename = os.path.basename(src_path)
            dst_path = os.path.join(self.current_folder, filename)
            try:
                shutil.copy2(src_path, dst_path)
                if filename.lower().endswith(".lua"):
                    src_dir = os.path.dirname(src_path)
                    possible_png = os.path.splitext(filename)[0] + ".png"
                    if os.path.exists(os.path.join(src_dir, possible_png)):
                        shutil.copy2(os.path.join(src_dir, possible_png), os.path.join(self.current_folder, possible_png))
                    with open(dst_path, 'r', encoding='utf-8', errors='ignore') as f:
                        if "ScriptResources" in f.read() or "utility" in f.read(): warnings = True
            except: pass
        self.load_files_list()
        if warnings:
            if messagebox.askyesno(self.txt["add_check_title"], self.txt["add_check_msg"]):
                self.open_in_explorer(os.path.dirname(self.current_folder))

if __name__ == "__main__":
    app = ScriptManagerApp()
    app.mainloop()
