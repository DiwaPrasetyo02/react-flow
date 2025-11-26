import React, { useState, useEffect } from 'react';
import './AgentConfigModal.css';

const AgentConfigModal = ({ isOpen, onClose, agentType, agentName, currentConfig, onSave }) => {
  const [config, setConfig] = useState({});

  useEffect(() => {
    if (currentConfig) {
      setConfig(currentConfig);
    } else {
      setConfig(getDefaultConfig(agentType));
    }
  }, [agentType, currentConfig]);

  const getDefaultConfig = (type) => {
    switch (type) {
      case 'ocr':
        return {
          maxPages: 10,
          language: 'en',
          dpi: 300,
          ocrEngine: 'mistral',
          extractImages: true,
          preserveLayout: true,
        };
      case 'vector':
        return {
          embeddingModel: 'sentence-transformers',
          chunkSize: 500,
          chunkOverlap: 50,
          vectorDimension: 384,
          storageEngine: 'pgvector',
          indexType: 'ivfflat',
        };
      case 'extraction':
        return {
          extractionModel: 'gemini',
          extractFields: ['name', 'date', 'amount', 'description'],
          customFields: '',
          confidenceThreshold: 0.7,
          enableNER: true,
          entityTypes: ['PERSON', 'DATE', 'MONEY', 'ORG'],
        };
      case 'summary':
        return {
          summaryModel: 'gemini',
          summaryLength: 'medium',
          summaryType: 'abstractive',
          customPrompt: 'Summarize the following document, highlighting key points and main ideas.',
          includeKeywords: true,
          language: 'en',
          temperature: 0.7,
        };
      default:
        return {};
    }
  };

  const handleChange = (field, value) => {
    setConfig((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleArrayChange = (field, value) => {
    const array = value.split(',').map((item) => item.trim()).filter((item) => item);
    setConfig((prev) => ({
      ...prev,
      [field]: array,
    }));
  };

  const handleSave = () => {
    onSave(config);
    onClose();
  };

  if (!isOpen) return null;

  const renderOCRConfig = () => (
    <>
      <div className="config-field">
        <label>Max Pages to Process</label>
        <input
          type="number"
          value={config.maxPages || 10}
          onChange={(e) => handleChange('maxPages', parseInt(e.target.value))}
          min="1"
          max="1000"
        />
        <span className="field-hint">Maximum number of pages to OCR</span>
      </div>

      <div className="config-field">
        <label>Language</label>
        <select
          value={config.language || 'en'}
          onChange={(e) => handleChange('language', e.target.value)}
        >
          <option value="en">English</option>
          <option value="id">Indonesian</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
        </select>
      </div>

      <div className="config-field">
        <label>DPI (Image Quality)</label>
        <input
          type="number"
          value={config.dpi || 300}
          onChange={(e) => handleChange('dpi', parseInt(e.target.value))}
          min="72"
          max="600"
          step="50"
        />
      </div>

      <div className="config-field">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.extractImages || false}
            onChange={(e) => handleChange('extractImages', e.target.checked)}
          />
          Extract images from document
        </label>
      </div>

      <div className="config-field">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.preserveLayout || false}
            onChange={(e) => handleChange('preserveLayout', e.target.checked)}
          />
          Preserve document layout
        </label>
      </div>
    </>
  );

  const renderVectorConfig = () => (
    <>
      <div className="config-field">
        <label>Chunk Size</label>
        <input
          type="number"
          value={config.chunkSize || 500}
          onChange={(e) => handleChange('chunkSize', parseInt(e.target.value))}
          min="100"
          max="2000"
          step="100"
        />
        <span className="field-hint">Number of characters per chunk</span>
      </div>

      <div className="config-field">
        <label>Chunk Overlap</label>
        <input
          type="number"
          value={config.chunkOverlap || 50}
          onChange={(e) => handleChange('chunkOverlap', parseInt(e.target.value))}
          min="0"
          max="500"
        />
        <span className="field-hint">Overlapping characters between chunks</span>
      </div>

      <div className="config-field">
        <label>Vector Dimension</label>
        <select
          value={config.vectorDimension || 384}
          onChange={(e) => handleChange('vectorDimension', parseInt(e.target.value))}
        >
          <option value="384">384 (default)</option>
          <option value="512">512</option>
          <option value="768">768</option>
          <option value="1024">1024</option>
        </select>
      </div>

      <div className="config-field">
        <label>Index Type</label>
        <select
          value={config.indexType || 'ivfflat'}
          onChange={(e) => handleChange('indexType', e.target.value)}
        >
          <option value="ivfflat">IVFFlat (Fast)</option>
          <option value="hnsw">HNSW (Accurate)</option>
        </select>
      </div>
    </>
  );

  const renderExtractionConfig = () => (
    <>
      <div className="config-field">
        <label>Fields to Extract (comma-separated)</label>
        <input
          type="text"
          value={config.extractFields?.join(', ') || ''}
          onChange={(e) => handleArrayChange('extractFields', e.target.value)}
          placeholder="e.g., name, date, amount, description"
        />
        <span className="field-hint">Specify which fields to extract from documents</span>
      </div>

      <div className="config-field">
        <label>Custom Fields</label>
        <textarea
          value={config.customFields || ''}
          onChange={(e) => handleChange('customFields', e.target.value)}
          rows="3"
          placeholder="Add any custom field definitions..."
        />
      </div>

      <div className="config-field">
        <label>Confidence Threshold</label>
        <input
          type="range"
          value={config.confidenceThreshold || 0.7}
          onChange={(e) => handleChange('confidenceThreshold', parseFloat(e.target.value))}
          min="0"
          max="1"
          step="0.1"
        />
        <span className="field-value">{config.confidenceThreshold || 0.7}</span>
      </div>

      <div className="config-field">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.enableNER || false}
            onChange={(e) => handleChange('enableNER', e.target.checked)}
          />
          Enable Named Entity Recognition
        </label>
      </div>

      <div className="config-field">
        <label>Entity Types</label>
        <input
          type="text"
          value={config.entityTypes?.join(', ') || ''}
          onChange={(e) => handleArrayChange('entityTypes', e.target.value)}
          placeholder="PERSON, DATE, MONEY, ORG"
        />
      </div>
    </>
  );

  const renderSummaryConfig = () => (
    <>
      <div className="config-field">
        <label>Summary Length</label>
        <select
          value={config.summaryLength || 'medium'}
          onChange={(e) => handleChange('summaryLength', e.target.value)}
        >
          <option value="short">Short (1-2 sentences)</option>
          <option value="medium">Medium (1 paragraph)</option>
          <option value="long">Long (Multiple paragraphs)</option>
        </select>
      </div>

      <div className="config-field">
        <label>Summary Type</label>
        <select
          value={config.summaryType || 'abstractive'}
          onChange={(e) => handleChange('summaryType', e.target.value)}
        >
          <option value="abstractive">Abstractive (AI-generated)</option>
          <option value="extractive">Extractive (Key sentences)</option>
          <option value="hybrid">Hybrid (Both)</option>
        </select>
      </div>

      <div className="config-field">
        <label>Custom Prompt</label>
        <textarea
          value={config.customPrompt || ''}
          onChange={(e) => handleChange('customPrompt', e.target.value)}
          rows="4"
          placeholder="Enter custom instructions for summarization..."
        />
        <span className="field-hint">
          Define the goal or specific instructions for the summary
        </span>
      </div>

      <div className="config-field">
        <label>Temperature</label>
        <input
          type="range"
          value={config.temperature || 0.7}
          onChange={(e) => handleChange('temperature', parseFloat(e.target.value))}
          min="0"
          max="1"
          step="0.1"
        />
        <span className="field-value">{config.temperature || 0.7}</span>
        <span className="field-hint">Higher = more creative, Lower = more focused</span>
      </div>

      <div className="config-field">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={config.includeKeywords || false}
            onChange={(e) => handleChange('includeKeywords', e.target.checked)}
          />
          Include extracted keywords
        </label>
      </div>
    </>
  );

  const renderConfigFields = () => {
    switch (agentType) {
      case 'ocr':
        return renderOCRConfig();
      case 'vector':
        return renderVectorConfig();
      case 'extraction':
        return renderExtractionConfig();
      case 'summary':
        return renderSummaryConfig();
      default:
        return <p>No configuration available for this agent.</p>;
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Configure {agentName}</h2>
          <button className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">{renderConfigFields()}</div>

        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleSave}>
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
};

export default AgentConfigModal;
