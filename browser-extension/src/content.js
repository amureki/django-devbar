const extensionApi = globalThis.browser ?? globalThis.chrome;
const usesPromiseApi = Boolean(globalThis.browser?.storage);
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
  if (styleElement?.parentNode) {
    styleElement.parentNode.removeChild(styleElement);
    styleElement = null;
  }
}

function getStorage(keys, callback) {
  if (usesPromiseApi) {
    extensionApi.storage.local.get(keys).then(callback);
    return;
  }

  extensionApi.storage.local.get(keys, callback);
}

function checkAndApply() {
  getStorage([STORAGE_KEY], (result) => {
    currentShowState = result[STORAGE_KEY] !== false;
    currentShowState ? removeHideCSS() : injectHideCSS();
  });
}

checkAndApply();

extensionApi.storage.onChanged.addListener((changes, area) => {
  if (area === 'local' && changes[STORAGE_KEY]) {
    currentShowState = changes[STORAGE_KEY].newValue;
    currentShowState ? removeHideCSS() : injectHideCSS();
  }
});
