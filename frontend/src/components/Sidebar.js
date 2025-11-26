import React from 'react';
import './Sidebar.css';

const Sidebar = ({ activeTab, onTabChange }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'workflow', label: 'Workflow', icon: '🔄' },
    { id: 'documents', label: 'Documents', icon: '📄' },
    { id: 'results', label: 'Results', icon: '📈' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h2>🤖 MultiAgent</h2>
        <p>Document Processing</p>
      </div>

      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <button
            key={item.id}
            className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => onTabChange(item.id)}
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span className="sidebar-label">{item.label}</span>
          </button>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">U</div>
          <div className="user-details">
            <p className="user-name">User</p>
            <p className="user-role">Admin</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
