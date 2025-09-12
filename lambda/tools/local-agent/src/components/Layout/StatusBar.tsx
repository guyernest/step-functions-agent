import { ListenStatus } from '../../App';

interface StatusBarProps {
  listenStatus: ListenStatus;
}

export default function StatusBar({ listenStatus }: StatusBarProps) {

  const getListenStatusText = () => {
    switch (listenStatus) {
      case 'idle': return 'Idle';
      case 'listening': return 'Listening';
      case 'executing': return 'Executing';
    }
  };

  const getListenStatusColor = () => {
    switch (listenStatus) {
      case 'idle': return 'bg-gray-400';
      case 'listening': return 'bg-blue-400';
      case 'executing': return 'bg-green-400';
    }
  };

  return (
    <div className="h-8 bg-gray-100 border-t border-gray-300 px-4 flex items-center justify-between text-xs">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1">
          <span className={`w-2 h-2 rounded-full ${getListenStatusColor()}`} />
          {getListenStatusText()}
        </span>
        <span className="text-gray-600">|</span>
        <span>Worker: local-agent</span>
        <span className="text-gray-600">|</span>
        <span>Profile: default</span>
      </div>
    </div>
  );
}