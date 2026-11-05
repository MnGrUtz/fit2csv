# Development & Maintenance Guide

This document is for developers and maintainers of fit2csv.

## 🏗️ Project Structure

### Branches

| Branch | Purpose | Audience |
|--------|---------|----------|
| **`main`** | Full development version | Developers |
| **`distro`** | Simplified distribution | End Users |

### Branch Contents

**`main` branch contains:**
- All source code
- Test files
- Development scripts
- Technical documentation
- Sample files
- Full README with all details

**`distro` branch contains:**
- `fit2csv.py` - Main CLI tool
- `app.py` - Flask web interface
- `templates/` - Flask HTML templates
- `requirements.txt` - Dependencies
- `README.md` - Simplified user documentation

## 🔄 Keeping Distro Branch Up to Date

The `distro` branch should always contain the latest stable version of the essential files. Here's how to update it:

### Method 1: Merge from Main (Recommended)

```bash
# Make sure main is up to date
git checkout main
git pull origin main

# Switch to distro
git checkout distro

# Merge changes from main (only for tracked files)
git merge main --no-commit

# Remove any files that shouldn't be in distro
git reset HEAD -- test_fit2csv.py create_sample_fit.py .gitignore MyWhoosh_Base_Miles_1.fit test

# Remove untracked files
git clean -fd

# Commit the update
git add -A
git commit -m "Update distro branch from main"
git push origin distro
```

### Method 2: Cherry Pick Commits

For specific changes to fit2csv.py or other distro files:

```bash
# Note the commit hash from main
git log main --oneline | head -5

# Switch to distro
git checkout distro

# Cherry pick the specific commit
git cherry-pick <commit-hash>

# Remove any unwanted files that were added
git rm unwanted_file.py

# Commit
git commit --amend -m "Update: <description>"
git push origin distro
```

### Method 3: Manual Copy

For more control, manually copy files from main to distro:

```bash
# Switch to distro
git checkout distro

# Copy specific files from main
git checkout main -- fit2csv.py app.py templates/ requirements.txt

# Update README if needed
git checkout main -- README.md

# Add all changes
git add -A
git commit -m "Update distro: <description of changes>"
git push origin distro
```

## 📝 Version Management

### When to Update Distro

Update the `distro` branch when:
- ✅ Bug fixes in core functionality
- ✅ New features that are stable and tested
- ✅ Security updates
- ✅ Documentation improvements

Do NOT update distro for:
- ❌ Unfinished features
- ❌ Experimental code
- ❌ Development/debug tools
- ❌ Test files

### Version Tags

For major releases, create tags in both branches:

```bash
# Tag main branch
git checkout main
git tag -a v1.0.0 -m "Version 1.0.0"
git push origin v1.0.0

# Tag distro branch
git checkout distro
git tag -a v1.0.0 -m "Version 1.0.0"
git push origin v1.0.0
```

## 🧪 Testing

Before updating distro, test with:

### CLI Tests

```bash
# Single file
python fit2csv.py test.fit -o /tmp/test_output

# Batch processing
mkdir -p /tmp/fit_files
cp *.fit /tmp/fit_files/
python fit2csv.py /tmp/fit_files/ -o /tmp/test_batch

# With verification
python fit2csv.py test.fit -o /tmp/test_verify --verify
```

### Web Interface Tests

```bash
# Start server
python app.py --port 8080

# Test in browser: http://localhost:8080
# Upload a FIT file and verify conversion works
```

### Validation Tests

Check that:
- All output files are created
- CSV files have headers
- JSON files are valid
- No errors are printed
- Record count is reasonable

## 📦 Release Checklist

Before updating distro branch:

- [ ] All tests pass
- [ ] No breaking changes
- [ ] README is up to date
- [ ] requirements.txt has correct versions
- [ ] Code is clean (no debug prints, etc.)
- [ ] Version numbers updated (if applicable)

After updating distro branch:

- [ ] Verify distro branch has only essential files
- [ ] Test download from GitHub
- [ ] Update any links or documentation

## 🤝 Contributing

If you want to contribute to fit2csv:

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Test thoroughly
5. Submit a pull request to `main`

After your PR is merged to `main`, a maintainer will update the `distro` branch.

## 📚 File Descriptions

| File | Purpose |
|------|---------|
| `fit2csv.py` | Main CLI conversion tool |
| `app.py` | Flask web interface |
| `templates/*.html` | Web interface templates |
| `requirements.txt` | Python dependencies |
| `README.md` | User documentation |
| `DEVELOPMENT.md` | This file (maintainer guide) |
| `test_fit2csv.py` | Test script (main only) |
| `create_sample_fit.py` | Sample FIT generator (main only) |
| `.gitignore` | Git ignore patterns (main only) |

## 🎯 Future Improvements

- Automated CI/CD pipeline to auto-update distro
- Version number in output files
- Better error messages
- More validation checks
- Support for additional FIT message types

---

**Maintainers:** Keep this document up to date with any changes to the development process.
