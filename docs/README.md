# 📚 docs Directory

This directory contains comprehensive documentation, architecture diagrams, and visual assets for the NL2DAX project.

## 📋 Overview

The docs directory serves as the central repository for all project documentation, including:
- Architecture diagrams and flowcharts
- API documentation and integration guides
- Troubleshooting guides and FAQs
- Visual assets and screenshots
- Setup and configuration documentation

## 📁 Structure

```
docs/
├── images/                    # Visual assets and diagrams
│   ├── architecture/         # System architecture diagrams
│   ├── screenshots/          # Application screenshots
│   ├── workflows/            # Process flow diagrams
│   └── logos/               # Project logos and branding
├── api/                      # API documentation
├── guides/                   # Step-by-step guides
├── troubleshooting/          # Problem resolution guides
├── export-diagrams.sh        # Diagram generation script
└── README.md                 # This file
```

## 🖼️ Visual Assets

### images/ Directory

The images directory contains all visual assets organized by category:

#### architecture/
- `system-overview.png` - High-level system architecture
- `data-flow.png` - Data flow through the pipeline
- `component-diagram.png` - Detailed component relationships
- `deployment-diagram.png` - Deployment architecture

#### screenshots/
- `main-interface.png` - Main application interface
- `query-results.png` - Example query results
- `configuration-screens.png` - Setup screenshots
- `error-examples.png` - Common error messages

#### workflows/
- `nl2dax-process.png` - Natural language to DAX workflow
- `authentication-flow.png` - Service principal authentication
- `troubleshooting-flowchart.png` - Problem resolution process

#### logos/
- `nl2dax-logo.png` - Project logo
- `nl2dax-icon.ico` - Application icon
- `badge-assets/` - GitHub badge SVGs

## 📊 Diagram Generation

### export-diagrams.sh

This script automatically generates PNG images from Mermaid diagrams in the main README.

**Usage:**
```bash
chmod +x export-diagrams.sh
./export-diagrams.sh
```

**Requirements:**
```bash
# Install Mermaid CLI
npm install -g @mermaid-js/mermaid-cli
```

**Generated files:**
- `images/diagram_0.png` - Architecture diagram
- `images/diagram_1.png` - Schema diagram
- `images/diagram_2.png` - Pipeline flow diagram

**Script features:**
- Extracts Mermaid code from README.md
- Generates high-quality PNG images
- Optimizes for GitHub display
- Maintains consistent styling

### Manual Diagram Creation

For custom diagrams not in the README:

```bash
# Create diagram from file
mmdc -i source-diagram.mmd -o output-diagram.png

# Specify theme and size
mmdc -i diagram.mmd -o diagram.png -t dark -w 1024 -H 768

# Generate SVG instead of PNG
mmdc -i diagram.mmd -o diagram.svg -f
```

## 📖 Documentation Structure

### API Documentation (api/)

**Planned contents:**
- `rest-api.md` - Power BI REST API integration
- `xmla-endpoints.md` - XMLA endpoint documentation
- `authentication.md` - Service principal auth guide
- `rate-limits.md` - API rate limiting information

### User Guides (guides/)

**Planned contents:**
- `quick-start.md` - 5-minute setup guide
- `configuration.md` - Detailed configuration options
- `advanced-usage.md` - Advanced features and tips
- `best-practices.md` - Recommended usage patterns
- `migration.md` - Migrating from previous versions

### Troubleshooting (troubleshooting/)

**Planned contents:**
- `common-issues.md` - Frequently encountered problems
- `authentication-errors.md` - Auth-specific troubleshooting
- `performance-tuning.md` - Performance optimization
- `error-codes.md` - Complete error code reference

## 🎨 Style Guide

### Diagram Standards

**Color Palette:**
- Primary: #0078D4 (Microsoft Blue)
- Secondary: #106EBE (Dark Blue)
- Success: #107C10 (Green)
- Warning: #FFB900 (Yellow)
- Error: #D13438 (Red)
- Neutral: #605E5C (Gray)

**Typography:**
- Headers: Segoe UI, sans-serif
- Body: Segoe UI, Tahoma, Geneva, Verdana, sans-serif
- Code: Consolas, Monaco, 'Courier New', monospace

**Diagram Conventions:**
- Use consistent shapes for similar components
- Maintain visual hierarchy with size and color
- Include legends for complex diagrams
- Optimize for both light and dark themes

### Documentation Standards

**Markdown Style:**
- Use semantic headers (H1 for titles, H2 for sections)
- Include code syntax highlighting
- Use tables for structured data
- Include emoji for visual hierarchy (sparingly)

**Code Examples:**
```markdown
# Always include language specification
```bash
echo "Shell commands"
```

```python
# Python code examples
def example_function():
    return "Hello, World!"
```

```powershell
# PowerShell examples
Write-Host "PowerShell commands"
```
```

## 🔧 Asset Management

### Image Optimization

**Guidelines:**
- Use PNG for screenshots and complex diagrams
- Use SVG for simple icons and logos
- Optimize file sizes for web display
- Maintain high DPI versions for documentation

**Tools:**
```bash
# Optimize PNG files
optipng -o7 *.png

# Convert to WebP for better compression
cwebp -q 80 input.png -o output.webp

# Resize images
convert input.png -resize 800x600 output.png
```

### Version Control

**File naming:**
- Use descriptive names: `authentication-flow-v2.png`
- Include version numbers for major changes
- Use kebab-case for filenames
- Avoid spaces and special characters

**Organization:**
- Group related assets in subdirectories
- Maintain consistent directory structure
- Use README files in each subdirectory
- Keep assets close to related documentation

## 📋 Content Templates

### New Documentation Template

```markdown
# [Document Title]

## Overview
Brief description of what this document covers.

## Prerequisites
- Requirement 1
- Requirement 2

## Step-by-Step Guide

### Step 1: [Action]
Detailed instructions...

### Step 2: [Action]
More instructions...

## Troubleshooting
Common issues and solutions.

## Related Documentation
- [Related Doc 1](./related-doc-1.md)
- [Related Doc 2](./related-doc-2.md)
```

### Diagram Template

```mermaid
---
title: [Diagram Title]
---
[Diagram Type]
    [Content]
```

## 🔍 Quality Checklist

### Documentation Review

- [ ] Spelling and grammar checked
- [ ] Code examples tested
- [ ] Links verified (internal and external)
- [ ] Screenshots current and accurate
- [ ] Consistent formatting applied
- [ ] Cross-references updated

### Diagram Review

- [ ] All text readable at standard zoom
- [ ] Color contrast sufficient
- [ ] Consistent with style guide
- [ ] Exported in correct format
- [ ] Optimized file size
- [ ] Accessible alt text provided

## 🔄 Maintenance

### Regular Updates

**Monthly:**
- Review screenshots for UI changes
- Update version numbers in examples
- Check external links for validity
- Regenerate diagrams if source changed

**Quarterly:**
- Comprehensive style guide review
- Asset optimization pass
- Documentation structure evaluation
- User feedback incorporation

### Automation

**Planned scripts:**
```bash
# Link checker
./scripts/check-links.sh

# Image optimizer
./scripts/optimize-images.sh

# Documentation validator
./scripts/validate-docs.sh
```

## 📊 Analytics and Metrics

### Documentation Usage

Track which documentation is most valuable:
- Page view analytics (if hosted)
- GitHub insights for README views
- Issue references to documentation
- Community feedback and contributions

### Asset Performance

Monitor asset effectiveness:
- Image load times
- File size optimization opportunities
- Format compatibility across platforms
- Accessibility compliance

---

💡 **Tip**: When adding new documentation, always include visual aids and practical examples. Users learn faster with concrete examples than abstract explanations.
