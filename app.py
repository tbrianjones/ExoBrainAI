import os
from pathlib import Path
from flask import Flask, render_template, abort, send_from_directory
import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.tables import TableExtension

app = Flask(__name__)

IDEAS_DIR = Path("ideas")

def get_idea_spaces():
    if not IDEAS_DIR.exists():
        return []
    
    ideas = []
    for folder in sorted(IDEAS_DIR.iterdir()):
        if folder.is_dir() and not folder.name.startswith('.'):
            readme_path = folder / "README.md"
            summary = ""
            if readme_path.exists():
                content = readme_path.read_text()
                lines = content.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#'):
                        summary = line.strip()[:150]
                        break
            
            name_parts = folder.name.split('-', 1)
            display_name = name_parts[1].replace('-', ' ').title() if len(name_parts) > 1 else folder.name
            
            ideas.append({
                'id': folder.name,
                'name': display_name,
                'summary': summary,
                'path': folder
            })
    
    return ideas

def get_idea_detail(idea_id):
    idea_path = IDEAS_DIR / idea_id
    if not idea_path.exists() or not idea_path.is_dir():
        return None
    
    name_parts = idea_id.split('-', 1)
    display_name = name_parts[1].replace('-', ' ').title() if len(name_parts) > 1 else idea_id
    
    readme_content = ""
    readme_path = idea_path / "README.md"
    if readme_path.exists():
        readme_content = readme_path.read_text()
    
    transcripts = []
    transcripts_path = idea_path / "transcripts"
    if transcripts_path.exists():
        for f in sorted(transcripts_path.iterdir()):
            if f.suffix == '.md':
                transcripts.append({
                    'name': f.stem,
                    'filename': f.name,
                    'content': f.read_text()
                })
    
    views = []
    views_path = idea_path / "views"
    if views_path.exists():
        for f in sorted(views_path.iterdir()):
            if f.suffix in ['.md', '.qmd']:
                views.append({
                    'name': f.stem.replace('-', ' ').title(),
                    'filename': f.name,
                    'content': f.read_text()
                })
    
    assets = []
    assets_path = idea_path / "assets"
    if assets_path.exists():
        for f in sorted(assets_path.iterdir()):
            if f.is_file():
                assets.append({
                    'name': f.name,
                    'path': f
                })
    
    return {
        'id': idea_id,
        'name': display_name,
        'readme': readme_content,
        'transcripts': transcripts,
        'views': views,
        'assets': assets
    }

def render_markdown(content):
    md = markdown.Markdown(extensions=[
        FencedCodeExtension(),
        CodeHiliteExtension(css_class='highlight', guess_lang=False),
        TableExtension(),
        'nl2br'
    ])
    return md.convert(content)

def check_setup_status():
    api_key = os.environ.get('GEMINI_API_KEY', '')
    gemini_configured = bool(api_key and api_key != 'your-api-key-here')
    
    return {
        'gemini_configured': gemini_configured
    }

@app.route('/')
def home():
    ideas = get_idea_spaces()
    status = check_setup_status()
    return render_template('home.html', ideas=ideas, status=status)

@app.route('/idea/<idea_id>')
def idea_detail(idea_id):
    idea = get_idea_detail(idea_id)
    if not idea:
        abort(404)
    return render_template('idea.html', idea=idea, render_markdown=render_markdown)

@app.route('/idea/<idea_id>/transcript/<filename>')
def transcript_detail(idea_id, filename):
    idea_path = IDEAS_DIR / idea_id / "transcripts" / filename
    if not idea_path.exists():
        abort(404)
    content = idea_path.read_text()
    name = idea_path.stem
    return render_template('document.html', 
                         title=name, 
                         content=render_markdown(content),
                         idea_id=idea_id,
                         doc_type='Transcript')

@app.route('/idea/<idea_id>/view/<filename>')
def view_detail(idea_id, filename):
    idea_path = IDEAS_DIR / idea_id / "views" / filename
    if not idea_path.exists():
        abort(404)
    content = idea_path.read_text()
    name = idea_path.stem.replace('-', ' ').title()
    return render_template('document.html', 
                         title=name, 
                         content=render_markdown(content),
                         idea_id=idea_id,
                         doc_type='View')

@app.route('/idea/<idea_id>/assets/<filename>')
def serve_asset(idea_id, filename):
    assets_path = IDEAS_DIR / idea_id / "assets"
    return send_from_directory(assets_path, filename)

@app.route('/setup')
def setup():
    status = check_setup_status()
    return render_template('setup.html', status=status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
