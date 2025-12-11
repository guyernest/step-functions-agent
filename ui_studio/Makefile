# Navigation Studio - Main Makefile
# Coordinates frontend (Tauri) and backend (Python/FastAPI)

.PHONY: setup dev dev-frontend dev-backend build clean help

# Default target
all: setup

# Setup both frontend and backend
setup: setup-frontend setup-backend

setup-frontend:
	cd frontend && npm install

setup-backend:
	cd backend && make setup

# Development mode - run both frontend and backend
# Run in separate terminals or use tmux/screen
dev:
	@echo "Starting Navigation Studio in development mode..."
	@echo "Run these commands in separate terminals:"
	@echo ""
	@echo "  Terminal 1 (Backend):  cd backend && make dev"
	@echo "  Terminal 2 (Frontend): cd frontend && npm run tauri:dev"
	@echo ""
	@echo "Or use: make dev-all (requires tmux)"

# Run backend only
dev-backend:
	cd backend && make dev

# Run frontend only
dev-frontend:
	cd frontend && npm run tauri:dev

# Run both with tmux (if available)
dev-all:
	@command -v tmux >/dev/null 2>&1 || { echo "tmux not installed. Run dev-backend and dev-frontend in separate terminals."; exit 1; }
	tmux new-session -d -s navstudio 'cd backend && make dev'
	tmux split-window -h 'cd frontend && npm run tauri:dev'
	tmux attach-session -t navstudio

# Build production
build: build-frontend

build-frontend:
	cd frontend && npm run tauri:build

# Clean everything
clean: clean-frontend clean-backend

clean-frontend:
	cd frontend && rm -rf node_modules dist src-tauri/target

clean-backend:
	cd backend && make clean

# Test
test: test-backend

test-backend:
	cd backend && make test

# Help
help:
	@echo "Navigation Studio"
	@echo ""
	@echo "A desktop tool for creating browser automation scripts"
	@echo ""
	@echo "Setup:"
	@echo "  make setup          - Install all dependencies"
	@echo "  make setup-frontend - Install frontend dependencies"
	@echo "  make setup-backend  - Install backend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev            - Show instructions for dev mode"
	@echo "  make dev-frontend   - Run Tauri frontend only"
	@echo "  make dev-backend    - Run Python backend only"
	@echo "  make dev-all        - Run both (requires tmux)"
	@echo ""
	@echo "Build:"
	@echo "  make build          - Build production Tauri app"
	@echo ""
	@echo "Other:"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Remove build artifacts"
