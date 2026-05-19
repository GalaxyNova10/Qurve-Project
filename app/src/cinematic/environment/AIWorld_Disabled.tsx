import React from 'react';

// AI World configuration
interface AIWorldProps {
  children?: React.ReactNode;
  quality?: 'high' | 'medium' | 'low';
}

// Disabled AI World for performance optimization
export const AIWorld: React.FC<AIWorldProps> = () => {
  // Completely disabled for performance
  return null;
};
