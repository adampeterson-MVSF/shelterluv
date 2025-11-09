let files = [];
let selectedFiles = new Set();

async function scanDirectory() {
    const directoryInput = document.getElementById('directoryInput');
    const scanBtn = document.getElementById('scanBtn');
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const selectedPath = document.getElementById('selectedPath');

    if (!directoryInput.value.trim()) {
        alert('Please enter a directory path');
        return;
    }

    scanBtn.disabled = true;
    loading.style.display = 'flex';
    loadingText.textContent = 'Scanning directory...';
    selectedPath.textContent = `Scanning: ${directoryInput.value}`;

    try {
        const response = await fetch('/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ directory: directoryInput.value })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        files = data.files;
        selectedFiles.clear();

        // Auto-select all files
        files.forEach(file => selectedFiles.add(file.path));

        renderFileTree();
        updateStats();
        selectedPath.textContent = `Selected: ${directoryInput.value}`;

    } catch (error) {
        console.error('Error scanning directory:', error);
        selectedPath.textContent = 'Error scanning directory';
        alert('Error scanning directory: ' + error.message);
    } finally {
        scanBtn.disabled = false;
        loading.style.display = 'none';
    }
}

function renderFileTree() {
    const fileTree = document.getElementById('fileTree');
    const searchInput = document.getElementById('searchInput');
    const searchTerm = searchInput.value.toLowerCase();

    const filteredFiles = files.filter(file =>
        !searchTerm ||
        file.name.toLowerCase().includes(searchTerm) ||
        file.path.toLowerCase().includes(searchTerm)
    );

    if (filteredFiles.length === 0) {
        fileTree.innerHTML = `
            <div class="text-center text-gray-500 py-6">
                <i class="fas fa-search text-3xl mb-2"></i>
                <p class="text-sm">${searchTerm ? 'No files match your search' : 'No source files found'}</p>
            </div>
        `;
        return;
    }

    const html = filteredFiles.map(file => {
        const isSelected = selectedFiles.has(file.path);
        const selectedClass = isSelected ? 'selected' : 'unselected';
        const iconClass = isSelected ? 'fas fa-check-circle text-green-500' : 'fas fa-circle text-gray-400';
        return `
        <div class="file-item ${selectedClass}" data-path="${file.path}">
            <span class="text-file">
                <i class="${iconClass} mr-2"></i>
                ${file.path}
                <span class="text-gray-500 text-xs ml-2">
                    (${(file.size / 1024).toFixed(1)} KB, ${file.lines} lines)
                </span>
            </span>
        </div>
        `;
    }).join('');

    fileTree.innerHTML = html;

    // Add click handlers
    document.querySelectorAll('.file-item').forEach(item => {
        item.addEventListener('click', () => {
            const path = item.dataset.path;
            if (selectedFiles.has(path)) {
                selectedFiles.delete(path);
            } else {
                selectedFiles.add(path);
            }
            renderFileTree();
            updateStats();
        });
    });
}

function updateStats() {
    let totalSize = 0;
    let totalLines = 0;

    selectedFiles.forEach(path => {
        const file = files.find(f => f.path === path);
        if (file) {
            totalSize += file.size;
            totalLines += file.lines;
        }
    });

    document.getElementById('totalSize').textContent = `${(totalSize / 1024).toFixed(1)} KB`;
    document.getElementById('totalLines').textContent = totalLines.toLocaleString();
    document.getElementById('selectedCount').textContent = selectedFiles.size;
    document.getElementById('combineBtn').disabled = selectedFiles.size === 0;
}

async function combineFiles() {
    if (selectedFiles.size === 0) {
        alert('No files selected');
        return;
    }

    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const combineBtn = document.getElementById('combineBtn');

    combineBtn.disabled = true;
    loading.style.display = 'flex';
    loadingText.textContent = 'Collecting source code...';

    try {
        const response = await fetch('/combine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                selectedFiles: Array.from(selectedFiles),
                includeStructure: document.getElementById('includeStructure').checked,
                includeMetadata: document.getElementById('includeMetadata').checked
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Trigger download
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'source-code-collection.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Error collecting source code:', error);
        alert('Error collecting source code: ' + error.message);
    } finally {
        combineBtn.disabled = false;
        loading.style.display = 'none';
    }
}

// Event listeners
document.getElementById('scanBtn').addEventListener('click', scanDirectory);
document.getElementById('directoryInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') scanDirectory();
});
document.getElementById('searchInput').addEventListener('input', renderFileTree);
document.getElementById('combineBtn').addEventListener('click', combineFiles);
