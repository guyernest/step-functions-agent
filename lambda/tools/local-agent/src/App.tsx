import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';
import { appWindow, LogicalSize } from '@tauri-apps/api/window';
import Sidebar from './components/Layout/Sidebar';
import ConfigScreen from './components/Screens/ConfigScreen';
import MonitorScreen from './components/Screens/MonitorScreen';
import TestScreen from './components/Screens/TestScreen';
import LogsScreen from './components/Screens/LogsScreen';
import StatusBar from './components/Layout/StatusBar';

type Screen = 'listen' | 'config' | 'test' | 'logs';

export type ListenStatus = 'idle' | 'listening' | 'executing';

function App() {
  const [activeScreen, setActiveScreen] = useState<Screen>('listen');
  const [isMinimized, setIsMinimized] = useState(false);
  const [listenStatus, setListenStatus] = useState<ListenStatus>('idle');
  const [isPolling, setIsPolling] = useState(false);

  // Check polling status on mount and periodically
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const pollingData = await invoke<any>('get_polling_status');
        const polling = pollingData.isPolling || false;
        setIsPolling(polling);
        setListenStatus(polling ? 'listening' : 'idle');
      } catch (error) {
        setIsPolling(false);
        setListenStatus('idle');
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 2000); // Check every 2 seconds
    return () => clearInterval(interval);
  }, []);

  const handleToggleMinimize = async () => {
    try {
      if (!isMinimized) {
        // Compact mode: collapse sidebar and set smaller default size
        setIsMinimized(true);
        // Set minimum size for compact mode - users can resize even smaller
        await appWindow.setMinSize(new LogicalSize(300, 250));
        await appWindow.setSize(new LogicalSize(400, 320));
        await appWindow.center();
      } else {
        // Restore mode: show sidebar and restore window size
        setIsMinimized(false);
        // Restore normal minimum size
        await appWindow.setMinSize(new LogicalSize(800, 600));
        await appWindow.setSize(new LogicalSize(1024, 768));
        await appWindow.center();
      }
    } catch (error) {
      console.error('Failed to toggle minimize:', error);
    }
  };

  const renderScreen = () => {
    switch (activeScreen) {
      case 'listen':
        return <MonitorScreen 
          listenStatus={listenStatus}
          setListenStatus={setListenStatus}
          isPolling={isPolling}
          setIsPolling={setIsPolling}
          onToggleMinimize={handleToggleMinimize}
          isMinimized={isMinimized}
        />;
      case 'config':
        return <ConfigScreen />;
      case 'test':
        return <TestScreen />;
      case 'logs':
        return <LogsScreen />;
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="flex flex-1 overflow-hidden">
        {!isMinimized && (
          <Sidebar activeScreen={activeScreen} onNavigate={setActiveScreen} />
        )}
        <main className="flex-1 overflow-auto bg-gray-50">
          {renderScreen()}
        </main>
      </div>
      <StatusBar listenStatus={listenStatus} />
    </div>
  );
}

export default App;