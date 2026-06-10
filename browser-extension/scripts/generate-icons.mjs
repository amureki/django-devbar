import { mkdirSync, readFileSync } from 'fs';
import { dirname, join, resolve } from 'path';
import { argv } from 'process';
import { fileURLToPath } from 'url';

import sharp from 'sharp';

const __dirname = dirname(fileURLToPath(import.meta.url));
const rootDir = join(__dirname, '..');
const outputDir = argv[2] ? resolve(rootDir, argv[2]) : join(rootDir, 'dist', 'icons');
const svgPath = join(rootDir, 'icon.svg');
const sizes = [16, 48, 128];

const svgBuffer = readFileSync(svgPath);
mkdirSync(outputDir, { recursive: true });

for (const size of sizes) {
  await sharp(svgBuffer)
    .resize(size, size)
    .png()
    .toFile(join(outputDir, `icon${size}.png`));
  console.info(`Generated ${join(outputDir, `icon${size}.png`)}`);
}

console.info('Done!');
