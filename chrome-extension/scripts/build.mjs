import { rmSync, cpSync, readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';
import { argv } from 'process';

const isDev = argv.includes('--dev');

function build() {
  rmSync('dist', { recursive: true, force: true });

  execSync('node scripts/generate-icons.mjs', { stdio: 'inherit' });

  const files = ['content.js', 'devtools.html', 'devtools.js', 'panel.html', 'panel.js', 'PRIVACY.md', 'manifest.json'];
  files.forEach(file => cpSync(file, `dist/${file}`));

  if (isDev) {
    const devtoolsPath = 'dist/devtools.js';
    let content = readFileSync(devtoolsPath, 'utf-8');
    content = content.replace(
      /'Django DevBar'/,
      "'Django DevBar (dev)'"
    );
    writeFileSync(devtoolsPath, content);
    console.info('✓ Dev mode enabled');
  }
}

build();
