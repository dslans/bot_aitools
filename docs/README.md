# AI Tools Wiki Bot - Documentation Index

Welcome to the comprehensive documentation for the AI Tools Wiki Slack Bot. This index helps you find the right documentation for your needs.

## 🚀 Getting Started

**New to the project?** Start here:

1. **[Main README](../README.md)** - Project overview and quick start
2. **[Setup Scripts Guide](../scripts/README.md)** - Database setup and initialization
3. **[API Documentation](api/COMMANDS.md)** - Learn all available commands

## 📚 Documentation Categories

### 🔧 For Users
- **[API Documentation](api/COMMANDS.md)** - Complete command reference with examples
- **[Community Tag System](guides/COMMUNITY_TAG_SYSTEM.md)** - How democratic tagging works
- **[Tag Suggestion UX Guide](guides/TAG_SUGGESTION_UX_GUIDE.md)** - User experience and workflows

### 🛠️ For Administrators
- **[Admin Guide](admin/ADMIN_GUIDE.md)** - Admin operations and management tools
- **[Setup Scripts](../scripts/README.md)** - Database setup and migration procedures

### 🚀 For Deployment
- **[Deployment Guide](guides/DEPLOYMENT.md)** - Production deployment to Google Cloud Run
- **[Project Plan](guides/PROJECT_PLAN.md)** - Architecture overview and development roadmap

## 📖 By Topic

### Commands & API
| Document | Description |
|----------|-------------|
| [API Documentation](api/COMMANDS.md) | Complete reference for all bot commands |
| [Admin Guide](admin/ADMIN_GUIDE.md) | Admin-only commands and operations |

### Setup & Configuration
| Document | Description |
|----------|-------------|
| [Setup Scripts](../scripts/README.md) | Database initialization and migration |
| [Deployment Guide](guides/DEPLOYMENT.md) | Production deployment instructions |

### Features & Architecture
| Document | Description |
|----------|-------------|
| [Community Tag System](guides/COMMUNITY_TAG_SYSTEM.md) | Democratic tagging system documentation |
| [Tag Suggestion UX Guide](guides/TAG_SUGGESTION_UX_GUIDE.md) | User experience design principles |
| [Project Plan](guides/PROJECT_PLAN.md) | Complete architecture and roadmap |

## 🎯 Quick Reference

### Essential Commands
```bash
# User commands
/aitools                          # Show help
/aitools-add <title> | <url>      # Add new tool
/aitools-search <keyword>         # Search tools
/aitools-list [tag]               # List tools
/aitools-top [limit]              # Show top-rated tools
/aitools-tags                     # Browse tags
/aitools-suggest-tag <id> <tag>   # Suggest community tag

# Admin commands (require admin permissions)
/aitools-admin-list [limit]       # Manage entries
/aitools-admin-edit <id>          # Edit entry
/aitools-admin-tags               # Manage tag suggestions
/aitools-admin-retag <id>         # Regenerate AI content
/aitools-admin-delete <id>        # Delete entry
```

### Quick Setup
```bash
# Local development
python scripts/setup.py          # Set up database
python app.py                    # Run bot locally

# Production deployment
./scripts/deploy.sh              # Deploy to Cloud Run
```

## 📁 Documentation Structure

```
docs/
├── README.md                    # This index file
├── api/
│   └── COMMANDS.md             # Complete API documentation
├── admin/
│   └── ADMIN_GUIDE.md          # Admin operations guide
└── guides/
    ├── DEPLOYMENT.md           # Production deployment guide
    ├── PROJECT_PLAN.md         # Architecture and roadmap
    ├── COMMUNITY_TAG_SYSTEM.md # Tag system documentation
    └── TAG_SUGGESTION_UX_GUIDE.md # UX design guide
```

## 🔄 Recent Updates

- **✅ Added `/aitools-top` command** - Show top-rated tools by score with optional limit
- **✅ Documentation reorganization** - Improved structure with categorized guides
- **✅ Updated Google GenAI SDK** - Upgraded to v1.31.0 for better performance
- **✅ Enhanced API documentation** - Comprehensive command reference with examples

## 🆘 Need Help?

### For Users
- Check [API Documentation](api/COMMANDS.md) for command syntax and examples
- Review [Community Tag System](guides/COMMUNITY_TAG_SYSTEM.md) for tagging help

### For Admins
- See [Admin Guide](admin/ADMIN_GUIDE.md) for management operations
- Check [Deployment Guide](guides/DEPLOYMENT.md) for production setup

### For Developers
- Review [Project Plan](guides/PROJECT_PLAN.md) for architecture details
- Check database setup in [Setup Scripts](../scripts/README.md)

---

**Happy building!** 🚀 The AI Tools Wiki Bot is designed to make AI tool discovery and sharing effortless for your team.
