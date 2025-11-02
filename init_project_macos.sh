#!/bin/bash
# PostgreSQL Backup Manager - macOS Project Initialization Script
# Version: 1.0.0
# Author: Michael BAG <mk@remark.pro>
# Supported: macOS 10.14+ (Mojave and later)

set -e  # Exit on any error

echo "========================================"
echo "PostgreSQL Backup Manager - macOS Setup"
echo "Version: 1.0.0"
echo "Author: Michael BAG <mk@remark.pro>"
echo "========================================"
echo ""

# Detect macOS version
detect_os() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo "ERROR: This script is designed for macOS only"
        exit 1
    fi
    
    OS_VERSION=$(sw_vers -productVersion)
    OS_NAME=$(sw_vers -productName)
    echo "Detected OS: $OS_NAME $OS_VERSION"
    
    # Check minimum version (10.14 Mojave)
    MAJOR_VERSION=$(echo $OS_VERSION | cut -d'.' -f1)
    MINOR_VERSION=$(echo $OS_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR_VERSION" -lt 10 ] || ([ "$MAJOR_VERSION" -eq 10 ] && [ "$MINOR_VERSION" -lt 14 ]); then
        echo "WARNING: macOS 10.14 (Mojave) or later is recommended"
    fi
}

# Check system requirements
check_requirements() {
    echo "[1/7] Checking system requirements..."
    
    # Check Homebrew
    if ! command -v brew &> /dev/null; then
        echo "WARNING: Homebrew is not installed"
        echo "Homebrew is recommended for installing PostgreSQL on macOS"
        echo "Install it from: https://brew.sh"
        echo ""
        read -p "Continue without Homebrew? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo "✓ Homebrew is installed: $(brew --version | head -n1)"
    fi
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python 3 is not installed"
        echo "Please install Python 3.8 or later:"
        echo "  Using Homebrew: brew install python3"
        echo "  Or download from: https://www.python.org/downloads/"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo "✓ Python 3 is installed: $(python3 --version)"
    
    # Check if Python version is 3.7 or later
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
        echo "ERROR: Python 3.7 or later is required (found $PYTHON_VERSION)"
        exit 1
    fi
    
    # Check PostgreSQL client utilities
    if ! command -v pg_dump &> /dev/null; then
        echo "WARNING: PostgreSQL client utilities not found"
        echo "Please install PostgreSQL client:"
        echo "  Using Homebrew: brew install postgresql"
        echo ""
        read -p "Install PostgreSQL client now using Homebrew? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            if command -v brew &> /dev/null; then
                brew install postgresql
                # Add to PATH if needed
                if [[ -d "/opt/homebrew/bin" ]]; then
                    export PATH="/opt/homebrew/bin:$PATH"
                    echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
                    echo "✓ Added Homebrew PostgreSQL to PATH"
                elif [[ -d "/usr/local/bin" ]]; then
                    export PATH="/usr/local/bin:$PATH"
                    echo "✓ Using PostgreSQL from /usr/local/bin"
                fi
            else
                echo "ERROR: Cannot install PostgreSQL without Homebrew"
                exit 1
            fi
        else
            echo "Continuing with setup anyway..."
        fi
    else
        echo "✓ PostgreSQL client utilities are available: $(pg_dump --version)"
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        echo "ERROR: pip3 is not installed"
        echo "Please install pip:"
        echo "  Using Homebrew: brew install python3 (includes pip3)"
        exit 1
    fi
    echo "✓ pip3 is available"
}

# Install system dependencies via Homebrew (optional)
install_system_deps() {
    echo ""
    echo "[2/7] Installing system dependencies..."
    
    if ! command -v brew &> /dev/null; then
        echo "Homebrew not available, skipping system dependency installation"
        return
    fi
    
    read -p "Install/update system dependencies via Homebrew? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Skipping system dependency installation..."
        return
    fi
    
    echo "Updating Homebrew..."
    brew update
    
    # Install PostgreSQL if not installed
    if ! command -v pg_dump &> /dev/null; then
        echo "Installing PostgreSQL client..."
        brew install postgresql
    fi
    
    # Ensure Python 3 is up to date
    echo "Ensuring Python 3 is installed..."
    brew install python3 || brew upgrade python3 || true
    
    echo "✓ System dependencies check completed"
}

# Create virtual environment
create_venv() {
    echo ""
    echo "[3/7] Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        echo "Virtual environment already exists, removing old one..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    echo ""
    echo "[4/7] Activating virtual environment..."
    source venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to activate virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment activated"
}

# Install Python dependencies
install_deps() {
    echo ""
    echo "[5/7] Installing Python dependencies..."
    
    # Upgrade pip, setuptools, and wheel first
    python -m pip install --upgrade pip setuptools wheel
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to upgrade pip, continuing..."
    else
        echo "✓ Pip, setuptools, and wheel upgraded"
    fi
    
    # Check Python version and upgrade psycopg2-binary if needed for Python 3.14+
    PYTHON_MAJOR=$(python -c "import sys; print(sys.version_info.major)")
    PYTHON_MINOR=$(python -c "import sys; print(sys.version_info.minor)")
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 14 ]; then
        echo "Python 3.14+ detected, ensuring psycopg2-binary compatibility..."
        pip install --upgrade 'psycopg2-binary>=2.9.11' || echo "WARNING: Could not upgrade psycopg2-binary"
    fi
    
    # Install requirements
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        echo "Please check requirements.txt and try again"
        exit 1
    fi
    echo "✓ Dependencies installed"
}

# Create project directories
create_dirs() {
    echo ""
    echo "[6/7] Creating project directories..."
    
    mkdir -p logs backups config/databases
    echo "✓ Project directories created"
}

# Set up permissions and test
setup_permissions() {
    echo ""
    echo "[7/7] Setting up permissions and testing..."
    
    # Make scripts executable
    chmod +x src/kma_pg_backup.py 2>/dev/null || true
    chmod +x src/kma_pg_restore.py 2>/dev/null || true
    chmod +x src/kma_pg_config_setup.py 2>/dev/null || true
    chmod +x src/kma_pg_config_manager.py 2>/dev/null || true
    chmod +x scripts/backup_cron.sh 2>/dev/null || true
    chmod +x scripts/*.sh 2>/dev/null || true
    echo "✓ Scripts made executable"
    
    # Test installation
    echo "Testing installation..."
    python -c "import psycopg2, yaml, requests; print('✓ All dependencies imported successfully')" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "WARNING: Some dependencies may not be working correctly"
        echo "Please check the installation"
    else
        echo "✓ All dependencies imported successfully"
    fi
    
    # Test scripts
    echo "Testing backup script..."
    python src/kma_pg_backup.py --version >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "WARNING: Backup script test failed"
    else
        echo "✓ Backup script is working"
    fi
    
    echo "Testing restore script..."
    python src/kma_pg_restore.py --version >/dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "WARNING: Restore script test failed"
    else
        echo "✓ Restore script is working"
    fi
}

# Main execution
main() {
    detect_os
    check_requirements
    
    # Ask if user wants to install system dependencies
    read -p "Install/update system dependencies via Homebrew? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        install_system_deps
    fi
    
    create_venv
    activate_venv
    install_deps
    create_dirs
    setup_permissions
    
    echo ""
    echo "========================================"
    echo "macOS setup completed successfully!"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "1. Configure your database settings:"
    echo "   source venv/bin/activate"
    echo "   python src/kma_pg_config_setup.py"
    echo ""
    echo "2. Test database connection:"
    echo "   python src/kma_pg_backup.py --test-connection"
    echo ""
    echo "3. Create your first backup:"
    echo "   python src/kma_pg_backup.py"
    echo ""
    echo "To activate virtual environment in the future:"
    echo "   source venv/bin/activate"
    echo ""
    echo "Note: If PostgreSQL utilities are not found, ensure they are in your PATH:"
    echo "   export PATH=\"/opt/homebrew/bin:\$PATH\"  # For Apple Silicon Macs"
    echo "   export PATH=\"/usr/local/bin:\$PATH\"     # For Intel Macs"
    echo ""
}

# Run main function
main "$@"

