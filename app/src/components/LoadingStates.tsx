import React from 'react';
import { Loader2, RefreshCw, AlertCircle, CheckCircle, Clock, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LoadingStateProps {
  type: 'spinner' | 'progress' | 'skeleton' | 'dots' | 'pulse';
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  className?: string;
}

interface ProgressStateProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  className?: string;
}

interface StatusStateProps {
  status: 'loading' | 'success' | 'error' | 'warning';
  message?: string;
  className?: string;
}

interface ExecutionStateProps {
  stage: 'initializing' | 'validating' | 'queueing' | 'executing' | 'completing' | 'completed' | 'failed';
  currentStep?: number;
  totalSteps?: number;
  message?: string;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ 
  type, 
  size = 'md', 
  message, 
  className 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8'
  };

  const renderLoader = () => {
    switch (type) {
      case 'spinner':
        return <Loader2 className={cn('animate-spin', sizeClasses[size])} />;
      case 'dots':
        return (
          <div className="flex space-x-1">
            <div className={cn('w-2 h-2 bg-blue-500 rounded-full animate-bounce', sizeClasses[size])} style={{ animationDelay: '0ms' }} />
            <div className={cn('w-2 h-2 bg-blue-500 rounded-full animate-bounce', sizeClasses[size])} style={{ animationDelay: '150ms' }} />
            <div className={cn('w-2 h-2 bg-blue-500 rounded-full animate-bounce', sizeClasses[size])} style={{ animationDelay: '300ms' }} />
          </div>
        );
      case 'pulse':
        return (
          <div className={cn('w-3 h-3 bg-blue-500 rounded-full animate-pulse', sizeClasses[size])} />
        );
      case 'skeleton':
        return (
          <div className={cn('animate-pulse bg-gray-200 rounded', sizeClasses[size])} />
        );
      case 'progress':
        return (
          <RefreshCw className={cn('animate-spin', sizeClasses[size])} />
        );
      default:
        return <Loader2 className={cn('animate-spin', sizeClasses[size])} />;
    }
  };

  return (
    <div className={cn('flex flex-col items-center justify-center space-y-2', className)}>
      {renderLoader()}
      {message && (
        <p className="text-sm text-gray-600 text-center">{message}</p>
      )}
    </div>
  );
};

export const ProgressState: React.FC<ProgressStateProps> = ({ 
  value, 
  max = 100, 
  label, 
  showPercentage = true, 
  className 
}) => {
  const percentage = Math.round((value / max) * 100);

  return (
    <div className={cn('w-full space-y-2', className)}>
      {label && (
        <div className="flex justify-between text-sm">
          <span>{label}</span>
          {showPercentage && <span>{percentage}%</span>}
        </div>
      )}
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export const StatusState: React.FC<StatusStateProps> = ({ 
  status, 
  message, 
  className 
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'loading':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'loading':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'success':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'error':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={cn(
      'flex items-center space-x-2 px-3 py-2 rounded-lg border',
      getStatusColor(),
      className
    )}>
      {getStatusIcon()}
      {message && <span className="text-sm font-medium">{message}</span>}
    </div>
  );
};

export const ExecutionState: React.FC<ExecutionStateProps> = ({ 
  stage, 
  currentStep = 1, 
  totalSteps = 4, 
  message, 
  className 
}) => {
  const getStageIcon = () => {
    switch (stage) {
      case 'initializing':
        return <Clock className="w-4 h-4 text-blue-500" />;
      case 'validating':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'queueing':
        return <Clock className="w-4 h-4 text-orange-500" />;
      case 'executing':
        return <Zap className="w-4 h-4 text-purple-500" />;
      case 'completing':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStageColor = () => {
    switch (stage) {
      case 'initializing':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'validating':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'queueing':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'executing':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'completing':
      case 'completed':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-600 bg-red-50 border-red-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStageMessage = () => {
    if (message) return message;
    
    switch (stage) {
      case 'initializing':
        return 'Initializing execution...';
      case 'validating':
        return 'Validating request...';
      case 'queueing':
        return 'Queueing execution...';
      case 'executing':
        return 'Executing benchmark...';
      case 'completing':
        return 'Completing execution...';
      case 'completed':
        return 'Execution completed successfully';
      case 'failed':
        return 'Execution failed';
      default:
        return 'Preparing execution...';
    }
  };

  const progressPercentage = totalSteps > 0 ? (currentStep / totalSteps) * 100 : 0;

  return (
    <div className={cn('space-y-4', className)}>
      {/* Current Stage */}
      <div className={cn(
        'flex items-center space-x-3 p-4 rounded-lg border',
        getStageColor()
      )}>
        {getStageIcon()}
        <div className="flex-1">
          <div className="font-medium">{getStageMessage()}</div>
          {totalSteps > 1 && (
            <div className="text-sm opacity-75">
              Step {currentStep} of {totalSteps}
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      {totalSteps > 1 && (
        <div className="w-full">
          <div className="flex justify-between text-sm mb-1">
            <span>Progress</span>
            <span>{Math.round(progressPercentage)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      )}

      {/* Step Indicators */}
      {totalSteps > 1 && (
        <div className="flex justify-between items-center">
          {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => (
            <div
              key={step}
              className={cn(
                'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium',
                step <= currentStep
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-500'
              )}
            >
              {step}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Predefined loading states for common use cases
export const BenchmarkLoadingState: React.FC<{ className?: string }> = ({ className }) => (
  <ExecutionState 
    stage="executing"
    currentStep={2}
    totalSteps={4}
    message="Executing quantum benchmark..."
    className={className}
  />
);

export const QueueLoadingState: React.FC<{ position?: number; total?: number; className?: string }> = ({ 
  position = 1, 
  total = 10, 
  className 
}) => (
  <div className={cn('space-y-2', className)}>
    <LoadingState type="dots" message={`Position ${position} of ${total} in queue`} />
    <ProgressState value={position} max={total} label="Queue Progress" />
  </div>
);

export const ValidationLoadingState: React.FC<{ className?: string }> = ({ className }) => (
  <ExecutionState 
    stage="validating"
    currentStep={1}
    totalSteps={3}
    message="Validating request and quotas..."
    className={className}
  />
);

export const CompletionLoadingState: React.FC<{ className?: string }> = ({ className }) => (
  <ExecutionState 
    stage="completing"
    currentStep={4}
    totalSteps={4}
    message="Finalizing execution results..."
    className={className}
  />
);

export const ErrorState: React.FC<{ error?: string; className?: string }> = ({ 
  error = "An error occurred", 
  className 
}) => (
  <StatusState 
    status="error" 
    message={error}
    className={className}
  />
);

export const SuccessState: React.FC<{ message?: string; className?: string }> = ({ 
  message = "Operation completed successfully", 
  className 
}) => (
  <StatusState 
    status="success" 
    message={message}
    className={className}
  />
);

// Empty state component
export const EmptyState: React.FC<{
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}> = ({ icon, title, description, action, className }) => {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {icon && (
        <div className="mb-4 text-gray-400">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-medium text-gray-900 mb-2">{title}</h3>
      {description && (
        <p className="text-gray-600 mb-6 max-w-md">{description}</p>
      )}
      {action && (
        <div>
          {action}
        </div>
      )}
    </div>
  );
};
