// Matches camera-source subfolder names like "Cam1", "CAM 2", "camera-3",
// "Cam_4" - these describe which camera shot the photo, not which part of
// the wedding it's from, so they should never become the category.
const CAMERA_FOLDER_PATTERN = /^cam(era)?[\s_-]?\d+$/i;

/**
 * Derive a photo's category from its upload folder path, e.g. for a
 * structure like "Muhurtam/Cam1/IMG_001.jpg" this returns "Muhurtam", not
 * "Cam1" - it walks outward from the file through folder names, skipping
 * anything that looks like a camera-source subfolder, regardless of how
 * deep the folder structure is nested.
 */
export function getFileCategory(file) {
  const relPath = file.webkitRelativePath;
  if (!relPath) return null;

  const folders = relPath.split('/').slice(0, -1); // drop the filename itself

  for (let i = folders.length - 1; i >= 0; i--) {
    const name = folders[i].trim();
    if (name && !CAMERA_FOLDER_PATTERN.test(name)) {
      return name;
    }
  }

  return null;
}
