**Moho Script Manager** is a tool for quickly managing Moho scripts.

[📚**中文介绍**](CNReadme.md)

---

## ✨ Features:
- **📂 Script Management**
  - Automatically identifies and lists Lua scripts in the `Tool` folder.
	- **Icon Synchronization**: Automatically displays `.png` icons with the same name as the script, automatically handling icon files when adding/deleting scripts.

- **💠 Dependency Safety**
	- **Smart Addition**: When adding a script, automatically detects whether the code contains `ScriptResources` or `utility` references and guides the user to add associated files.
	- **Safe Deletion**: When deleting a script, automatically detects whether there are associated resource files and prompts a pop-up window asking whether to delete or keep them, preventing accidental deletion or residual files.

- **⇅ Flexible Sorting**
	- Supports three sorting modes that cycle through: `filename (A-Z)`, `filename (Z-A)`, and `modified time (latest)`.

- **🎨 Visual Interface**
	- Built on CustomTkinter, it's aesthetically pleasing and simple.
	- **Day/Night Mode**: Supports one-click switching between dark and light themes (☀ / ☪).
	- **Multi-Language Support**: Built-in support for six languages: Chinese, English, Russian, Japanese, Korean, and Spanish.

- **🚀 Easy to use**
	- Automatically remembers the last opened folder path.
	- One-click opening of the current directory in File Explorer/Finder.

---

## 🛠️ Installation and Running:
Ensure that your computer has [Python](https://www.python.org/downloads/) installed.
1. Download [MohoScriptManager.py](https://github.com/hailey07/Moho-Scripts-Manager/releases/download/2026-01-07/MohoScriptsManager.py) to your local machine.

2. Install dependencies
   
Open Terminal or CMD and run the following command:

```
pip install customtkinter Pillow
```

3. Open Terminal or CMD and navigate to the folder containing the ``MohoScriptsManager.py`` file.

4. Run the tool

```
python MohoScriptsManager.py

or

python3 MohoScriptsManager.py
```

---

## 📖 Usage:
1. **Initial Launch**:
	- Open the software and click the **"📂 Select Tool Folder"** in the upper left corner.
	- Navigate to the `scripts/tool` folder within your custom Moho folder.

2. **Add Script**:
	- Click **"➕ Add Files"** and select the downloaded `.lua` file.
	- If there's a `.png` file with the same name in the same directory, the tool will automatically copy it.
	- If the script needs to associate with resources, the tool will display a pop-up notification.

3. **Delete Script**:
	- Click the red "Delete" button in the list.
	- If the script is safe, it will be deleted directly; if the script contains dependencies, a confirmation dialog will appear.

---

## 🖼︎ Screenshot
![](screenshot/2026-01-07.png)

## 💗 Thanks
This tool was written using Gemini.
If you find this tool useful, please share it with more Moho animation creators!
