import customtkinter as ctk
import os
import shutil
import json
import platform
import subprocess
import re
import webbrowser
import glob
from tkinter import filedialog, messagebox
from PIL import Image

# --- 引入外部语言包 ---
try:
    import lang_config
except ImportError:
    print("Error: lang_config.py not found!")
    exit()

# --- 获取路径 ---
def get_app_data_path():
    home = os.path.expanduser("~")
    app_data_dir = os.path.join(home, ".moho_tool_manager")
    if not os.path.exists(app_data_dir):
        try:
            os.makedirs(app_data_dir)
        except Exception:
            return home
    return app_data_dir

# --- 配置与常量 ---
APP_DATA_DIR = get_app_data_path()
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")
PLACEHOLDER_ICON = "❓"
BTN_WIDTH = 180

COLOR_SUN = "#F9A825"
COLOR_MOON = "#9575CD"
ICON_SUN = "☀︎"
ICON_MOON = "☪"

SORT_MODES = ["name_asc", "name_desc", "date_desc"]
URL_SCRIPTS = "https://mohoscripts.com/"
URL_NOTION = "https://moeu33.notion.site/Moho-a49ca9864920461ab9bef0763d47ca21"

class ScriptManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.config = self.load_config()
        self.current_lang = self.config.get("language", "English")
        self.txt = lang_config.get_lang(self.current_lang)
        self.sort_mode = self.config.get("sort_mode", "name_asc")
        
        self.current_scripts_folder = ""
        self.check_vars = {} 
        self.all_selected_flag = False
        
        self.title(self.txt["title"])
        self.geometry("800x800")
        self.set_theme(self.config.get("theme", "System"))

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        
        self.sidebar_frame.grid_rowconfigure(0, minsize=20) 
        self.sidebar_frame.grid_columnconfigure(0, minsize=200)

        # --- 按钮重新排序 ---
        
        # 1. 选择 Scripts 文件夹
        self.btn_select_folder = ctk.CTkButton(self.sidebar_frame, anchor="w", command=self.select_folder)
        self.btn_select_folder.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="ew")

        # 2. 打开 Scripts 文件夹
        self.btn_open_folder = ctk.CTkButton(self.sidebar_frame, anchor="w", command=self.open_in_explorer)
        self.btn_open_folder.grid(row=2, column=0, padx=20, pady=5, sticky="ew")
        
        # 3. 导入外部文件夹
        self.btn_add_file = ctk.CTkButton(self.sidebar_frame, anchor="w", fg_color="#2CC985", hover_color="#229A65", command=self.import_folder_dialog)
        self.btn_add_file.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        
        # 4. 排序按钮
        self.btn_sort = ctk.CTkButton(self.sidebar_frame, anchor="w", command=self.toggle_sort_mode)
        self.btn_sort.grid(row=4, column=0, padx=20, pady=5, sticky="ew")

        # 5. 刷新列表
        self.btn_refresh = ctk.CTkButton(self.sidebar_frame, anchor="w", fg_color="#3B8ED0", hover_color="#36719F", command=self.load_files_list)
        self.btn_refresh.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        # --- 空行效果 (通过 pady 实现) ---

        # 6. 全选/取消全选 (上方增加 25px 间距)
        self.btn_select_all = ctk.CTkButton(self.sidebar_frame, anchor="w", fg_color="gray", hover_color="darkgray", command=self.toggle_select_all)
        self.btn_select_all.grid(row=6, column=0, padx=20, pady=(25, 5), sticky="ew")

        # 7. 删除选中项
        self.btn_del_selected = ctk.CTkButton(self.sidebar_frame, anchor="w", fg_color="#FF5555", hover_color="#CC0000", command=self.delete_selected_scripts)
        self.btn_del_selected.grid(row=7, column=0, padx=20, pady=5, sticky="ew")

        self.sidebar_frame.grid_rowconfigure(8, weight=1) 

        # Theme & Lang
        self.theme_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.theme_frame.grid(row=9, column=0, padx=20, pady=(0, 5), sticky="ew") 
        self.lbl_theme_icon = ctk.CTkLabel(self.theme_frame, text=ICON_SUN, font=("Arial", 24), text_color=COLOR_SUN)
        self.lbl_theme_icon.pack(side="left", padx=(5, 10)) 
        self.switch_mode = ctk.CTkSwitch(self.theme_frame, text="", width=40, command=self.toggle_mode)
        self.switch_mode.pack(side="left")
        
        if self.config.get("theme") == "Dark":
            self.switch_mode.select()
            self.lbl_theme_icon.configure(text=ICON_MOON, text_color=COLOR_MOON)
        else:
            self.lbl_theme_icon.configure(text=ICON_SUN, text_color=COLOR_SUN)

        self.option_lang = ctk.CTkOptionMenu(self.sidebar_frame, values=list(lang_config.LANGUAGES.keys()), command=self.change_language)
        self.option_lang.set(self.current_lang)
        self.option_lang.grid(row=10, column=0, padx=20, pady=(5, 45), sticky="ew") 

        self.link_scripts = ctk.CTkButton(self.sidebar_frame, text="", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w", hover_color=("gray70", "gray30"), command=lambda: webbrowser.open(URL_SCRIPTS))
        self.link_scripts.grid(row=11, column=0, padx=20, pady=1, sticky="ew")
        self.link_notion = ctk.CTkButton(self.sidebar_frame, text="📓 Moho 脚本整理", fg_color="transparent", text_color=("gray10", "gray90"), anchor="w", hover_color=("gray70", "gray30"), command=lambda: webbrowser.open(URL_NOTION))
        self.link_notion.grid(row=12, column=0, padx=20, pady=(1, 10), sticky="ew")

        self.lbl_author = ctk.CTkLabel(self.sidebar_frame, text="", font=("Arial", 12), text_color="gray50")
        self.lbl_author.grid(row=13, column=0, padx=20, pady=(0, 20))

        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.update_ui_text()
        
        last_folder = self.config.get("last_folder")
        if last_folder and os.path.exists(last_folder):
            if os.path.basename(last_folder).lower() == "scripts":
                self.current_scripts_folder = last_folder
                self.load_files_list()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding='utf-8') as f: return json.load(f)
            except: return {}
        return {}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False)

    def update_ui_text(self):
        self.txt = lang_config.get_lang(self.current_lang)
        self.title(self.txt["title"])
        self.btn_select_folder.configure(text=self.txt["select_folder"])
        self.btn_open_folder.configure(text=self.txt["open_folder"])
        self.btn_add_file.configure(text=self.txt["add_folder"]) 
        self.btn_refresh.configure(text=self.txt["refresh"])
        self.btn_del_selected.configure(text=self.txt["del_selected"])
        
        if self.all_selected_flag:
            self.btn_select_all.configure(text=self.txt["deselect_all"])
        else:
            self.btn_select_all.configure(text=self.txt["select_all"])

        self.btn_sort.configure(text=self.get_sort_text())
        self.link_scripts.configure(text=self.txt["link_scripts"])
        self.lbl_author.configure(text=self.txt["author"])
        
        if self.current_scripts_folder:
             self.main_frame.configure(label_text=f"{self.txt['list_label']}")
        else:
             self.main_frame.configure(label_text=self.txt["no_folder"])
        
        if self.current_scripts_folder:
            self.load_files_list()

    def get_sort_text(self):
        if self.sort_mode == "name_asc": return self.txt["sort_az"]
        elif self.sort_mode == "name_desc": return self.txt["sort_za"]
        elif self.sort_mode == "date_desc": return self.txt["sort_time"]
        return self.txt["sort_az"]

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
            idx = SORT_MODES.index(self.sort_mode)
            self.sort_mode = SORT_MODES[(idx + 1) % len(SORT_MODES)]
        except: self.sort_mode = SORT_MODES[0]
        self.config["sort_mode"] = self.sort_mode
        self.save_config()
        self.btn_sort.configure(text=self.get_sort_text())
        self.load_files_list()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        folder_name = os.path.basename(folder).lower()
        if folder_name != "scripts":
            messagebox.showerror(self.txt["error_folder_name"], self.txt["error_folder_msg"].format(path=os.path.basename(folder)))
            return
        self.current_scripts_folder = folder
        self.config["last_folder"] = folder
        self.save_config()
        self.update_ui_text()
        
    def open_in_explorer(self):
        target = self.current_scripts_folder
        if not target or not os.path.exists(target):
            messagebox.showwarning(self.txt["error"], self.txt["no_folder"])
            return
        sys_name = platform.system()
        try:
            if sys_name == "Windows": os.startfile(target)
            elif sys_name == "Darwin": subprocess.call(["open", target])
            else: subprocess.call(["xdg-open", target])
        except: pass

    def toggle_select_all(self):
        if not self.check_vars: return
        self.all_selected_flag = not self.all_selected_flag
        target_val = 1 if self.all_selected_flag else 0
        for var in self.check_vars.values():
            var.set(target_val)
        if self.all_selected_flag:
            self.btn_select_all.configure(text=self.txt["deselect_all"])
        else:
            self.btn_select_all.configure(text=self.txt["select_all"])

    def load_files_list(self):
        for widget in self.main_frame.winfo_children(): widget.destroy()
        self.check_vars.clear()
        self.all_selected_flag = False
        self.btn_select_all.configure(text=self.txt["select_all"])

        if not self.current_scripts_folder:
            self.main_frame.configure(label_text=self.txt["no_folder"])
            return
        
        tool_folder = os.path.join(self.current_scripts_folder, "Tool")
        if not os.path.exists(tool_folder):
            ctk.CTkLabel(self.main_frame, text="No 'Tool' folder found inside Scripts.", text_color="gray").pack(pady=20)
            return
        
        try:
            files = os.listdir(tool_folder)
            lua_files = [f for f in files if f.lower().endswith('.lua')]
            
            if self.sort_mode == "name_asc": 
                lua_files.sort(key=str.lower)
            elif self.sort_mode == "name_desc": 
                lua_files.sort(key=str.lower, reverse=True)
            elif self.sort_mode == "date_desc":
                lua_files.sort(key=lambda f: os.path.getmtime(os.path.join(tool_folder, f)), reverse=True)
            else: 
                lua_files.sort()
            
            for f in lua_files: self.create_file_item(f, tool_folder)
        except Exception as e: print(f"List error: {e}")

    def create_file_item(self, lua_filename, tool_folder):
        file_path = os.path.join(tool_folder, lua_filename)
        base_name = os.path.splitext(lua_filename)[0]
        png_path = os.path.join(tool_folder, base_name + ".png")
        meta = self.parse_lua_metadata(file_path)
        
        card = ctk.CTkFrame(self.main_frame, fg_color="transparent") 
        card.pack(fill="x", padx=5, pady=(5, 0))
        check_var = ctk.IntVar()
        self.check_vars[lua_filename] = check_var
        
        chk = ctk.CTkCheckBox(card, text="", variable=check_var, width=24, checkbox_width=24, checkbox_height=24, corner_radius=12)
        chk.pack(side="left", padx=(10, 5), pady=5)

        if os.path.exists(png_path):
            try:
                img = Image.open(png_path)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(24, 20))
                icon_label = ctk.CTkLabel(card, text="", image=ctk_img, 
                                          fg_color=("#D0D0D0", "#505050"), 
                                          corner_radius=4, 
                                          width=34, height=34)
            except: icon_label = ctk.CTkLabel(card, text=PLACEHOLDER_ICON, font=("Arial", 20))
        else:
            icon_label = ctk.CTkLabel(card, text=PLACEHOLDER_ICON, font=("Arial", 20))
        icon_label.pack(side="left", padx=5, pady=5, anchor="n")

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        title_text = meta["name"] if meta["name"] else lua_filename
        lbl_title = ctk.CTkLabel(info_frame, text=title_text, font=("Arial", 14, "bold"), anchor="w", height=20)
        lbl_title.pack(fill="x", pady=(0, 0))

        meta_parts = []
        if meta["version"]: meta_parts.append(f"v{meta["version"]}")
        if meta["creator"]: meta_parts.append(f"@{meta["creator"]}")
        
        if meta_parts:
            meta_str = "  |  ".join(meta_parts)
            ctk.CTkLabel(info_frame, text=meta_str, font=("Arial", 11), text_color="gray60", anchor="w", height=16).pack(fill="x", pady=(0, 0))
        
        if meta["name"] and meta["name"] != lua_filename:
             ctk.CTkLabel(info_frame, text=lua_filename, font=("Arial", 10), text_color="gray50", anchor="w", height=14).pack(fill="x", pady=(0, 0))

        divider = ctk.CTkFrame(self.main_frame, height=1, fg_color=("gray90", "gray30"))
        divider.pack(fill="x", padx=15, pady=(5, 0))

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

    def delete_selected_scripts(self):
        selected_files = [fname for fname, var in self.check_vars.items() if var.get() == 1]
        
        if not selected_files:
            messagebox.showinfo(self.txt["title"], self.txt["del_no_selection"])
            return

        all_files_to_delete = [] 
        all_resources_to_delete = [] 
        
        tool_folder = os.path.join(self.current_scripts_folder, "Tool")
        
        for filename in selected_files:
            file_path = os.path.join(tool_folder, filename)
            base_name = os.path.splitext(filename)[0]
            
            all_files_to_delete.append(file_path)
            all_pngs = glob.glob(os.path.join(tool_folder, "*.png"))
            for png_path in all_pngs:
                if os.path.basename(png_path).startswith(base_name):
                    all_files_to_delete.append(png_path)
            
            resources = self.scan_resources_for_script(file_path)
            all_resources_to_delete.extend(resources)

        all_files_to_delete = list(set(all_files_to_delete))
        all_resources_to_delete = list(set(all_resources_to_delete))
        
        # 记录用户选择的脚本数量，用于弹窗提示
        script_count = len(selected_files)

        if not all_resources_to_delete:
             self.execute_batch_delete(all_files_to_delete, script_count)
        else:
            msg_files = "\n".join([f"• {os.path.basename(p)}" for p in all_resources_to_delete])
            if len(all_resources_to_delete) > 8:
                 msg_files = "\n".join([f"• {os.path.basename(p)}" for p in all_resources_to_delete[:8]]) + "\n..."
            
            confirm_msg = self.txt["confirm_del_msg"].format(count=len(selected_files), deps=msg_files)
            
            dialog = ctk.CTkToplevel(self)
            dialog.title(self.txt["confirm_del_title"])
            dialog.geometry("500x500")
            dialog.attributes("-topmost", True)
            
            ctk.CTkLabel(dialog, text=confirm_msg, wraplength=450, justify="left").pack(pady=20, padx=20)
            
            btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
            btn_frame.pack(pady=10)
            
            ctk.CTkButton(btn_frame, text=self.txt["dep_del_yes"], fg_color="#FF5555", hover_color="#CC0000", 
                          command=lambda: [dialog.destroy(), self.execute_batch_delete(all_files_to_delete + all_resources_to_delete, script_count)]).pack(side="left", padx=10)
            ctk.CTkButton(btn_frame, text=self.txt["dep_del_no"], fg_color="gray", hover_color="darkgray", 
                          command=lambda: dialog.destroy()).pack(side="left", padx=10)
            dialog.wait_window()

    def scan_resources_for_script(self, file_path):
        candidates = []
        IGNORED_SYS_FILES = [".ds_store", "thumbs.db", "desktop.ini"]

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                matches = re.findall(r'["\'](ScriptResources[\\/][^"\']+)["\']', content, re.IGNORECASE)
                
                folder_map = {} 
                direct_files = [] 

                for m in matches:
                    rel_path = m.replace("\\", os.sep).replace("/", os.sep)
                    parts = rel_path.split(os.sep)
                    
                    if len(parts) > 2:
                        folder_name = parts[1]
                        file_name = parts[2] 
                        full_folder_path = os.path.join(self.current_scripts_folder, "ScriptResources", folder_name)
                        
                        if full_folder_path not in folder_map:
                            folder_map[full_folder_path] = set()
                        folder_map[full_folder_path].add(file_name)
                        
                    elif len(parts) == 2:
                        full_path = os.path.join(self.current_scripts_folder, rel_path)
                        if os.path.exists(full_path) and os.path.isfile(full_path):
                            direct_files.append(full_path)
                        else:
                            if os.path.exists(full_path + ".png"): direct_files.append(full_path + ".png")
                            if os.path.exists(full_path + ".lua"): direct_files.append(full_path + ".lua")

                for folder_path, referenced_names_set in folder_map.items():
                    if not os.path.exists(folder_path): continue
                    
                    files_in_folder_to_delete = []
                    has_alien_files = False 

                    for f in os.listdir(folder_path):
                        full_p = os.path.join(folder_path, f)
                        if not os.path.isfile(full_p): continue 
                        
                        if f.lower() in IGNORED_SYS_FILES:
                            continue

                        is_dolayout_file = False
                        name_no_ext = os.path.splitext(f)[0]

                        if (f in referenced_names_set) or (name_no_ext in referenced_names_set):
                            is_dolayout_file = True
                        else:
                            for ref in referenced_names_set:
                                if name_no_ext.startswith(ref + "_") or name_no_ext.startswith(ref + "@"):
                                    is_dolayout_file = True
                                    break
                        
                        if is_dolayout_file:
                            files_in_folder_to_delete.append(full_p)
                        else:
                            has_alien_files = True

                    if not has_alien_files:
                        candidates.append(folder_path)
                    else:
                        candidates.extend(files_in_folder_to_delete)

                candidates.extend(direct_files)

        except Exception as e:
            print(f"Scan error {file_path}: {e}")
            
        return candidates

    def execute_batch_delete(self, path_list, script_count_for_msg):
        try:
            path_list = list(set(path_list))
            # 注意：实际删除文件不依赖 script_count，它只负责显示
            for p in path_list:
                if not os.path.exists(p): continue
                if os.path.isfile(p): 
                    os.remove(p)
                elif os.path.isdir(p): 
                    shutil.rmtree(p, ignore_errors=True)
            
            self.load_files_list()
            # 这里调用的是用户选择的数量，而不是实际文件数
            messagebox.showinfo(self.txt["title"], self.txt["delete_success_msg"].format(count=script_count_for_msg))
            
        except Exception as e: messagebox.showerror(self.txt["error"], str(e))

    def import_folder_dialog(self):
        if not self.current_scripts_folder:
            messagebox.showwarning(self.txt["error"], self.txt["no_folder"])
            return
        
        src_root = filedialog.askdirectory(title=self.txt["add_folder"])
        if not src_root: return

        target_map = {
            "tool": "Tool",
            "scriptresources": "ScriptResources",
            "utility": "Utility",
            "menu": "Menu",
            "modules": "Modules",
            "tool_pro": "Tool_pro"
        }
        
        imported_count = 0
        any_valid_found = False 
        
        for current_root, dirs, files in os.walk(src_root):
            for dirname in dirs:
                dir_lower = dirname.lower()
                if dir_lower in target_map:
                    any_valid_found = True
                    standard_name = target_map[dir_lower]
                    src_dir_full = os.path.join(current_root, dirname)
                    dst_dir_full = os.path.join(self.current_scripts_folder, standard_name)
                    try:
                        self.copy_tree_merge(src_dir_full, dst_dir_full)
                        if standard_name == "Tool":
                            imported_count += 1
                    except Exception as e:
                        print(f"Merge error: {e}")

        if any_valid_found:
            messagebox.showinfo(self.txt["import_title"], self.txt["import_success_msg"].format(count=imported_count))
            self.load_files_list()
        else:
            messagebox.showwarning(self.txt["error"], self.txt["import_err"])

    def copy_tree_merge(self, src, dst):
        if not os.path.exists(dst): os.makedirs(dst)
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s): self.copy_tree_merge(s, d)
            else: shutil.copy2(s, d)

if __name__ == "__main__":
    app = ScriptManagerApp()
    app.mainloop()
