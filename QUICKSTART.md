# Quick Start Guide - Console Chat App

Get up and running with Vanna v2 console chat in 3 simple steps!

## 🚀 Quick Start (3 Steps)

### Step 1: Setup

```bash
# Run the setup script
./setup_demo.sh

# Or manually:
curl -o Chinook.sqlite https://vanna.ai/Chinook.sqlite
export ANTHROPIC_API_KEY='your-key-here'
```

### Step 2: Install Dependencies

```bash
pip install anthropic
```

### Step 3: Run!

**Choose your version:**

```bash
# Schema-Aware Version (RECOMMENDED - 3x faster!)
python console_chat_app_with_schema.py Chinook.sqlite

# Basic Version (LLM explores database as needed)
python console_chat_app.py Chinook.sqlite
```

**Recommendation:** Use the schema-aware version! It's much faster because the LLM knows your database structure from the start.

## 📝 Example Session

```
💬 You: What tables are in this database?

[Shows SQL being generated]
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

[Shows results immediately]
11 tables found: Album, Artist, Customer, Employee...

💬 You: Show me top 5 customers by total purchases

[Generates and executes SQL]
[Shows formatted results table]
[AI explains the findings]
```

## 🎯 Key Features

✅ **See the SQL** - Watch exactly what queries are generated
✅ **Fast** - No web UI overhead
✅ **Transparent** - See thinking, execution, results
✅ **Interactive** - Ask follow-up questions
✅ **Debug-Friendly** - Perfect for understanding Vanna v2

## 💡 Try These Questions

With Chinook database:

```
What tables are in this database?
Show me the first 10 customers
Who are the top 5 artists by number of albums?
What's the total revenue by country?
Which genre has the most tracks?
Show me the 10 longest tracks
What's the average invoice total?
List all employees and their job titles
```

## 🔧 Troubleshooting

**No API key?**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

**Database not found?**
```bash
curl -o Chinook.sqlite https://vanna.ai/Chinook.sqlite
```

**Missing dependencies?**
```bash
pip install anthropic pandas
```

## 📚 Full Documentation

See [CONSOLE_CHAT_README.md](CONSOLE_CHAT_README.md) for complete documentation.

## 🆚 Two Console App Versions

| Feature | Schema-Aware | Basic |
|---------|--------------|-------|
| **Speed** | ⚡ Fast (1 query) | 🐌 Slower (3-4 queries) |
| **Schema Discovery** | Automatic on startup | LLM explores as needed |
| **Best For** | Production use | Learning how Vanna works |
| **Accuracy** | High (knows exact schema) | Good (discovers schema) |

**Recommendation:** Use `console_chat_app_with_schema.py` for best performance!

## 🆚 Console vs FastAPI Server

| Console App | FastAPI Server |
|-------------|----------------|
| See SQL queries | Hidden in UI |
| Direct table output | Web components |
| Fast, no overhead | Slower rendering |
| Great for dev/debug | Great for end users |
| Terminal-based | Browser-based |

**Bottom line:** Use console app when you want to **understand what's happening**!

## 📖 Understanding Schema Discovery

See [SCHEMA_DISCOVERY_EXPLAINED.md](SCHEMA_DISCOVERY_EXPLAINED.md) to learn:
- Why Vanna v2 doesn't automatically provide schema to the LLM
- How the schema-aware version solves this
- Performance comparison (3.5x faster!)
- How to add schema awareness to your own apps
