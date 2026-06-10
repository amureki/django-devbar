import { cpSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'fs';
import { execFileSync } from 'child_process';
import { dirname, join } from 'path';
import { argv } from 'process';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');
const distDir = join(rootDir, 'dist');
const srcDir = join(rootDir, 'src');
const manifestDir = join(rootDir, 'manifests');
const supportedBrowsers = ['chrome', 'firefox'];
const args = argv.slice(2);
const unknownArgs = args.filter(arg => arg !== '--dev' && !supportedBrowsers.includes(arg));
const isDev = args.includes('--dev');
const requestedBrowsers = args.filter(arg => supportedBrowsers.includes(arg));
const browsers = requestedBrowsers.length ? requestedBrowsers : supportedBrowsers;

if (unknownArgs.length) {
  console.error(`Unknown build argument: ${unknownArgs.join(', ')}`);
  console.error(`Usage: node scripts/build.mjs [${supportedBrowsers.join('|')}] [--dev]`);
  process.exit(1);
}

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf-8'));
}

function copySource(outputDir) {
  for (const file of readdirSync(srcDir)) {
    cpSync(join(srcDir, file), join(outputDir, file), { recursive: true });
  }

  cpSync(join(rootDir, 'PRIVACY.md'), join(outputDir, 'PRIVACY.md'));
}

function writeManifest(browser, outputDir) {
  const common = readJson(join(manifestDir, 'common.json'));
  const browserOverrides = readJson(join(manifestDir, `${browser}.json`));
  const manifest = { ...common, ...browserOverrides };

  writeFileSync(join(outputDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`);
}

function enableDevMode(outputDir) {
  const devtoolsPath = join(outputDir, 'devtools.js');
  const content = readFileSync(devtoolsPath, 'utf-8').replace(
    /'Django DevBar'/,
    "'Django DevBar (dev)'"
  );
  writeFileSync(devtoolsPath, content);
}

function buildBrowser(browser) {
  const outputDir = join(distDir, browser);

  rmSync(outputDir, { recursive: true, force: true });
  mkdirSync(outputDir, { recursive: true });

  copySource(outputDir);
  writeManifest(browser, outputDir);
  execFileSync('node', ['scripts/generate-icons.mjs', join('dist', browser, 'icons')], {
    cwd: rootDir,
    stdio: 'inherit',
  });

  if (isDev) enableDevMode(outputDir);

  console.info(`✓ Built ${browser} extension in ${join('dist', browser)}`);
}

if (!requestedBrowsers.length) {
  rmSync(distDir, { recursive: true, force: true });
}

for (const browser of browsers) {
  buildBrowser(browser);
}

if (isDev) console.info('✓ Dev mode enabled');
