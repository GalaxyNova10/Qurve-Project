import { Component, type ErrorInfo, type ReactNode } from 'react';
import { ServerCrash, RefreshCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  errorMsg: string;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    errorMsg: ''
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, errorMsg: error.message };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-terminal-bg flex items-center justify-center p-4">
          <div className="max-w-md w-full bg-terminal-card border border-red-500/30 rounded-lg p-6 shadow-2xl relative overflow-hidden">
            {/* Ambient red glow */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 via-red-600 to-red-500" />
            
            <div className="flex flex-col items-center text-center space-y-6">
              <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center">
                <ServerCrash className="w-8 h-8 text-red-500 animate-pulse" />
              </div>
              
              <div className="space-y-2">
                <h1 className="text-xl font-bold text-white tracking-wide">
                  Connection to Quantitative Engine Lost
                </h1>
                <p className="text-sm text-terminal-muted">
                  The backend FastAPI server is currently unreachable. Please ensure the server is running on port 8000 and try again.
                </p>
              </div>

              <div className="w-full bg-black/40 border border-terminal-border rounded p-3 font-mono text-xs text-red-400 text-left overflow-x-auto">
                <p className="opacity-70">ERR_CONNECTION_REFUSED</p>
                <p className="mt-1">{this.state.errorMsg}</p>
              </div>

              <Button 
                onClick={() => window.location.reload()}
                className="w-full bg-terminal-accent hover:bg-terminal-accent/90 text-black font-semibold tracking-wide"
              >
                <RefreshCcw className="w-4 h-4 mr-2" />
                Reconnect Engine
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
