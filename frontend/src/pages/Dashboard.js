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

import AgentNode from '../components/AgentNode';
import ResultsPanel from '../components/ResultsPanel';
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
    },
  },
];

const initialEdges = [
  { id: 'e1-2', source: 'ocr-1', target: 'vector-1', animated: true },
  { id: 'e2-3', source: 'vector-1', target: 'extraction-1', animated: true },
  { id: 'e3-4', source: 'extraction-1', target: 'summary-1', animated: true },
];

const Dashboard = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [results, setResults] = useState([]);
  const [inputData, setInputData] = useState('');

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

  const handleExecuteAgent = useCallback(async (agentType) => {
    const nodeId = nodes.find(n => n.data.type === agentType)?.id;
    if (!nodeId) return;

    updateNodeStatus(nodeId, 'running');

    try {
      const response = await executeAgent(agentType, {
        input: inputData || `Sample input for ${agentType}`,
      });

      const result = {
        agentName: response.agent_name,
        layer: response.layer,
        status: 'completed',
        input: response.input,
        output: response.output,
        timestamp: new Date().toISOString(),
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
  }, [inputData, nodes, updateNodeStatus]);

  const nodesWithExecute = useMemo(() => {
    return nodes.map((node) => ({
      ...node,
      data: {
        ...node.data,
        onExecute: handleExecuteAgent,
      },
    }));
  }, [nodes, handleExecuteAgent]);

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Multi-Agent Dashboard</h1>
        <p>4-Layer Agent System with React Flow</p>
      </header>

      <div className="dashboard-content">
        <div className="input-section">
          <label htmlFor="input-data">Input Data:</label>
          <textarea
            id="input-data"
            placeholder="Enter input data for agents..."
            value={inputData}
            onChange={(e) => setInputData(e.target.value)}
            rows={3}
          />
        </div>

        <div className="flow-container">
          <ReactFlow
            nodes={nodesWithExecute}
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

        <ResultsPanel results={results} />
      </div>
    </div>
  );
};

export default Dashboard;
