#!/bin/bash
# PostgreSQL Backup Manager - Linux Project Initialization Script
# Version: 1.0.0
# Author: Michael BAG <mk@remark.pro>
# Supported: Ubuntu Server 18.04, 20.04, and other Linux distributions

set -e  # Exit on any error

echo "========================================"
echo "PostgreSQL Backup Manager - Linux Setup"
echo "Version: 1.0.0"
echo "Author: Michael BAG <mk@remark.pro>"
echo "========================================"
echo ""

# Detect OS and version
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        echo "ERROR: Cannot detect operating system"
        exit 1
    fi
    echo "Detected OS: $OS $VER"
}

# Check if running as root
check_root() {
    if [ "$EUID" -eq 0 ]; then
        echo "WARNING: Running as root is not recommended"
        echo "Consider running as a regular user with sudo privileges"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check system requirements
check_requirements() {
    echo "[1/7] Checking system requirements..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        echo "ERROR: Python 3 is not installed"
        echo "Please install Python 3.7 or later:"
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
        echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
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
        echo "  Ubuntu/Debian: sudo apt install postgresql-client"
        echo "  CentOS/RHEL: sudo yum install postgresql"
        echo ""
        echo "Continuing with setup anyway..."
    else
        echo "✓ PostgreSQL client utilities are available: $(pg_dump --version)"
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        echo "ERROR: pip3 is not installed"
        echo "Please install pip:"
        echo "  Ubuntu/Debian: sudo apt install python3-pip"
        echo "  CentOS/RHEL: sudo yum install python3-pip"
        exit 1
    fi
    echo "✓ pip3 is available"
}

# Install system dependencies for Ubuntu
install_system_deps() {
    echo ""
    echo "[2/7] Installing system dependencies..."
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        echo "Detected Ubuntu/Debian system"
        
        # Update package list
        echo "Updating package list..."
        sudo apt update
        
        # Install required packages
        echo "Installing required packages..."
        sudo apt install -y \
            python3-venv \
            python3-pip \
            postgresql-client \
            build-essential \
            libpq-dev \
            python3-dev
        
        echo "✓ System dependencies installed"
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        echo "Detected CentOS/RHEL system"
        
        # Install required packages
        echo "Installing required packages..."
        sudo yum install -y \
            python3 \
            python3-pip \
            python3-venv \
            postgresql \
            gcc \
            python3-devel \
            postgresql-devel
        
        echo "✓ System dependencies installed"
    else
        echo "WARNING: Unsupported OS detected"
        echo "Please ensure the following packages are installed:"
        echo "  - Python 3.7+ with venv support"
        echo "  - pip3"
        echo "  - PostgreSQL client utilities"
        echo "  - Build tools (gcc, make)"
        echo "  - Python development headers"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
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
    
    # Upgrade pip
    python -m pip install --upgrade pip
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to upgrade pip, continuing..."
    else
        echo "✓ Pip upgraded"
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
    chmod +x src/kma_pg_backup.py
    chmod +x src/kma_pg_restore.py
    chmod +x src/kma_pg_config_setup.py
    chmod +x src/kma_pg_config_manager.py
    chmod +x scripts/backup_cron.sh
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
    check_root
    check_requirements
    
    # Ask if user wants to install system dependencies
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]] || [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        read -p "Install system dependencies? (Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo "Skipping system dependency installation..."
        else
            install_system_deps
        fi
    fi
    
    create_venv
    activate_venv
    install_deps
    create_dirs
    setup_permissions
    
    echo ""
    echo "========================================"
    echo "Setup completed successfully!"
    echo "========================================"
    echo ""
    echo "Next steps:"
    echo "1. Configure your database settings:"
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
    echo "For Ubuntu Server setup guide, see README.md"
    echo ""
}

# Run main function
main "$@"
