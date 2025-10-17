# PyForest Major Refactoring Plan

**Date:** 2025-10-17
**Status:** IN PROGRESS
**Goal:** Fix all critical serializer issues to make PyForest production-ready

---

## 🎯 User Requirements & Insights

### Key User Insights (Chronological)

1. **GUI Metadata Pollution** (Critical Design Flaw)
   > "i dont think any one will ever care about the GUI related info being saved to the JSON, rather the GUI visualizer should just have a standard rule for positioning nodes etc onto the page"

   **Impact:** JSON should be pure tree semantics, not UI state

2. **Blackboard Separation** (Architectural Change)
   > "we shouldnt need to include anything backboard related into the serilization, only whats contained in the tree, blackboard stuff may eventually be a database or some other api sending data to some database etc"

   **Impact:** Blackboard data is runtime state, not tree structure

3. **Data Source Concept**
   > "unless it's like check black board for something etc, so perhaps we design it such that the data source can be pointed at, e.g. load tree with data_source = bb or soemthing"

   **Impact:** Trees should reference external data sources, not embed data

4. **Visualization Auto-Layout**
   > "also if you remove ui metadata you need to ensure the visulization code can automatically position things, so you need to propogate these low level changes throughout the repo"

   **Impact:** Must implement auto-layout algorithm in visualizer

5. **Comprehensive Refactoring**
   > "ok we need to fix all of these, ultrathink"

   **Impact:** Fix ALL issues in SERIALIZER_ANALYSIS.md

6. **Documentation & Planning**
   > "you may want to record all the prompts i recently sent you so you dont get lost eventualyt, so since were addressing major refactors keep a detailed plan youcan reference"

   **Impact:** Create this document!

---

## 📋 Refactoring Checklist

### Phase 1: Data Model Cleanup ✅ (70% Complete)

- [x] **Remove UIMetadata class** from tree.py
- [x] **Remove ui_metadata field** from TreeNodeDefinition
- [x] **Add description field** to TreeNodeDefinition (optional semantic notes)
- [x] **Update serializer.py** to not use ui_metadata
- [x] **Update diff.py** to not compare ui_metadata
- [ ] **Update existing JSON files** to remove ui_metadata (migration needed)

### Phase 2: SetBlackboardVariable Data Loss Fix ✅ DONE

- [x] **Add value extraction** using reflection (multiple approaches)
  - Try `_value` attribute (private)
  - Try `variable_value` (older API)
  - Try `__dict__['_value']` (fallback)
- [x] **Add warning** if value cannot be extracted
- [ ] **Test round-trip** conversion with SetBlackboardVariable

### Phase 3: ComparisonExpression Abstraction ✅ DONE

- [x] **Create ComparisonExpressionExtractor class**
  - Clear method names (`extract`, `create`)
  - Documents py_trees quirk (operator/value swap)
- [x] **Update _extract_config()** to use abstraction
- [x] **Update _collect_blackboard_variables()** to use abstraction
- [ ] **Update tests** to use abstraction

### Phase 4: Deterministic UUIDs ⏳ PENDING

- [ ] **Implement UUID generation** based on node structure
  - Use SHA-256 hash of (type, name, path, config)
  - Ensures same node → same UUID
- [ ] **Add optional uuid_map** parameter to `from_py_trees()`
- [ ] **Update adapter** to use deterministic UUIDs
- [ ] **Test UUID stability** across multiple conversions

### Phase 5: Conversion Warnings ⏳ PENDING

- [ ] **Create ConversionContext class**
  - `warnings: List[str]`
  - `warn(message, node_name)` method
- [ ] **Update from_py_trees()** to return `(TreeDefinition, ConversionContext)`
- [ ] **Add warnings** for:
  - SetBlackboardVariable value not accessible
  - Unknown node type (falls back to Action)
  - Type inference fails
  - Parallel policy unsupported
- [ ] **Update examples** to check warnings

### Phase 6: Round-Trip Validation ⏳ PENDING

- [ ] **Create RoundTripValidator class**
  - `validate(original, round_trip)` method
  - `assert_equivalent(original, round_trip)` method
- [ ] **Check validations:**
  - Same number of nodes
  - Same node types
  - Same node names
  - Same configurations
  - Same structure
  - SetBlackboardVariable values preserved
- [ ] **Add to test suite**
- [ ] **Document limitations**

### Phase 7: Type Inference Improvements ⏳ PENDING

- [ ] **Extend _infer_type()** function
  - Support `list`, `dict`, `tuple`
  - Support `None` (nullable types)
  - Support nested structures
  - Return JSON Schema format
- [ ] **Update blackboard schema** generation
- [ ] **Add type validation** option

### Phase 8: Security Hardening ⏳ PENDING

- [ ] **Add cycle detection** in subtree resolution
  - Track visited refs with set
  - Raise ValueError on circular refs
- [ ] **Add depth limits**
  - Max depth configurable (default 100)
  - Raise ValueError if exceeded
- [ ] **Add class whitelist** for custom behaviors
  - Prevent arbitrary code execution
  - Document whitelisting API

### Phase 9: Blackboard Architecture Change ⏳ PENDING

**Critical architectural decision based on user insight:**

- [ ] **Remove blackboard_schema** from TreeDefinition
  - Tree only contains logic (check X, set Y)
  - Blackboard data comes from external sources
- [ ] **Add data_source concept** to execution
  - `execution = pf.create_execution(tree, data_source=...)`
  - Data source can be: blackboard, database, API, etc.
- [ ] **Update execution engine** to accept external data
- [ ] **Document new architecture**
- [ ] **Migrate existing code**

### Phase 10: Visualization Auto-Layout ⏳ PENDING

**Required due to ui_metadata removal:**

- [ ] **Implement auto-layout algorithm** in tree_editor_pro.html
  - Hierarchical layout (parent above children)
  - Balanced tree spacing
  - Depth-first left-to-right positioning
  - Deterministic (same tree → same layout)
- [ ] **Remove ui_metadata** from visualization code
- [ ] **Store UI state** in localStorage (optional)
  - Separate from tree JSON
  - Per-tree-id preferences
- [ ] **Test layout** with various tree structures
- [ ] **Document layout algorithm**

### Phase 11: Testing & Migration ⏳ PENDING

- [ ] **Update all tests** for new serializer
  - test_py_trees_adapter.py
  - test_integration.py
  - test_rest_api_integration.py
- [ ] **Add new tests**:
  - Round-trip preservation
  - SetBlackboardVariable value extraction
  - Deterministic UUID generation
  - Conversion warnings
  - Security (cycle detection, depth limits)
- [ ] **Migration script** for existing JSON files
  - Strip ui_metadata
  - Strip blackboard_schema (optional)
  - Preserve all tree logic
- [ ] **Test migration** on examples/tutorials

---

## 🏗️ Current Progress

### ✅ Completed (3/11 phases)

1. **Data Model Cleanup** - 70% complete
   - UIMetadata removed from code
   - description field added
   - Migration script still needed

2. **SetBlackboardVariable Fix** - 100% complete
   - Value extraction with 3 fallback approaches
   - Warning added for data loss
   - Round-trip testing still needed

3. **ComparisonExpression Abstraction** - 100% complete
   - Clean abstraction layer created
   - All usages updated
   - Much clearer code

### ⏳ In Progress (0/11 phases)

None currently active

### ⏸️ Pending (8/11 phases)

4. Deterministic UUIDs
5. Conversion Warnings
6. Round-Trip Validation
7. Type Inference
8. Security Hardening
9. Blackboard Architecture
10. Visualization Auto-Layout
11. Testing & Migration

---

## 📊 Impact Analysis

### Breaking Changes

1. **ui_metadata removed** - Visualization code needs update
2. **blackboard_schema optional/removed** - Execution engine needs update
3. **from_py_trees() returns tuple** - API change for warnings

### Non-Breaking Enhancements

1. **SetBlackboardVariable value preserved** - Better round-trip
2. **ComparisonExpression abstraction** - Internal improvement
3. **Deterministic UUIDs** - Opt-in via parameter
4. **Conversion warnings** - Additional return value

### Migration Required

1. **Existing JSON files** - Need ui_metadata stripped
2. **Visualization HTML** - Need auto-layout implementation
3. **Examples/tutorials** - Need blackboard_schema handling update
4. **Tests** - Need updates for new API

---

## 🎯 Success Criteria

### Must Have (Critical)

- [ ] No data loss in round-trip conversion
- [ ] Clean JSON (no GUI pollution)
- [ ] Deterministic UUIDs
- [ ] Conversion warnings visible
- [ ] Auto-layout working in visualizer

### Should Have (Important)

- [ ] Round-trip validation in tests
- [ ] Security hardening (cycle detection)
- [ ] Improved type inference
- [ ] All tests passing

### Nice to Have (Optional)

- [ ] Blackboard architecture redesign
- [ ] Migration script for old JSONs
- [ ] Performance optimizations

---

## 🔄 Iteration Strategy

### Current Iteration (Iteration 1)

**Focus:** Core serializer fixes

**Tasks:**
1. ✅ Remove ui_metadata
2. ✅ Fix SetBlackboardVariable
3. ✅ Add ComparisonExpression abstraction
4. ⏳ Implement deterministic UUIDs
5. ⏳ Add conversion warnings
6. ⏳ Create round-trip validator

**Goal:** Lossless, validated, clean serialization

### Next Iteration (Iteration 2)

**Focus:** Visualization & architecture

**Tasks:**
1. Implement auto-layout algorithm
2. Remove ui_metadata from HTML/JS
3. Redesign blackboard architecture
4. Update execution engine

**Goal:** Clean separation of concerns, no UI in data

### Final Iteration (Iteration 3)

**Focus:** Testing & hardening

**Tasks:**
1. Update all tests
2. Add security hardening
3. Improve type inference
4. Migration script
5. Documentation

**Goal:** Production-ready, well-tested, documented

---

## 📝 Notes & Decisions

### Design Decisions

1. **ui_metadata removal:** Store UI state client-side only, not in tree JSON
2. **blackboard_schema optional:** Tree logic separate from data schema
3. **SetBlackboardVariable reflection:** Use private attributes as last resort
4. **ComparisonExpression abstraction:** Hide py_trees' confusing API
5. **Deterministic UUIDs:** Hash-based for version control friendliness

### Technical Debt

- [ ] Custom behavior plugin system (deferred)
- [ ] Parallel SuccessOnSelected support (incomplete)
- [ ] Performance optimizations (single-pass conversion)

### Open Questions

1. **Blackboard architecture:** How to point trees at data sources?
   - Option A: `execution = pf.create_execution(tree, blackboard=bb)`
   - Option B: `execution = pf.create_execution(tree, data_source=db)`
   - Option C: `tree.bind_data_source(db)` then `execution = pf.create_execution(tree)`

2. **UI state storage:** Where to persist layout preferences?
   - Option A: Browser localStorage (per-tree-id)
   - Option B: Separate `.ui.json` file alongside tree JSON
   - Option C: Server-side user preferences

3. **Migration strategy:** How to handle old JSON files?
   - Option A: Auto-migrate on load (transparent)
   - Option B: Explicit migration script (one-time)
   - Option C: Support both formats (backward compatible)

---

## 🚀 Next Steps

**Immediate (This Session):**
1. ✅ Document refactoring plan (this file)
2. ⏳ Implement deterministic UUIDs
3. ⏳ Add ConversionContext warnings
4. ⏳ Create RoundTripValidator

**Short-term (Next Session):**
1. Implement visualization auto-layout
2. Update all tests
3. Test on existing examples/tutorials

**Medium-term (Future):**
1. Redesign blackboard architecture
2. Add security hardening
3. Migration script for old files
4. Complete documentation

---

**Status:** Ready to continue with Phase 4 (Deterministic UUIDs)
