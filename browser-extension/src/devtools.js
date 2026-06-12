const extensionApi = globalThis.browser ?? globalThis.chrome;

if (globalThis.browser?.devtools) {
  extensionApi.devtools.panels
    .create('Django DevBar', 'icons/icon16.png', 'panel.html')
    .catch((error) => console.error('Failed to create Django DevBar panel:', error));
} else {
  extensionApi.devtools.panels.create(
    'Django DevBar',
    'icons/icon16.png',
    'panel.html',
    () => {}
  );
}
