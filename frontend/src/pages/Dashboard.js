import React, { useState, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';

import Sidebar from '../components/Sidebar';
import AgentNode from '../components/AgentNode';
import ResultsPanel from '../components/ResultsPanel';
import FileUpload from '../components/FileUpload';
import AgentConfigModal from '../components/AgentConfigModal';
import { executeAgent } from '../services/api';
import './Dashboard.css';

const nodeTypes = {
  agentNode: AgentNode,
};

const initialNodes = [
  {
    id: 'ocr-1',
    type: 'agentNode',
    position: { x: 400, y: 50 },
    data: {
      label: 'OCR Agent',
      layer: 1,
      type: 'ocr',
      status: 'idle',
      config: null,
    },
  },
  {
    id: 'vector-1',
    type: 'agentNode',
    position: { x: 400, y: 200 },
    data: {
      label: 'Vector & Embedding Agent',
      layer: 2,
      type: 'vector',
      status: 'idle',
      config: null,
    },
  },
  {
    id: 'extraction-1',
    type: 'agentNode',
    position: { x: 400, y: 350 },
    data: {
      label: 'Extraction Agent',
      layer: 3,
      type: 'extraction',
      status: 'idle',
      config: null,
    },
  },
  {
    id: 'summary-1',
    type: 'agentNode',
    position: { x: 400, y: 500 },
    data: {
      label: 'Summary Agent',
      layer: 4,
      type: 'summary',
      status: 'idle',
      config: null,
    },
  },
];

const initialEdges = [
  { id: 'e1-2', source: 'ocr-1', target: 'vector-1', animated: true },
  { id: 'e2-3', source: 'vector-1', target: 'extraction-1', animated: true },
  { id: 'e3-4', source: 'extraction-1', target: 'summary-1', animated: true },
];

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [results, setResults] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState([]);

  // Configuration modal state
  const [configModal, setConfigModal] = useState({
    isOpen: false,
    agentType: null,
    agentName: null,
    currentConfig: null,
  });

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const updateNodeStatus = useCallback((nodeId, status) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              status,
            },
          };
        }
        return node;
      })
    );
  }, [setNodes]);

  const updateNodeConfig = useCallback((agentType, config) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.data.type === agentType) {
          return {
            ...node,
            data: {
              ...node.data,
              config,
            },
          };
        }
        return node;
      })
    );
  }, [setNodes]);

  const handleFileUpload = async (files) => {
    console.log('Files uploaded:', files);
    setUploadedFiles(files);
    // Files are already uploaded to backend via FileUpload component
  };

  const handleConfigureAgent = useCallback((agentType, agentName) => {
    const node = nodes.find(n => n.data.type === agentType);
    setConfigModal({
      isOpen: true,
      agentType,
      agentName,
      currentConfig: node?.data.config || null,
    });
  }, [nodes]);

  const handleSaveConfig = useCallback((config) => {
    updateNodeConfig(configModal.agentType, config);
    console.log('Config saved for', configModal.agentType, config);
  }, [configModal.agentType, updateNodeConfig]);

  const handleExecuteAgent = useCallback(async (agentType) => {
    const nodeId = nodes.find(n => n.data.type === agentType)?.id;
    const node = nodes.find(n => n.data.type === agentType);
    if (!nodeId) return;

    // Check if file is needed for OCR agent
    if (agentType === 'ocr' && uploadedFiles.length === 0) {
      alert('Please upload a document first before executing OCR Agent');
      return;
    }

    updateNodeStatus(nodeId, 'running');

    try {
      // Prepare input based on agent type
      let inputData;
      if (agentType === 'ocr' && uploadedFiles.length > 0) {
        // Use file path from uploaded file
        const uploadedFile = uploadedFiles[0];
        if (uploadedFile.file_path) {
          // Use file_path directly (absolute path from backend)
          inputData = uploadedFile.file_path;
        } else if (uploadedFile.document_id) {
          // If we have document_id, send it as string (OCR Agent will resolve it)
          inputData = uploadedFile.document_id.toString();
        } else if (uploadedFile.uploadResult?.file_path) {
          // Fallback to uploadResult
          inputData = uploadedFile.uploadResult.file_path;
        } else {
          throw new Error('File path not available. Please upload the file again.');
        }
      } else if (uploadedFiles.length > 0) {
        // For other agents, pass the uploaded file info
        const uploadedFile = uploadedFiles[0];
        inputData = {
          document_id: uploadedFile.document_id || uploadedFile.uploadResult?.document_id,
          file_path: uploadedFile.file_path || uploadedFile.uploadResult?.file_path,
          ...uploadedFile
        };
      } else {
        inputData = 'Sample document input';
      }

      const response = await executeAgent(agentType, {
        input: inputData,
        config: node?.data.config || {},
        parameters: node?.data.config || {},
      });

      const result = {
        agentName: response.agent_name,
        layer: response.layer,
        status: 'completed',
        input: response.input,
        output: response.output,
        timestamp: new Date().toISOString(),
        config: node?.data.config,
      };

      setResults((prev) => [result, ...prev]);
      updateNodeStatus(nodeId, 'completed');

      setTimeout(() => {
        updateNodeStatus(nodeId, 'idle');
      }, 3000);
    } catch (error) {
      const result = {
        agentName: agentType.toUpperCase(),
        layer: nodes.find(n => n.data.type === agentType)?.data.layer || 0,
        status: 'error',
        error: error.message || 'Failed to execute agent',
        timestamp: new Date().toISOString(),
      };

      setResults((prev) => [result, ...prev]);
      updateNodeStatus(nodeId, 'error');

      setTimeout(() => {
        updateNodeStatus(nodeId, 'idle');
      }, 3000);
    }
  }, [uploadedFiles, nodes, updateNodeStatus]);

  const nodesWithCallbacks = useMemo(() => {
    return nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        onExecute: handleExecuteAgent,
        onConfigure: handleConfigureAgent,
      },
    }));
  }, [nodes, handleExecuteAgent, handleConfigureAgent]);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return (
          <div className="dashboard-overview">
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">📊</div>
                <div className="stat-content">
                  <h3>Total Processed</h3>
                  <p className="stat-value">{results.length}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📄</div>
                <div className="stat-content">
                  <h3>Documents</h3>
                  <p className="stat-value">{uploadedFiles.length}</p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">✅</div>
                <div className="stat-content">
                  <h3>Successful</h3>
                  <p className="stat-value">
                    {results.filter(r => r.status === 'completed').length}
                  </p>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">❌</div>
                <div className="stat-content">
                  <h3>Failed</h3>
                  <p className="stat-value">
                    {results.filter(r => r.status === 'error').length}
                  </p>
                </div>
              </div>
            </div>
            <div className="recent-activity">
              <h2>Recent Activity</h2>
              {results.length === 0 ? (
                <p className="no-activity">No recent activity</p>
              ) : (
                results.slice(0, 5).map((result, index) => (
                  <div key={index} className="activity-item">
                    <span className={`activity-status ${result.status}`}>
                      {result.status === 'completed' ? '✓' : '✗'}
                    </span>
                    <div className="activity-details">
                      <p className="activity-name">{result.agentName}</p>
                      <p className="activity-time">
                        {new Date(result.timestamp).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        );

      case 'workflow':
        return (
          <>
            <div className="workflow-header">
              <h2>Agent Workflow</h2>
              <p>Configure and execute your multi-agent pipeline</p>
              {uploadedFiles.length > 0 && (
                <div className="uploaded-files-indicator">
                  <span className="file-count-badge">{uploadedFiles.length}</span>
                  <span>Document{uploadedFiles.length > 1 ? 's' : ''} ready</span>
                  {uploadedFiles[0]?.name && (
                    <span className="file-name-preview">: {uploadedFiles[0].name}</span>
                  )}
                </div>
              )}
            </div>
            <div className="workflow-upload-section">
              <FileUpload onFileUpload={handleFileUpload} />
            </div>
            <div className="flow-container">
              <ReactFlow
                nodes={nodesWithCallbacks}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                fitView
              >
                <Background />
                <Controls />
                <MiniMap />
              </ReactFlow>
            </div>
          </>
        );

      case 'documents':
        return (
          <div className="documents-page">
            <h2>Document Upload</h2>
            <p className="page-description">
              Upload your documents to be processed by the agent pipeline
            </p>
            <FileUpload onFileUpload={handleFileUpload} />
          </div>
        );

      case 'results':
        return (
          <div className="results-page">
            <h2>Processing Results</h2>
            <p className="page-description">
              View detailed results from agent executions
            </p>
            <ResultsPanel results={results} />
          </div>
        );

      case 'settings':
        return (
          <div className="settings-page">
            <h2>Settings</h2>
            <div className="settings-section">
              <h3>API Configuration</h3>
              <div className="setting-item">
                <label>Mistral API Key</label>
                <input type="password" placeholder="Enter Mistral API key" />
              </div>
              <div className="setting-item">
                <label>Gemini API Key</label>
                <input type="password" placeholder="Enter Gemini API key" />
              </div>
              <div className="setting-item">
                <label>Database Connection</label>
                <input type="text" placeholder="PostgreSQL connection string" />
              </div>
            </div>
            <button className="save-settings-btn">Save Settings</button>
          </div>
        );

      default:
        return <div>Select a menu item</div>;
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      <main className="main-content">
        <div className="content-wrapper">
          {renderContent()}
        </div>
      </main>

      <AgentConfigModal
        isOpen={configModal.isOpen}
        onClose={() => setConfigModal({ ...configModal, isOpen: false })}
        agentType={configModal.agentType}
        agentName={configModal.agentName}
        currentConfig={configModal.currentConfig}
        onSave={handleSaveConfig}
      />
    </div>
  );
};

export default Dashboard;
