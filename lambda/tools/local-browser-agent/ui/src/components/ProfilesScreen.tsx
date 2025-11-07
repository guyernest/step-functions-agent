import { useState, useEffect } from 'react'
import { invoke } from '@tauri-apps/api/tauri'

interface Profile {
  name: string
  description: string
  tags: string[]
  auto_login_sites: string[]
  user_data_dir: string
  created_at: string
  last_used: string | null
  usage_count: number
  requires_human_login: boolean
  login_notes: string
  session_timeout_hours: number
}

interface ProfileListResponse {
  profiles: Profile[]
  total_count: number
}

export default function ProfilesScreen() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [showLoginDialog, setShowLoginDialog] = useState(false)
  const [filterTag, setFilterTag] = useState<string>('')
  const [showValidateDialog, setShowValidateDialog] = useState(false)
  const [validationResult, setValidationResult] = useState<any | null>(null)
  const [validating, setValidating] = useState(false)
  const [showEditTagsDialog, setShowEditTagsDialog] = useState(false)
  const [editingTags, setEditingTags] = useState<string>('')

  // Validation form state
  const [validation, setValidation] = useState({
    mode: 'static', // 'static' | 'runtime' | 'both'
    starting_page: '',
    ui_prompt: 'Return true if the page shows the user is logged in.',
    cookie_domains: '', // comma-separated
    cookie_names: '',   // comma-separated
    local_storage_keys: '', // comma-separated
    clone_user_data_dir: false,
  })

  // Create profile form state
  const [newProfile, setNewProfile] = useState({
    name: '',
    description: '',
    tags: '',
    auto_login_sites: '',
    session_timeout_hours: 24
  })

  // Login setup state
  const [loginSetup, setLoginSetup] = useState({
    profile_name: '',
    starting_url: ''
  })

  useEffect(() => {
    loadProfiles()
  }, [filterTag])

  const loadProfiles = async () => {
    setLoading(true)
    try {
      const result = await invoke<ProfileListResponse>('list_profiles', {
        tags: filterTag ? [filterTag] : null
      })
      setProfiles(result.profiles)
    } catch (error) {
      console.error('Failed to load profiles:', error)
      setProfiles([])
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProfile = async () => {
    try {
      await invoke('create_profile', {
        profileName: newProfile.name,
        description: newProfile.description,
        tags: newProfile.tags.split(',').map(t => t.trim()).filter(t => t),
        autoLoginSites: newProfile.auto_login_sites.split('\n').map(s => s.trim()).filter(s => s),
        sessionTimeoutHours: newProfile.session_timeout_hours
      })

      // Reset form
      setNewProfile({
        name: '',
        description: '',
        tags: '',
        auto_login_sites: '',
        session_timeout_hours: 24
      })
      setShowCreateDialog(false)

      // Reload profiles
      await loadProfiles()
    } catch (error) {
      alert(`Failed to create profile: ${error}`)
    }
  }

  const handleDeleteProfile = async (profileName: string) => {
    if (!confirm(`Are you sure you want to delete profile "${profileName}"?`)) {
      return
    }

    try {
      await invoke('delete_profile', {
        profileName,
        keepData: false
      })

      if (selectedProfile?.name === profileName) {
        setSelectedProfile(null)
      }

      await loadProfiles()
    } catch (error) {
      alert(`Failed to delete profile: ${error}`)
    }
  }

  const handleOpenEditTags = () => {
    if (selectedProfile) {
      setEditingTags(selectedProfile.tags.join(', '))
      setShowEditTagsDialog(true)
    }
  }

  const handleUpdateTags = async () => {
    if (!selectedProfile) return

    try {
      const tags = editingTags.split(',').map(t => t.trim()).filter(t => t)

      await invoke('update_profile_tags', {
        profileName: selectedProfile.name,
        tags
      })

      // Update the selected profile in state
      const updatedProfile = { ...selectedProfile, tags }
      setSelectedProfile(updatedProfile)

      // Close dialog and reload profiles
      setShowEditTagsDialog(false)
      await loadProfiles()
    } catch (error) {
      alert(`Failed to update tags: ${error}`)
    }
  }

  const handleSetupLogin = async () => {
    try {
      setShowLoginDialog(false)

      // This will open a browser window for the user to log in
      await invoke('setup_profile_login', {
        profileName: loginSetup.profile_name,
        startingUrl: loginSetup.starting_url
      })

      alert(`Login setup completed for profile "${loginSetup.profile_name}"`)

      // Reset and reload
      setLoginSetup({ profile_name: '', starting_url: '' })
      await loadProfiles()
    } catch (error) {
      alert(`Failed to setup login: ${error}`)
    }
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    return date.toLocaleString()
  }

  const getProfileStatus = (profile: Profile): { text: string, color: string } => {
    if (!profile.last_used) {
      return { text: 'Never Used', color: 'text-gray-500' }
    }

    const lastUsed = new Date(profile.last_used)
    const now = new Date()
    const hoursSinceUse = (now.getTime() - lastUsed.getTime()) / (1000 * 60 * 60)

    if (hoursSinceUse < profile.session_timeout_hours) {
      return { text: 'Active', color: 'text-green-600' }
    } else if (hoursSinceUse < profile.session_timeout_hours * 2) {
      return { text: 'Expired', color: 'text-orange-500' }
    } else {
      return { text: 'Stale', color: 'text-red-500' }
    }
  }

  const allTags = Array.from(new Set(profiles.flatMap(p => p.tags)))

  return (
    <div className="screen-container">
      <div className="screen-header">
        <h2>Browser Profiles</h2>
        <p className="screen-description">
          Manage browser profiles for persistent sessions and authentication
        </p>
      </div>

      {/* Action Bar */}
      <div className="card">
        <div className="button-group">
          <button onClick={() => setShowCreateDialog(true)} className="btn-primary">
            ➕ Create Profile
          </button>
          <button onClick={() => setShowLoginDialog(true)} className="btn-success">
            🔐 Setup Login
          </button>
          <button onClick={() => setShowValidateDialog(true)} className="btn-secondary" disabled={!selectedProfile}>
            ✅ Validate Profile
          </button>
          <button onClick={loadProfiles} className="btn-secondary">
            🔄 Refresh
          </button>
        </div>

        {/* Filter by tags */}
        {allTags.length > 0 && (
          <div style={{ marginTop: '1rem' }}>
            <label style={{ marginRight: '0.5rem' }}>Filter by tag:</label>
            <select
              value={filterTag}
              onChange={(e) => setFilterTag(e.target.value)}
              className="select-input"
            >
              <option value="">All Profiles</option>
              {allTags.map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Profiles Grid */}
      <div className="profiles-grid">
        {/* Profiles List */}
        <div className="card">
          <h3>Profiles ({profiles.length})</h3>

          {loading ? (
            <p className="empty-state">Loading profiles...</p>
          ) : profiles.length === 0 ? (
            <div className="empty-state">
              <p>No profiles yet</p>
              <p style={{ fontSize: '0.9rem', marginTop: '0.5rem' }}>
                Create a profile to get started with persistent browser sessions
              </p>
            </div>
          ) : (
            <div className="profiles-list">
              {profiles.map(profile => {
                const status = getProfileStatus(profile)
                return (
                  <div
                    key={profile.name}
                    className={`profile-card ${selectedProfile?.name === profile.name ? 'selected' : ''}`}
                    onClick={() => setSelectedProfile(profile)}
                  >
                    <div className="profile-header">
                      <h4>{profile.name}</h4>
                      <span className={`profile-status ${status.color}`}>
                        {status.text}
                      </span>
                    </div>
                    <p className="profile-description">{profile.description || 'No description'}</p>
                    <div className="profile-tags">
                      {profile.tags.map(tag => (
                        <span key={tag} className="tag">{tag}</span>
                      ))}
                    </div>
                    <div className="profile-meta">
                      <span>Used {profile.usage_count} times</span>
                      {profile.last_used && (
                        <span>Last: {new Date(profile.last_used).toLocaleDateString()}</span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Profile Details */}
        <div className="card">
          <h3>Profile Details</h3>

          {selectedProfile ? (
            <div className="profile-details">
              <div className="detail-section">
                <h4>{selectedProfile.name}</h4>
                <p>{selectedProfile.description}</p>
              </div>

              <div className="detail-section">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <label style={{ margin: 0 }}>Tags</label>
                  <button
                    onClick={handleOpenEditTags}
                    className="btn-secondary"
                    style={{ padding: '0.25rem 0.75rem', fontSize: '0.875rem' }}
                  >
                    ✏️ Edit Tags
                  </button>
                </div>
                <div className="profile-tags">
                  {selectedProfile.tags.length > 0 ? (
                    selectedProfile.tags.map(tag => (
                      <span key={tag} className="tag">{tag}</span>
                    ))
                  ) : (
                    <span className="text-muted">No tags</span>
                  )}
                </div>
              </div>

              <div className="detail-section">
                <label>Auto-Login Sites</label>
                {selectedProfile.auto_login_sites.length > 0 ? (
                  <ul className="site-list">
                    {selectedProfile.auto_login_sites.map(site => (
                      <li key={site}>{site}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-muted">No auto-login sites configured</p>
                )}
              </div>

              <div className="detail-section">
                <label>Session Configuration</label>
                <div className="detail-row">
                  <span>Timeout:</span>
                  <span>{selectedProfile.session_timeout_hours} hours</span>
                </div>
                <div className="detail-row">
                  <span>Requires Human Login:</span>
                  <span>{selectedProfile.requires_human_login ? 'Yes' : 'No'}</span>
                </div>
              </div>

              <div className="detail-section">
                <label>Usage Statistics</label>
                <div className="detail-row">
                  <span>Created:</span>
                  <span>{formatDate(selectedProfile.created_at)}</span>
                </div>
                <div className="detail-row">
                  <span>Last Used:</span>
                  <span>{formatDate(selectedProfile.last_used)}</span>
                </div>
                <div className="detail-row">
                  <span>Total Uses:</span>
                  <span>{selectedProfile.usage_count}</span>
                </div>
              </div>

              {selectedProfile.login_notes && (
                <div className="detail-section">
                  <label>Login Notes</label>
                  <p className="login-notes">{selectedProfile.login_notes}</p>
                </div>
              )}

              <div className="detail-section">
                <label>Profile Directory</label>
                <code className="path-display">{selectedProfile.user_data_dir}</code>
              </div>

              <div className="profile-actions">
                <button
                  onClick={() => handleDeleteProfile(selectedProfile.name)}
                  className="btn-danger"
                >
                  🗑️ Delete Profile
                </button>
              </div>
            </div>
          ) : (
            <p className="empty-state">Select a profile to view details</p>
          )}
        </div>
      </div>

      {/* Create Profile Dialog */}
      {showCreateDialog && (
        <div className="dialog-overlay" onClick={() => setShowCreateDialog(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Create New Profile</h3>

            <div className="form-group">
              <label>Profile Name *</label>
              <input
                type="text"
                value={newProfile.name}
                onChange={(e) => setNewProfile({ ...newProfile, name: e.target.value })}
                placeholder="e.g., banking_profile"
              />
            </div>

            <div className="form-group">
              <label>Description</label>
              <input
                type="text"
                value={newProfile.description}
                onChange={(e) => setNewProfile({ ...newProfile, description: e.target.value })}
                placeholder="What is this profile for?"
              />
            </div>

            <div className="form-group">
              <label>Tags (comma-separated)</label>
              <input
                type="text"
                value={newProfile.tags}
                onChange={(e) => setNewProfile({ ...newProfile, tags: e.target.value })}
                placeholder="e.g., production, authenticated"
              />
            </div>

            <div className="form-group">
              <label>Auto-Login Sites (one per line)</label>
              <textarea
                value={newProfile.auto_login_sites}
                onChange={(e) => setNewProfile({ ...newProfile, auto_login_sites: e.target.value })}
                placeholder="https://example.com&#10;https://app.example.com"
                rows={3}
              />
            </div>

            <div className="form-group">
              <label>Session Timeout (hours)</label>
              <input
                type="number"
                value={newProfile.session_timeout_hours}
                onChange={(e) => setNewProfile({ ...newProfile, session_timeout_hours: parseInt(e.target.value) })}
                min={1}
                max={168}
              />
            </div>

            <div className="dialog-actions">
              <button onClick={() => setShowCreateDialog(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleCreateProfile}
                className="btn-primary"
                disabled={!newProfile.name}
              >
                Create Profile
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Login Setup Dialog */}
      {showLoginDialog && (
        <div className="dialog-overlay" onClick={() => setShowLoginDialog(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Setup Login for Profile</h3>
            <p className="dialog-description">
              This will open a browser window where you can manually log in.
              The session will be saved for future automation.
            </p>

            <div className="form-group">
              <label>Profile Name *</label>
              <input
                type="text"
                value={loginSetup.profile_name}
                onChange={(e) => setLoginSetup({ ...loginSetup, profile_name: e.target.value })}
                placeholder="e.g., banking_profile"
                list="existing-profiles"
              />
              <datalist id="existing-profiles">
                {profiles.map(p => (
                  <option key={p.name} value={p.name} />
                ))}
              </datalist>
              <span className="form-hint">
                Use an existing profile name to update it, or enter a new name to create one
              </span>
            </div>

            <div className="form-group">
              <label>Login Page URL *</label>
              <input
                type="url"
                value={loginSetup.starting_url}
                onChange={(e) => setLoginSetup({ ...loginSetup, starting_url: e.target.value })}
                placeholder="https://example.com/login"
              />
            </div>

            <div className="alert alert-info">
              <strong>How it works:</strong>
              <ol style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                <li>Browser will open to the login page</li>
                <li>You manually log in (enter credentials, solve CAPTCHA, complete MFA)</li>
                <li>You press a button to continue</li>
                <li>The session is saved in the profile</li>
              </ol>
            </div>

            <div className="dialog-actions">
              <button onClick={() => setShowLoginDialog(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleSetupLogin}
                className="btn-success"
                disabled={!loginSetup.profile_name || !loginSetup.starting_url}
              >
                Start Login Setup
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Validate Profile Dialog */}
      {showValidateDialog && selectedProfile && (
        <div className="dialog-overlay" onClick={() => setShowValidateDialog(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Validate Profile: {selectedProfile.name}</h3>
            <p className="dialog-description">
              Check the profile's folder structure and optionally verify that it is logged-in at runtime.
            </p>

            <div className="form-group">
              <label>Validation Mode</label>
              <select
                value={validation.mode}
                onChange={(e) => setValidation(v => ({ ...v, mode: e.target.value }))}
                className="select-input"
              >
                <option value="static">Static (filesystem only)</option>
                <option value="runtime">Runtime (in-browser)</option>
                <option value="both">Both</option>
              </select>
            </div>

            {(validation.mode === 'runtime' || validation.mode === 'both') && (
              <>
                <div className="form-group">
                  <label>Starting Page (required for runtime)</label>
                  <input
                    type="url"
                    value={validation.starting_page}
                    onChange={(e) => setValidation(v => ({ ...v, starting_page: e.target.value }))}
                    placeholder={selectedProfile.auto_login_sites[0] || 'https://example.com'}
                  />
                </div>

                <div className="form-group">
                  <label>UI Prompt (BOOL)</label>
                  <input
                    type="text"
                    value={validation.ui_prompt}
                    onChange={(e) => setValidation(v => ({ ...v, ui_prompt: e.target.value }))}
                  />
                </div>

                <div className="form-group">
                  <label>Cookie Domains (comma-separated)</label>
                  <input
                    type="text"
                    value={validation.cookie_domains}
                    onChange={(e) => setValidation(v => ({ ...v, cookie_domains: e.target.value }))}
                    placeholder={new URL(selectedProfile.auto_login_sites[0] || 'https://example.com').hostname}
                  />
                </div>

                <div className="form-group">
                  <label>Cookie Names (comma-separated)</label>
                  <input
                    type="text"
                    value={validation.cookie_names}
                    onChange={(e) => setValidation(v => ({ ...v, cookie_names: e.target.value }))}
                    placeholder="session, auth, sid"
                  />
                </div>

                <div className="form-group">
                  <label>localStorage Keys (comma-separated)</label>
                  <input
                    type="text"
                    value={validation.local_storage_keys}
                    onChange={(e) => setValidation(v => ({ ...v, local_storage_keys: e.target.value }))}
                    placeholder="token, id_token, logged_in"
                  />
                </div>

                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={validation.clone_user_data_dir}
                      onChange={(e) => setValidation(v => ({ ...v, clone_user_data_dir: e.target.checked }))}
                    />
                    <span style={{ marginLeft: '0.5rem' }}>Clone profile for validation run (use for isolation)</span>
                  </label>
                </div>
              </>
            )}

            <div className="dialog-actions">
              <button onClick={() => setShowValidateDialog(false)} className="btn-secondary">
                Close
              </button>
              <button
                onClick={async () => {
                  if (!selectedProfile) return
                  setValidating(true)
                  setValidationResult(null)
                  try {
                    const payload: any = {
                      userDataDir: selectedProfile.user_data_dir,
                      mode: validation.mode,
                    }
                    if (validation.mode !== 'static') {
                      if (validation.starting_page) payload.startingPage = validation.starting_page
                      if (validation.ui_prompt) payload.uiPrompt = validation.ui_prompt
                      if (validation.cookie_domains.trim()) payload.cookieDomains = validation.cookie_domains.split(',').map(s => s.trim()).filter(Boolean)
                      if (validation.cookie_names.trim()) payload.cookieNames = validation.cookie_names.split(',').map(s => s.trim()).filter(Boolean)
                      if (validation.local_storage_keys.trim()) payload.localStorageKeys = validation.local_storage_keys.split(',').map(s => s.trim()).filter(Boolean)
                      if (validation.clone_user_data_dir) payload.cloneUserDataDir = true
                    }

                    const res = await invoke<any>('validate_profile', payload)
                    setValidationResult(res)
                  } catch (err: any) {
                    setValidationResult({ success: false, error: String(err) })
                  } finally {
                    setValidating(false)
                  }
                }}
                className="btn-primary"
                disabled={validating || (validation.mode !== 'static' && !validation.starting_page)}
              >
                {validating ? 'Validating…' : 'Run Validation'}
              </button>
            </div>

            {validationResult && (
              <div className="form-group" style={{ maxHeight: '40vh', overflow: 'auto' }}>
                <label>Validation Result</label>
                <pre className="code-block">{JSON.stringify(validationResult, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Edit Tags Dialog */}
      {showEditTagsDialog && selectedProfile && (
        <div className="dialog-overlay" onClick={() => setShowEditTagsDialog(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Tags: {selectedProfile.name}</h3>
            <p className="dialog-description">
              Add or modify tags for this profile. Tags help with automatic profile selection and organization.
            </p>

            <div className="form-group">
              <label>Tags (comma-separated)</label>
              <input
                type="text"
                value={editingTags}
                onChange={(e) => setEditingTags(e.target.value)}
                placeholder="e.g., amazon.com, authenticated, buyer, personal"
              />
              <span className="form-hint">
                Common tag types: domain (amazon.com), auth status (authenticated), permissions (buyer, read-only), purpose (personal, pool)
              </span>
            </div>

            <div className="alert alert-info">
              <strong>Tag Examples:</strong>
              <ul style={{ marginTop: '0.5rem', marginLeft: '1.5rem' }}>
                <li><strong>Domain:</strong> amazon.com, google.com, github.com</li>
                <li><strong>Auth:</strong> authenticated, unauthenticated</li>
                <li><strong>Permission:</strong> buyer, read-only, admin</li>
                <li><strong>Purpose:</strong> personal, pool, testing, production</li>
              </ul>
            </div>

            <div className="dialog-actions">
              <button onClick={() => setShowEditTagsDialog(false)} className="btn-secondary">
                Cancel
              </button>
              <button
                onClick={handleUpdateTags}
                className="btn-primary"
              >
                Save Tags
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
