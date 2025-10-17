# Local Browser Agent - Build Guide

## Development vs Production

### Development Mode (with hot reload)

Run the application in development mode with hot reload:

```bash
cd /Users/guy/projects/step-functions-agent/lambda/tools/local-browser-agent

# Start the dev server
cd src-tauri
cargo tauri dev
```

This will:
- Start Vite dev server on port 3030 (with hot reload for UI changes)
- Start the Tauri Rust application
- Automatically reload when you make changes to TypeScript/React files

**Note**: The Vite config now ignores `browser-profiles/` to prevent rebuild loops when browser sessions are created/updated.

---

## Production Build (Binary)

### Building the Application Binary

To build a production-ready binary that doesn't require the dev server:

```bash
cd /Users/guy/projects/step-functions-agent/lambda/tools/local-browser-agent

# Build the production binary
cd src-tauri
cargo tauri build
```

This will:
1. Build the React/TypeScript UI in production mode (minified, optimized)
2. Compile the Rust backend
3. Package everything into a native application binary

### Build Output Locations

After building, the binary will be located at:

**macOS:**
- Application bundle: `src-tauri/target/release/bundle/macos/Local Browser Agent.app`
- DMG installer: `src-tauri/target/release/bundle/dmg/Local Browser Agent_0.1.0_x64.dmg`
- Executable: `src-tauri/target/release/local-browser-agent`

**Linux:**
- AppImage: `src-tauri/target/release/bundle/appimage/local-browser-agent_0.1.0_amd64.AppImage`
- Deb package: `src-tauri/target/release/bundle/deb/local-browser-agent_0.1.0_amd64.deb`
- Executable: `src-tauri/target/release/local-browser-agent`

**Windows:**
- MSI installer: `src-tauri/target/release/bundle/msi/Local Browser Agent_0.1.0_x64_en-US.msi`
- Executable: `src-tauri/target/release/local-browser-agent.exe`

### Running the Production Binary

**macOS:**
```bash
# Run from build output
./src-tauri/target/release/local-browser-agent

# Or open the app bundle
open "src-tauri/target/release/bundle/macos/Local Browser Agent.app"
```

**Linux:**
```bash
./src-tauri/target/release/local-browser-agent
```

**Windows:**
```powershell
.\src-tauri\target\release\local-browser-agent.exe
```

---

## Quick Build Commands

### Just build (no run)
```bash
cd src-tauri
cargo tauri build --no-bundle  # Faster, just creates executable
```

### Build with debug symbols
```bash
cd src-tauri
TAURI_DEBUG=1 cargo tauri build
```

### Clean build (if you have issues)
```bash
cd src-tauri
cargo clean
cd ../ui
rm -rf node_modules dist
npm install
cd ../src-tauri
cargo tauri build
```

---

## Troubleshooting

### Issue: UI keeps rebuilding in dev mode

**Cause**: Vite was watching the `browser-profiles/` directory and triggering rebuilds when Nova Act created/updated browser sessions.

**Fix**: The `ui/vite.config.ts` has been updated to ignore the `browser-profiles/` directory. Restart the dev server:
```bash
# Kill the current dev process (Ctrl+C)
# Then restart
cd src-tauri
cargo tauri dev
```

### Issue: Build fails with missing dependencies

**Fix**: Install dependencies:
```bash
# Install UI dependencies
cd ui
npm install

# Update Rust dependencies
cd ../src-tauri
cargo update
```

### Issue: Binary won't run on other machines (macOS)

**Cause**: Code signing or notarization required for distribution.

**Fix**: For local use, allow the app in System Preferences > Security & Privacy. For distribution, you'll need to sign and notarize with an Apple Developer certificate.

---

## Distribution

To distribute the application:

1. **macOS**: Share the `.dmg` file from `bundle/dmg/`
2. **Linux**: Share the `.AppImage` or `.deb` file from `bundle/appimage/` or `bundle/deb/`
3. **Windows**: Share the `.msi` installer from `bundle/msi/`

Users can install these packages without needing any development tools.

---

## Development Tips

### Fast iteration during development
- Use `cargo tauri dev` for frontend changes (hot reload)
- For Rust backend changes, restart with `cargo tauri dev`
- For profile management testing, use the UI's Profiles tab

### Testing production build locally
```bash
# Build
cd src-tauri
cargo tauri build

# Run the binary
./target/release/local-browser-agent
```

### Checking build size
```bash
ls -lh src-tauri/target/release/local-browser-agent
ls -lh src-tauri/target/release/bundle/dmg/*.dmg
```

---

## Related Files

- `ui/vite.config.ts` - Vite configuration (including watch ignore patterns)
- `src-tauri/tauri.conf.json` - Tauri configuration
- `src-tauri/Cargo.toml` - Rust dependencies
- `ui/package.json` - Node dependencies
- `.gitignore` - Excludes browser-profiles from version control
