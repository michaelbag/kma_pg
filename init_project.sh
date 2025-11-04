#!/bin/bash
# PostgreSQL Backup Manager - Linux Project Initialization Script
# Version: 1.0.1
# Author: Michael BAG <mk@remark.pro>
# Supported: Ubuntu Server 18.04, 20.04, and other Linux distributions

set -e  # Exit on any error

echo "========================================"
echo "PostgreSQL Backup Manager - Linux Setup"
echo "Version: 1.0.1"
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
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    echo "✓ Python 3 is installed: $(python3 --version)"
    
    # Check if Python version is 3.7 or later
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
        echo "WARNING: Python 3.7 or later is required (found $PYTHON_VERSION)"
        
        # First, check if Python 3.8 (or higher) is already installed
        if command -v python3.8 &> /dev/null; then
            if python3.8 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
                echo "✓ Python 3.8 is already installed, will use it"
                PYTHON_BIN="python3.8"
                return 0
            fi
        fi
        
        # Check for other Python 3.x versions (3.9, 3.10, etc.)
        for pyver in python3.9 python3.10 python3.11 python3.12; do
            if command -v $pyver &> /dev/null; then
                if $pyver -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
                    echo "✓ $pyver is already installed, will use it"
                    PYTHON_BIN="$pyver"
                    return 0
                fi
            fi
        done
        
        # For Ubuntu 18.04, try to install Python 3.8
        if [[ "$OS" == *"Ubuntu"* ]] && [[ "$VER" == "18.04" ]]; then
            echo ""
            echo "Detected Ubuntu 18.04 - attempting to install Python 3.8..."
            echo "This will install Python 3.8 from deadsnakes PPA"
            
            # Check if we're in an interactive terminal
            if [ -t 0 ]; then
                read -p "Install Python 3.8? (Y/n): " -n 1 -r
                echo
                INSTALL_PYTHON38=$REPLY
            else
                # Non-interactive mode - check if sudo is available without password
                if sudo -n true 2>/dev/null || [ "$EUID" -eq 0 ]; then
                    echo "Non-interactive mode detected. Installing Python 3.8 automatically..."
                    INSTALL_PYTHON38="Y"
                else
                    echo "Non-interactive mode and no passwordless sudo. Skipping automatic installation."
                    INSTALL_PYTHON38="N"
                fi
            fi
            
            if [[ ! $INSTALL_PYTHON38 =~ ^[Nn]$ ]]; then
                if install_python38_ubuntu; then
                    # Check again after installation
                    if command -v python3.8 &> /dev/null; then
                        if python3.8 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
                            echo "✓ Python 3.8 installed successfully"
                            PYTHON_BIN="python3.8"
                            return 0
                        fi
                    fi
                else
                    echo ""
                    echo "Failed to install Python 3.8 automatically"
                    echo ""
                    # Check if Python 3.8 might have been installed manually (don't exit yet)
                    if command -v python3.8 &> /dev/null; then
                        if python3.8 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
                            echo "✓ Python 3.8 found in system, continuing..."
                            PYTHON_BIN="python3.8"
                            return 0
                        fi
                    fi
                    echo "Python 3.8 is not installed. Please install it manually as root:"
                    echo "  sudo apt update"
                    echo "  sudo apt install -y software-properties-common"
                    echo "  sudo add-apt-repository -y ppa:deadsnakes/ppa"
                    echo "  sudo apt update"
                    echo "  sudo apt install -y python3.8 python3.8-venv python3.8-dev python3.8-distutils"
                    echo "  curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | sudo python3.8"
                    echo ""
                    echo "Then run this script again."
                    echo ""
                fi
            fi
        fi
        
        # Final check - maybe Python 3.8 was installed between checks or is available
        if command -v python3.8 &> /dev/null; then
            if python3.8 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
                echo "✓ Python 3.8 found in system, continuing..."
                PYTHON_BIN="python3.8"
                return 0
            fi
        fi
        
        # Check for other Python versions one more time
        for pyver in python3.9 python3.10 python3.11 python3.12; do
            if command -v $pyver &> /dev/null; then
                if $pyver -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
                    echo "✓ $pyver found in system, continuing..."
                    PYTHON_BIN="$pyver"
                    return 0
                fi
            fi
        done
        
        echo "ERROR: Python 3.7 or later is required (found $PYTHON_VERSION)"
        echo ""
        echo "Please install Python 3.7 or later manually:"
        echo "  Ubuntu 18.04: sudo add-apt-repository -y ppa:deadsnakes/ppa && sudo apt update && sudo apt install -y python3.8 python3.8-venv python3.8-dev python3.8-distutils"
        echo "  Ubuntu 20.04+: sudo apt install -y python3.8 python3.8-venv"
        echo ""
        echo "After installation, run this script again."
        exit 1
    fi
}

# Install Python 3.8 on Ubuntu 18.04
install_python38_ubuntu() {
    echo "Installing Python 3.8 for Ubuntu 18.04..."
    
    # Check if we're root or can use sudo without password
    if [ "$EUID" -eq 0 ]; then
        # Running as root, no sudo needed
        SUDO_CMD=""
    elif sudo -n true 2>/dev/null; then
        # Can use sudo without password
        SUDO_CMD="sudo"
    else
        # Cannot use sudo without password
        echo ""
        echo "ERROR: This operation requires sudo privileges, but sudo requires a password"
        echo ""
        echo "Please install Python 3.8 manually as root:"
        echo "  sudo apt update"
        echo "  sudo apt install -y software-properties-common"
        echo "  sudo add-apt-repository -y ppa:deadsnakes/ppa"
        echo "  sudo apt update"
        echo "  sudo apt install -y python3.8 python3.8-venv python3.8-dev python3.8-distutils"
        echo "  curl -sS https://bootstrap.pypa.io/get-pip.py | sudo python3.8"
        echo ""
        echo "Or configure passwordless sudo for this user, then run the script again"
        echo ""
        return 1
    fi
    
    # Add deadsnakes PPA (non-interactive)
    $SUDO_CMD apt update || return 1
    $SUDO_CMD apt install -y software-properties-common || return 1
    $SUDO_CMD DEBIAN_FRONTEND=noninteractive add-apt-repository -y ppa:deadsnakes/ppa || return 1
    
    # Update package list
    $SUDO_CMD apt update || return 1
    
    # Install Python 3.8 and required packages
    $SUDO_CMD apt install -y \
        python3.8 \
        python3.8-venv \
        python3.8-dev \
        python3.8-distutils || return 1
    
    # Install pip for Python 3.8
    if ! python3.8 -c "import pip" 2>/dev/null; then
        # Python 3.8 requires specific pip installer
        curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | $SUDO_CMD python3.8 || return 1
    fi
    
    echo "✓ Python 3.8 installation completed"
    return 0
}

# Install system dependencies for Ubuntu
install_system_deps() {
    echo ""
    echo "[2/7] Installing system dependencies..."
    
    # Determine sudo command
    SUDO_CMD=""
    if [ "$EUID" -ne 0 ]; then
        SUDO_CMD="sudo"
    fi
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        echo "Detected Ubuntu/Debian system"
        
        # Update package list
        echo "Updating package list..."
        $SUDO_CMD apt update
        
        # Determine Python version to use
        PYTHON_BIN="python3"
        if [[ "$VER" == "18.04" ]] && command -v python3.8 &> /dev/null; then
            PYTHON_BIN="python3.8"
            echo "Using Python 3.8 for Ubuntu 18.04"
        elif [[ "$VER" == "18.04" ]] && ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
            # Python 3.6 detected, need to install 3.8
            if command -v python3.8 &> /dev/null; then
                PYTHON_BIN="python3.8"
                echo "Python 3.8 already installed, using it"
            else
                echo "Python 3.6 detected, but Python 3.8 is not installed"
                echo "Please run the script again after installing Python 3.8 manually"
                echo "Or answer 'Y' when prompted to install Python 3.8"
            fi
        fi
        
        # Install required packages
        echo "Installing required packages..."
        $SUDO_CMD apt install -y \
            python3-venv \
            python3-pip \
            postgresql-client \
            build-essential \
            libpq-dev \
            python3-dev
        
        # For Ubuntu 18.04 with Python 3.8, install additional packages
        if [[ "$VER" == "18.04" ]] && [[ "$PYTHON_BIN" == "python3.8" ]]; then
            $SUDO_CMD apt install -y \
                python3.8-venv \
                python3.8-dev
        fi
        
        echo "✓ System dependencies installed"
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
        echo "Detected CentOS/RHEL system"
        
        # Install required packages
        echo "Installing required packages..."
        $SUDO_CMD yum install -y \
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
    
    # Set PYTHON_BIN for use in create_venv
    if [ -z "$PYTHON_BIN" ]; then
        if command -v python3.8 &> /dev/null && python3.8 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
            PYTHON_BIN="python3.8"
        else
            PYTHON_BIN="python3"
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
    
    # Use appropriate Python version
    if [ -z "$PYTHON_BIN" ]; then
        if command -v python3.8 &> /dev/null && python3.8 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)" 2>/dev/null; then
            PYTHON_BIN="python3.8"
        else
            PYTHON_BIN="python3"
        fi
    fi
    
    $PYTHON_BIN -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created using $PYTHON_BIN"
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
