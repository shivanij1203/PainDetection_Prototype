import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { videoService } from '../services/api';

function VideoList() {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadVideos();
  }, []);

  const loadVideos = async () => {
    try {
      const response = await videoService.getAll();
      setVideos(response.data);
    } catch (error) {
      console.error('Failed to load videos:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (videoId, videoName) => {
    try {
      const response = await videoService.exportAnnotations(videoId, 'csv');
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${videoName}_annotations.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const filteredVideos = filter === 'all'
    ? videos
    : videos.filter(v => v.recording_context === filter);

  const contexts = ['all', ...new Set(videos.map(v => v.recording_context).filter(Boolean))];

  if (loading) {
    return <div className="loading">Loading videos...</div>;
  }

  return (
    <div className="video-list-page">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>Videos</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {contexts.map(ctx => (
            <button
              key={ctx}
              className={`btn ${filter === ctx ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setFilter(ctx)}
            >
              {ctx === 'all' ? 'All' : ctx.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {filteredVideos.length === 0 ? (
        <div className="card">
          <p style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
            No videos found. Upload videos to begin annotation.
          </p>
        </div>
      ) : (
        <div className="video-grid">
          {filteredVideos.map(video => (
            <div key={video.id} className="video-card">
              <div className="video-card-body">
                <div className="video-card-title">{video.name}</div>

                {video.description && (
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                    {video.description}
                  </p>
                )}

                <div className="video-card-meta">
                  <span className={`context-badge context-${video.recording_context}`}>
                    {video.recording_context?.replace('_', ' ') || 'Unknown'}
                  </span>
                </div>

                <div style={{ margin: '0.75rem 0', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  <div>Subject: {video.subject_id || 'N/A'}</div>
                  <div>Frames: {video.frame_count}</div>
                  <div>Duration: {video.duration_seconds ? `${video.duration_seconds}s` : 'N/A'}</div>
                </div>

                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${video.annotation_progress}%` }}
                  />
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  {video.annotation_progress}% annotated
                </div>

                <div style={{ display: 'flex', gap: '0.5rem' }}>
                  <Link
                    to={`/annotate/${video.id}`}
                    className="btn btn-primary"
                    style={{ flex: 1, justifyContent: 'center' }}
                  >
                    Annotate
                  </Link>
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleExport(video.id, video.name)}
                    title="Export annotations as CSV"
                  >
                    Export
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default VideoList;
