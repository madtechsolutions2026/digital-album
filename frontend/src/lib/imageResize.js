// Matches ImageCompressor.MAX_DIMENSION and TARGET_SIZE_KB on the backend.
// When a resized file comes in under both limits, the server stores it as-is
// instead of decoding and re-encoding it (see ImageValidator.try_passthrough),
// which is what makes bulk uploads fast. Keep these two in sync with
// backend/app/services/image_compressor.py.
const MAX_DIMENSION = 1920;
const TARGET_BYTES = 200 * 1024;

// Tried in order until one fits TARGET_BYTES. Most photos succeed on the first.
const QUALITY_LADDER = [0.8, 0.7, 0.6];

// One worker per core, capped - past ~4 the encode work saturates and extra
// workers just multiply peak memory (each holds a full-resolution bitmap).
const POOL_SIZE = Math.max(1, Math.min(4, (navigator.hardwareConcurrency || 4) - 1));

// Marks rejections caused by cancelPendingResizes, so callers can tell a
// deliberate stop apart from a genuine encode failure.
const CANCELED = 'ResizeCanceled';

let pool = null;
let nextJobId = 0;
const pending = new Map();

function supportsWorkerPath() {
  return typeof Worker !== 'undefined' && typeof OffscreenCanvas !== 'undefined';
}

function getPool() {
  if (pool) return pool;

  pool = [];
  for (let i = 0; i < POOL_SIZE; i++) {
    const worker = new Worker(new URL('./resizeWorker.js', import.meta.url), {
      type: 'module',
    });

    worker.onmessage = (event) => {
      const { id, blob, error } = event.data;
      const job = pending.get(id);
      if (!job) return; // canceled while in flight
      pending.delete(id);
      if (error) job.reject(new Error(error));
      else job.resolve(blob);
    };

    worker.onerror = (err) => {
      // A worker that dies takes its in-flight job with it; fail that job so
      // the caller falls back rather than hanging forever.
      for (const [id, job] of pending) {
        if (job.worker === worker) {
          pending.delete(id);
          job.reject(new Error(`worker: ${err?.message || 'crashed'}`));
        }
      }
    };

    pool.push({ worker, load: 0 });
  }

  return pool;
}

function encodeInWorker(file) {
  const workers = getPool();

  // Least-loaded assignment - keeps a slow photo from blocking a worker's queue
  // while others sit idle.
  const slot = workers.reduce((a, b) => (b.load < a.load ? b : a));
  slot.load++;

  const id = nextJobId++;

  return new Promise((resolve, reject) => {
    pending.set(id, {
      worker: slot.worker,
      resolve: (blob) => {
        slot.load--;
        resolve(blob);
      },
      reject: (err) => {
        slot.load--;
        reject(err);
      },
    });

    slot.worker.postMessage({
      id,
      file,
      maxDimension: MAX_DIMENSION,
      qualityLadder: QUALITY_LADDER,
      targetBytes: TARGET_BYTES,
    });
  });
}

/**
 * Main-thread fallback for browsers without OffscreenCanvas, and for any photo
 * the worker pool failed on. Same output, just serialized.
 */
async function encodeOnMainThread(file) {
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });

  try {
    const { width, height } = bitmap;

    let targetWidth = width;
    let targetHeight = height;
    if (width > MAX_DIMENSION || height > MAX_DIMENSION) {
      const scale = MAX_DIMENSION / Math.max(width, height);
      targetWidth = Math.round(width * scale);
      targetHeight = Math.round(height * scale);
    }

    const canvas = document.createElement('canvas');
    canvas.width = targetWidth;
    canvas.height = targetHeight;
    canvas.getContext('2d').drawImage(bitmap, 0, 0, targetWidth, targetHeight);

    let blob = null;
    for (const quality of QUALITY_LADDER) {
      blob = await new Promise((resolve) =>
        canvas.toBlob(resolve, 'image/webp', quality)
      );
      if (!blob || blob.size <= TARGET_BYTES) break;
    }

    return blob;
  } finally {
    bitmap.close();
  }
}

/**
 * Resize an image file on the client before upload and convert it to WebP.
 *
 * Runs in a pool of Web Workers so several photos are processed genuinely in
 * parallel; falls back to the main thread where workers or OffscreenCanvas
 * aren't available.
 *
 * Falls back to the original file on any failure (unsupported browser, decode
 * error, etc.) - a failed client-side optimization should never block an
 * upload. The server still compresses anything that arrives unoptimized.
 */
export async function resizeImageFile(file) {
  if (!file.type.startsWith('image/')) {
    return file;
  }

  let blob = null;

  if (supportsWorkerPath()) {
    try {
      blob = await encodeInWorker(file);
    } catch (err) {
      // A cancel must not be treated as a worker failure - falling back would
      // re-encode on the main thread the very work the user just stopped.
      if (err?.name === CANCELED) throw err;
      console.warn('Worker resize failed, retrying on main thread', err);
    }
  }

  if (!blob) {
    try {
      blob = await encodeOnMainThread(file);
    } catch (err) {
      console.warn('Client-side resize failed, uploading original', err);
      return file;
    }
  }

  if (!blob) {
    return file;
  }

  const dot = file.name.lastIndexOf('.');
  const baseName = dot > 0 ? file.name.slice(0, dot) : file.name;
  return new File([blob], `${baseName}.webp`, { type: 'image/webp' });
}

/**
 * Drop every queued and in-flight resize, for when the user cancels an upload.
 *
 * Workers are terminated rather than asked to stop, since a canvas encode
 * already under way can't be interrupted cooperatively. The pool is rebuilt
 * lazily on the next upload.
 */
export function cancelPendingResizes() {
  for (const [id, job] of pending) {
    pending.delete(id);
    const err = new Error('Resize canceled');
    err.name = CANCELED;
    job.reject(err);
  }

  if (pool) {
    for (const slot of pool) slot.worker.terminate();
    pool = null;
  }
}
