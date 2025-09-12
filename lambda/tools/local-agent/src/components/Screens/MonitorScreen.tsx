import { invoke } from '@tauri-apps/api/tauri';
import { ListenStatus } from '../../App';

interface MonitorScreenProps {
  listenStatus: ListenStatus;
  setListenStatus: (status: ListenStatus) => void;
  isPolling: boolean;
  setIsPolling: (polling: boolean) => void;
  onToggleMinimize: () => void;
  isMinimized: boolean;
}

export default function MonitorScreen({ 
  listenStatus, 
  setListenStatus, 
  isPolling, 
  setIsPolling,
  onToggleMinimize,
  isMinimized 
}: MonitorScreenProps) {

  const handleStart = async () => {
    try {
      await invoke('start_polling');
      setIsPolling(true);
      setListenStatus('listening');
    } catch (error) {
      console.error('Failed to start polling:', error);
    }
  };

  const handleStop = async () => {
    try {
      await invoke('stop_polling');
      setIsPolling(false);
      setListenStatus('idle');
    } catch (error) {
      console.error('Failed to stop polling:', error);
    }
  };


  const getStatusColor = () => {
    switch (listenStatus) {
      case 'idle': return 'text-gray-500';
      case 'listening': return 'text-blue-500';
      case 'executing': return 'text-green-500';
    }
  };

  const getStatusIcon = () => {
    switch (listenStatus) {
      case 'idle': return '⏸️';
      case 'listening': return '👂';
      case 'executing': return '⚡';
    }
  };

  const getStatusText = () => {
    switch (listenStatus) {
      case 'idle': return 'Idle';
      case 'listening': return 'Listening for tasks...';
      case 'executing': return 'Executing script';
    }
  };

  // Compact mode UI - minimal with icon and button side by side
  if (isMinimized) {
    return (
      <div className="p-4 h-full flex flex-col items-center justify-center">
        {/* Icon and Button side by side */}
        <div className="flex items-center gap-4 mb-4">
          {/* Status Icon */}
          <div className={`text-5xl ${getStatusColor()}`}>
            {getStatusIcon()}
          </div>
          
          {/* Control Button - icon only */}
          {!isPolling ? (
            <button
              onClick={handleStart}
              className="w-14 h-14 bg-green-500 text-white rounded-full hover:bg-green-600 flex items-center justify-center text-xl shadow-lg transition-all hover:scale-105"
              title="Start Listening"
            >
              ▶️
            </button>
          ) : (
            <button
              onClick={handleStop}
              className="w-14 h-14 bg-red-500 text-white rounded-full hover:bg-red-600 flex items-center justify-center text-xl shadow-lg transition-all hover:scale-105"
              title="Stop Listening"
            >
              ⏹️
            </button>
          )}
        </div>
        
        {/* Expand Link */}
        <button
          onClick={onToggleMinimize}
          className="text-xs text-gray-500 hover:text-gray-700 underline"
        >
          Expand
        </button>
      </div>
    );
  }

  // Full mode UI - original design
  return (
    <div className="p-6 h-full flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
        {/* Status Display */}
        <div className="mb-8">
          <div className={`text-6xl mb-4 ${getStatusColor()}`}>
            {getStatusIcon()}
          </div>
          <h2 className={`text-2xl font-semibold mb-2 ${getStatusColor()}`}>
            {getStatusText()}
          </h2>
          <p className="text-gray-400 text-sm">
            {listenStatus === 'idle' && 'Ready to listen for Step Functions activities'}
            {listenStatus === 'listening' && 'Polling for new automation tasks'}
            {listenStatus === 'executing' && 'Running automation script'}
          </p>
        </div>

        {/* Controls */}
        <div className="space-y-4">
          <div className="flex gap-4 justify-center">
            {!isPolling ? (
              <button
                onClick={handleStart}
                className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 font-medium flex items-center gap-2"
              >
                ▶️ Start Listening
              </button>
            ) : (
              <button
                onClick={handleStop}
                className="px-6 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 font-medium flex items-center gap-2"
              >
                ⏹️ Stop Listening
              </button>
            )}
          </div>

          {/* Secondary Actions */}
          <div className="flex gap-2 justify-center text-sm">
            <button
              onClick={onToggleMinimize}
              className="px-3 py-1 text-gray-500 hover:text-gray-700 underline"
            >
              Compact Mode
            </button>
          </div>
        </div>

        {/* Quick Status Indicator */}
        <div className="mt-8 pt-6 border-t border-gray-100">
          <div className="flex items-center justify-center gap-2 text-sm">
            <div className={`w-2 h-2 rounded-full ${
              listenStatus === 'idle' ? 'bg-gray-400' :
              listenStatus === 'listening' ? 'bg-blue-400 animate-pulse' :
              'bg-green-400 animate-pulse'
            }`}></div>
            <span className="text-gray-600">Status: {getStatusText()}</span>
          </div>
        </div>
      </div>
    </div>
  );
}