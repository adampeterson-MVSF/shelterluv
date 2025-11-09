"""
Source code scanner module.
Handles file discovery, filtering, and metadata extraction.
"""

import os
from pathlib import Path
from typing import List, Dict, Any

# Configuration - could be moved to a config file
IGNORE_PATTERNS = {
    # Version control
    '.git', '.svn', '.hg',
    # Dependencies and virtual environments
    'node_modules', 'bower_components', '.venv', 'venv', 'env', 'ENV',
    '__pycache__', '.pytest_cache', '.mypy_cache', '.tox',
    # Build outputs and distributions
    'dist', 'build', 'out', 'target', 'bin', 'obj', 'lib',
    '.next', '.nuxt', '.svelte-kit', '.vuepress', '.cache',
    'coverage', 'htmlcov', '.coverage', 'test-results', 'playwright-report',
    '*.egg-info', '.eggs', 'dist-info',
    # Framework-specific build artifacts
    '.next', '.nuxt', '.svelte-kit', '.vuepress', '.docusaurus',
    '.vercel', '.netlify', '_nuxt', '.output', '.vitepress',
    # Cache and temporary files
    '.cache', '.parcel-cache', '.eslintcache', '.stylelintcache',
    '.sass-cache', '.nyc_output', '.webpack', 'tmp', 'temp',
    '*.log', '*.tmp', '*.temp', '.DS_Store', 'Thumbs.db',
    # Environment and secrets
    '.env', '.env.local', '.env.development', '.env.production',
    '.env.test', '.env.staging', '.env.*',
    # IDE and editor files
    '.vscode', '.idea', '.vs', '.eclipse', '*.swp', '*.swo',
    '*~', '.project', '.classpath', '.settings',
    # Lock files
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'Pipfile.lock', 'poetry.lock', 'Gemfile.lock',
    # Compiled and minified files
    '*.min.js', '*.min.css', '*.bundle.js', '*.chunk.js',
    '*.compiled.js', '*.compiled.css',
    '*.pyc', '*.pyo', '*.pyd', '*.so', '*.dll', '*.exe',
    # Assets and media (keep some config but exclude media)
    'public/assets', 'static/assets', 'assets/images', 'assets/fonts',
    '*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg', '*.ico', '*.webp',
    '*.woff', '*.woff2', '*.ttf', '*.eot', '*.mp4', '*.mp3', '*.wav',
    '*.mov', '*.avi', '*.mkv',
    # Archives and binaries
    '*.zip', '*.tar.gz', '*.rar', '*.7z', '*.dmg', '*.iso',
    '*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx',
    '*.sqlite', '*.db', '*.sqlite3', '*.mdb',
    # CI/CD and deployment
    '.github/workflows', '.circleci', '.travis.yml', '.gitlab-ci.yml',
    'Dockerfile', 'docker-compose*.yml', '.dockerignore',
    # Testing frameworks' outputs
    'test-results', 'allure-results', 'cypress/videos', 'cypress/screenshots'
}

TEXT_EXTENSIONS = {
    # Programming languages - source files
    'js', 'ts', 'jsx', 'tsx', 'py', 'java', 'go', 'rs', 'php', 'rb',
    'cpp', 'c', 'h', 'hpp', 'cs', 'swift', 'kt', 'scala', 'clj', 'hs',
    'ml', 'fs', 'elm', 'dart', 'lua', 'r', 'm', 'mm', 'vb', 'fsx',
    # Web technologies - source files
    'html', 'css', 'scss', 'sass', 'less', 'vue', 'svelte', 'astro',
    'ejs', 'pug', 'jade', 'hbs', 'handlebars',
    # Configuration and data files
    'json', 'yaml', 'yml', 'toml', 'xml', 'ini', 'conf', 'cfg',
    'properties', 'env', 'dotenv', 'config', 'settings',
    # Scripts and shell files
    'sh', 'bash', 'zsh', 'fish', 'ps1', 'bat', 'cmd', 'awk', 'sed',
    'perl', 'pl', 'tcl', 'expect',
    # Documentation files
    'md', 'rst', 'txt', 'adoc', 'asciidoc', 'tex', 'latex',
    # Database and queries
    'sql', 'prisma', 'graphql', 'gql', 'cypher',
    # Build and project files
    'dockerfile', 'makefile', 'Cargo.toml', 'package.json', 'setup.py',
    'requirements.txt', 'Pipfile', 'pyproject.toml', 'Cargo.lock',
    'go.mod', 'go.sum',
    # Config files
    'gitignore', 'eslintignore', 'prettierignore', 'editorconfig',
    'babelrc', 'eslintrc', 'prettierrc', 'tsconfig', 'jsconfig',
    'webpack.config', 'rollup.config', 'vite.config', 'jest.config'
}

NO_EXT_FILES = {
    'Dockerfile', 'Makefile', 'CMakeLists.txt', 'README', 'CHANGELOG',
    'LICENSE', 'NOTICE', 'AUTHORS', 'CONTRIBUTORS', 'CONTRIBUTING',
    'INSTALL', 'BUILD', 'DEVELOP', 'HACKING', 'manage.py', 'wsgi.py', 'asgi.py'
}

def is_text_file(filename: str) -> bool:
    """Check if a file is a text file we want to include."""
    name_lower = filename.lower()

    # Check for files without extensions
    if filename in NO_EXT_FILES:
        return True

    # Check for README, etc. patterns
    if (name_lower.startswith(('readme', 'changelog', 'license', 'contribut', 'install', 'build'))):
        return True

    # Check extension
    ext = Path(filename).suffix.lower().lstrip('.')
    return ext in TEXT_EXTENSIONS

def get_file_priority(filename: str, path: Path) -> int:
    """Get priority score for file sorting."""
    priority = 0
    name_lower = filename.lower()
    path_lower = str(path).lower()

    # Core source files get highest priority
    if any(ext in name_lower for ext in ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.go', '.rs', '.cpp', '.c', '.php', '.rb', '.cs', '.swift', '.kt']):
        priority += 20

    # Web source files
    if any(ext in name_lower for ext in ['.html', '.css', '.scss', '.sass', '.vue', '.svelte', '.astro']):
        priority += 18

    # Configuration files
    if any(ext in name_lower for ext in ['.json', '.yaml', '.yml', '.toml', '.xml']) or 'config' in name_lower or 'settings' in name_lower:
        priority += 15

    # Package/project definition files
    if name_lower in ['package.json', 'setup.py', 'requirements.txt', 'cargo.toml', 'pyproject.toml', 'go.mod', 'composer.json', 'gemfile']:
        priority += 19

    # Build configuration files
    if any(term in name_lower for term in ['webpack', 'babel', 'vite', 'rollup', 'tsconfig', 'jest']):
        priority += 14

    # Documentation
    if name_lower.startswith('readme') or '/docs/' in path_lower or '/documentation/' in path_lower or any(ext in name_lower for ext in ['.md', '.rst', '.txt', '.adoc']):
        priority += 10

    # Database and API files
    if any(ext in name_lower for ext in ['.sql', '.prisma', '.graphql', '.gql']):
        priority += 12

    # Scripts and shell files
    if any(ext in name_lower for ext in ['.sh', '.bash', '.zsh', '.ps1', '.bat', '.cmd', '.awk', '.sed']):
        priority += 8

    # Test files get lower priority
    if any(pattern in name_lower for pattern in ['.test.', '.spec.', '__tests__', 'test_']) or any(dir_name in path_lower for dir_name in ['/tests/', '/test/', '/spec/']):
        priority -= 5

    # Generated or build files get lowest priority
    if any(pattern in name_lower for pattern in ['.min.', '.bundle.', '.chunk.', '.compiled.']):
        priority -= 10

    return priority

def should_ignore(path: Path) -> bool:
    """Check if path should be ignored."""
    path_str = str(path)
    return any(pattern in path_str or (pattern.startswith('*.') and path_str.endswith(pattern[1:])) or
               (pattern.endswith('*') and path_str.startswith(pattern[:-1])) for pattern in IGNORE_PATTERNS)

def scan_directory(directory: str) -> List[Dict[str, Any]]:
    """Scan directory for text files."""
    files = []
    directory_path = Path(directory)

    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and not should_ignore(file_path.relative_to(directory_path)):
            if is_text_file(file_path.name):
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    lines = len(content.split('\n'))
                    size = file_path.stat().st_size

                    files.append({
                        'path': str(file_path.relative_to(directory_path)),
                        'name': file_path.name,
                        'size': size,
                        'lines': lines,
                        'content': content,
                        'priority': get_file_priority(file_path.name, file_path.relative_to(directory_path))
                    })
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
                    continue

    return sorted(files, key=lambda x: (-x['priority'], x['path']))
