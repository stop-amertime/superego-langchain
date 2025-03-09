import React from 'react';
import './FlowConnector.css';
import { MessageRole } from '../types';

interface FlowConnectorProps {
  fromType: MessageRole;
  toType: MessageRole;
  status?: 'active' | 'blocked' | 'completed';
}

const FlowConnector: React.FC<FlowConnectorProps> = ({ 
  fromType, 
  toType, 
  status = 'completed' 
}) => {
  // Determine connector class based on the from/to types and status
  const getConnectorClass = () => {
    let baseClass = 'flow-connector';
    
    // Add status-specific class
    baseClass += ` ${status}`;
    
    // Add specific classes based on the connection types
    if (fromType === MessageRole.USER && toType === MessageRole.SUPEREGO) {
      baseClass += ' user-to-superego';
    } else if (fromType === MessageRole.SUPEREGO && toType === MessageRole.ASSISTANT) {
      baseClass += ' superego-to-assistant';
    } else if (fromType === MessageRole.USER && toType === MessageRole.ASSISTANT) {
      baseClass += ' user-to-assistant';
    } else if (fromType === MessageRole.ASSISTANT && toType === MessageRole.USER) {
      baseClass += ' assistant-to-user';
    }
    
    return baseClass;
  };

  return (
    <div className={getConnectorClass()}>
      <div className="connector-line"></div>
      <div className="connector-dot from-dot"></div>
      <div className="connector-dot to-dot"></div>
    </div>
  );
};

export default FlowConnector;
