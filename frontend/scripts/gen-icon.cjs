// scripts/gen-icon.cjs
// Converts src/assets/white-logo.svg -> build/icon.ico (multi-size)
// Uses: sharp + to-ico

const fs = require('fs');
const path = require('path');
const sharp = require('sharp');
const toIco = require('to-ico');

const SRC_SVG = path.join(__dirname, '..', 'src', 'assets', 'white-logo.svg');
const OUT_DIR = path.join(__dirname, '..', 'build');
const SIZES = [16, 32, 48, 64, 128, 256];

(async () => {
  try {
    if (!fs.existsSync(SRC_SVG)) throw new Error(`Source SVG not found: ${SRC_SVG}`);
    if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

    // Render each size to an in-memory PNG buffer
    const pngBuffers = [];
    for (const size of SIZES) {
      const buf = await sharp(SRC_SVG)
        .resize(size, size, { fit: 'contain', background: { r: 0, g: 0, b: 0, alpha: 0 } })
        .png()
        .toBuffer();
      pngBuffers.push(buf);
    }

    // Build multi-resolution .ico
    const icoBuffer = await toIco(pngBuffers);
    const outIco = path.join(OUT_DIR, 'icon.ico');
    fs.writeFileSync(outIco, icoBuffer);

    console.log(`✅ Wrote ${outIco}`);
  } catch (e) {
    console.error('❌ Icon generation failed:', e.message);
    process.exit(1);
  }
})();
