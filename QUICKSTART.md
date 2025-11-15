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
# Single-Table Version (BEST for 1-5 specific tables - 97% token savings!)
python console_chat_app_single_table.py Chinook.sqlite Album Artist

# Schema-Aware Version (GOOD for small databases < 50 tables)
python console_chat_app_with_schema.py Chinook.sqlite

# Basic Version (LLM explores database as needed)
python console_chat_app.py Chinook.sqlite
```

**Recommendations:**
- **Many tables, need just 1?** → Use single-table version
- **Small database?** → Use schema-aware version
- **Learning Vanna?** → Use basic version to see exploration

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

## 🆚 Three Console App Versions

| Feature | Single-Table | Schema-Aware | Basic |
|---------|--------------|--------------|-------|
| **Speed** | ⚡⚡ Fastest | ⚡ Fast | 🐌 Slower |
| **Token Usage** | 💰 Minimal (~200) | 💸 Moderate (~8K) | 💸 Moderate |
| **Schema Discovery** | Only specified tables | All tables | LLM explores |
| **Best For** | 50 tables, need 1-5 | Small databases | Learning |
| **Accuracy** | ⭐⭐⭐ Highest | ⭐⭐ High | ⭐ Good |

**Recommendations:**
- **Production, focused queries:** Use `console_chat_app_single_table.py` ⭐
- **Development, all tables:** Use `console_chat_app_with_schema.py`
- **Learning/debugging:** Use `console_chat_app.py`

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

## 💰 Single-Table Optimization

See [SINGLE_TABLE_USAGE.md](SINGLE_TABLE_USAGE.md) for:
- Using single-table version with your staffing_table
- 97% token savings analysis (200 vs 8,000 tokens)
- When to use single-table vs full-schema
- Examples and FAQ
