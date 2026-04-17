# HAC MCP

Home Access Center (HAC) is a portal used by school districts. This project logs into HAC, extracts classwork data, and formats it.

## Installation

Install the dependencies using pip or your preferred package manager.

```bash
pip install -r requirements.txt
```

## Configuration

This project requires simple authentication configuration.

### Standalone Script (`.env`)

The command line script reads environment variables. Copy `.env.example` to `.env` and provide your credentials.

```env
HAC_USERNAME=your_username
HAC_PASSWORD=your_password
HAC_DISTRICT_PARSER=leander_isd
```

### MCP Server (`hac_config.json`)

The MCP server uses a JSON file. This structure maps multiple students to shared parent login credentials. This prevents credential duplication across a family. Copy `hac_config.example.json` to `hac_config.json`.

```json
{
  "district_parser": "leander_isd",
  "logins": {
    "parent1": {
      "username": "your_username",
      "password": "your_password"
    }
  },
  "students": {
    "billy": "parent1"
  }
}
```

Currently supported district parsers:

* `leander_isd` (Leander ISD)

## Usage

### Standalone Script

Run `hac.py` from the command line to fetch data or run analytical skills.

```bash
python hac.py --skill missing_last_week
```

### MCP Server

Launch the MCP server to integrate with AI agents. You can restrict access by specifying allowed students.

```bash
HAC_ALLOWED_STUDENTS=billy npx -y @modelcontextprotocol/inspector mcp run mcp_server.py
```

## Architecture

The project contains three main components.

* `hac_client`: A Python library that handles session authentication, data parsing, and caching.
* `hac.py`: A command line interface for direct queries.
* `mcp_server.py`: A server that exposes the library via the Model Context Protocol.

The library uses an eventually consistent cache. Data requests return instantly from a local file. If the cache is older than 60 minutes, a background thread logs in and fetches updates.

## Contributing

District HAC installations use different HTML structures. You can add support for your district by creating a new parser.

1. Add a module in `hac_client/parsers`.
2. Implement a function that accepts raw HTML and returns a `ClassworkReport`.
3. Update `hac_client/parsers/__init__.py` to map your district name to the new parser.

## Development

This project was built autonomously with Antigravity.

## Sample Output

```markdown
## Past Due / Missing Assignments
| Course | Assignment | Due Date | Score |
|---|---|---|---|
| Science 7 | Lesson 13 Chart | 04/09/2026 | |
| Math 7 | Choice Board 5:4 | 03/27/2026 | 0.0 |
| Band MS 2 | Week 5-7 Assignment | 04/16/2026 | |
```
