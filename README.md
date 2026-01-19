# Code Store (代码存储器)

Code Store 是一个基于 Python Flask 和 SQLite 构建的轻量级本地代码片段管理工具。它旨在帮助开发者高效地组织、存储、搜索和同步常用的代码片段。

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Flask](https://img.shields.io/badge/flask-2.x-orange.svg)

## ✨ 主要功能

### 📁 组织与管理
*   **无限级目录**：支持创建多层级的目录结构，灵活分类代码。
*   **拖拽移动**：支持直接将代码文件拖拽到左侧目录树进行移动。
*   **代码高亮**：集成 CodeMirror 编辑器，支持 Python, JS, HTML, CSS, SQL 等多种语言的语法高亮（根据文件名后缀自动检测）。

### 🏷️ 标记与检索
*   **智能搜索**：支持对文件名、代码内容、备注进行全文搜索。
*   **彩色标签**：支持为代码添加彩色标签，交互式添加/删除，直观分类。
*   **置顶与收藏**：重要代码一键置顶（📌）或收藏（⭐），快速访问。

### 💾 存储与同步
*   **自动保存**：编辑内容时自动静默保存，防止数据丢失。
*   **SQLite 存储**：所有数据存储在本地单文件数据库 (`codestore.db`) 中，安全且易于备份。
*   **Github 同步**：支持将本地代码库**全量镜像同步**到指定的 Github 仓库，实现云端备份。
    *   自动处理目录映射。
    *   支持空仓库自动初始化。

### 🎨 个性化
*   **主题切换**：内置 Monokai, Dracula, Eclipse, Material 等多款编辑器主题。
*   **字体设置**：可自定义编辑器字体（如 Fira Code, Consolas）和字号。

## 🚀 快速开始

### 环境要求
*   Python 3.6+

### 安装步骤

1.  **克隆或下载项目**
    ```bash
    git clone <repository-url>
    cd code-store
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **运行应用**
    ```bash
    python app.py
    ```

4.  **访问**
    打开浏览器访问：[http://127.0.0.1:5000](http://127.0.0.1:5000)

## 📖 使用指南

### 1. 目录与代码管理
*   点击左侧栏顶部的 `+` 按钮创建根目录。
*   右键点击目录可创建子目录、重命名或删除。
*   点击“新建代码”按钮在当前目录下创建代码片段。
*   在编辑器顶部下拉框可直接修改代码所属目录。

### 2. Github 同步配置
点击顶部的 **"🐙 同步到 Github"** 按钮进行配置：
*   **Token**: 需要一个具有 `repo` 权限的 Github Personal Access Token (PAT)。
*   **Owner/Repo**: 你的 Github 用户名和仓库名。
*   **Branch**: 同步的分支（默认为 `main`）。
*   **⚠️ 注意**：同步操作是**镜像模式**，会使远程仓库完全与本地一致（远程多余的文件会被删除），请确保使用专门的备份仓库。

### 3. 快捷键与操作
*   **保存**：Ctrl+S (或等待自动保存)。
*   **搜索**：在搜索框输入关键词后回车。
*   **标签**：在标签输入框输入内容后按 **Enter** 添加，按 **Backspace** 删除最后一个标签。

## 📂 项目结构

```
code-store/
├── app.py              # Flask 后端应用入口，API 路由定义
├── database.py         # SQLite 数据库操作封装 (CRUD)
├── codestore.db        # (自动生成) 数据存储文件
├── requirements.txt    # 项目依赖列表
├── templates/
│   └── index.html      # 前端单页应用 (HTML/CSS/JS)
└── README.md           # 项目说明文档
```

## 🛠️ 技术栈
*   **Backend**: Python, Flask, SQLite3
*   **Frontend**: HTML5, CSS3, Vanilla JavaScript
*   **Editor**: CodeMirror 5
*   **Network**: Requests (for Github API)

## 📄 License
MIT License
