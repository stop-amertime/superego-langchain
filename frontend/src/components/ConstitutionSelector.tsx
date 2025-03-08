import React, { useState, useRef, useEffect } from 'react';
import { Constitution } from '../types';
import './ConstitutionSelector.css';

interface ConstitutionSelectorProps {
  onSelectConstitution: (constitutionId: string) => void;
  selectedConstitutionId: string;
  constitutions?: Constitution[];
  isLoading?: boolean;
  error?: string | null;
}

const ConstitutionSelector: React.FC<ConstitutionSelectorProps> = ({ 
  onSelectConstitution, 
  selectedConstitutionId,
  constitutions = [],
  isLoading = false,
  error = null
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Set default constitution if selected ID is invalid
  useEffect(() => {
    if (constitutions.length > 0 && !isLoading) {
      const isValidSelection = constitutions.some(c => c.id === selectedConstitutionId);
      if (!isValidSelection) {
        onSelectConstitution(constitutions[0].id);
      }
    }
  }, [constitutions, selectedConstitutionId, isLoading, onSelectConstitution]);

  // Get the selected constitution name
  const selectedConstitution = constitutions.find(c => c.id === selectedConstitutionId);
  const selectedName = selectedConstitution ? selectedConstitution.name : (isLoading ? 'Loading...' : 'Select Constitution');

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSelect = (constitutionId: string) => {
    // Only call the callback if the constitution actually changed
    if (constitutionId !== selectedConstitutionId) {
      onSelectConstitution(constitutionId);
    }
    
    // Always close the dropdown
    setIsOpen(false);
  };

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  if (isLoading) {
    return <div className="constitution-selector-loading">Loading constitutions...</div>;
  }

  if (error || constitutions.length === 0) {
    return (
      <div className="constitution-selector-error">
        {error ? String(error) : 'No constitutions available'}
      </div>
    );
  }

  return (
    <div className="constitution-selector" ref={dropdownRef}>
      <div 
        className="constitution-selector-header" 
        onClick={toggleDropdown}
      >
        <span className="constitution-name">{selectedName}</span>
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </div>
      
      {isOpen && (
        <div className="constitution-dropdown">
          {constitutions.map((constitution) => (
            <div 
              key={constitution.id} 
              className={`constitution-option ${constitution.id === selectedConstitutionId ? 'selected' : ''}`}
              onClick={() => handleSelect(constitution.id)}
            >
              {constitution.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConstitutionSelector;
