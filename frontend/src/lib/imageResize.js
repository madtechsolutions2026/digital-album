const MAX_DIMENSION = 2048;
const WEBP_QUALITY = 0.8;

/**
 * Resize an image file on the client before upload, if it's larger than
 * MAX_DIMENSION. Converts to WebP format to reduce file size by 50-80%
 * and speed up transmission over the network.
 *
 * Falls back to the original file on any failure (unsupported browser,
 * decode error, etc.) - a failed client-side optimization should never
 * block an upload.
 */
export async function resizeImageFile(file) {
  if (!file.type.startsWith('image/')) {
    return file;
  }

  let bitmap;
  try {
    bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
  } catch (err) {
    console.warn('Client-side resize: could not decode image, uploading original', err);
    return file;
  }

  try {
    const { width, height } = bitmap;

    // Even if it's smaller, we still convert to WebP to optimize the compression
    const needsResize = width > MAX_DIMENSION || height > MAX_DIMENSION;
    
    let newWidth = width;
    let newHeight = height;
    
    if (needsResize) {
      const scale = MAX_DIMENSION / Math.max(width, height);
      newWidth = Math.round(width * scale);
      newHeight = Math.round(height * scale);
    }

    const canvas = document.createElement('canvas');
    canvas.width = newWidth;
    canvas.height = newHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(bitmap, 0, 0, newWidth, newHeight);

    // Modern browsers support WebP blob conversion
    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, 'image/webp', WEBP_QUALITY)
    );

    if (!blob) {
      return file;
    }

    const newName = file.name.replace(/\.[^./\\]+$/, '') + '.webp';
    return new File([blob], newName, { type: 'image/webp' });
  } catch (err) {
    console.warn('Client-side resize failed, uploading original', err);
    return file;
  } finally {
    bitmap.close();
  }
}
