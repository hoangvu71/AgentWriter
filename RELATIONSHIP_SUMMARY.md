# Author-Plot Relationship System

## Overview
The Multi-Agent Book Writer system implements a **one-to-many relationship** where **one author can have multiple plots**. This is the correct relationship for a book writing system.

## Database Schema

### Current Structure (After Migration 004)
```sql
-- Authors table (independent)
CREATE TABLE authors (
    id UUID PRIMARY KEY,
    author_name VARCHAR(255) NOT NULL,
    pen_name VARCHAR(255),
    biography TEXT NOT NULL,
    writing_style TEXT NOT NULL,
    -- No plot_id column
);

-- Plots table (references authors)
CREATE TABLE plots (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    plot_summary TEXT NOT NULL,
    author_id UUID REFERENCES authors(id),  -- Multiple plots per author
    -- Other metadata columns
);
```

### Relationship
- **`plots.author_id → authors.id`**
- **One author → Many plots** ✅
- **One plot → One author** ✅

## Workflow Logic

### Author-First Approach (Recommended)
1. **User Request**: *"Create a fantasy author and a plot for them"*
2. **System Flow**:
   ```
   Orchestrator → Author Agent → Plot Agent
        ↓              ↓             ↓
   Route Request → Create Author → Create Plot
                       ↓             ↓
                   Save Author → Save Plot (with author_id)
   ```
3. **Result**: Author can have additional plots created later

### Standalone Creation
- **Authors**: Can exist without plots (author profiles)
- **Plots**: Can exist without authors (unassigned plots)
- **Assignment**: Plots can be manually assigned to authors

## API Endpoints

### Core Endpoints
- **`GET /api/authors`** - List all authors with plot counts
- **`GET /api/plots`** - List all plots with author information
- **`GET /data/plot/{plot_id}`** - Get plot with author details

### New Methods Added
- **`get_plots_by_author(author_id)`** - Get all plots by specific author
- **`save_plot(..., author_id=None)`** - Save plot with optional author assignment
- **`save_author(...)`** - Save author (no plot_id parameter)

## Library Interface Features

### Author Modals
- **Plot Count**: Shows number of plots by author
- **Plot List**: Scrollable list of all author's plots with metadata
- **Plot Preview**: Title, summary preview, genre tags
- **Author Details**: Biography, writing style, pen name

### Plot Modals  
- **Author Section**: Shows assigned author information
- **Author Biography**: Author background and writing style
- **Author Context**: Link to author's other works
- **Metadata**: Complete plot and author metadata

## Migration Applied

### Migration 004: `reverse_author_plot_relationship.sql`
```sql
-- Add author_id to plots
ALTER TABLE plots ADD COLUMN author_id UUID REFERENCES authors(id);

-- Migrate existing relationships
UPDATE plots SET author_id = (
    SELECT id FROM authors WHERE authors.plot_id = plots.id
);

-- Remove old plot_id from authors
ALTER TABLE authors DROP COLUMN plot_id;

-- Update indexes
CREATE INDEX idx_plots_author_id ON plots(author_id);
DROP INDEX idx_authors_plot_id;
```

**Migration Results**:
- ✅ Migrated 2 existing relationships
- ✅ Preserved all data integrity
- ✅ Updated indexes for performance
- ✅ Verified final structure

## Usage Examples

### Create Author with Plot
```
User: "Create a sci-fi author who writes space operas"
System: 
1. Creates author profile
2. Creates space opera plot assigned to that author
3. Shows both in library with relationship
```

### Add Plot to Existing Author
```
User: "Create another plot for Jake Thompson"
System:
1. Finds existing author "Jake Thompson"
2. Creates new plot assigned to that author
3. Author modal now shows 2 plots
```

### View Author's Works
```
Library Interface:
1. Click on author card
2. Modal shows author details + all their plots
3. Each plot shows preview with metadata
4. Can see author's writing consistency across works
```

## Benefits

### For Users
- **Consistent Authors**: One author can write multiple plots
- **Author Portfolios**: View all works by a specific author
- **Writing Style Consistency**: Author context informs plot generation
- **Flexible Workflow**: Create authors first, then add plots

### For System
- **Proper Relationships**: Database reflects real-world author-book relationships
- **Scalable**: Authors can have unlimited plots
- **Performance**: Optimized indexes for author-plot queries
- **Data Integrity**: Foreign key constraints maintain consistency

## Current Status
- ✅ **Database Migration**: Complete and verified
- ✅ **API Updates**: All endpoints updated for new relationship
- ✅ **UI Enhancement**: Library interface shows relationships
- ✅ **Workflow Logic**: Multi-agent system uses author-first approach
- ✅ **Documentation**: Complete documentation updated

The system now correctly implements **multiple plots per author** with a clean, intuitive interface for managing author-plot relationships.