(function() {
  'use strict';

  if (typeof chrome === 'undefined' || !chrome.storage) {
    return;
  }

  const STORAGE_KEY = 'django-devbar-show-bar';
  let currentShowState = true;
  let styleElement = null;

  function injectHideCSS() {
    if (!styleElement) {
      styleElement = document.createElement('style');
      styleElement.id = 'devbar-visibility-control';
      styleElement.textContent = '#django-devbar { display: none !important; }';
      (document.head || document.documentElement).appendChild(styleElement);
    }
  }

  function removeHideCSS() {
    if (styleElement && styleElement.parentNode) {
      styleElement.parentNode.removeChild(styleElement);
      styleElement = null;
    }
  }

  function checkAndApply() {
    chrome.storage.local.get([STORAGE_KEY], (result) => {
      currentShowState = result[STORAGE_KEY] !== false;
      currentShowState ? removeHideCSS() : injectHideCSS();
    });
  }

  checkAndApply();

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes[STORAGE_KEY]) {
      currentShowState = changes[STORAGE_KEY].newValue;
      currentShowState ? removeHideCSS() : injectHideCSS();
    }
  });
})();
