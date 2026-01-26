import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { statisticsService, videoService } from '../services/api';

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [statsRes, videosRes] = await Promise.all([
        statisticsService.get(),
        videoService.getAll()
      ]);
      setStats(statsRes.data);
      setVideos(videosRes.data.slice(0, 3)); // Show only 3 recent
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  const maxScore = Math.max(...(stats?.score_distribution || [1]));

  return (
    <div className="dashboard">
      <h2 style={{ marginBottom: '1.5rem' }}>Annotation Dashboard</h2>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats?.total_videos || 0}</div>
          <div className="stat-label">Videos</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.total_frames || 0}</div>
          <div className="stat-label">Total Frames</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.total_annotations || 0}</div>
          <div className="stat-label">Annotations</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.annotation_rate || 0}%</div>
          <div className="stat-label">Completion Rate</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Pain Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">Pain Distribution</h3>
          </div>
          <div className="pain-distribution">
            <div className="pain-item">
              <div className="pain-count" style={{ color: 'var(--success-color)' }}>
                {stats?.pain_distribution?.no_pain || 0}
              </div>
              <div className="pain-label">No Pain (0-2)</div>
            </div>
            <div className="pain-item">
              <div className="pain-count" style={{ color: 'var(--warning-color)' }}>
                {stats?.pain_distribution?.mild_pain || 0}
              </div>
              <div className="pain-label">Mild Pain (3-4)</div>
            </div>
            <div className="pain-item">
              <div className="pain-count" style={{ color: 'var(--danger-color)' }}>
                {stats?.pain_distribution?.severe_pain || 0}
              </div>
              <div className="pain-label">Severe Pain (5-7)</div>
            </div>
          </div>
        </div>

        {/* Score Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">NIPS Score Distribution</h3>
          </div>
          <div className="chart-container">
            {(stats?.score_distribution || []).map((count, score) => (
              <div
                key={score}
                className="chart-bar"
                style={{
                  height: `${(count / maxScore) * 100}%`,
                  background: score <= 2 ? 'var(--success-color)' :
                             score <= 4 ? 'var(--warning-color)' : 'var(--danger-color)'
                }}
              >
                <span className="chart-bar-label">{score}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Videos */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">Recent Videos</h3>
          <Link to="/videos" className="btn btn-secondary">View All</Link>
        </div>
        {videos.length === 0 ? (
          <p style={{ color: 'var(--text-secondary)' }}>No videos uploaded yet.</p>
        ) : (
          <div className="video-grid">
            {videos.map(video => (
              <div key={video.id} className="video-card">
                <div className="video-card-body">
                  <div className="video-card-title">{video.name}</div>
                  <div className="video-card-meta">
                    <span className={`context-badge context-${video.recording_context}`}>
                      {video.recording_context?.replace('_', ' ') || 'Unknown'}
                    </span>
                    <span style={{ marginLeft: '0.5rem' }}>
                      {video.frame_count} frames
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${video.annotation_progress}%` }}
                    />
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    {video.annotation_progress}% annotated
                  </div>
                  <Link
                    to={`/annotate/${video.id}`}
                    className="btn btn-primary"
                    style={{ marginTop: '0.75rem', width: '100%', justifyContent: 'center' }}
                  >
                    Annotate
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* NIPS Reference */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">NIPS Quick Reference</h3>
        </div>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
          <p style={{ marginBottom: '0.5rem' }}>
            <strong>Neonatal Infant Pain Scale (NIPS)</strong> - Behavioral assessment tool for neonates
          </p>
          <ul style={{ paddingLeft: '1.5rem' }}>
            <li>Score Range: 0-7</li>
            <li>0-2: No pain or minimal discomfort</li>
            <li>3-4: Mild to moderate pain</li>
            <li>5-7: Severe pain - intervention recommended</li>
          </ul>
          <p style={{ marginTop: '0.5rem' }}>
            Components: Facial Expression, Cry, Breathing Pattern, Arms, Legs, State of Arousal
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
