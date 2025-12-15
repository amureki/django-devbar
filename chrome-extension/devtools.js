// Create the Django DevBar panel
chrome.devtools.panels.create(
  'Django DevBar',
  'icons/icon16.png',
  'panel.html',
  function(panel) {
    console.log('Django DevBar panel created');
  }
);
