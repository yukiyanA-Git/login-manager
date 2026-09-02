const fs = require('fs');
const path = require('path');
const zlib = require('zlib');

function create1080Png() {
    const width = 1080;
    const height = 1080;

    // Build raw RGBA image data
    const rawData = Buffer.alloc(height * (1 + width * 4));
    let offset = 0;

    for (let y = 0; y < height; y++) {
        rawData[offset++] = 0; // Filter type None
        for (let x = 0; x < width; x++) {
            // Dark Slate background #0F172A
            let r = 15;
            let g = 23;
            let b = 42;
            let a = 255;

            // Draw a stylish centered square icon box (300x300 centered at 390..690)
            if (x >= 340 && x <= 740 && y >= 340 && y <= 740) {
                // Border 4px emerald green #10B981
                if (x <= 344 || x >= 736 || y <= 344 || y >= 736) {
                    r = 16; g = 185; b = 129;
                } else {
                    // Inner box dark blue #1E293B
                    r = 30; g = 41; b = 59;

                    // Centered key symbol accent in emerald
                    if ((x >= 520 && x <= 560 && y >= 440 && y <= 480) || 
                        (x >= 530 && x <= 550 && y >= 480 && y <= 620) ||
                        (x >= 530 && x <= 580 && y >= 580 && y <= 600)) {
                        r = 52; g = 211; b = 153;
                    }
                }
            }

            rawData[offset++] = r;
            rawData[offset++] = g;
            rawData[offset++] = b;
            rawData[offset++] = a;
        }
    }

    const compressed = zlib.deflateSync(rawData);

    // PNG signature
    const sig = Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);

    // IHDR chunk
    const ihdr = Buffer.alloc(13);
    ihdr.writeUInt32BE(width, 0);
    ihdr.writeUInt32BE(height, 4);
    ihdr[8] = 8;  // bit depth
    ihdr[9] = 6;  // color type RGBA
    ihdr[10] = 0; // compression
    ihdr[11] = 0; // filter
    ihdr[12] = 0; // interlace

    const ihdrChunk = makeChunk('IHDR', ihdr);
    const idatChunk = makeChunk('IDAT', compressed);
    const iendChunk = makeChunk('IEND', Buffer.alloc(0));

    const finalBuf = Buffer.concat([sig, ihdrChunk, idatChunk, iendChunk]);

    const outDir = path.join(__dirname, 'store_assets');
    if (!fs.existsSync(outDir)) {
        fs.mkdirSync(outDir, { recursive: true });
    }
    const outPath = path.join(outDir, 'BoxArt_1080x1080.png');
    fs.writeFileSync(outPath, finalBuf);
    console.log('Successfully generated 1080x1080 PNG logo at:', outPath);
}

function makeChunk(type, data) {
    const len = data.length;
    const buf = Buffer.alloc(4 + 4 + len + 4);
    buf.writeUInt32BE(len, 0);
    buf.write(type, 4);
    data.copy(buf, 8);
    
    // CRC32
    const crcVal = crc32(buf.subarray(4, 8 + len));
    buf.writeUInt32BE(crcVal >>> 0, 8 + len);
    return buf;
}

function crc32(buf) {
    let crc = -1;
    for (let i = 0; i < buf.length; i++) {
        crc = crcTable[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
    }
    return crc ^ -1;
}

const crcTable = new Int32Array(256);
for (let i = 0; i < 256; i++) {
    let c = i;
    for (let k = 0; k < 8; k++) {
        c = (c & 1) ? (0xedb88320 ^ (c >>> 1)) : (c >>> 1);
    }
    crcTable[i] = c;
}

create1080Png();
