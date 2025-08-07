# Notion API Reference Overview

*Fetched from: https://developers.notion.com/reference/intro*

## API Overview
- **Base URL**: `https://api.notion.com`
- **Protocol**: Requires HTTPS
- **Style**: RESTful conventions with `GET`, `POST`, `PATCH`, and `DELETE` requests
- **Format**: JSON-encoded requests and responses

## Key Conventions
- Resources have an `"object"` property identifying resource type
- Resources use UUIDv4 `"id"` properties
- Property names use `snake_case`
- Dates in ISO 8601 format

## Major Endpoint Categories
1. **Authentication** - Token management
2. **Blocks** - Content manipulation
3. **Pages** - Page operations
4. **Databases** - Database operations
5. **Comments** - Comment management
6. **File Uploads** - File handling
7. **Search** - Content search
8. **Users** - User management

## Pagination Features
- **Default**: 10 items per call
- **Maximum**: 100 items per page
- **Type**: Cursor-based pagination
- **Endpoints with pagination**:
  - List all users
  - Retrieve block children
  - Retrieve comments
  - Query database
  - Search

## Authentication
- Requires integration token
- Can create, introspect, revoke, and refresh tokens

## Key Objects
- Block
- Page
- Database
- Comment
- File
- User
- Parent
- Emoji