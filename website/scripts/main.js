(() => {
  const body = document.body;
  const menuToggle = document.querySelector('.menu-toggle');
  const backdrop = document.querySelector('.nav-backdrop');

  function setNavigation(open) {
    body.classList.toggle('nav-open', open);
    menuToggle?.setAttribute('aria-expanded', String(open));
    if (backdrop) backdrop.hidden = !open;
  }

  menuToggle?.addEventListener('click', () => setNavigation(!body.classList.contains('nav-open')));
  backdrop?.addEventListener('click', () => setNavigation(false));
  document.querySelectorAll('.site-navigation a').forEach(link => link.addEventListener('click', () => setNavigation(false)));

  const backToTop = document.querySelector('.back-to-top');
  if (backToTop) {
    const updateBackToTop = () => backToTop.classList.toggle('visible', window.scrollY > 700);
    window.addEventListener('scroll', updateBackToTop, { passive: true });
    updateBackToTop();
    backToTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  const tocLinks = [...document.querySelectorAll('.toc-list a')];
  const observedHeadings = tocLinks.map(link => document.querySelector(link.getAttribute('href'))).filter(Boolean);
  if (observedHeadings.length) {
    const observer = new IntersectionObserver(entries => {
      const visible = entries.filter(entry => entry.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (!visible) return;
      tocLinks.forEach(link => link.classList.toggle('active', link.getAttribute('href') === `#${visible.target.id}`));
    }, { rootMargin: '-75px 0px -70% 0px', threshold: 0 });
    observedHeadings.forEach(heading => observer.observe(heading));
  }

  const searchDialog = document.querySelector('.search-dialog');
  const searchInput = searchDialog?.querySelector('input[type="search"]');
  const searchResults = searchDialog?.querySelector('.search-results');
  const searchHint = searchDialog?.querySelector('.search-hint');

  function openSearch() {
    if (!searchDialog) return;
    searchDialog.showModal();
    setTimeout(() => searchInput?.focus(), 0);
  }

  document.querySelectorAll('.search-trigger').forEach(button => button.addEventListener('click', openSearch));
  searchDialog?.querySelector('.dialog-close')?.addEventListener('click', () => searchDialog.close());
  searchDialog?.addEventListener('click', event => {
    if (event.target === searchDialog) searchDialog.close();
  });
  document.addEventListener('keydown', event => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      openSearch();
    }
  });

  function escapeRegExp(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function highlight(value, query) {
    const safe = value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return safe.replace(new RegExp(`(${escapeRegExp(query)})`, 'ig'), '<mark>$1</mark>');
  }

  searchInput?.addEventListener('input', () => {
    const query = searchInput.value.trim();
    if (!query) {
      searchHint.hidden = false;
      searchResults.innerHTML = '';
      return;
    }
    searchHint.hidden = true;
    const index = window.SEARCH_INDEX || [];
    const matches = index.filter(item => `${item.title} ${item.description} ${item.text}`.toLowerCase().includes(query.toLowerCase())).slice(0, 20);
    if (!matches.length) {
      searchResults.innerHTML = '<p class="search-empty">没有找到相关内容，试试更短的关键词。</p>';
      return;
    }
    searchResults.innerHTML = matches.map(item => {
      const lowerText = item.text.toLowerCase();
      const position = Math.max(0, lowerText.indexOf(query.toLowerCase()));
      const start = Math.max(0, position - 45);
      const excerpt = `${start > 0 ? '…' : ''}${item.text.slice(start, position + query.length + 75)}${position + query.length + 75 < item.text.length ? '…' : ''}`;
      return `<a class="search-result" href="${item.url}"><small>${highlight(item.breadcrumb || item.title, query)}</small><strong>${highlight(item.title, query)}</strong><p>${highlight(excerpt, query)}</p></a>`;
    }).join('');
  });

  const imageDialog = document.querySelector('.image-dialog');
  const dialogImage = imageDialog?.querySelector('img');
  document.querySelectorAll('.image-button').forEach(button => button.addEventListener('click', () => {
    if (!imageDialog || !dialogImage) return;
    const sourceImage = button.querySelector('img');
    dialogImage.src = button.dataset.image;
    dialogImage.alt = sourceImage?.alt || '';
    imageDialog.showModal();
  }));
  imageDialog?.querySelector('.image-close')?.addEventListener('click', () => imageDialog.close());
  imageDialog?.addEventListener('click', event => {
    if (event.target === imageDialog) imageDialog.close();
  });
})();
