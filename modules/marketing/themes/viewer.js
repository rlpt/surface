(function() {
  var ROOT = VIEWER_ROOT;
  var PAGE_PATH = VIEWER_PAGE_PATH;

  // --- Directory tree ---
  fetch(ROOT + '/tree.json')
    .then(function(r) { return r.json(); })
    .then(function(tree) { renderTree(tree); })
    .catch(function() {});

  function renderTree(tree) {
    var container = document.getElementById('dir-tree');
    var html = '';
    tree.forEach(function(dir) {
      html += '<div class="dir-section">';
      html += '<div class="dir-heading" data-dir="' + dir.name + '">';
      html += '<span class="arrow">&#9660;</span>' + escapeHtml(dir.label);
      html += '</div>';
      html += '<ul class="dir-files" data-dir="' + dir.name + '">';
      dir.files.forEach(function(f) {
        var isActive = f.path === PAGE_PATH;
        html += '<li><a href="' + ROOT + '/' + f.path + '.html"' +
          (isActive ? ' class="active"' : '') + '>' +
          escapeHtml(f.title) + '</a></li>';
      });
      html += '</ul></div>';
    });
    container.innerHTML = html;

    // Collapsible sections
    container.querySelectorAll('.dir-heading').forEach(function(heading) {
      heading.addEventListener('click', function() {
        this.classList.toggle('collapsed');
        var dirName = this.getAttribute('data-dir');
        var fileList = container.querySelector('.dir-files[data-dir="' + dirName + '"]');
        if (fileList) fileList.classList.toggle('hidden');
      });
    });
  }

  // --- Search ---
  var searchIndex = null;
  var searchInput = document.getElementById('search-input');
  var searchResults = document.getElementById('search-results');

  searchInput.addEventListener('focus', function() {
    if (!searchIndex) {
      fetch(ROOT + '/search-index.json')
        .then(function(r) { return r.json(); })
        .then(function(data) { searchIndex = data; });
    }
  });

  searchInput.addEventListener('input', function() {
    var query = this.value.trim().toLowerCase();
    if (query.length < 2 || !searchIndex) {
      searchResults.classList.remove('active');
      searchResults.innerHTML = '';
      return;
    }

    var results = searchIndex.filter(function(entry) {
      return entry.title.toLowerCase().indexOf(query) !== -1 ||
             entry.content.toLowerCase().indexOf(query) !== -1;
    }).slice(0, 10);

    if (results.length === 0) {
      searchResults.innerHTML = '<div class="no-results">No results found</div>';
      searchResults.classList.add('active');
      return;
    }

    var html = '';
    results.forEach(function(r) {
      var snippet = getSnippet(r.content, query, 150);
      html += '<a href="' + ROOT + '/' + r.path + '.html">';
      html += '<div class="result-title">' + escapeHtml(r.title) + '</div>';
      html += '<div class="result-path">' + escapeHtml(r.path) + '</div>';
      if (snippet) html += '<div class="result-snippet">' + snippet + '</div>';
      html += '</a>';
    });
    searchResults.innerHTML = html;
    searchResults.classList.add('active');
  });

  // Close search on click outside
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.search-wrapper')) {
      searchResults.classList.remove('active');
    }
  });

  // Close search on Escape
  searchInput.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      this.value = '';
      searchResults.classList.remove('active');
      searchResults.innerHTML = '';
    }
  });

  function getSnippet(content, query, maxLen) {
    var lower = content.toLowerCase();
    var idx = lower.indexOf(query);
    if (idx === -1) return '';
    var start = Math.max(0, idx - 40);
    var end = Math.min(content.length, idx + query.length + maxLen - 40);
    var snippet = (start > 0 ? '...' : '') +
                  content.substring(start, end) +
                  (end < content.length ? '...' : '');
    var re = new RegExp('(' + escapeRegex(query) + ')', 'gi');
    return escapeHtml(snippet).replace(re, '<mark>$1</mark>');
  }

  function escapeHtml(s) {
    var d = document.createElement('div');
    d.appendChild(document.createTextNode(s));
    return d.innerHTML;
  }

  function escapeRegex(s) {
    return s.replace(/[.*+?^${}()|[\]\\]/g, function(m) { return '\\' + m; });
  }
})();
