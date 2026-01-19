# 手把手教你开发一个“代码存储器”：基于 Flask + SQLite 的个人代码片段管理工具

在日常开发中，我们经常会写一些有用的小片段、配置脚本或者算法实现。这些代码往往散落在各个项目的角落，或者临时的文本文件中，想用的时候很难找。

为了解决这个问题，我开发了一个轻量级的**代码存储器 (Code Store)**。它支持目录分类、标签管理、全文搜索以及代码高亮显示。今天就来分享一下这个项目的开发过程和技术细节。

## 🛠️ 技术栈选择

作为一个本地运行的轻量级工具，我选择了以下技术栈：

*   **后端**: Python Flask - 简单灵活，适合快速开发 RESTful API。
*   **数据库**: SQLite - 无需配置服务器，单文件存储，非常适合个人工具。
*   **前端**: 原生 HTML/JS/CSS - 保持轻量，不依赖复杂的构建工具。
*   **代码编辑器**: CodeMirror - 强大的网页代码编辑器组件，支持语法高亮。

## ✨ 核心功能预览

1.  **无限级目录树**：左侧提供类似于 IDE 的文件资源管理器，支持创建多级子目录。
2.  **代码高亮编辑**：集成 CodeMirror，根据文件名自动检测语言（Python, JS, SQL 等）并高亮。
3.  **标签系统**：除了目录分类，还可以给代码打上多个 Tag，方便跨目录检索。
4.  **全文搜索**：支持搜索文件名、代码内容和备注。
5.  **收藏夹**：一键收藏常用代码，快速访问。

## 💾 数据库设计

为了支持上述功能，我们需要设计合理的数据库结构。主要包含四张表：

1.  **directories (目录表)**
    *   `id`: 主键
    *   `parent_id`: 父目录 ID（实现无限层级）
    *   `name`: 目录名称

2.  **codes (代码表)**
    *   `id`: 主键
    *   `directory_id`: 所属目录
    *   `filename`: 文件名
    *   `content`: 代码内容
    *   `note`: 备注/说明
    *   `is_favorite`: 是否收藏 (0/1)

3.  **tags (标签表)**
    *   `id`: 主键
    *   `name`: 标签名（唯一）

4.  **code_tags (关联表)**
    *   `code_id`: 代码 ID
    *   `tag_id`: 标签 ID
    *   *多对多关系映射*

## 💻 核心代码实现

### 1. 后端 API 设计 (Flask)

我们采用 RESTful 风格设计 API，使得前后端完全分离。

```python
# app.py 示例
@app.route('/api/codes', methods=['POST'])
def add_code():
    data = request.json
    # ... 参数校验 ...
    code_id = db.add_code(directory_id, filename, content, note, is_favorite)
    if tags:
        db.update_code_tags(code_id, tags) # 处理标签关联
    return jsonify({'id': code_id}), 201
```

### 2. 数据库操作封装

为了保持代码整洁，我们将所有 SQL 操作封装在 `Database` 类中。

```python
# database.py 示例
class Database:
    def update_code_tags(self, code_id, tag_names):
        # 1. 确保标签存在
        # 2. 清理旧关联
        # 3. 建立新关联
        # ...
```

### 3. 前端编辑器集成

使用 CodeMirror 非常简单，只需要引入资源文件并初始化即可。我们还实现了一个简单的语言检测逻辑：

```javascript
// templates/index.html
function detectLanguage() {
    const filename = document.getElementById('edit-filename').value;
    let mode = "javascript"; // 默认
    
    if (filename.endsWith('.py')) mode = "python";
    else if (filename.endsWith('.html')) mode = "htmlmixed";
    else if (filename.endsWith('.sql')) mode = "sql";
    // ... 更多语言 ...
    
    if (cmEditor) cmEditor.setOption("mode", mode);
}

// 初始化
cmEditor = CodeMirror.fromTextArea(document.getElementById('edit-content'), {
    lineNumbers: true,
    theme: "monokai",
    lineWrapping: true
});
```

### 4. 目录树与交互

左侧的目录树是完全动态生成的。通过递归渲染 DOM 节点，实现了层级结构的展示。同时利用右键菜单（Context Menu）实现了新建子目录、重命名和删除功能。

```javascript
function createNode(dir) {
    // ... 创建 DOM ...
    item.oncontextmenu = (e) => showDirContextMenu(e, dir.id); // 绑定右键菜单
    // ... 递归渲染子节点 ...
}
```

## 🚀 如何运行

如果你也想拥有这个工具，只需几步即可运行：

1.  **克隆代码**: 下载本项目的代码。
2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **启动应用**:
    ```bash
    python app.py
    ```
4.  **访问**: 打开浏览器访问 `http://127.0.0.1:5000`。

## 🔮 未来展望

目前的版本已经满足了基本的存储和检索需求，未来还可以考虑加入：

*   **Markdown 预览**: 针对 `.md` 文件提供渲染预览。
*   **版本控制**: 记录代码的历史修改版本。
*   **Gist 同步**: 将代码同步到 GitHub Gist。
*   **多主题切换**: 支持更多编辑器配色。

---

希望这个小项目能给你的开发生活带来便利！如果你有任何建议，欢迎交流。
