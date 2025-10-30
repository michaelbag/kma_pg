#!/bin/bash
# PostgreSQL Backup Manager - Ubuntu Server Setup Script
# Version: 1.0.3
# Author: Michael BAG <mk@remark.pro>
# Supported: Ubuntu Server 18.04, 20.04, 22.04

set -e  # Exit on any error

# Selected project user (will be set during setup)
SELECTED_USER=""
# Project directory (where script is being run)
PROJECT_DIR="$(pwd)"
# Preferred Python binary (will prefer python3.8 on Ubuntu 18.04 if available)
PYTHON_BIN="python3"

# Helper: run a command as selected user with proper HOME (-H) and login shell (-l)
run_as_selected() {
    if [ -n "$SELECTED_USER" ]; then
        sudo -H -u "$SELECTED_USER" bash -lc "$*"
    else
        bash -lc "$*"
    fi
}

echo "========================================"
echo "PostgreSQL Backup Manager - Ubuntu Server"
echo "Version: 1.0.3"
echo "Author: Michael BAG <mk@remark.pro>"
echo "Supported: Ubuntu Server 18.04, 20.04, 22.04"
echo "========================================"
echo ""

# Detect Ubuntu version
detect_ubuntu_version() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        if [[ "$ID" == "ubuntu" ]]; then
            UBUNTU_VERSION=$VERSION_ID
            echo "Detected Ubuntu Server $UBUNTU_VERSION"
        else
            echo "ERROR: This script is designed for Ubuntu Server"
            echo "Detected: $ID $VERSION_ID"
            exit 1
        fi
    else
        echo "ERROR: Cannot detect Ubuntu version"
        exit 1
    fi
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

# Update system packages
update_system() {
    echo "[1/8] Updating system packages..."
    echo "This may take a few minutes..."
    
    sudo apt update
    sudo apt upgrade -y
    
    echo "✓ System packages updated"
}

# Install system dependencies
install_system_deps() {
    echo ""
    echo "[2/8] Installing system dependencies..."
    
    # Install essential packages
    sudo apt install -y \
        software-properties-common \
        apt-transport-https \
        ca-certificates \
        curl \
        wget \
        gnupg \
        lsb-release
    
    # Install Python and development tools
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        python3-setuptools \
        build-essential \
        libssl-dev \
        libffi-dev \
        libxml2-dev \
        libxslt1-dev \
        zlib1g-dev
    
    # PostgreSQL client utilities: install ONLY if missing (respect pinned versions)
    if ! command -v psql >/dev/null 2>&1 || ! command -v pg_dump >/dev/null 2>&1; then
        echo "Installing PostgreSQL client utilities (psql/pg_dump)..."
        sudo apt install -y postgresql-client || echo "WARNING: Could not install postgresql-client; please ensure psql/pg_dump are available in PATH"
    else
        echo "✓ PostgreSQL client utilities already present"
    fi
    
    # For Ubuntu 18.04, install additional packages
    if [[ "$UBUNTU_VERSION" == "18.04" ]]; then
        echo "Installing additional packages for Ubuntu 18.04..."
        sudo apt install -y \
            python3.8 \
            python3.8-venv \
            python3.8-dev
    fi
    
    # Prefer newer Python if available (e.g., python3.8 on 18.04)
    if command -v python3.8 >/dev/null 2>&1; then
        PYTHON_BIN="python3.8"
        echo "✓ Using Python interpreter: $PYTHON_BIN"
    else
        PYTHON_BIN="python3"
        echo "✓ Using Python interpreter: $PYTHON_BIN"
    fi
    
    echo "✓ System dependencies installed"
}

# PostgreSQL server installation removed (client-only setup)

# Create project user (optional)
create_project_user() {
    echo ""
    echo "[3/7] Project user setup..."
    
    read -p "Create dedicated user for backup operations? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        while true; do
            read -p "Enter username for backup operations [backup]: " username
            username=${username:-backup}
            
            if id -u "$username" >/dev/null 2>&1; then
                read -p "User '$username' already exists. Use this user? (Y/n): " -n 1 -r use_existing
                echo
                if [[ ! $use_existing =~ ^[Nn]$ ]]; then
                    SELECTED_USER="$username"
                    echo "Using existing user '$SELECTED_USER'"
                    break
                else
                    read -p "Create a different user instead? (y/N): " -n 1 -r try_another
                    echo
                    if [[ $try_another =~ ^[Yy]$ ]]; then
                        continue
                    else
                        SELECTED_USER="$USER"
                        echo "Skipping user creation. Using current user '$SELECTED_USER' for backup operations"
                        return
                    fi
                fi
            else
                # Create user
                sudo useradd -m -s /bin/bash "$username"
                
                # Add user to necessary groups
                sudo usermod -aG sudo "$username"
                
                # Set up SSH key (if exists)
                if [ -f ~/.ssh/id_rsa.pub ]; then
                    sudo mkdir -p /home/$username/.ssh
                    sudo cp ~/.ssh/id_rsa.pub /home/$username/.ssh/authorized_keys
                    sudo chown -R $username:$username /home/$username/.ssh
                    sudo chmod 700 /home/$username/.ssh
                    sudo chmod 600 /home/$username/.ssh/authorized_keys
                fi
                
                SELECTED_USER="$username"
                echo "✓ User '$SELECTED_USER' created"
                echo "  Switch to this user: sudo su - $SELECTED_USER"
                break
            fi
        done
    else
        SELECTED_USER="$USER"
        echo "Using current user '$SELECTED_USER' for backup operations"
    fi
    echo "Selected project user: $SELECTED_USER"
}

# Ensure selected user owns the project files
ensure_project_ownership() {
    echo ""
    echo "[Ownership] Applying ownership to project files for user '$SELECTED_USER'..."
    if [ -z "$SELECTED_USER" ]; then
        echo "No selected user defined; skipping ownership change"
        return
    fi
    if [ ! -d "$PROJECT_DIR" ]; then
        echo "WARNING: Project directory not found: $PROJECT_DIR"
        return
    fi
    read -p "Change ownership of all project files in '$PROJECT_DIR' to '$SELECTED_USER'? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo chown -R "$SELECTED_USER":"$SELECTED_USER" "$PROJECT_DIR"
        echo "✓ Ownership applied to $PROJECT_DIR"
    else
        echo "Skipping ownership change"
    fi
}

# Create virtual environment
create_venv() {
    echo ""
    echo "[4/7] Creating Python virtual environment..."
    
    if [ -d "venv" ]; then
        echo "Virtual environment already exists, removing old one..."
        run_as_selected "rm -rf venv" || rm -rf venv
    fi
    
    run_as_selected "$PYTHON_BIN -m venv venv"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    echo ""
    echo "[5/7] Activating virtual environment..."
    # Activation is performed inside run_as_selected calls for each step
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to activate virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment activated"
}

# Install Python dependencies
install_deps() {
    echo ""
    echo "[6/7] Installing Python dependencies..."
    
    # Upgrade pip in venv under selected user
    run_as_selected "source venv/bin/activate && python -m pip install --upgrade pip"
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to upgrade pip, continuing..."
    else
        echo "✓ Pip upgraded"
    fi
    
    # Install requirements under selected user to avoid wrong HOME/cache ownership
    run_as_selected "source venv/bin/activate && pip install -r requirements.txt"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        echo "Please check requirements.txt and try again"
        exit 1
    fi
    echo "✓ Dependencies installed"
}

# Set up project and test
setup_project() {
    echo ""
    echo "[7/7] Setting up project and testing..."
    
    # Create project directories
    mkdir -p logs backups config/databases
    # Ensure ownership by selected user (if set)
    if [ -n "$SELECTED_USER" ]; then
        sudo chown -R "$SELECTED_USER":"$SELECTED_USER" logs backups config || true
    fi
    echo "✓ Project directories created"
    
    # Make scripts executable
    chmod +x src/kma_pg_backup.py
    chmod +x src/kma_pg_restore.py
    chmod +x src/kma_pg_config_setup.py
    chmod +x src/kma_pg_config_manager.py
    chmod +x scripts/backup_cron.sh
    echo "✓ Scripts made executable"
    
    # Test installation
    echo "Testing installation..."
    if [ -n "$SELECTED_USER" ]; then
        sudo -u "$SELECTED_USER" bash -lc "python -c 'import psycopg2, yaml, requests; print(\"✓ All dependencies imported successfully\")'" 2>/dev/null || true
    else
        python -c "import psycopg2, yaml, requests; print('✓ All dependencies imported successfully')" 2>/dev/null || true
    fi
    if [ $? -ne 0 ]; then
        echo "WARNING: Some dependencies may not be working correctly"
        echo "Please check the installation"
    else
        echo "✓ All dependencies imported successfully"
    fi
    
    # Test scripts
    echo "Testing backup script..."
    if [ -n "$SELECTED_USER" ]; then
        sudo -u "$SELECTED_USER" bash -lc "source venv/bin/activate && python src/kma_pg_backup.py --version" >/dev/null 2>&1
    else
        python src/kma_pg_backup.py --version >/dev/null 2>&1
    fi
    if [ $? -ne 0 ]; then
        echo "WARNING: Backup script test failed"
    else
        echo "✓ Backup script is working"
    fi
    
    echo "Testing restore script..."
    if [ -n "$SELECTED_USER" ]; then
        sudo -u "$SELECTED_USER" bash -lc "source venv/bin/activate && python src/kma_pg_restore.py --version" >/dev/null 2>&1
    else
        python src/kma_pg_restore.py --version >/dev/null 2>&1
    fi
    if [ $? -ne 0 ]; then
        echo "WARNING: Restore script test failed"
    else
        echo "✓ Restore script is working"
    fi
}

# Set up cron job
setup_cron() {
    echo ""
    echo "Setting up automated backup..."
    
    read -p "Set up automated daily backup? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Get current directory
        CURRENT_DIR=$(pwd)
        
        # Create cron job
        CRON_JOB="0 2 * * * cd $CURRENT_DIR && source venv/bin/activate && python src/kma_pg_backup.py >> logs/cron.log 2>&1"
        
        # Add to crontab for selected user
        if [ -n "$SELECTED_USER" ] && [ "$SELECTED_USER" != "$USER" ]; then
            (sudo -u "$SELECTED_USER" crontab -l 2>/dev/null; echo "$CRON_JOB") | sudo -u "$SELECTED_USER" crontab -
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
    detect_ubuntu_version
    check_root
    update_system
    install_system_deps
    create_project_user
    ensure_project_ownership
    create_venv
    activate_venv
    install_deps
    setup_project
    setup_cron
    
    echo ""
    echo "========================================"
    echo "Ubuntu Server setup completed successfully!"
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
    echo "4. Check cron job:"
    echo "   crontab -l"
    echo ""
    echo "To activate virtual environment in the future:"
    echo "   source venv/bin/activate"
    echo ""
    echo "For Ubuntu Server specific setup, see README.md"
    echo ""
}

# Run main function
main "$@"
