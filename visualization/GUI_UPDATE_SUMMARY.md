# GUI Library Update - Summary

## What Changed

The GUI now loads the tree library from the REST API instead of using hardcoded demo trees.

### Changes Made:

1. **Library Version**: 2.0 → 3.0 (forces browser cache refresh)

2. **New Function**: `loadTreesFromAPI()`
   - Fetches tree catalog from `http://localhost:8000/trees/`
   - Then fetches each full tree from `http://localhost:8000/trees/{tree_id}`
   - Converts API format (TreeDefinition) to GUI format
   - Returns null if API is not available

3. **Updated Function**: `getLibrary()`
   - Now `async`
   - Tries to load from API first
   - Falls back to demo trees if API unavailable
   - Caches result in localStorage

4. **Made Async**: All functions that call `getLibrary()`
   - `loadLibrary()`
   - `openLoadModal()`
   - `confirmSaveToLibrary()`
   - `loadFromLibrary()`
   - `loadFromLibraryAndClose()`

## How It Works

1. When you open the Library tab, it calls `loadLibrary()`
2. `loadLibrary()` calls `await getLibrary()`
3. `getLibrary()` checks localStorage for cached trees
4. If cache is stale (version changed), it calls `loadTreesFromAPI()`
5. If API is running, it fetches all 11 example trees
6. If API is not running, it falls back to 2 hardcoded demo trees

## API Format → GUI Format Conversion

**API Format** (TreeDefinition):
```json
{
  "tree_id": "uuid",
  "metadata": { "name": "...", "description": "...", "created_at": "..." },
  "root": {
    "node_type": "Sequence",
    "name": "Root",
    "config": {},
    "children": [...]
  }
}
```

**GUI Format**:
```json
{
  "id": "uuid",
  "name": "Tree Name",
  "description": "Description",
  "created": "timestamp",
  "nodes": [
    { "id": 1, "type": "Sequence", "name": "Root", "x": 400, "y": 100, ... }
  ],
  "rootNodeId": 1
}
```

The converter:
- Flattens the recursive tree structure into a flat array
- Assigns sequential IDs (1, 2, 3...)
- Positions nodes automatically
- Preserves parent-child relationships

## Testing

### With API Running:
```bash
cd /Users/deniz/Documents/GitHub/TalkingTrees
PYTHONPATH=src python -m talking_trees.api.main
```

Then open `visualization/tree_editor.html` and:
1. Open browser DevTools (F12)
2. Go to Application → Local Storage
3. Delete `pyforest_tree_library` and `pyforest_tree_library_version`
4. Refresh the page
5. Click "Library" tab
6. You should see all 11 example trees!

### Without API Running:
- GUI will show 2 demo trees (Robot Controller, Simple Patrol)
- Both use `CheckBlackboardCondition` (deprecated custom node)
- These are just fallbacks for offline use

## Files Modified

- `visualization/tree_editor.html` - All changes in this one file

## Rollback

If something breaks:
```bash
git checkout visualization/tree_editor.html
```

Or restore from backup:
```bash
cp visualization/tree_editor.html.backup visualization/tree_editor.html
```
