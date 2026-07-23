const MAX_DIMENSION = 2500;
const JPEG_QUALITY = 0.9;

/**
 * Resize an image file on the client before upload, if it's larger than
 * MAX_DIMENSION. Cuts upload payload size (and server-side decode cost)
 * for large camera/phone originals, without touching quality beyond a
 * dimension trim - the server's own compression still does the real
 * quality/size tradeoff, so this intentionally doesn't compress hard.
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

    if (width <= MAX_DIMENSION && height <= MAX_DIMENSION) {
      return file;
    }

    const scale = MAX_DIMENSION / Math.max(width, height);
    const newWidth = Math.round(width * scale);
    const newHeight = Math.round(height * scale);

    const canvas = document.createElement('canvas');
    canvas.width = newWidth;
    canvas.height = newHeight;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(bitmap, 0, 0, newWidth, newHeight);

    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY)
    );

    if (!blob) {
      return file;
    }

    const newName = file.name.replace(/\.[^./\\]+$/, '') + '.jpg';
    return new File([blob], newName, { type: 'image/jpeg' });
  } catch (err) {
    console.warn('Client-side resize failed, uploading original', err);
    return file;
  } finally {
    bitmap.close();
  }
}
