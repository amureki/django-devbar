import sharp from 'sharp';
import { readFileSync, mkdirSync } from 'fs';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const svgPath = join(__dirname, '..', 'icon.svg');
const distPath = join(__dirname, '..', 'dist');

const sizes = [16, 48, 128];

const svgBuffer = readFileSync(svgPath);

mkdirSync(distPath, { recursive: true });

for (const size of sizes) {
  await sharp(svgBuffer)
    .resize(size, size)
    .png()
    .toFile(join(distPath, `icon${size}.png`));
  console.info(`Generated icon${size}.png`);
}

console.info('Done!');
