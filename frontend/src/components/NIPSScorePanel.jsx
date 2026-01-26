function NIPSScorePanel({ nipsScale, annotation, onChange, onSave, onSkip, saving, hasExisting }) {
  // Calculate total score
  const totalScore =
    annotation.facial_expression +
    annotation.cry +
    annotation.breathing_pattern +
    annotation.arms +
    annotation.legs +
    annotation.state_of_arousal;

  // Determine pain level
  const getPainLevel = (score) => {
    if (score <= 2) return { label: 'No Pain', class: 'no-pain' };
    if (score <= 4) return { label: 'Mild Pain', class: 'mild-pain' };
    return { label: 'Severe Pain', class: 'severe-pain' };
  };

  const painLevel = getPainLevel(totalScore);

  // Component configurations (fallback if nipsScale not loaded)
  const components = nipsScale?.components || {
    facial_expression: {
      label: 'Facial Expression',
      options: [
        { value: 0, label: 'Relaxed', description: 'Restful face, neutral expression' },
        { value: 1, label: 'Grimace', description: 'Tight facial muscles, furrowed brow' }
      ]
    },
    cry: {
      label: 'Cry',
      options: [
        { value: 0, label: 'No cry', description: 'Quiet, not crying' },
        { value: 1, label: 'Whimper', description: 'Mild moaning, intermittent' },
        { value: 2, label: 'Vigorous', description: 'Loud scream, shrill, continuous' }
      ]
    },
    breathing_pattern: {
      label: 'Breathing Pattern',
      options: [
        { value: 0, label: 'Relaxed', description: 'Usual pattern' },
        { value: 1, label: 'Changed', description: 'Irregular, faster, gagging' }
      ]
    },
    arms: {
      label: 'Arms',
      options: [
        { value: 0, label: 'Relaxed', description: 'No rigidity, random movements' },
        { value: 1, label: 'Flexed/Extended', description: 'Tense, rigid' }
      ]
    },
    legs: {
      label: 'Legs',
      options: [
        { value: 0, label: 'Relaxed', description: 'No rigidity, random movements' },
        { value: 1, label: 'Flexed/Extended', description: 'Tense, rigid' }
      ]
    },
    state_of_arousal: {
      label: 'State of Arousal',
      options: [
        { value: 0, label: 'Sleeping/Awake', description: 'Quiet, peaceful' },
        { value: 1, label: 'Fussy', description: 'Alert, restless, thrashing' }
      ]
    }
  };

  return (
    <div className="nips-panel">
      {/* Header */}
      <div className="nips-header">
        <div className="nips-title">NIPS Assessment</div>
        <div className="nips-subtitle">Neonatal Infant Pain Scale</div>
      </div>

      {/* Scoring Components */}
      <div className="nips-body">
        {Object.entries(components).map(([key, component]) => (
          <div key={key} className="nips-component">
            <div className="nips-component-label">{component.label}</div>
            <div className="nips-options">
              {component.options.map((option) => (
                <label
                  key={option.value}
                  className={`nips-option ${annotation[key] === option.value ? 'selected' : ''}`}
                >
                  <input
                    type="radio"
                    name={key}
                    value={option.value}
                    checked={annotation[key] === option.value}
                    onChange={() => onChange(key, option.value)}
                  />
                  <div className="nips-option-content">
                    <div className="nips-option-label">
                      {option.label}
                      <span className="nips-score-badge" style={{ marginLeft: '0.5rem' }}>
                        +{option.value}
                      </span>
                    </div>
                    <div className="nips-option-desc">{option.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Score Display */}
      <div className="score-display">
        <div className="score-total">
          <span className="score-label">Total Score</span>
          <span className={`score-value ${painLevel.class}`}>{totalScore}/7</span>
        </div>
        <div className={`score-interpretation ${painLevel.class}`}>
          {painLevel.label}
        </div>
      </div>

      {/* Metadata */}
      <div className="metadata-section">
        <div className="form-group">
          <label className="form-label">Confidence</label>
          <select
            className="form-select"
            value={annotation.confidence}
            onChange={(e) => onChange('confidence', e.target.value)}
          >
            <option value="high">High - Clear indicators</option>
            <option value="medium">Medium - Some uncertainty</option>
            <option value="low">Low - Difficult to assess</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Notes (optional)</label>
          <textarea
            className="form-textarea"
            value={annotation.notes}
            onChange={(e) => onChange('notes', e.target.value)}
            placeholder="Any observations, occlusions, difficulties..."
          />
        </div>
      </div>

      {/* Actions */}
      <div className="nips-actions">
        <button className="btn btn-secondary" onClick={onSkip}>
          Skip
        </button>
        <button
          className="btn btn-success"
          onClick={onSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : hasExisting ? 'Update' : 'Save & Next'}
        </button>
      </div>
    </div>
  );
}

export default NIPSScorePanel;
