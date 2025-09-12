import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/tauri';

interface Config {
  activity_arn: string;
  profile_name: string;
  worker_name: string;
  poll_interval_ms: number;
}

export default function ConfigScreen() {
  const [config, setConfig] = useState<Config>({
    activity_arn: '',
    profile_name: 'default',
    worker_name: 'local-agent-worker',
    poll_interval_ms: 5000,
  });
  const [profiles, setProfiles] = useState<string[]>(['default']);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  useEffect(() => {
    loadConfig();
    loadProfiles();
  }, []);

  const loadConfig = async () => {
    try {
      const loaded = await invoke<Config>('load_config');
      setConfig(loaded);
    } catch (error) {
      console.error('Failed to load config:', error);
      // Use default config if loading fails
    }
  };

  const loadProfiles = async () => {
    try {
      const profileList = await invoke<string[]>('list_aws_profiles');
      if (profileList.length > 0) {
        setProfiles(profileList);
      }
    } catch (error) {
      console.error('Failed to load profiles:', error);
      // Keep default profile
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    try {
      await invoke('save_config', { config });
      setTestResult({ success: true, message: 'Configuration saved successfully!' });
    } catch (error) {
      console.error('Failed to save config:', error);
      setTestResult({ success: false, message: `Failed to save: ${error}` });
    } finally {
      setSaving(false);
      setTimeout(() => setTestResult(null), 3000);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await invoke<boolean>('test_connection', { config });
      setTestResult({
        success: result,
        message: result ? 'Connection successful!' : 'Connection failed. Check your settings.',
      });
    } catch (error) {
      console.error('Connection test failed:', error);
      setTestResult({ success: false, message: `Connection test failed: ${error}` });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="p-6">
      <h2 className="text-2xl font-bold mb-6">Configuration</h2>
      
      <div className="space-y-4 max-w-2xl">
        <div>
          <label className="block text-sm font-medium mb-1">AWS Profile</label>
          <select 
            className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={config.profile_name}
            onChange={(e) => setConfig({...config, profile_name: e.target.value})}
          >
            {profiles.map(p => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Activity ARN</label>
          <input
            type="text"
            className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={config.activity_arn}
            onChange={(e) => setConfig({...config, activity_arn: e.target.value})}
            placeholder="arn:aws:states:region:account:activity:name"
          />
          <p className="text-xs text-gray-500 mt-1">
            The ARN of the Step Functions Activity to poll for tasks
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Worker Name</label>
          <input
            type="text"
            className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={config.worker_name}
            onChange={(e) => setConfig({...config, worker_name: e.target.value})}
          />
          <p className="text-xs text-gray-500 mt-1">
            A unique name to identify this worker instance
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Poll Interval (ms)</label>
          <input
            type="number"
            className="w-full p-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={config.poll_interval_ms}
            onChange={(e) => setConfig({...config, poll_interval_ms: parseInt(e.target.value) || 5000})}
            min="1000"
            max="60000"
          />
          <p className="text-xs text-gray-500 mt-1">
            How often to check for new tasks (1000-60000 ms)
          </p>
        </div>

        {testResult && (
          <div className={`p-3 rounded ${testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {testResult.success ? '✅' : '❌'} {testResult.message}
          </div>
        )}

        <div className="flex gap-4 pt-4">
          <button
            onClick={saveConfig}
            disabled={saving}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Configuration'}
          </button>
          <button
            onClick={testConnection}
            disabled={testing || !config.activity_arn}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
        </div>
      </div>
    </div>
  );
}