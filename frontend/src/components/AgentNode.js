import React from 'react';
import { Handle, Position } from 'reactflow';
import './AgentNode.css';

const AgentNode = ({ data }) => {
  const { label, layer, type, status, onExecute } = data;

  const getStatusColor = () => {
    switch (status) {
      case 'idle':
        return '#6b7280';
      case 'running':
        return '#f59e0b';
      case 'completed':
        return '#10b981';
      case 'error':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  return (
    <div className="agent-node" style={{ borderColor: getStatusColor() }}>
      <Handle type="target" position={Position.Top} />

      <div className="agent-node-header">
        <div className="layer-badge">Layer {layer}</div>
        <div className="status-indicator" style={{ backgroundColor: getStatusColor() }} />
      </div>

      <div className="agent-node-content">
        <h3>{label}</h3>
        <p className="agent-type">{type}</p>
      </div>

      <button
        className="execute-btn"
        onClick={() => onExecute && onExecute(type)}
        disabled={status === 'running'}
      >
        {status === 'running' ? 'Running...' : 'Execute'}
      </button>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default AgentNode;
