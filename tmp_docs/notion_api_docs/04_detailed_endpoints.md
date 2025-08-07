# Notion API Detailed Endpoints

## Blocks API

### Get Block Children
- **Method**: `GET`
- **URL**: `https://api.notion.com/v1/blocks/{block_id}/children`
- **Purpose**: Returns a paginated array of child block objects
- **Key Points**:
  - Returns only first-level children
  - Requires read content capabilities
  - Supports pagination
  - Page content is represented by block children

### Append Block Children
- **Method**: `PATCH`
- **URL**: `https://api.notion.com/v1/blocks/{block_id}/children`
- **Purpose**: Create and append new child blocks to a parent
- **Key Points**:
  - Appends blocks to the bottom by default
  - Supports up to two levels of nesting
  - Limit of 100 blocks per request
  - Requires insert content capabilities
  - Cannot move existing blocks
  - Optional `after` parameter for placement

### Delete a Block
- **Method**: `DELETE`
- **URL**: `https://api.notion.com/v1/blocks/{block_id}`
- **Purpose**: Archive a block (moves to Trash)
- **Key Points**:
  - Sets `archived: true`
  - Requires update content capabilities
  - Can be restored using Update block endpoint

## Pages API

### Page Object Structure
- **Properties**: `id`, creation/edit timestamps, creator, archival status
- **Optional**: icon, cover, public_url
- **Key Fields**: `properties` (page data), `parent` (database/workspace), `url`
- **Content Access**: Via block children endpoints

### Create a Page
- **Method**: `POST`
- **URL**: `https://api.notion.com/v1/pages`
- **Purpose**: Create page as child of existing page or database
- **Key Points**:
  - Use `title` property for pages under pages
  - Match database schema for database pages
  - Requires Insert Content capabilities
  - Cannot set Notion-generated properties
  - Optional `children` parameter for initial content

## Databases API

### Database Object Structure
- **Key Fields**: `id`, `created_time`, `properties` (schema), `title`, `url`
- **Purpose**: Describes property schema of database
- **Contains**: Pages as items
- **Schema Limit**: 50KB recommended maximum

### Available Operations
- Create a database
- Query a database
- Retrieve a database
- Update database properties

## Search API

### Search Endpoint
- **Method**: `POST`
- **URL**: `https://api.notion.com/v1/search`
- **Purpose**: Search pages and databases by title
- **Key Points**:
  - Searches all shared content with integration
  - Optional filtering for pages/databases only
  - Supports pagination
  - For specific database search, use Query database instead

## Authentication & Capabilities

### Required Capabilities
- **Read Content**: Access to retrieve blocks and pages
- **Insert Content**: Create pages and append blocks
- **Update Content**: Modify and delete blocks

### Integration Types
- **Internal**: Single workspace, member access
- **Public**: Multiple workspaces, OAuth 2.0