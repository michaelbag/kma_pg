#!/bin/bash
# PostgreSQL Backup Manager - Linux Project Initialization Script
# Version: 1.0.3
# Author: Michael BAG <mk@remark.pro>
# Supported: Ubuntu Server 18.04, 20.04, and other Linux distributions
#
# This script can be run by administrator to setup the project.
# The project will be configured to run under a regular user (without sudo).
# The administrator can specify the runtime user during setup.

set -e  # Exit on any error

# Global variables
PROJECT_USER=""  # User who will run the project (without sudo)
PROJECT_DIR="$(pwd)"  # Current directory

echo "========================================"
echo "PostgreSQL Backup Manager - Linux Setup"
echo "Version: 1.0.3"
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

# Update system packages (optional)
update_system() {
    echo ""
    echo "[System Update] Updating system packages..."
    echo "This may take a few minutes..."
    
    # Determine sudo command
    SUDO_CMD=""
    if [ "$EUID" -ne 0 ]; then
        SUDO_CMD="sudo"
    fi
    
    $SUDO_CMD apt update
    $SUDO_CMD apt upgrade -y
    
    echo "✓ System packages updated"
}

# Create project user (optional)
create_project_user() {
    echo ""
    echo "[User Creation] Create dedicated user for backup operations?"
    echo ""
    read -p "Create new user? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        while true; do
            read -p "Enter username for backup operations [kma_pg]: " username
            username=${username:-kma_pg}
            
            if id -u "$username" >/dev/null 2>&1; then
                read -p "User '$username' already exists. Use this user? (Y/n): " -n 1 -r use_existing
                echo
                if [[ ! $use_existing =~ ^[Nn]$ ]]; then
                    PROJECT_USER="$username"
                    export PROJECT_USER
                    echo "✓ Using existing user '$PROJECT_USER'"
                    return 0
                else
                    read -p "Create a different user instead? (y/N): " -n 1 -r try_another
                    echo
                    if [[ ! $try_another =~ ^[Yy]$ ]]; then
                        return 1
                    fi
                    continue
                fi
            else
                # Create user
                SUDO_CMD=""
                if [ "$EUID" -ne 0 ]; then
                    SUDO_CMD="sudo"
                fi
                
                $SUDO_CMD useradd -m -s /bin/bash "$username"
                
                # Set up SSH key (if exists)
                if [ -f ~/.ssh/id_rsa.pub ]; then
                    $SUDO_CMD mkdir -p /home/$username/.ssh
                    $SUDO_CMD cp ~/.ssh/id_rsa.pub /home/$username/.ssh/authorized_keys
                    $SUDO_CMD chown -R $username:$username /home/$username/.ssh
                    $SUDO_CMD chmod 700 /home/$username/.ssh
                    $SUDO_CMD chmod 600 /home/$username/.ssh/authorized_keys
                fi
                
                PROJECT_USER="$username"
                export PROJECT_USER
                echo "✓ User '$PROJECT_USER' created"
                return 0
            fi
        done
    fi
    return 1
}

# Select project user (who will run the project without sudo)
select_project_user() {
    echo ""
    echo "[User Selection] Selecting user for project runtime..."
    echo ""
    echo "This script will setup the project so it can run under a regular user"
    echo "without sudo privileges. The administrator will install system dependencies."
    echo ""
    
    # Try to create user first (optional)
    if create_project_user; then
        # User was created, continue
        :
    else
        # User creation was skipped, select existing user
        read -p "Enter username who will run the project [$(whoami)]: " username
        username=${username:-$(whoami)}
        
        # Check if user exists
        if ! id -u "$username" >/dev/null 2>&1; then
            echo ""
            echo "ERROR: User '$username' does not exist"
            echo "Please create the user first or enter an existing username"
            read -p "Enter username: " username
            if ! id -u "$username" >/dev/null 2>&1; then
                echo "ERROR: User '$username' still does not exist. Exiting."
                exit 1
            fi
        fi
        
        PROJECT_USER="$username"
        export PROJECT_USER  # Export for use in subprocesses
    fi
    
    echo "✓ Project will run under user: $PROJECT_USER"
    echo ""
    
    # Save PROJECT_USER to file for use by other scripts
    echo "$PROJECT_USER" > "$PROJECT_DIR/.project_user"
    echo "✓ Project user saved to .project_user"
}

# Ensure project user owns the project files
ensure_project_ownership() {
    echo ""
    echo "[Ownership] Setting ownership of project files to '$PROJECT_USER'..."
    
    if [ -z "$PROJECT_USER" ]; then
        echo "WARNING: PROJECT_USER not set, skipping ownership change"
        return
    fi
    
    # Check if we need sudo to change ownership
    CURRENT_USER=$(whoami)
    if [ "$CURRENT_USER" != "$PROJECT_USER" ]; then
        if [ "$EUID" -ne 0 ] && ! sudo -n true 2>/dev/null; then
            echo "WARNING: Cannot change ownership without sudo privileges"
            echo "You may need to run: sudo chown -R $PROJECT_USER:$PROJECT_USER $PROJECT_DIR"
            return
        fi
        
        # Use sudo if not root
        if [ "$EUID" -ne 0 ]; then
            SUDO_CMD="sudo"
        else
            SUDO_CMD=""
        fi
        
        echo "Changing ownership of $PROJECT_DIR to $PROJECT_USER..."
        $SUDO_CMD chown -R "$PROJECT_USER":"$PROJECT_USER" "$PROJECT_DIR"
        echo "✓ Ownership changed to $PROJECT_USER"
    else
        echo "Current user is $PROJECT_USER, ownership is correct"
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
        echo "  curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py | sudo python3.8"
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
        
        # Install packages that are usually safe
        $SUDO_CMD apt install -y \
            python3-venv \
            python3-pip \
            build-essential \
            python3-dev 2>&1 | tee /tmp/apt_install.log
        
        INSTALL_RESULT=$?
        
        # Try to install postgresql-client and libpq-dev
        # These might have dependency conflicts with custom PostgreSQL installations
        if $SUDO_CMD apt install -y postgresql-client libpq-dev 2>&1 | tee -a /tmp/apt_install.log; then
            echo "✓ PostgreSQL client and libpq-dev installed"
        else
            echo ""
            echo "WARNING: Failed to install postgresql-client or libpq-dev"
            echo "This might be due to version conflicts with an existing PostgreSQL installation."
            echo ""
            echo "Common solutions:"
            echo "1. If you have PostgreSQL 11 installed, try:"
            echo "   sudo apt install -y postgresql-client-11 libpq-dev"
            echo ""
            echo "2. Or fix broken dependencies first:"
            echo "   sudo apt --fix-broken install"
            echo "   sudo apt install -y postgresql-client libpq-dev"
            echo ""
            echo "3. If you have a custom PostgreSQL installation, libpq-dev might already be available."
            echo "   You can continue and the script will try to install Python dependencies."
            echo ""
            read -p "Continue with installation? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Installation cancelled. Please fix package dependencies and run the script again."
                exit 1
            fi
        fi
        
        # For Ubuntu 18.04 with Python 3.8, install additional packages
        if [[ "$VER" == "18.04" ]] && [[ "$PYTHON_BIN" == "python3.8" ]]; then
            if $SUDO_CMD apt install -y python3.8-venv python3.8-dev 2>&1 | tee -a /tmp/apt_install.log; then
                echo "✓ Python 3.8 packages installed"
            else
                echo "WARNING: Failed to install Python 3.8 packages"
                echo "This might not be critical if Python 3.8 is already working."
            fi
        fi
        
        # Check if critical packages are installed
        if command -v python3 &> /dev/null && command -v pip3 &> /dev/null; then
            echo "✓ Critical system dependencies installed"
        else
            echo "ERROR: Critical dependencies (python3, pip3) are missing"
            echo "Please install them manually and run the script again"
            exit 1
        fi
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
    
    # Set ownership if PROJECT_USER is set and different from current user
    if [ -n "$PROJECT_USER" ] && [ "$(whoami)" != "$PROJECT_USER" ]; then
        if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
            SUDO_CMD=""
            if [ "$EUID" -ne 0 ]; then
                SUDO_CMD="sudo"
            fi
            $SUDO_CMD chown -R "$PROJECT_USER":"$PROJECT_USER" venv 2>/dev/null || true
            echo "✓ Virtual environment ownership set to $PROJECT_USER"
        fi
    fi
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
    
    # If PROJECT_USER is set and different from current user, install as that user
    if [ -n "$PROJECT_USER" ] && [ "$(whoami)" != "$PROJECT_USER" ]; then
        # Install as project user with proper environment
        echo "Installing dependencies for user $PROJECT_USER..."
        
        # Get user's home directory
        USER_HOME=$(getent passwd "$PROJECT_USER" | cut -d: -f6)
        
        # Install with proper home directory and cache directory
        sudo -u "$PROJECT_USER" bash -c "
            cd $PROJECT_DIR
            export HOME='$USER_HOME'
            export PIP_CACHE_DIR='$USER_HOME/.cache/pip'
            source venv/bin/activate
            python -m pip install --upgrade pip --user 2>/dev/null || python -m pip install --upgrade pip
        " 2>/dev/null || true
        
        # Install requirements as project user
        # First upgrade pip, setuptools, wheel
        sudo -u "$PROJECT_USER" bash -c "
            cd $PROJECT_DIR
            export HOME='$USER_HOME'
            export PIP_CACHE_DIR='$USER_HOME/.cache/pip'
            source venv/bin/activate
            pip install --upgrade pip setuptools wheel
        " 2>/dev/null || true
        
        # Try to install psycopg2-binary first (prefer binary wheels)
        echo "Installing psycopg2-binary..."
        if sudo -u "$PROJECT_USER" bash -c "
            cd $PROJECT_DIR
            export HOME='$USER_HOME'
            export PIP_CACHE_DIR='$USER_HOME/.cache/pip'
            source venv/bin/activate
            pip install --only-binary :all: --no-cache-dir psycopg2-binary>=2.9.9
        " 2>&1 | grep -q "Successfully installed\|Requirement already satisfied"; then
            echo "✓ psycopg2-binary installed (binary package)"
        else
            echo "WARNING: Failed to install psycopg2-binary as binary package"
            echo "Attempting to install from source..."
            
            # Check if pg_config is available (from existing PostgreSQL installation)
            PG_CONFIG_PATH=$(command -v pg_config 2>/dev/null || which pg_config 2>/dev/null || find /usr -name pg_config 2>/dev/null | head -1)
            
            if [ -n "$PG_CONFIG_PATH" ] && [ -x "$PG_CONFIG_PATH" ]; then
                echo "✓ Found pg_config at: $PG_CONFIG_PATH"
                echo "Using existing PostgreSQL installation for compilation..."
                
                # Get paths from pg_config
                PG_INCLUDE_DIR=$($PG_CONFIG_PATH --includedir 2>/dev/null || echo "")
                PG_LIB_DIR=$($PG_CONFIG_PATH --libdir 2>/dev/null || echo "")
                
                # Try to install from source using existing PostgreSQL
                if sudo -u "$PROJECT_USER" bash -c "
                    cd $PROJECT_DIR
                    export HOME='$USER_HOME'
                    export PIP_CACHE_DIR='$USER_HOME/.cache/pip'
                    source venv/bin/activate
                    export PG_CONFIG='$PG_CONFIG_PATH'
                    [ -n '$PG_INCLUDE_DIR' ] && export PG_INCLUDE_DIR='$PG_INCLUDE_DIR' || true
                    [ -n '$PG_LIB_DIR' ] && export PG_LIB_DIR='$PG_LIB_DIR' || true
                    pip install --no-cache-dir psycopg2-binary>=2.9.9
                "; then
                    echo "✓ psycopg2-binary installed from source using existing PostgreSQL"
                else
                    echo "ERROR: Failed to install psycopg2-binary from source"
                    echo "pg_config found but compilation failed. Please check PostgreSQL installation."
                    exit 1
                fi
            elif ! dpkg -l | grep -q "^ii.*libpq-dev"; then
                echo ""
                echo "ERROR: Cannot install psycopg2-binary:"
                echo "  - Binary package not available for this platform"
                echo "  - pg_config not found (PostgreSQL development files missing)"
                echo "  - libpq-dev package not installed (and cannot be installed due to conflicts)"
                echo ""
                echo "Solutions:"
                echo ""
                echo "1. If PostgreSQL 11 is installed, ensure pg_config is in PATH:"
                echo "   which pg_config"
                echo "   # If not found, locate it:"
                echo "   find /usr -name pg_config 2>/dev/null"
                echo "   # Then add to PATH or create symlink:"
                echo "   sudo ln -s \$(find /usr -name pg_config 2>/dev/null | head -1) /usr/local/bin/pg_config"
                echo ""
                echo "2. If PostgreSQL 11 development files are installed separately,"
                echo "   ensure they are accessible and pg_config is available."
                echo ""
                echo "3. Manual installation after fixing PostgreSQL paths:"
                echo "   sudo -u $PROJECT_USER bash -c 'cd $PROJECT_DIR && source venv/bin/activate && pip install -r requirements.txt'"
                echo ""
                read -p "Continue anyway and try to install other dependencies? (y/N): " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            else
                # libpq-dev is installed, try normal compilation
                echo "libpq-dev found, attempting standard compilation..."
                if sudo -u "$PROJECT_USER" bash -c "
                    cd $PROJECT_DIR
                    export HOME='$USER_HOME'
                    export PIP_CACHE_DIR='$USER_HOME/.cache/pip'
                    source venv/bin/activate
                    pip install --no-cache-dir psycopg2-binary>=2.9.9
                "; then
                    echo "✓ psycopg2-binary installed from source"
                else
                    echo "ERROR: Failed to install psycopg2-binary even from source"
                    echo "Please check PostgreSQL development files installation"
                    exit 1
                fi
            fi
        fi
        
        # Install remaining dependencies
        echo "Installing remaining dependencies..."
        if sudo -u "$PROJECT_USER" bash -c "
            cd $PROJECT_DIR
            export HOME='$USER_HOME'
            export PIP_CACHE_DIR='$USER_HOME/.cache/pip'
            source venv/bin/activate
            pip install --no-cache-dir PyYAML==6.0.1 requests==2.31.0 webdavclient3==3.14.6
        "; then
            echo "✓ All dependencies installed for $PROJECT_USER"
        else
            echo "ERROR: Failed to install remaining dependencies for $PROJECT_USER"
            echo "Please check requirements.txt and try again"
            exit 1
        fi
    else
        # Install as current user
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
    fi
}

# Create project directories
create_dirs() {
    echo ""
    echo "[6/7] Creating project directories..."
    
    mkdir -p logs backups config/databases
    
    # Set ownership if PROJECT_USER is set and different from current user
    if [ -n "$PROJECT_USER" ] && [ "$(whoami)" != "$PROJECT_USER" ]; then
        if [ "$EUID" -eq 0 ] || sudo -n true 2>/dev/null; then
            SUDO_CMD=""
            if [ "$EUID" -ne 0 ]; then
                SUDO_CMD="sudo"
            fi
            $SUDO_CMD chown -R "$PROJECT_USER":"$PROJECT_USER" logs backups config 2>/dev/null || true
        fi
    fi
    
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
    
    # Test installation as project user if specified
    echo "Testing installation..."
    if [ -n "$PROJECT_USER" ] && [ "$(whoami)" != "$PROJECT_USER" ]; then
        # Test as project user
        if sudo -u "$PROJECT_USER" bash -lc "source $PROJECT_DIR/venv/bin/activate && python -c 'import psycopg2, yaml, requests; print(\"✓ All dependencies imported successfully\")'" 2>/dev/null; then
            echo "✓ All dependencies imported successfully (tested as $PROJECT_USER)"
        else
            echo "WARNING: Some dependencies may not be working correctly for $PROJECT_USER"
            echo "Please check the installation"
        fi
        
        # Test scripts as project user
        echo "Testing backup script..."
        if sudo -u "$PROJECT_USER" bash -lc "source $PROJECT_DIR/venv/bin/activate && python $PROJECT_DIR/src/kma_pg_backup.py --version" >/dev/null 2>&1; then
            echo "✓ Backup script is working (tested as $PROJECT_USER)"
        else
            echo "WARNING: Backup script test failed for $PROJECT_USER"
        fi
        
        echo "Testing restore script..."
        if sudo -u "$PROJECT_USER" bash -lc "source $PROJECT_DIR/venv/bin/activate && python $PROJECT_DIR/src/kma_pg_restore.py --version" >/dev/null 2>&1; then
            echo "✓ Restore script is working (tested as $PROJECT_USER)"
        else
            echo "WARNING: Restore script test failed for $PROJECT_USER"
        fi
    else
        # Test as current user
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
    fi
}

# Set up cron job (optional)
setup_cron() {
    echo ""
    echo "[Cron Setup] Setting up automated backup..."
    
    read -p "Set up automated daily backup? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Get current directory
        CURRENT_DIR=$(pwd)
        
        # Create cron job
        CRON_JOB="0 2 * * * cd $CURRENT_DIR && source venv/bin/activate && python src/kma_pg_backup.py >> logs/cron.log 2>&1"
        
        # Add to crontab for project user
        if [ -n "$PROJECT_USER" ] && [ "$PROJECT_USER" != "$(whoami)" ]; then
            SUDO_CMD=""
            if [ "$EUID" -ne 0 ]; then
                SUDO_CMD="sudo"
            fi
            ($SUDO_CMD -u "$PROJECT_USER" crontab -l 2>/dev/null; echo "$CRON_JOB") | $SUDO_CMD -u "$PROJECT_USER" crontab -
        else
            (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
        fi
        
        echo "✓ Automated backup scheduled for 2:00 AM daily"
        echo "  Logs will be written to: logs/cron.log"
    else
        echo "Skipping automated backup setup"
    fi
}

# Main execution
main() {
    detect_os
    
    # Select project user (who will run without sudo)
    select_project_user
    
    check_requirements
    
    # Ask if user wants to update system packages (Ubuntu/Debian only)
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        read -p "Update system packages (apt update && apt upgrade)? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            update_system
        fi
    fi
    
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
    
    # Ensure project ownership before setting permissions
    ensure_project_ownership
    
    setup_permissions
    
    # Setup cron job (optional)
    setup_cron
    
    # Save PROJECT_USER to file for use by other scripts (if not already saved)
    if [ -n "$PROJECT_USER" ]; then
        echo "$PROJECT_USER" > "$PROJECT_DIR/.project_user"
        chmod 644 "$PROJECT_DIR/.project_user"
        # Set ownership if different from current user
        if [ "$(whoami)" != "$PROJECT_USER" ]; then
            if [ "$EUID" -eq 0 ]; then
                chown "$PROJECT_USER":"$PROJECT_USER" "$PROJECT_DIR/.project_user" 2>/dev/null || true
            fi
        fi
        echo "✓ Project user saved to .project_user file"
    fi
    
    echo ""
    echo "========================================"
    echo "Setup completed successfully!"
    echo "========================================"
    echo ""
    
    if [ -n "$PROJECT_USER" ] && [ "$(whoami)" != "$PROJECT_USER" ]; then
        echo "Project setup for user: $PROJECT_USER"
        echo ""
        echo "To switch to project user:"
        echo "   sudo su - $PROJECT_USER"
        echo "   cd $PROJECT_DIR"
        echo ""
        echo "Next steps (as user $PROJECT_USER):"
        echo "1. Activate virtual environment:"
        echo "   source venv/bin/activate"
        echo ""
        echo "2. Configure your database settings:"
        echo "   python src/kma_pg_config_setup.py"
        echo ""
        echo "3. Test database connection:"
        echo "   python src/kma_pg_backup.py --test-connection"
        echo ""
        echo "4. Create your first backup:"
        echo "   python src/kma_pg_backup.py"
    else
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
    fi
    
    # Show cron info if it was set up
    if crontab -l 2>/dev/null | grep -q "kma_pg_backup.py" || ([ -n "$PROJECT_USER" ] && sudo -u "$PROJECT_USER" crontab -l 2>/dev/null | grep -q "kma_pg_backup.py"); then
        echo ""
        echo "5. Check cron job:"
        if [ -n "$PROJECT_USER" ] && [ "$PROJECT_USER" != "$(whoami)" ]; then
            echo "   sudo -u $PROJECT_USER crontab -l"
        else
            echo "   crontab -l"
        fi
    fi
    
    echo ""
    echo "For Ubuntu Server setup guide, see README.md"
    echo ""
}

# Run main function
main "$@"
