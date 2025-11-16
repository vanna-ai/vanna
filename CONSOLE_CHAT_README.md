# Vanna v2 Console Chat App

A simple, transparent console-based chat application for querying SQLite databases using Vanna v2's AI agent. This app provides **full visibility** into the SQL generation and execution process.

## Why Use This Instead of the FastAPI Server?

The console chat app offers several advantages:

- **🔍 Complete Transparency**: See exactly what SQL is being generated
- **⚡ Real-time Updates**: Watch the AI think, generate SQL, and execute queries with timestamps
- **📊 Direct Results**: View query results directly in your terminal as formatted tables
- **🚀 Fast & Lightweight**: No web UI overhead, just pure command-line efficiency
- **📝 Debug-Friendly**: Perfect for understanding how Vanna translates natural language to SQL

## Features

- ✅ Interactive chat interface
- ✅ Real-time SQL query generation display
- ✅ Query execution timing
- ✅ Formatted table results (pandas DataFrames)
- ✅ Streaming responses with thinking indicators
- ✅ Conversation history (persistent within session)
- ✅ Clear visibility into tool calls and LLM reasoning

## Installation

### 1. Install Vanna with Anthropic Support

```bash
pip install -e .[anthropic]
```

Or if you want all features:

```bash
pip install -e .[anthropic,visualization]
```

### 2. Set Your API Key

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Or create a `.env` file:

```bash
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

### 3. Get a SQLite Database

For testing, download the Chinook sample database:

```bash
curl -o Chinook.sqlite https://vanna.ai/Chinook.sqlite
```

Or use your own SQLite database.

## Usage

### Basic Usage

```bash
python console_chat_app.py <path-to-database.db>
```

### Example

```bash
python console_chat_app.py Chinook.sqlite
```

### Sample Session

```
======================================================================
🤖 VANNA v2 CONSOLE CHAT - Interactive SQL Query Assistant
======================================================================
Type your questions in natural language.
The AI will generate and execute SQL queries to answer them.
Commands: 'quit' or 'exit' to end, 'clear' to clear conversation
======================================================================

📊 Database: /home/user/Chinook.sqlite
🤖 Model: claude-sonnet-4-20250514
✅ Ready!

----------------------------------------------------------------------

💬 You: What tables are in this database?

======================================================================
⏱️  [10:30:45.123] Query received
⏱️  [10:30:45.234] 🧠 AI is thinking...

⏱️  [10:30:46.567] 🔧 Tool called: run_sql

📝 Generated SQL Query:
----------------------------------------------------------------------
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;
----------------------------------------------------------------------
⏱️  [10:30:46.789] ⚡ Executing SQL...
⏱️  [10:30:46.892] ✅ Tool execution completed
📊 Query returned: 11 rows × 1 columns

📋 Query Results:
----------------------------------------------------------------------
          name
         Album
        Artist
      Customer
      Employee
         Genre
       Invoice
   InvoiceLine
    MediaType
      Playlist
 PlaylistTrack
         Track
----------------------------------------------------------------------

🤖 Assistant: The database contains 11 tables:
1. Album - Music albums
2. Artist - Music artists
3. Customer - Customer information
4. Employee - Employee data
5. Genre - Music genres
6. Invoice - Purchase invoices
7. InvoiceLine - Individual items in invoices
8. MediaType - Types of media formats
9. Playlist - Music playlists
10. PlaylistTrack - Tracks in playlists
11. Track - Individual music tracks

======================================================================
⏱️  Total time: 2.45s
🔧 Tools used: run_sql
======================================================================

💬 You: Show me the top 5 artists by number of albums

======================================================================
⏱️  [10:31:15.234] Query received
⏱️  [10:31:15.345] 🧠 AI is thinking...

⏱️  [10:31:16.678] 🔧 Tool called: run_sql

📝 Generated SQL Query:
----------------------------------------------------------------------
SELECT a.Name as Artist, COUNT(al.AlbumId) as AlbumCount
FROM Artist a
JOIN Album al ON a.ArtistId = al.ArtistId
GROUP BY a.ArtistId, a.Name
ORDER BY AlbumCount DESC
LIMIT 5;
----------------------------------------------------------------------
⏱️  [10:31:16.890] ⚡ Executing SQL...
⏱️  [10:31:16.998] ✅ Tool execution completed
📊 Query returned: 5 rows × 2 columns

📋 Query Results:
----------------------------------------------------------------------
              Artist  AlbumCount
          Iron Maiden          21
               U2               10
       Led Zeppelin             14
        Metallica                10
      Deep Purple                11
----------------------------------------------------------------------

🤖 Assistant: Here are the top 5 artists by album count:
1. Iron Maiden - 21 albums
2. Led Zeppelin - 14 albums
3. Deep Purple - 11 albums
4. U2 - 10 albums
5. Metallica - 10 albums

======================================================================
⏱️  Total time: 1.87s
🔧 Tools used: run_sql
======================================================================

💬 You: quit

👋 Goodbye!
```

## What You'll See

The console app shows you:

1. **Timestamps**: Exact timing of each operation
2. **Thinking Indicators**: When the AI is processing
3. **Tool Calls**: Which tools the agent decides to use
4. **Generated SQL**: The exact SQL query created by the LLM
5. **Execution Status**: Real-time execution updates
6. **Query Results**: Formatted table output
7. **AI Explanations**: Natural language interpretation of results
8. **Performance Metrics**: Total time and tools used

## Commands

- **Type any question**: The AI will interpret and execute
- **`clear`**: Clear conversation history and start fresh
- **`quit` or `exit`**: Exit the application
- **Ctrl+C**: Interrupt current query

## Configuration

### Using a Different Model

Set the `ANTHROPIC_MODEL` environment variable:

```bash
export ANTHROPIC_MODEL="claude-sonnet-4-20250514"
python console_chat_app.py Chinook.sqlite
```

Available models:
- `claude-sonnet-4-20250514` (default, fast and capable)
- `claude-opus-4-20250514` (most capable, slower)
- `claude-haiku-4-20250301` (fastest, less capable)

### Changing Data Directory

The app stores temporary data in `./console_data/`. You can modify this in the code:

```python
file_system = LocalFileSystem(working_directory="./your_directory")
```

## Example Questions

Try these with the Chinook database:

- "What tables are in this database?"
- "Show me the first 10 customers"
- "Who are the top 5 artists by number of albums?"
- "What's the total revenue by country?"
- "List all employees and their titles"
- "Which genre has the most tracks?"
- "Show me the 10 longest tracks"
- "What's the average invoice total?"

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

Make sure you've exported your API key:

```bash
export ANTHROPIC_API_KEY='your-key-here'
```

### "anthropic integration not installed"

Install the anthropic extra:

```bash
pip install anthropic
```

### "Database file not found"

Ensure the path to your database is correct:

```bash
# Use absolute path
python console_chat_app.py /full/path/to/database.db

# Or relative path from current directory
python console_chat_app.py ./Chinook.sqlite
```

### Slow Responses

- Try using a faster model: `claude-haiku-4-20250301`
- Check your internet connection
- Large query results may take longer to format

## How It Works

1. **User Input**: You type a natural language question
2. **AI Processing**: Claude analyzes the question and database schema
3. **SQL Generation**: The LLM generates appropriate SQL using the `run_sql` tool
4. **Execution**: The SQL is executed against your SQLite database
5. **Results**: Query results are returned as a pandas DataFrame
6. **Presentation**: Results are formatted and displayed in your terminal
7. **Explanation**: The AI explains the results in natural language

## Differences from FastAPI Server

| Feature | Console App | FastAPI Server |
|---------|-------------|----------------|
| **Transparency** | Full visibility into SQL | Limited visibility |
| **Speed** | Fast, no UI overhead | Slower, rendering UI |
| **Results Display** | Direct table output | Web components |
| **Debugging** | Easy to see what's happening | Harder to debug |
| **Use Case** | Development, debugging | Production, end users |
| **Setup** | Single command | Server + browser |

## Advanced Usage

### Custom SQL Runner

You can modify the app to use different databases:

```python
# PostgreSQL
from vanna.integrations.postgres import PostgresRunner
postgres_runner = PostgresRunner(connection_string="postgresql://...")

# MySQL
from vanna.integrations.mysql import MySQLRunner
mysql_runner = MySQLRunner(host="localhost", database="mydb", ...)
```

### Adding More Tools

Add visualization or other tools:

```python
from vanna.tools import VisualizeDataTool

viz_tool = VisualizeDataTool(file_system=file_system)
tool_registry.register(viz_tool)
```

### Verbose Mode

For even more detail, you can print the raw component objects:

```python
async for component in agent.send_message(...):
    print(f"Component type: {type(component)}")
    print(f"Component: {component}")
```

## Contributing

This is a simple example app. Feel free to extend it with:

- Colored output (using `colorama` or `rich`)
- Export results to CSV
- Query history with up/down arrows
- Multi-line query input
- Schema visualization
- SQL syntax highlighting

## License

This app follows the same license as the Vanna project.
