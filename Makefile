.PHONY: help db-init db-reset db-status db-migrate db-shell generate-types clean test

# Default target
help:
	@echo "SQL AI Agent - Database Management Commands"
	@echo ""
	@echo "Usage:"
	@echo "  make db-init          Initialize database with migrations and default users"
	@echo "  make db-init-clean    Initialize database without default users"
	@echo "  make db-reset         Reset database (WARNING: deletes all data)"
	@echo "  make db-status        Show migration status"
	@echo "  make db-migrate       Run pending migrations"
	@echo "  make db-dry-run       Preview pending migrations without running"
	@echo "  make db-shell         Open SQLite shell"
	@echo "  make generate-types   Generate TypeScript types from database schema"
	@echo "  make clean            Clean generated files"
	@echo "  make test             Run tests"
	@echo ""

# Initialize database with default users
db-init:
	@echo "Initializing database..."
	python3 scripts/init_db.py

# Initialize database without default users
db-init-clean:
	@echo "Initializing database (no default users)..."
	python3 scripts/init_db.py --no-defaults

# Reset database (with confirmation)
db-reset:
	@echo "Resetting database..."
	python3 scripts/init_db.py --reset

# Show migration status
db-status:
	@echo "Checking migration status..."
	python3 backend/app/migrations_runner.py status

# Run pending migrations
db-migrate:
	@echo "Running migrations..."
	python3 backend/app/migrations_runner.py

# Preview pending migrations
db-dry-run:
	@echo "Previewing migrations..."
	python3 backend/app/migrations_runner.py dry-run

# Open SQLite shell
db-shell:
	@echo "Opening database shell..."
	@if [ -f data/app_data/app.db ]; then \
		sqlite3 data/app_data/app.db; \
	else \
		echo "Database does not exist. Run 'make db-init' first."; \
	fi

# Generate TypeScript types from database schema
generate-types:
	@echo "Generating TypeScript types from database schema..."
	python3 scripts/generate_types.py

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete"

# Run tests
test:
	@echo "Running tests..."
	pytest tests/ -v

# Development setup
setup-dev:
	@echo "Setting up development environment..."
	pip install -r requirements.txt
	make db-init
	@echo "Development setup complete"