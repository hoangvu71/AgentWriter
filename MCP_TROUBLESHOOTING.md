# MCP Supabase Troubleshooting Guide

## Issue: MCP Supabase Tools Not Showing in Agent Editor

### Root Cause
The MCP Supabase server requires environment variables to be set as **system environment variables**, not just in the `.env` file. Claude Code's MCP integration doesn't automatically load from `.env` files.

### Current Status
- ✅ MCP configuration in `.claude/mcp.json` is correct
- ✅ Supabase credentials are in `.env` file
- ❌ Environment variables not available to MCP server
- ❌ MCP tools not appearing in agent tool selection

### Solution Options

#### Option 1: Set System Environment Variables (Recommended)

**Windows (Command Prompt):**
```cmd
cd C:\Users\hoang\Documents\BooksWriter
setup_mcp_env.bat
```

**Windows (PowerShell):**
```powershell
cd C:\Users\hoang\Documents\BooksWriter
$env:SUPABASE_URL = "https://cfqgzbudjnvtyxrrvvmo.supabase.co"
$env:SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNmcWd6YnVkam52dHl4cnJ2dm1vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI2MDc4NTcsImV4cCI6MjA2ODE4Mzg1N30.htAv5kEmCFYdpGwhczSclA26pBDofhkMHu4OPmARp6w"
$env:SUPABASE_ACCESS_TOKEN = "sbp_52daeb2d737663036052abc28d90aa4cefdb3e4d"
```

**After setting variables:**
1. **Restart Claude Code completely**
2. Navigate back to your project
3. Try `/agents` again
4. Check if MCP tools appear under "MCP & Other tools"

#### Option 2: Modify MCP Configuration

Update `.claude/mcp.json` to include all required environment variables:

```json
{
  "servers": {
    "supabase": {
      "command": "npx",
      "args": [
        "@supabase/mcp-server-supabase@latest"
      ],
      "env": {
        "SUPABASE_URL": "https://cfqgzbudjnvtyxrrvvmo.supabase.co",
        "SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNmcWd6YnVkam52dHl4cnJ2dm1vIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI2MDc4NTcsImV4cCI6MjA2ODE4Mzg1N30.htAv5kEmCFYdpGwhczSclA26pBDofhkMHu4OPmARp6w",
        "SUPABASE_ACCESS_TOKEN": "sbp_52daeb2d737663036052abc28d90aa4cefdb3e4d"
      }
    }
  }
}
```

### Verification Steps

#### 1. Check Environment Variables
```cmd
echo %SUPABASE_ACCESS_TOKEN%
```
Should output: `sbp_52daeb2d737663036052abc28d90aa4cefdb3e4d`

#### 2. Test MCP Server
```cmd
npx @supabase/mcp-server-supabase@latest
```
Should start without errors and wait for input.

#### 3. Check Agent Tools
1. Run `/agents` in Claude Code
2. Select any agent (e.g., tech-lead-architect)
3. Look for MCP tools in the tool selection menu
4. Should see tools like:
   - `mcp__supabase__list_tables`
   - `mcp__supabase__describe_table`
   - `mcp__supabase__query`

### Expected MCP Tools

Once working, you should see these tools available to agents:

**Database Query Tools:**
- `mcp__supabase__list_tables` - Get all table names
- `mcp__supabase__describe_table` - Get table schema details
- `mcp__supabase__query` - Execute SQL queries
- `mcp__supabase__count` - Count records with filters

**Data Modification Tools:**
- `mcp__supabase__insert` - Insert new records
- `mcp__supabase__update` - Update existing records
- `mcp__supabase__delete` - Delete records

### Common Issues

#### Issue: "Unknown option" error when testing MCP server
**Solution:** This is normal - the MCP server expects JSON-RPC communication, not command line arguments.

#### Issue: Environment variables not persisting
**Solution:** Use `setx` command instead of `set` to make variables permanent.

#### Issue: MCP server starts but no tools appear
**Solution:** Check Claude Code logs for MCP connection errors.

#### Issue: Authentication errors
**Solution:** Verify the SUPABASE_ACCESS_TOKEN is correct and has proper permissions.

### Testing MCP Integration

Once MCP tools are available to agents, test with:

```
/agents debug-master
"Test MCP connection by listing all database tables using mcp__supabase__list_tables() and show the count of records in the authors table using mcp__supabase__count(table_name='authors')"
```

Expected output should include:
- List of all 18+ database tables
- Confirmation that authors table has 28 records

### Security Notes

⚠️ **Important:** The MCP configuration now contains sensitive credentials. Ensure:
1. `.claude/mcp.json` is not committed to version control
2. Add `.claude/mcp.json` to `.gitignore` if using hardcoded credentials
3. Consider using environment variable references when possible

### Next Steps After Fix

1. **Update agent configurations** to include MCP tool awareness
2. **Test each agent type** with MCP tools
3. **Create MCP-enhanced workflows** for database operations
4. **Document successful MCP usage patterns** for team use

This troubleshooting should resolve the MCP tool availability issue and make Supabase tools accessible to all Claude Code agents.