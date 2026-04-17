# HAC Scraper MCP - Context
This document serves as the primary architectural reference for AI coding agents interacting with or expanding the `hac-mcp` repository.

## Overview
The `hac-mcp` project is a fully-featured, caching Model Context Protocol (MCP) server that securely fetches student classwork, grades, and assignments from the Home Access Center (HAC).

It allows AI Agents to read grades seamlessly by caching HTTP responses and intelligently parsing multi-iframe ASP.NET architecture into LLM-ready markdown formats natively.

## Architecture

1. **`hac_client/`**: The core package.
   - `client.py`: Manages the requests session, handles authentication bypass and tokens, and fetches the Classwork iframe page.
   - `parsers/`: Contains district-specific parser implementations (e.g. `leander_isd`) that use `BeautifulSoup` to scrape `sg-asp-table` elements structurally and parse into type-safe models.
   - `models.py`: Pydantic definitions for `Course`, `Assignment`, and `ClassworkReport`.
   - `cache_manager.py`: An eventually-consistent background caching daemon protecting LLM tool requests from timeouts.
   - `skills.py`: Analytical filters that natively process `ClassworkReport` objects to generate custom markdown lists (e.g. missing assignments, low grades, specific due dates).
   - `formatters.py`: Exposes `to_markdown` and `to_sqlite` converters.

2. **`hac.py`**: A standalone CLI tool that leverages the package directly to run tests locally or fetch analytical output via the `--skill` argument.

3. **`mcp_server.py`**: The final MCP layer that provides integration endpoints using `mcp.server.fastmcp`. Exposes analytical skills and raw fetches natively to the LLM agent using standard IO communication.

## Core Systems & Design Principles

### Asynchronous Daemon Caching
Because LLM agents have restrictive timeouts, performing a live ASP.NET iframe-scraping session per tool call sequentially is prone to failure and UX blockages.
- An eventually-consistent 60-minute TTL `CacheManager` architecture is centrally utilized.
- Stale TTLs trigger re-fetches completely transparently via background daemon threads, ensuring LLM tool calls return instantly from disk caches synchronously and immediately without blocking. 
- Wait periods must only occur locally in `hac.py` during manual shell execution via `thread.join()`, but absolutely never in `mcp_server.py`.
- MCP tools explicitly provide a `force_refresh` boolean parameter.

### Multi-Account Agent Authentication
To support blended families dynamically:
- Primary credentials map sequentially into `hac_config.json`, associating simple student nicknames (e.g. "billy") to parent portal logins to enforce DRY credential management across sibling datasets.
- Built-in Role Based Access: The server instance enforces context via the `HAC_ALLOWED_STUDENTS` environment variable, ensuring isolated kid-version agents cannot access sibling data matrices, while a "Parent" agent can access `"all"`.
