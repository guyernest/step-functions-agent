import { FC } from 'react';

interface SidebarProps {
  activeScreen: string;
  onNavigate: (screen: string) => void;
}

const Sidebar: FC<SidebarProps> = ({ activeScreen, onNavigate }) => {
  const menuItems = [
    { id: 'listen', label: 'Listen', icon: '👂' },
    { id: 'config', label: 'Configuration', icon: '⚙️' },
    { id: 'test', label: 'Test Scripts', icon: '🧪' },
    { id: 'logs', label: 'Logs', icon: '📝' },
  ];

  return (
    <aside className="w-64 bg-gray-800 text-white flex flex-col">
      <div className="p-4 flex-1">
        <h1 className="text-xl font-bold mb-8">🤖 Local Agent</h1>
        <nav>
          <ul className="space-y-2">
            {menuItems.map(item => (
              <li key={item.id}>
                <button
                  onClick={() => onNavigate(item.id)}
                  className={`w-full text-left px-4 py-2 rounded transition-colors ${
                    activeScreen === item.id
                      ? 'bg-blue-600 text-white'
                      : 'hover:bg-gray-700'
                  }`}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </div>
      
      {/* Version info at bottom */}
      <div className="p-4 text-xs text-gray-400">
        <div className="border-t border-gray-700 pt-4">
          <p>Version 0.2.0</p>
          <p>© 2024 Step Functions Agent</p>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;