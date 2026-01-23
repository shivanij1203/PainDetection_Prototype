# NeoAnnotate - NICU Image Analyzer & Annotation Tool

Tool for analyzing image quality and annotating neonatal pain expressions in NICU settings.

## Background

This project is based on research challenges identified in neonatal pain detection studies - specifically around image quality issues and occlusion from medical equipment that makes facial detection difficult.

Key issues addressed:
- Dark images (research suggests images with pixel intensity ≤25 are unusable)
- Blur and motion blur
- Occlusion from NICU equipment blocking faces
- Low contrast making facial features hard to distinguish

## Features

**Image Quality Analysis**
- Checks brightness, blur, contrast
- Detects if faces are visible or blocked
- Uses MediaPipe for face detection and landmark analysis

**Batch Processing**
- Upload multiple images for analysis
- Get summary of usable vs unusable images

**NIPS Annotation**
- Standard NIPS scoring interface (6 components)
- Export annotations to CSV/JSON

## Tech Stack

- Backend: Django + Django REST Framework
- Frontend: React + Vite
- Image Processing: OpenCV, MediaPipe

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Go to http://localhost:5173 and click Quality Analyzer to test.

## API Endpoints

```
POST /api/analyze/image/     - Analyze single image
POST /api/analyze/batch/     - Batch analysis
GET  /api/analyze/thresholds/ - Get threshold values
```

## References

- Hausmann et al. (2024). "Accurate Neonatal Face Detection for Improved Pain Classification" IEEE Access
- USF RPAL Neonatal Pain Project
- Lawrence et al. (1993). NIPS development paper

---

Research prototype for neonatal pain detection work.
