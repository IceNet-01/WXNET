# Contributing to WXNET

Thank you for your interest in contributing to WXNET! This document provides guidelines and instructions for contributing.

## Ways to Contribute

### 1. Report Bugs
- Use the GitHub issue tracker
- Include detailed reproduction steps
- Provide system information (OS, Python version)
- Include error messages and logs

### 2. Suggest Features
- Open a feature request issue
- Describe the use case
- Explain how it benefits users
- Consider implementation complexity

### 3. Submit Code
- Fork the repository
- Create a feature branch
- Write clean, documented code
- Include tests if applicable
- Submit a pull request

### 4. Improve Documentation
- Fix typos and errors
- Add examples
- Clarify confusing sections
- Translate to other languages

### 5. Share Experience
- Write tutorials
- Create videos
- Share on social media
- Help other users

## Development Setup

### 1. Fork and Clone
First, fork the repository on GitHub: https://github.com/IceNet-01/WXNET

Then clone your fork:
```bash
git clone https://github.com/YOUR-USERNAME/WXNET.git
cd WXNET
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists
```

### 4. Run in Development Mode
```bash
python3 wxnet.py
```

## Code Style

### Python
- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for functions/classes
- Keep functions focused and small

### Example
```python
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula.
    
    Args:
        lat1: Latitude of first point
        lon1: Longitude of first point
        lat2: Latitude of second point
        lon2: Longitude of second point
        
    Returns:
        Distance in miles
    """
    # Implementation here
    pass
```

## Project Structure

```
WXNET/
├── wxnet/              # Main package
│   ├── api/           # API clients
│   ├── ui/            # TUI components
│   ├── models.py      # Data models
│   ├── config.py      # Configuration
│   ├── utils.py       # Utilities
│   └── app.py         # Main application
├── docs/              # Documentation
├── tests/             # Test suite
├── install.sh         # Installer
├── update.sh          # Updater
└── uninstall.sh       # Uninstaller
```

## Pull Request Process

### 1. Create Feature Branch
```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes
- Write code
- Add tests
- Update documentation
- Test thoroughly

### 3. Commit Changes
```bash
git add .
git commit -m "Add feature: description"
```

Use clear commit messages:
- `Add: New feature`
- `Fix: Bug description`
- `Update: Component changes`
- `Docs: Documentation updates`

### 4. Push and Create PR
```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

### 5. PR Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Meaningful commit messages

## Feature Ideas

### High Priority
- [ ] Real lightning data integration
- [ ] Satellite imagery overlay
- [ ] Enhanced cell tracking algorithms
- [ ] Historical storm data analysis
- [ ] Mobile app companion

### Medium Priority
- [ ] Sound alerts for warnings
- [ ] Push notifications
- [ ] Multiple location monitoring
- [ ] Custom alert filters
- [ ] Data export features

### Low Priority
- [ ] Themes and color schemes
- [ ] Plugin system
- [ ] International weather services
- [ ] Web dashboard
- [ ] API for third-party apps

## Testing

### Manual Testing
```bash
# Run the application
python3 wxnet.py

# Test different locations
# Test alert handling
# Test radar display
# Test error conditions
```

### Automated Testing (when implemented)
```bash
pytest tests/
```

## Documentation

### Code Documentation
- Use docstrings
- Include type hints
- Add inline comments for complex logic
- Update README for new features

### User Documentation
- Update README.md
- Add to QUICKSTART.md
- Include examples
- Document configuration options

## API Integration

### Adding New Data Sources

1. Create client in `wxnet/api/`
2. Add models in `wxnet/models.py`
3. Update UI components
4. Add configuration options
5. Document the integration

### Example: Adding Lightning Data
```python
# wxnet/api/lightning.py
class LightningClient:
    """Client for lightning data."""
    
    async def get_strikes(self, lat, lon, radius):
        """Fetch lightning strikes in area."""
        pass
```

## UI Components

### Adding New Widgets

1. Create widget in `wxnet/ui/`
2. Inherit from Textual widgets
3. Implement reactive properties
4. Add to main app layout
5. Document keyboard shortcuts

## Release Process

### Version Numbering
- Major.Minor.Patch (e.g., 1.2.3)
- Major: Breaking changes
- Minor: New features
- Patch: Bug fixes

### Creating a Release
1. Update version in `setup.py`
2. Update CHANGELOG.md
3. Create git tag
4. Push to GitHub
5. Create GitHub release

## Community Guidelines

### Be Respectful
- Treat everyone with respect
- Welcome newcomers
- Provide constructive feedback
- Help others learn

### Stay On Topic
- Keep discussions relevant
- Use appropriate channels
- Search before posting

### Quality Over Quantity
- Test your code
- Write clear documentation
- Provide helpful examples

## Getting Help

### Questions?
- Check existing issues
- Read documentation
- Ask in discussions
- Contact maintainers

### Found a Security Issue?
- DO NOT open a public issue
- Email: security@wxnet.example.com
- Provide detailed description
- Allow time for fix before disclosure

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for making WXNET better!** ⛈️

Together we're building the best severe weather monitoring tool for storm chasers and weather enthusiasts worldwide.
