/**
 * Web Worker: downscale and WebP-encode a photo off the main thread.
 *
 * The main thread can only run one canvas encode at a time, so uploading with
 * a concurrency of 6 still resized photos one after another. Running this in a
 * pool of workers makes that concurrency real.
 *
 * Encoding also enforces the size budget here rather than letting the server
 * discover it: a photo that lands over the budget is re-encoded at a lower
 * quality locally. Retrying on the client is nearly free (idle CPU, in
 * parallel), while the same retry on the server costs ~1s of the one resource
 * every upload is queued behind.
 */

self.onmessage = async (event) => {
  const { id, file, maxDimension, qualityLadder, targetBytes } = event.data;

  let bitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  } catch (err) {
    // Undecodable here does not mean undecodable everywhere - hand it back so
    // the caller can fall back to uploading the original untouched.
    self.postMessage({ id, error: `decode: ${err?.message || err}` });
    return;
  }

  try {
    const { width, height } = bitmap;

    let targetWidth = width;
    let targetHeight = height;
    if (width > maxDimension || height > maxDimension) {
      const scale = maxDimension / Math.max(width, height);
      targetWidth = Math.round(width * scale);
      targetHeight = Math.round(height * scale);
    }

    const canvas = new OffscreenCanvas(targetWidth, targetHeight);
    const ctx = canvas.getContext('2d');
    ctx.drawImage(bitmap, 0, 0, targetWidth, targetHeight);

    // Try each quality until one fits the budget; keep the last (smallest)
    // result if none do, so the server still gets the best we managed.
    let blob = null;
    for (const quality of qualityLadder) {
      blob = await canvas.convertToBlob({ type: 'image/webp', quality });
      if (blob.size <= targetBytes) break;
    }

    self.postMessage({ id, blob, width: targetWidth, height: targetHeight });
  } catch (err) {
    self.postMessage({ id, error: `encode: ${err?.message || err}` });
  } finally {
    bitmap.close();
  }
};
