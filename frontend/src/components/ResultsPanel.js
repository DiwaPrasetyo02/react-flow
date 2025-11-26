import React from 'react';
import './ResultsPanel.css';

const ResultsPanel = ({ results }) => {
  return (
    <div className="results-panel">
      <h2>Agent Results</h2>
      <div className="results-container">
        {results.length === 0 ? (
          <div className="no-results">
            <p>No results yet. Execute an agent to see results here.</p>
          </div>
        ) : (
          results.map((result, index) => (
            <div key={index} className="result-card">
              <div className="result-header">
                <div className="result-agent-info">
                  <span className="result-layer">Layer {result.layer}</span>
                  <h3>{result.agentName}</h3>
                </div>
                <span className={`result-status ${result.status}`}>
                  {result.status}
                </span>
              </div>
              <div className="result-timestamp">
                {new Date(result.timestamp).toLocaleString()}
              </div>
              <div className="result-content">
                {result.status === 'error' ? (
                  <div className="error-message">
                    <strong>Error:</strong> {result.error}
                  </div>
                ) : (
                  <>
                    {result.input && (
                      <div className="result-section">
                        <strong>Input:</strong>
                        <pre>{JSON.stringify(result.input, null, 2)}</pre>
                      </div>
                    )}
                    {result.output && (
                      <div className="result-section">
                        <strong>Output:</strong>
                        <pre>{JSON.stringify(result.output, null, 2)}</pre>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ResultsPanel;
