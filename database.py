import sqlite3
import os

class Database:
    def __init__(self, db_file="codestore.db"):
        self.db_file = db_file
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 创建目录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS directories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                name TEXT NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES directories (id) ON DELETE CASCADE
            )
        ''')

        # 创建代码表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                directory_id INTEGER,
                filename TEXT NOT NULL,
                content TEXT,
                note TEXT,
                is_favorite INTEGER DEFAULT 0,
                is_pinned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (directory_id) REFERENCES directories (id) ON DELETE CASCADE
            )
        ''')

        # 检查并迁移 is_pinned 字段
        cursor.execute("PRAGMA table_info(codes)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'is_pinned' not in columns:
            cursor.execute('ALTER TABLE codes ADD COLUMN is_pinned INTEGER DEFAULT 0')

        # 创建标签表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')

        # 创建代码标签关联表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_tags (
                code_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (code_id, tag_id),
                FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
            )
        ''')
        
        # 插入根目录（如果不存在）
        cursor.execute('SELECT count(*) FROM directories WHERE parent_id IS NULL')
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO directories (name, parent_id) VALUES (?, ?)', ('Root', None))

        conn.commit()
        conn.close()

    def _attach_tags_to_codes(self, codes):
        """Helper to attach tags to a list of code dicts"""
        if not codes:
            return codes
            
        conn = self.get_connection()
        cursor = conn.cursor()
        
        for code in codes:
            cursor.execute('''
                SELECT t.name FROM tags t
                JOIN code_tags ct ON t.id = ct.tag_id
                WHERE ct.code_id = ?
            ''', (code['id'],))
            tags = [row[0] for row in cursor.fetchall()]
            code['tags'] = tags
            
        conn.close()
        return codes

    # --- 目录操作 ---
    def get_directories(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM directories')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def add_directory(self, name, parent_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO directories (name, parent_id) VALUES (?, ?)', (name, parent_id))
        conn.commit()
        directory_id = cursor.lastrowid
        conn.close()
        return directory_id

    def delete_directory(self, directory_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # 级联删除由外键约束处理，但SQLite默认不开启外键约束，这里手动开启或递归删除比较安全
        # 简单起见，我们假设用户知道删除目录会删除下面的内容
        # 也可以先删除子内容
        cursor.execute('DELETE FROM codes WHERE directory_id = ?', (directory_id,))
        # 递归删除子目录比较麻烦，这里简单处理：先只允许删除空目录或者让数据库处理
        # 更好的方式是启用 PRAGMA foreign_keys = ON;
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.execute('DELETE FROM directories WHERE id = ?', (directory_id,))
        conn.commit()
        conn.close()
    
    def update_directory(self, directory_id, name):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE directories SET name = ? WHERE id = ?', (name, directory_id))
        conn.commit()
        conn.close()

    # --- 代码操作 ---
    def get_codes_by_directory(self, directory_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        # Order by pinned (descending), then filename
        cursor.execute('SELECT * FROM codes WHERE directory_id = ? ORDER BY is_pinned DESC, filename', (directory_id,))
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return self._attach_tags_to_codes(result)

    def get_code(self, code_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM codes WHERE id = ?', (code_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            code = dict(row)
            # Attach tags for single code too
            return self._attach_tags_to_codes([code])[0]
        return None

    def get_all_codes(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM codes')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return self._attach_tags_to_codes(result)

    def add_code(self, directory_id, filename, content, note, is_favorite=0, is_pinned=0):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO codes (directory_id, filename, content, note, is_favorite, is_pinned)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (directory_id, filename, content, note, is_favorite, is_pinned))
        conn.commit()
        code_id = cursor.lastrowid
        conn.close()
        return code_id

    def update_code(self, code_id, filename, content, note, is_favorite, is_pinned, directory_id=None):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build query dynamically based on whether directory_id is provided
        if directory_id is not None:
            cursor.execute('''
                UPDATE codes 
                SET filename = ?, content = ?, note = ?, is_favorite = ?, is_pinned = ?, directory_id = ?
                WHERE id = ?
            ''', (filename, content, note, is_favorite, is_pinned, directory_id, code_id))
        else:
            cursor.execute('''
                UPDATE codes 
                SET filename = ?, content = ?, note = ?, is_favorite = ?, is_pinned = ?
                WHERE id = ?
            ''', (filename, content, note, is_favorite, is_pinned, code_id))
            
        conn.commit()
        conn.close()

    def delete_code(self, code_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM codes WHERE id = ?', (code_id,))
        conn.commit()
        conn.close()

    def search_codes(self, query):
        conn = self.get_connection()
        cursor = conn.cursor()
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT * FROM codes 
            WHERE filename LIKE ? OR content LIKE ? OR note LIKE ?
        ''', (search_term, search_term, search_term))
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return self._attach_tags_to_codes(result)

    def get_favorites(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM codes WHERE is_favorite = 1')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return self._attach_tags_to_codes(result)

    # --- 标签操作 ---
    def get_tags(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM tags ORDER BY name')
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result
    
    def add_tag(self, name):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO tags (name) VALUES (?)', (name,))
            conn.commit()
            tag_id = cursor.lastrowid
            return tag_id
        except sqlite3.IntegrityError:
            # Tag already exists
            cursor.execute('SELECT id FROM tags WHERE name = ?', (name,))
            return cursor.fetchone()[0]
        finally:
            conn.close()

    def get_code_tags(self, code_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.* FROM tags t
            JOIN code_tags ct ON t.id = ct.tag_id
            WHERE ct.code_id = ?
        ''', (code_id,))
        result = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return result

    def update_code_tags(self, code_id, tag_names):
        """
        全量更新代码的标签：tag_names 是标签名称列表
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 1. 确保所有标签都存在，获取它们的 ID
        tag_ids = []
        for name in tag_names:
            name = name.strip()
            if not name: continue
            
            # 尝试插入，如果存在则忽略
            cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (name,))
            
            # 获取 ID
            cursor.execute('SELECT id FROM tags WHERE name = ?', (name,))
            tag_ids.append(cursor.fetchone()[0])
            
        # 2. 删除该代码的所有现有标签关联
        cursor.execute('DELETE FROM code_tags WHERE code_id = ?', (code_id,))
        
        # 3. 插入新的关联
        for tag_id in tag_ids:
            cursor.execute('INSERT INTO code_tags (code_id, tag_id) VALUES (?, ?)', (code_id, tag_id))
            
        conn.commit()
        conn.close()
