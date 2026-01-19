from flask import Flask, render_template, request, jsonify
import requests
import base64
from database import Database

app = Flask(__name__)
db = Database()

@app.route('/')
def index():
    return render_template('index.html')

# --- Directory API ---
@app.route('/api/directories', methods=['GET'])
def get_directories():
    directories = db.get_directories()
    return jsonify(directories)

@app.route('/api/directories', methods=['POST'])
def add_directory():
    data = request.json
    name = data.get('name')
    parent_id = data.get('parent_id')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    try:
        dir_id = db.add_directory(name, parent_id)
        return jsonify({'id': dir_id, 'name': name, 'parent_id': parent_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/directories/<int:dir_id>', methods=['PUT'])
def update_directory(dir_id):
    data = request.json
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    try:
        db.update_directory(dir_id, name)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/directories/<int:dir_id>', methods=['DELETE'])
def delete_directory(dir_id):
    try:
        db.delete_directory(dir_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Code API ---
@app.route('/api/directories/<int:dir_id>/codes', methods=['GET'])
def get_codes_by_directory(dir_id):
    codes = db.get_codes_by_directory(dir_id)
    return jsonify(codes)

@app.route('/api/codes', methods=['POST'])
def add_code():
    data = request.json
    directory_id = data.get('directory_id')
    filename = data.get('filename')
    content = data.get('content', '')
    note = data.get('note', '')
    is_favorite = data.get('is_favorite', 0)
    is_pinned = data.get('is_pinned', 0)
    tags = data.get('tags', []) # List of strings
    
    if not filename or not directory_id:
        return jsonify({'error': 'Filename and Directory ID are required'}), 400
        
    try:
        code_id = db.add_code(directory_id, filename, content, note, is_favorite, is_pinned)
        if tags:
            db.update_code_tags(code_id, tags)
        return jsonify({'id': code_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/codes/<int:code_id>', methods=['GET'])
def get_code(code_id):
    code = db.get_code(code_id)
    if code:
        # tags are already attached by db.get_code
        return jsonify(code)
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/codes/<int:code_id>', methods=['PUT'])
def update_code(code_id):
    data = request.json
    filename = data.get('filename')
    content = data.get('content')
    note = data.get('note')
    is_favorite = data.get('is_favorite') # 0 or 1
    is_pinned = data.get('is_pinned') # 0 or 1
    directory_id = data.get('directory_id') # Optional, for moving code
    tags = data.get('tags') # List of strings
    
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400
        
    try:
        db.update_code(code_id, filename, content, note, is_favorite, is_pinned, directory_id)
        if tags is not None:
            db.update_code_tags(code_id, tags)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/codes/<int:code_id>', methods=['DELETE'])
def delete_code(code_id):
    try:
        db.delete_code(code_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- Search & Favorites ---
@app.route('/api/search', methods=['GET'])
def search_codes():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    results = db.search_codes(query)
    return jsonify(results)

@app.route('/api/favorites', methods=['GET'])
def get_favorites():
    favorites = db.get_favorites()
    return jsonify(favorites)

@app.route('/api/tags', methods=['GET'])
def get_tags():
    tags = db.get_tags()
    return jsonify(tags)

# --- Github Sync API ---
@app.route('/api/github/sync', methods=['POST'])
def github_sync():
    data = request.json
    token = data.get('token')
    owner = data.get('owner')
    repo = data.get('repo')
    branch = data.get('branch', 'main')
    path_prefix = data.get('path', '').strip('/')

    if not all([token, owner, repo, branch]):
        return jsonify({'error': 'Missing required fields'}), 400

    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    base_url = f'https://api.github.com/repos/{owner}/{repo}'

    try:
        # 1. Get directories and codes
        dirs = db.get_directories()
        codes = db.get_all_codes()

        # Build directory path map
        id_to_parent = {d['id']: d['parent_id'] for d in dirs}
        id_to_name = {d['id']: d['name'] for d in dirs}
        
        # Find system default 'Root' directory ID to treat it as repository root
        root_dir = next((d for d in dirs if d['name'] == 'Root' and d['parent_id'] is None), None)
        root_id = root_dir['id'] if root_dir else -1

        def build_path(did):
            if did == root_id: return "" # 'Root' directory maps to repo root
            
            if did not in id_to_parent: return ""
            
            pid = id_to_parent[did]
            name = id_to_name[did]
            
            if pid is None: 
                # Top-level directory (but not 'Root')
                return name
                
            parent_path = build_path(pid)
            return f"{parent_path}/{name}" if parent_path else name

        tree_items = []
        for code in codes:
            dir_id = code['directory_id']
            dir_path = build_path(dir_id)
            filename = code['filename']
            
            full_path = f"{dir_path}/{filename}" if dir_path else filename
            if path_prefix:
                full_path = f"{path_prefix}/{full_path}"
            
            content = code['content'] or ''
            
            tree_items.append({
                "path": full_path,
                "mode": "100644",
                "type": "blob",
                "content": content
            })

        if not tree_items:
             return jsonify({'error': 'No files to sync'}), 400

        # 2. Try to get latest commit SHA
        resp = requests.get(f'{base_url}/git/ref/heads/{branch}', headers=headers)
        
        is_empty_repo = False
        latest_sha = None
        base_tree_sha = None
        
        if resp.status_code == 409:
            # 409: Git Repository is empty
            is_empty_repo = True
        elif resp.status_code == 404:
            # 404: Branch not found.
            # Check if repo is truly empty by checking commits
            commits_resp = requests.get(f'{base_url}/commits', headers=headers)
            if commits_resp.status_code == 409:
                 is_empty_repo = True
            # else: Branch doesn't exist, but repo is not empty. We will start a new branch.
        elif resp.status_code != 200:
             return jsonify({'error': f'Get ref failed: {resp.text}'}), 400
        else:
            latest_sha = resp.json()['object']['sha']

        # SPECIAL HANDLING FOR EMPTY REPO
        if is_empty_repo:
            # Initialize repo with a README via Contents API to create the first commit
            # This is necessary because Git Data API cannot easily create the first commit in an empty repo
            init_url = f'{base_url}/contents/README.md'
            init_data = {
                "message": "Initial commit by Code Store",
                "content": base64.b64encode(b"# Code Store Backup\n\nSync from Code Store tool.").decode('utf-8'),
                "branch": branch
            }
            put_resp = requests.put(init_url, json=init_data, headers=headers)
            if put_resp.status_code not in [200, 201]:
                 return jsonify({'error': f'Init empty repo failed: {put_resp.text}'}), 400
            
            # Now repo is not empty. Get the new commit sha.
            latest_sha = put_resp.json()['commit']['sha']
            
            # We have a base commit now. We can proceed to create our tree based on this, 
            # or just create a new tree.
            # Since we just created README.md, let's try to base our new tree on it so we don't delete it?
            # Actually, if we just want to push our files, we can just create a new tree.
            # But if we use base_tree=None, it might delete README.md if we don't include it.
            # So let's get the base_tree of this new commit.
            is_empty_repo = False
            
            # Since we just created it, we can get the tree sha from the commit we just made
            # But the PUT response structure for commit is slightly different, let's fetch it via Git Data API to be safe/consistent
            resp = requests.get(f'{base_url}/git/commits/{latest_sha}', headers=headers)
            if resp.status_code == 200:
                base_tree_sha = resp.json()['tree']['sha']

        if not is_empty_repo and not base_tree_sha:
            # 3. Get base tree SHA if we have a latest_sha but didn't get base_tree_sha yet
            resp = requests.get(f'{base_url}/git/commits/{latest_sha}', headers=headers)
            if resp.status_code != 200:
                return jsonify({'error': f'Get commit failed: {resp.text}'}), 400
            base_tree_sha = resp.json()['tree']['sha']

        # 4. Create new tree
        # We do NOT use base_tree here because we want to perform a full mirror sync.
        # Using base_tree would result in incremental updates where deleted/moved files 
        # would remain in their old locations on the remote.
        payload = {
            "tree": tree_items
        }
        # if base_tree_sha:
        #    payload["base_tree"] = base_tree_sha
            
        resp = requests.post(f'{base_url}/git/trees', json=payload, headers=headers)
        if resp.status_code != 201:
            return jsonify({'error': f'Create tree failed: {resp.text}'}), 400
        new_tree_sha = resp.json()['sha']

        # 5. Create commit
        payload = {
            "message": "Sync from Code Store",
            "tree": new_tree_sha,
            "parents": [latest_sha] if latest_sha else []
        }
        resp = requests.post(f'{base_url}/git/commits', json=payload, headers=headers)
        if resp.status_code != 201:
            return jsonify({'error': f'Create commit failed: {resp.text}'}), 400
        new_commit_sha = resp.json()['sha']

        # 6. Update or Create ref
        if is_empty_repo:
            # Create ref
            payload = {
                "ref": f"refs/heads/{branch}",
                "sha": new_commit_sha
            }
            resp = requests.post(f'{base_url}/git/refs', json=payload, headers=headers)
            if resp.status_code != 201:
                return jsonify({'error': f'Create ref failed: {resp.text}'}), 400
        else:
            # Update ref
            payload = {
                "sha": new_commit_sha
            }
            resp = requests.patch(f'{base_url}/git/refs/heads/{branch}', json=payload, headers=headers)
            if resp.status_code != 200:
                 return jsonify({'error': f'Update ref failed: {resp.text}'}), 400

        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
