import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { videoService, frameService, annotationService, nipsService } from '../services/api';
import NIPSScorePanel from '../components/NIPSScorePanel';

function AnnotationWorkspace() {
  const { videoId } = useParams();
  const [video, setVideo] = useState(null);
  const [frames, setFrames] = useState([]);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [nipsScale, setNipsScale] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Default annotation state
  const defaultAnnotation = {
    facial_expression: 0,
    cry: 0,
    breathing_pattern: 0,
    arms: 0,
    legs: 0,
    state_of_arousal: 0,
    annotator_id: 'demo_annotator',
    confidence: 'medium',
    notes: ''
  };

  const [annotation, setAnnotation] = useState(defaultAnnotation);

  useEffect(() => {
    loadInitialData();
  }, [videoId]);

  useEffect(() => {
    if (frames.length > 0) {
      loadFrameDetails(frames[currentFrameIndex]?.id);
    }
  }, [currentFrameIndex, frames]);

  const loadInitialData = async () => {
    try {
      const [videoRes, framesRes, nipsRes] = await Promise.all([
        videoService.getOne(videoId),
        videoService.getFrames(videoId, 1, 100),
        nipsService.getScale()
      ]);

      setVideo(videoRes.data);
      setFrames(framesRes.data.frames);
      setNipsScale(nipsRes.data);
    } catch (error) {
      console.error('Failed to load workspace data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFrameDetails = async (frameId) => {
    if (!frameId) return;

    try {
      const response = await frameService.getOne(frameId);
      setCurrentFrame(response.data);

      // Load existing annotation if present
      if (response.data.annotations?.length > 0) {
        const existing = response.data.annotations[0];
        setAnnotation({
          facial_expression: existing.facial_expression,
          cry: existing.cry,
          breathing_pattern: existing.breathing_pattern,
          arms: existing.arms,
          legs: existing.legs,
          state_of_arousal: existing.state_of_arousal,
          annotator_id: existing.annotator_id,
          confidence: existing.confidence,
          notes: existing.notes || '',
          id: existing.id
        });
      } else {
        setAnnotation(defaultAnnotation);
      }
    } catch (error) {
      console.error('Failed to load frame:', error);
    }
  };

  const handleAnnotationChange = (field, value) => {
    setAnnotation(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    if (!currentFrame) return;

    setSaving(true);
    try {
      const data = {
        ...annotation,
        frame: currentFrame.id
      };

      if (annotation.id) {
        await annotationService.update(annotation.id, data);
      } else {
        const response = await annotationService.create(data);
        setAnnotation(prev => ({ ...prev, id: response.data.id }));
      }

      // Update frames list to show annotation status
      setFrames(prev => prev.map(f =>
        f.id === currentFrame.id ? { ...f, is_annotated: true } : f
      ));

      // Auto-advance to next frame
      if (currentFrameIndex < frames.length - 1) {
        setCurrentFrameIndex(prev => prev + 1);
      }
    } catch (error) {
      console.error('Failed to save annotation:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleSkip = () => {
    if (currentFrameIndex < frames.length - 1) {
      setCurrentFrameIndex(prev => prev + 1);
    }
  };

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'ArrowLeft' && currentFrameIndex > 0) {
      setCurrentFrameIndex(prev => prev - 1);
    } else if (e.key === 'ArrowRight' && currentFrameIndex < frames.length - 1) {
      setCurrentFrameIndex(prev => prev + 1);
    } else if (e.key === 'Enter' && e.ctrlKey) {
      handleSave();
    }
  }, [currentFrameIndex, frames.length]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  if (loading) {
    return <div className="loading">Loading workspace...</div>;
  }

  if (!video) {
    return (
      <div className="card">
        <p>Video not found.</p>
        <Link to="/videos" className="btn btn-primary">Back to Videos</Link>
      </div>
    );
  }

  const currentFrameData = frames[currentFrameIndex];

  return (
    <div className="annotation-workspace">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <div>
          <Link to="/videos" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.875rem' }}>
            ← Back to Videos
          </Link>
          <h2 style={{ margin: '0.25rem 0' }}>{video.name}</h2>
          <span className={`context-badge context-${video.recording_context}`}>
            {video.recording_context?.replace('_', ' ')}
          </span>
        </div>
        <div style={{ textAlign: 'right', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          <div>Subject: {video.subject_id}</div>
          <div>Progress: {video.annotation_progress}%</div>
        </div>
      </div>

      {/* Workspace Grid */}
      <div className="workspace">
        {/* Frame Viewer */}
        <div className="frame-viewer">
          <div className="frame-display">
            {/* Placeholder for actual frame image */}
            <div className="frame-placeholder">
              <div className="frame-placeholder-icon">🖼</div>
              <div>Frame {currentFrameData?.frame_number || 0}</div>
              <div style={{ fontSize: '0.75rem', marginTop: '0.5rem' }}>
                {currentFrameData?.image_path}
              </div>
              <div style={{ fontSize: '0.625rem', marginTop: '1rem', maxWidth: '300px' }}>
                In production, actual NICU footage would display here.
                For this demo, frame metadata is shown instead.
              </div>
            </div>
          </div>

          {/* Frame Controls */}
          <div className="frame-controls">
            <button
              className="frame-nav-btn"
              onClick={() => setCurrentFrameIndex(prev => prev - 1)}
              disabled={currentFrameIndex === 0}
            >
              ←
            </button>

            <div className="frame-info">
              <div className="frame-number">
                Frame {currentFrameIndex + 1} of {frames.length}
              </div>
              <div className="frame-timestamp">
                {currentFrameData?.timestamp_seconds?.toFixed(1)}s
              </div>
            </div>

            <button
              className="frame-nav-btn"
              onClick={() => setCurrentFrameIndex(prev => prev + 1)}
              disabled={currentFrameIndex === frames.length - 1}
            >
              →
            </button>
          </div>

          {/* Timeline */}
          <div className="timeline">
            <div className="timeline-label">
              Timeline (green = annotated, blue = current)
            </div>
            <div className="timeline-track">
              {frames.map((frame, idx) => (
                <div
                  key={frame.id}
                  className={`timeline-frame ${frame.is_annotated ? 'annotated' : ''} ${idx === currentFrameIndex ? 'current' : ''}`}
                  onClick={() => setCurrentFrameIndex(idx)}
                  title={`Frame ${frame.frame_number}`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* NIPS Scoring Panel */}
        <NIPSScorePanel
          nipsScale={nipsScale}
          annotation={annotation}
          onChange={handleAnnotationChange}
          onSave={handleSave}
          onSkip={handleSkip}
          saving={saving}
          hasExisting={!!annotation.id}
        />
      </div>

      {/* Keyboard Shortcuts */}
      <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
        Keyboard shortcuts: ← Previous | → Next | Ctrl+Enter Save
      </div>
    </div>
  );
}

export default AnnotationWorkspace;
