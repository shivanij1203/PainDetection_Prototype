import { useState, useRef } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

function QualityAnalyzer() {
  // Mode: 'images' or 'video'
  const [mode, setMode] = useState('video');

  // Image upload state
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [imageResults, setImageResults] = useState([]);
  const [imageSummary, setImageSummary] = useState(null);

  // Video upload state
  const [videoFile, setVideoFile] = useState(null);
  const [videoResults, setVideoResults] = useState(null);

  // Common state
  const [analyzing, setAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('upload');
  const fileInputRef = useRef(null);
  const videoInputRef = useRef(null);

  // Image handlers
  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(files);
    setImageResults([]);
    setImageSummary(null);

    const newPreviews = [];
    files.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        newPreviews[index] = e.target.result;
        if (newPreviews.filter(Boolean).length === files.length) {
          setPreviews([...newPreviews]);
        }
      };
      reader.readAsDataURL(file);
    });
  };

  const analyzeImages = async () => {
    if (selectedFiles.length === 0) return;
    setAnalyzing(true);
    setActiveTab('results');

    try {
      const base64Images = await Promise.all(
        selectedFiles.map((file) => new Promise((resolve) => {
          const reader = new FileReader();
          reader.onload = (e) => resolve(e.target.result);
          reader.readAsDataURL(file);
        }))
      );

      const response = await axios.post(`${API_BASE}/analyze/batch/`, { images: base64Images });
      setImageResults(response.data.results);
      setImageSummary(response.data.summary);
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Make sure the backend is running.');
    } finally {
      setAnalyzing(false);
    }
  };

  // Video handlers
  const handleVideoSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoFile(file);
      setVideoResults(null);
    }
  };

  const analyzeVideo = async () => {
    if (!videoFile) return;
    setAnalyzing(true);
    setActiveTab('results');

    try {
      const formData = new FormData();
      formData.append('file', videoFile);
      formData.append('extraction_fps', '1');  // 1 frame per second

      const response = await axios.post(`${API_BASE}/analyze/video/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setVideoResults(response.data);
    } catch (error) {
      console.error('Video analysis failed:', error);
      alert('Video analysis failed. Make sure the backend is running.');
    } finally {
      setAnalyzing(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return '#22c55e';
    if (score >= 40) return '#f59e0b';
    return '#ef4444';
  };

  const getUsabilityBadge = (usability) => {
    const styles = {
      usable: { background: '#dcfce7', color: '#166534' },
      marginal: { background: '#fef3c7', color: '#92400e' },
      unusable: { background: '#fee2e2', color: '#991b1b' }
    };
    return styles[usability] || styles.unusable;
  };

  return (
    <div className="quality-analyzer">
      <div className="page-header">
        <div>
          <h2>NICU Image Quality Analyzer</h2>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
            Pre-screen videos/images for quality issues before annotation
          </p>
        </div>
      </div>

      {/* Research Context Banner */}
      <div className="research-banner">
        <div className="banner-title">Addressing Published Research Challenges</div>
        <div className="banner-content">
          <div className="finding">
            <strong>Problem 1:</strong> Images with pixel intensity ≤25 are unusable
            <span className="citation">— IEEE Access, 2024</span>
          </div>
          <div className="finding">
            <strong>Problem 2:</strong> Medical equipment occludes facial detection
            <span className="citation">— USF RPAL Research</span>
          </div>
        </div>
      </div>

      {/* Mode Toggle */}
      <div className="mode-toggle">
        <button
          className={`mode-btn ${mode === 'video' ? 'active' : ''}`}
          onClick={() => { setMode('video'); setActiveTab('upload'); }}
        >
          Video Upload
        </button>
        <button
          className={`mode-btn ${mode === 'images' ? 'active' : ''}`}
          onClick={() => { setMode('images'); setActiveTab('upload'); }}
        >
          Image Upload
        </button>
      </div>

      {/* Tabs */}
      <div className="analyzer-tabs">
        <button
          className={`tab ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => setActiveTab('upload')}
        >
          Upload {mode === 'video' ? 'Video' : 'Images'}
        </button>
        <button
          className={`tab ${activeTab === 'results' ? 'active' : ''}`}
          onClick={() => setActiveTab('results')}
          disabled={mode === 'video' ? !videoResults : imageResults.length === 0}
        >
          Analysis Results
        </button>
      </div>

      {/* VIDEO MODE */}
      {mode === 'video' && (
        <>
          {activeTab === 'upload' && (
            <div className="upload-section">
              <div
                className="upload-dropzone"
                onClick={() => videoInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={videoInputRef}
                  onChange={handleVideoSelect}
                  accept="video/*"
                  style={{ display: 'none' }}
                />
                <div className="dropzone-icon">🎬</div>
                <div className="dropzone-text">
                  Click to select a NICU video
                </div>
                <div className="dropzone-hint">
                  Supports MP4, AVI, MOV | Frames extracted at 1 fps
                </div>
              </div>

              {videoFile && (
                <div className="selected-file">
                  <div className="file-info">
                    <strong>{videoFile.name}</strong>
                    <span>{(videoFile.size / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                  <button
                    className="btn btn-primary analyze-btn"
                    onClick={analyzeVideo}
                    disabled={analyzing}
                  >
                    {analyzing ? 'Analyzing Video...' : 'Analyze Video'}
                  </button>
                </div>
              )}

              {/* Workflow Explanation */}
              <div className="workflow-explainer">
                <h4>How It Works</h4>
                <div className="workflow-steps">
                  <div className="step">
                    <div className="step-num">1</div>
                    <div className="step-text">Upload NICU video</div>
                  </div>
                  <div className="step-arrow">→</div>
                  <div className="step">
                    <div className="step-num">2</div>
                    <div className="step-text">Extract frames (1/sec)</div>
                  </div>
                  <div className="step-arrow">→</div>
                  <div className="step">
                    <div className="step-num">3</div>
                    <div className="step-text">Analyze each frame</div>
                  </div>
                  <div className="step-arrow">→</div>
                  <div className="step">
                    <div className="step-num">4</div>
                    <div className="step-text">Get usable frames only</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'results' && videoResults && (
            <div className="results-section">
              {/* Video Summary */}
              <div className="summary-card">
                <h3>Video Analysis: {videoResults.filename}</h3>
                <div className="video-meta">
                  Duration: {videoResults.duration_seconds}s |
                  FPS: {videoResults.fps} |
                  Frames Extracted: {videoResults.total_frames_extracted}
                </div>

                <div className="summary-grid">
                  <div className="summary-stat">
                    <div className="stat-value">{videoResults.total_frames_extracted}</div>
                    <div className="stat-label">Frames Analyzed</div>
                  </div>
                  <div className="summary-stat usable">
                    <div className="stat-value">{videoResults.summary.usable}</div>
                    <div className="stat-label">Usable ({videoResults.summary.usable_percentage}%)</div>
                  </div>
                  <div className="summary-stat marginal">
                    <div className="stat-value">{videoResults.summary.marginal}</div>
                    <div className="stat-label">Marginal</div>
                  </div>
                  <div className="summary-stat unusable">
                    <div className="stat-value">{videoResults.summary.unusable}</div>
                    <div className="stat-label">Unusable</div>
                  </div>
                </div>

                {videoResults.summary.boosted_by_adjacent > 0 && (
                  <div className="boost-info">
                    <span className="boost-icon">↑</span>
                    {videoResults.summary.boosted_by_adjacent} frames improved by temporal smoothing
                    <span className="boost-hint">(adjacent frame analysis)</span>
                  </div>
                )}

                {/* Issues Breakdown */}
                <div className="issues-breakdown">
                  <h4>Issues Detected</h4>
                  <div className="issues-grid">
                    {videoResults.issues.too_dark > 0 && (
                      <div className="issue-item">
                        <span className="issue-icon dark">●</span>
                        Too Dark: {videoResults.issues.too_dark}
                      </div>
                    )}
                    {videoResults.issues.blurry > 0 && (
                      <div className="issue-item">
                        <span className="issue-icon blur">●</span>
                        Blurry: {videoResults.issues.blurry}
                      </div>
                    )}
                    {videoResults.issues.no_face > 0 && (
                      <div className="issue-item">
                        <span className="issue-icon face">●</span>
                        No Face: {videoResults.issues.no_face}
                      </div>
                    )}
                    {videoResults.issues.occluded > 0 && (
                      <div className="issue-item">
                        <span className="issue-icon occlude">●</span>
                        Occluded: {videoResults.issues.occluded}
                      </div>
                    )}
                  </div>
                </div>

                {/* Recommendation */}
                <div className="recommendation-box">
                  {videoResults.recommendation}
                </div>
              </div>

              {/* Frame Timeline */}
              <div className="card">
                <h4>Frame Quality Timeline</h4>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                  Green = Usable | Yellow = Marginal | Red = Unusable
                </p>
                <div className="frame-timeline">
                  {videoResults.frames.map((frame, idx) => (
                    <div
                      key={idx}
                      className={`timeline-block ${frame.usability}`}
                      title={`Frame ${frame.frame_number}: ${frame.usability} (${frame.quality_score.toFixed(0)})`}
                    />
                  ))}
                </div>
              </div>

              {/* Frame Grid */}
              <div className="card">
                <h4>Frame-by-Frame Results</h4>
                <div className="frame-grid">
                  {videoResults.frames.map((frame, idx) => (
                    <div key={idx} className={`frame-card ${frame.usability} ${frame.adjacent_boost ? 'boosted' : ''}`}>
                      <img src={frame.thumbnail} alt={`Frame ${frame.frame_number}`} />
                      <div className="frame-info">
                        <div className="frame-time">{frame.timestamp_seconds}s</div>
                        <div
                          className="frame-score"
                          style={{ color: getScoreColor(frame.quality_score) }}
                        >
                          {frame.quality_score.toFixed(0)}
                          {frame.adjacent_boost && <span className="boost-arrow">↑</span>}
                        </div>
                      </div>
                      <div
                        className="frame-badge"
                        style={getUsabilityBadge(frame.usability)}
                      >
                        {frame.usability}
                      </div>
                      {frame.adjacent_boost && (
                        <div className="boost-indicator" title={`Boosted from ${frame.original_score?.toFixed(0)} (${frame.original_usability})`}>
                          ↑
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* IMAGE MODE */}
      {mode === 'images' && (
        <>
          {activeTab === 'upload' && (
            <div className="upload-section">
              <div
                className="upload-dropzone"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageSelect}
                  multiple
                  accept="image/*"
                  style={{ display: 'none' }}
                />
                <div className="dropzone-icon">+</div>
                <div className="dropzone-text">
                  Click to select images
                </div>
                <div className="dropzone-hint">
                  Supports JPG, PNG, BMP | Multiple files allowed
                </div>
              </div>

              {previews.length > 0 && (
                <>
                  <div className="preview-grid">
                    {previews.map((preview, index) => (
                      <div key={index} className="preview-item">
                        <img src={preview} alt={`Preview ${index + 1}`} />
                        <div className="preview-name">{selectedFiles[index]?.name}</div>
                      </div>
                    ))}
                  </div>
                  <button
                    className="btn btn-primary analyze-btn"
                    onClick={analyzeImages}
                    disabled={analyzing}
                  >
                    {analyzing ? 'Analyzing...' : `Analyze ${selectedFiles.length} Image${selectedFiles.length > 1 ? 's' : ''}`}
                  </button>
                </>
              )}
            </div>
          )}

          {activeTab === 'results' && imageSummary && (
            <div className="results-section">
              <div className="summary-card">
                <h3>Batch Analysis Summary</h3>
                <div className="summary-grid">
                  <div className="summary-stat">
                    <div className="stat-value">{imageSummary.total}</div>
                    <div className="stat-label">Total</div>
                  </div>
                  <div className="summary-stat usable">
                    <div className="stat-value">{imageSummary.usable}</div>
                    <div className="stat-label">Usable</div>
                  </div>
                  <div className="summary-stat marginal">
                    <div className="stat-value">{imageSummary.marginal}</div>
                    <div className="stat-label">Marginal</div>
                  </div>
                  <div className="summary-stat unusable">
                    <div className="stat-value">{imageSummary.unusable}</div>
                    <div className="stat-label">Unusable</div>
                  </div>
                </div>
              </div>

              <div className="results-list">
                {imageResults.map((result, index) => (
                  <div key={index} className="result-card">
                    <div className="result-header">
                      <div className="result-preview">
                        {previews[index] && <img src={previews[index]} alt="" />}
                      </div>
                      <div className="result-summary">
                        <div className="result-title">{selectedFiles[index]?.name}</div>
                        <div className="usability-badge" style={getUsabilityBadge(result.overall?.usability)}>
                          {result.overall?.usability?.toUpperCase()}
                        </div>
                        <div className="score-circle" style={{ borderColor: getScoreColor(result.overall?.score) }}>
                          <span style={{ color: getScoreColor(result.overall?.score) }}>{result.overall?.score}</span>
                        </div>
                      </div>
                    </div>
                    <div className="result-details">
                      <div className="metrics-section">
                        <h4>Quality Metrics</h4>
                        <div className="metrics-grid">
                          <div className={`metric ${result.quality?.brightness?.is_too_dark ? 'bad' : 'good'}`}>
                            <div className="metric-label">Brightness</div>
                            <div className="metric-value">{result.quality?.brightness?.mean?.toFixed(1)}</div>
                          </div>
                          <div className={`metric ${result.quality?.blur?.is_blurry ? 'bad' : 'good'}`}>
                            <div className="metric-label">Sharpness</div>
                            <div className="metric-value">{result.quality?.blur?.laplacian_variance?.toFixed(0)}</div>
                          </div>
                          <div className={`metric ${result.occlusion?.face_detected ? 'good' : 'bad'}`}>
                            <div className="metric-label">Face</div>
                            <div className="metric-value">{result.occlusion?.face_detected ? 'Yes' : 'No'}</div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default QualityAnalyzer;
