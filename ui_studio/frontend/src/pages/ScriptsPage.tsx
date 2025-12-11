export default function ScriptsPage() {
  // Placeholder scripts for demo
  const scripts = [
    { id: '1', name: 'BT Broadband Checker', version: '2.0.0', steps: 15, lastRun: '2024-01-15' },
    { id: '2', name: 'Login Flow Test', version: '1.0.0', steps: 5, lastRun: '2024-01-14' },
  ]

  return (
    <div className="p-4 h-full">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold text-white">Scripts</h1>
        <button className="btn btn-primary">New Script</button>
      </div>

      <div className="panel">
        <table className="w-full">
          <thead>
            <tr className="border-b border-studio-accent/30 text-left text-sm text-gray-400">
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Version</th>
              <th className="px-4 py-3">Steps</th>
              <th className="px-4 py-3">Last Run</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          <tbody>
            {scripts.map((script) => (
              <tr key={script.id} className="border-b border-studio-accent/20 hover:bg-studio-accent/10">
                <td className="px-4 py-3 text-white">{script.name}</td>
                <td className="px-4 py-3 text-gray-400">{script.version}</td>
                <td className="px-4 py-3 text-gray-400">{script.steps}</td>
                <td className="px-4 py-3 text-gray-400">{script.lastRun}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button className="text-sm text-studio-highlight hover:underline">Edit</button>
                    <button className="text-sm text-gray-400 hover:text-white">Run</button>
                    <button className="text-sm text-gray-400 hover:text-red-400">Delete</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
