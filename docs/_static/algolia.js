docsearch({
  appId: '3XDGDSUGC0',
  apiKey: '3233c833eeb0f000e5e1b0a3b81c59c4',
  indexName: 'owlery_dev',
  // Replace inputSelector with a CSS selector
  // matching your search input
  inputSelector: '.sidebar-search',
  // Set debug to true if you want to inspect the dropdown
  debug: false,
  algoliaOptions: {
    hitsPerPage: 8,
  }
});
