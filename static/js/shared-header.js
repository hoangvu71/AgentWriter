// Shared header component
function createHeader(currentPage = '') {
    return `
        <header class="header">
            <div class="header-content">
                <a href="/" class="logo">
                    <div class="logo-icon">AI</div>
                    BooksWriter AI
                </a>
                <div class="nav-actions">
                    <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">
                        <span id="theme-icon">🌙</span>
                    </button>
                    <a href="/library" class="nav-link${currentPage === 'library' ? ' active' : ''}">Library</a>
                </div>
            </div>
        </header>
    `;
}

// Apply header to pages that need it
function applySharedHeader(currentPage = '') {
    const headerPlaceholder = document.getElementById('header-placeholder');
    if (headerPlaceholder) {
        headerPlaceholder.innerHTML = createHeader(currentPage);
    }
}