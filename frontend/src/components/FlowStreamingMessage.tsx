import React from 'react';
import './FlowStep.css';
import { MessageRole } from '../types';

interface FlowStreamingMessageProps {
  content: string;
  role: MessageRole;
  stepNumber?: number;
}

const FlowStreamingMessage: React.FC<FlowStreamingMessageProps> = ({ 
  content, 
  role = MessageRole.ASSISTANT,
  stepNumber
}) => {
  // Format the current time
  const formattedTime = new Date().toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  // Get the sender name based on role
  const getSender = () => {
    switch (role) {
      case MessageRole.USER:
        return 'You';
      case MessageRole.ASSISTANT:
        return 'Assistant';
      case MessageRole.SUPEREGO:
        return 'Superego';
      case MessageRole.SYSTEM:
        return 'System';
      default:
        return 'Unknown';
    }
  };

  // Get the step label
  const getStepLabel = () => {
    if (!stepNumber) return '';
    
    switch (role) {
      case MessageRole.SUPEREGO:
        return `Step ${stepNumber}: Evaluating content`;
      case MessageRole.ASSISTANT:
        return `Step ${stepNumber}: Generating response`;
      default:
        return `Step ${stepNumber}`;
    }
  };

  return (
    <div className={`flow-step ${role} streaming`}>
      <div className="step-connector">
        <div className="connector-line"></div>
        <div className="connector-dot"></div>
      </div>
      
      <div className="step-content">
        <div className="step-header">
          <div className="step-info">
            <span className="step-sender">{getStepLabel() || getSender()}</span>
            <span className="step-time">{formattedTime}</span>
          </div>
        </div>
        
        <div className="step-message">
          {content}
          <span className="cursor-blink">|</span>
        </div>
      </div>
    </div>
  );
};

export default FlowStreamingMessage;
