# NeoAnnotate - NICU Image Quality Analyzer & Annotation Tool

A research tool addressing key challenges in neonatal pain detection: **image quality pre-screening** and **occlusion detection**.

## The Problem (From Published Research)

USF's neonatal pain detection research identified critical challenges:

> "Images with average pixel intensity of 25 or lower are unusable for annotation"
> — *IEEE Access, 2024*

> "Occlusion from medical equipment blocks facial detection in NICU settings"
> — *USF RPAL Research*

This tool directly addresses these challenges with automated quality analysis.

## Key Features

### 1. Image Quality Pre-Screener
Automatically detects:
- **Dark images** (threshold: pixel intensity ≤25, per research findings)
- **Blur/motion blur** (Laplacian variance analysis)
- **Low contrast** (hard to distinguish facial features)
- **Resolution issues** (faces too small for reliable detection)

### 2. Occlusion & Face Visibility Detector
Using MediaPipe and OpenCV:
- Face detection with confidence scoring
- Landmark visibility analysis (468 facial landmarks)
- Occlusion level assessment (none/partial/severe)
- Likely cause identification (equipment, pose, framing)

### 3. Batch Processing
- Analyze multiple images at once
- Get summary statistics (usable/marginal/unusable counts)
- Export quality reports

### 4. NIPS Annotation Interface
Standard annotation workflow:
- Video/frame management
- NIPS scoring (6 components, 0-7 scale)
- Export to CSV/JSON for ML pipelines

## Tech Stack

- **Backend**: Django + Django REST Framework + OpenCV + MediaPipe
- **Frontend**: React + Vite
- **Analysis**: OpenCV for image processing, MediaPipe for face detection

## Running Locally

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_demo_data  # load sample annotation data
python generate_test_images.py   # generate quality test images
python manage.py runserver 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 → Click "Quality Analyzer" to test

## Sample Test Images

The `backend/test_images/` folder contains synthetic images demonstrating:
- `good_quality.jpg` - Passes all checks
- `very_dark_below_threshold.jpg` - Below ≤25 intensity threshold
- `blurry.jpg` - Motion blur detection
- `occluded_equipment.jpg` - Simulated medical equipment
- `low_contrast.jpg` - Feature detection difficulty

## API Endpoints

```
POST /api/analyze/image/     - Analyze single image (base64 or file upload)
POST /api/analyze/batch/     - Batch analysis with summary
GET  /api/analyze/thresholds/ - Get threshold values and research references
```

## Research References

- Hausmann, J. et al. (2024). "Accurate Neonatal Face Detection for Improved Pain Classification in the Challenging NICU Setting." *IEEE Access*.
- USF RPAL Neonatal Pain Project: https://rpal.cse.usf.edu/project_neonatal_pain/
- Lawrence, J. et al. (1993). "The development of a tool to assess neonatal pain." *Neonatal Network*.

## Why This Matters

Before training ML models for pain detection, you need clean data. This tool helps:
1. **Filter out unusable images** before annotation (saves time)
2. **Identify systematic issues** in data collection (lighting, equipment placement)
3. **Prioritize annotation efforts** on high-quality frames
4. **Improve model training** by ensuring data quality

---

Built as a research prototype to support USF's neonatal pain detection work.
