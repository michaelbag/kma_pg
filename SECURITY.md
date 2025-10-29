# Security Guidelines

## Password Protection

This repository is configured to **exclude all configuration files containing real passwords** from version control.

### Files Excluded from Repository

The following files are **ignored** by `.gitignore`:

- `config/config.yaml` - Main configuration file (may contain passwords)
- `config/databases/*.yaml` - Database-specific configurations (except example files)
  - ✅ `config/databases/1c-srv-rhana-local.yaml` - **EXCLUDED** (contains real passwords)
  - ✅ All other production/test configurations - **EXCLUDED**

### Files Included in Repository

Only **example configuration files** are tracked:

- `config/config.example.yaml` - Example main configuration
- `config/databases/example_*.yaml` - Example database configurations
  - These files contain **placeholder passwords** (e.g., `your_password`, `your_secure_password`)

### Security Checks

Before committing changes, always verify:

1. ✅ No real passwords in tracked files
2. ✅ Production/test configurations are properly ignored
3. ✅ Only example files with placeholders are committed

### Verification Commands

```bash
# Check if sensitive files are ignored
git check-ignore -v config/databases/1c-srv-rhana-local.yaml

# List ignored files
git status --ignored | grep config

# Search for passwords in tracked files
git grep -i "password" | grep -v example
```

### Best Practices

1. **Never commit** files with real passwords
2. **Use environment variables** for sensitive data when possible
3. **Use placeholder passwords** in example files
4. **Review .gitignore** before adding new configuration files
5. **Regular security audits** of repository content

---

**Last Security Audit:** $(date)
**Status:** ✅ All sensitive files properly excluded
