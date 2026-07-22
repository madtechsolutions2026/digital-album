# Wedding Photo Portal - Frontend

React-based frontend for the AI-powered wedding photo portal with face detection and search.

## Features

- **Photo Upload**: Upload wedding photos with automatic face detection
- **Face Search**: Upload a selfie to find photos containing your face
- **Real-time Results**: See detected face counts and similarity scores
- **Modern UI**: Beautiful gradient design with responsive layout

## Prerequisites

- Node.js 18+ and npm
- Backend server running on http://localhost:8000

## Installation

```bash
npm install
```

## Development

```bash
npm run dev
```

The app will be available at **http://localhost:3000**

## Build for Production

```bash
npm run build
npm run preview
```

## Usage

### Upload Photos
1. Select the "Upload Photos" tab
2. Enter the Event ID (default: 1)
3. Choose a wedding photo (JPEG, PNG, or WEBP)
4. Click "Upload & Detect Faces"
5. View the number of faces detected

### Search by Face
1. Select the "Search by Face" tab
2. Enter the Event ID
3. Upload a selfie (clear photo of your face)
4. Adjust the similarity threshold slider
   - Lower (0.3-0.5): More matches, less strict
   - Medium (0.5-0.7): Balanced
   - Higher (0.7-0.9): Fewer matches, stricter
5. Click "Find My Photos"
6. View matching photos with similarity scores

## API Endpoints

The frontend connects to:
- `POST /api/photos/upload` - Upload and detect faces
- `POST /api/photos/search` - Search photos by face similarity

## Configuration

Vite proxy configuration in `vite.config.js` routes `/api/*` requests to the backend at `http://localhost:8000`.

## Tech Stack

- React 18
- Vite (build tool)
- Axios (HTTP client)
- Modern CSS with gradients and blur effects
