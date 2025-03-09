import React, { useState } from 'react';
import { Message, MessageRole, SuperegoDecision } from '../types';
import './MessageBubble.css';
import ConstitutionSelector from './ConstitutionSelector';
import SyspromptSelector from './SyspromptSelector';
import { AppData } from '../App';

interface MessageBubbleProps {
  message: Message;
  appData: AppData;
  onRerun?: (messageId: string, constitutionId: string, syspromptId: string) => void;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, appData, onRerun }) => {
  // State for rerun settings
  const [selectedConstitutionId, setSelectedConstitutionId] = useState<string>(message.constitutionId || 'default');
  const [selectedSyspromptId, setSelectedSyspromptId] = useState<string>(message.syspromptId || 'assistant_default');
  // Format the timestamp to a readable format
  const formattedTime = new Date(message.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  // Get the sender name based on role
  const getSender = (role: MessageRole) => {
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

  // Get badge content based on superego decision
  const getDecisionBadge = () => {
    if (message.role !== MessageRole.SUPEREGO || !message.decision) {
      return null;
    }

    const badgeClassMap: Record<string, string> = {
      'ALLOW': 'badge-success',
      'CAUTION': 'badge-warning',
      'BLOCK': 'badge-danger'
    };

    const badgeClass = badgeClassMap[message.decision] || 'badge-secondary';

    return (
      <span className={`decision-badge ${badgeClass}`}>
        {message.decision}
      </span>
    );
  };

  // Toggle thinking visibility
  const [showThinking, setShowThinking] = useState(false);
  
  // Handle rerun with selected constitution and system prompt
  const handleRerun = () => {
    if (onRerun) {
      onRerun(message.id, selectedConstitutionId, selectedSyspromptId);
    }
  };

  return (
    <div className={`message-bubble ${message.role}`}>
      <div className="message-header">
        <div className="message-info">
          <span className="message-sender">{getSender(message.role)}</span>
          <span className="message-time">{formattedTime}</span>
          {getDecisionBadge()}
        </div>
        <div className="message-actions">
          <div className="action-buttons">
            {message.thinking && (
              <button
                className="action-button"
                onClick={() => setShowThinking(!showThinking)}
                title={showThinking ? "Hide thinking process" : "Show thinking process"}
              >
                {showThinking ? "🧠❌" : "🧠"}
              </button>
            )}
            {(message.role === MessageRole.SUPEREGO || message.role === MessageRole.ASSISTANT) && (
              <button
                className="action-button rerun-action"
                onClick={handleRerun}
                title="Rerun with current settings"
              >
                🔄
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="message-content">
        {message.role === MessageRole.SUPEREGO && appData && (
          <div className="message-metadata-header">
            <span className="metadata-label">Constitution:</span> 
            <ConstitutionSelector
              onSelectConstitution={setSelectedConstitutionId}
              selectedConstitutionId={selectedConstitutionId}
              constitutions={appData?.constitutions || []}
              isLoading={appData?.constitutionsLoading || false}
              error={appData?.constitutionsError || null}
            />
          </div>
        )}
        
        {message.role === MessageRole.ASSISTANT && appData && (
          <div className="message-metadata-header">
            <span className="metadata-label">System Prompt:</span>
            <SyspromptSelector
              onSelectSysprompt={setSelectedSyspromptId}
              selectedSyspromptId={selectedSyspromptId}
              sysprompts={appData?.sysprompts || []}
              isLoading={appData?.syspromptsLoading || false}
              error={appData?.syspromptsError || null}
            />
          </div>
        )}
        
        {message.content.split('\n').map((line, i, arr) => (
          <React.Fragment key={i}>
            {line}
            {i < arr.length - 1 && <br />}
          </React.Fragment>
        ))}
      </div>

      {message.thinking && showThinking && (
        <div className="message-thinking">
          <h4>Thinking Process</h4>
          <pre>{message.thinking}</pre>
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
