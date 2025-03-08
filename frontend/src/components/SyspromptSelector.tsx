import React, { useEffect } from 'react';
import { Sysprompt } from '../types';
import './SyspromptSelector.css';

interface SyspromptSelectorProps {
  onSelectSysprompt: (syspromptId: string) => void;
  selectedSyspromptId: string;
  sysprompts?: Sysprompt[];
  isLoading?: boolean;
  error?: string | null;
}

const SyspromptSelector: React.FC<SyspromptSelectorProps> = ({ 
  onSelectSysprompt, 
  selectedSyspromptId,
  sysprompts = [],
  isLoading = false,
  error = null
}) => {
  
  // Set default sysprompt if selected ID is invalid
  useEffect(() => {
    if (sysprompts.length > 0 && !isLoading) {
      const isValidSelection = sysprompts.some(s => s.id === selectedSyspromptId);
      if (!isValidSelection) {
        onSelectSysprompt(sysprompts[0].id);
      }
    }
  }, [sysprompts, selectedSyspromptId, isLoading, onSelectSysprompt]);

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const syspromptId = event.target.value;
    onSelectSysprompt(syspromptId);
  };

  if (isLoading) {
    return <div className="sysprompt-selector-loading">Loading system prompts...</div>;
  }

  if (error || sysprompts.length === 0) {
    return (
      <div className="sysprompt-selector-error">
        {error ? String(error) : 'No system prompts available'}
      </div>
    );
  }

  return (
    <div className="sysprompt-selector">
      <select 
        id="sysprompt-select" 
        value={selectedSyspromptId} 
        onChange={handleChange}
      >
        {sysprompts.map((sysprompt) => (
          <option key={sysprompt.id} value={sysprompt.id}>
            {sysprompt.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default SyspromptSelector;
