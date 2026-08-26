# `composicao` — indicator hierarchy

Purpose: parent → child edges between indicators declared in `descricao` (protocol §2.4, p.10).
The edges must form a tree rooted at the sector; the code treats code `1` as the root of the graph
and inserts a virtual code `0` when checking levels. Files: `composicao.xlsx`/`.csv`. Single header.
Required.

## Columns

| Column | Kind | Type after cleaning | Constraints | Source in code |
|---|---|---|---|---|
| `codigo_pai` | required | int ≥ 0 (validators) / ≥ 1 (model) | parent indicator code | `models/sp_composition.py::RequiredColumn.COLUMN_PARENT_CODE` |
| `codigo_filho` | required | int ≥ 1 | child code, one level below the parent | `RequiredColumn.COLUMN_CHILD_CODE` |

Two validators consume this sheet: `SpCompositionGraphValidator` (networkx `DiGraph`) and
`SpCompositionTreeValidator` (adjacency dict). Both re-clean the integer columns locally.

## Rules

### CLEAN-004 · `codigo_pai` and `codigo_filho` must be integers ≥ 1
- Severity: error
- NamesEnum: FC (`verification_name_file_cleaning`)
- Protocol: §2.4
- Statement: as CLEAN-001 for both columns (minimum 1 in the model; validators re-clean the parent column with minimum 0 to admit the virtual root).
- Current message (pt-BR): `{file_name}, linha {idx + 2}: A coluna '{column}' contém um valor inválido: {message}`
- Target message key: `rule.CLEAN-004.error`
- Implemented by: `models/sp_composition.py::SpComposition.data_cleaning`
- Covered by tests: helper covered by `tests/unit/helpers/common/processing/test_data_cleaning.py`
- Notes / known defects: BUG-002 (class attribute mutation).

### COMP-001 · Composition codes and description codes must match
- Severity: error
- NamesEnum: IR (`verification_name_indicator_relations`)
- Protocol: §2.4 ("a coluna codigo_filho contenha todos os indicadores em descricao.xlsx")
- Statement: the set of valid integer codes in `descricao.codigo` must equal the union of `codigo_pai ∪ codigo_filho`; differences in either direction are errors. Skipped when `descricao` is empty.
- Current message (pt-BR): `{descricao}: Códigos dos indicadores ausentes em {composicao}: [..].` · `{composicao}: Códigos dos indicadores ausentes em {descricao}: [..].` · missing columns → `{file}: A verificação foi abortada para a coluna obrigatória '{column}' que está ausente.`
- Target message key: `rule.COMP-001.error`
- Implemented by: `validators/spreadsheets/composition/compostion_graph_validator.py::SpCompositionGraphValidator.validate_relation_indicators_in_composition` → `CollectionsProcessing.find_differences_in_two_set_with_message`
- Covered by tests: helper covered by `tests/unit/helpers/common/processing/test_collections_processing.py`
- Notes / known defects: parent code `0`/`1` semantics not special-cased here; re-executed inside COMP-004 (BUG-019).

### COMP-002 · The composition graph must be acyclic
- Severity: error
- NamesEnum: IR
- Protocol: §1 (hierarchy "no formato de árvore")
- Statement: `nx.find_cycle` on the directed graph built from all edges must find nothing; the first cycle found is reported as an edge path.
- Current message (pt-BR): `{composicao}: Ciclo encontrado: [{a} -> {b}, {b} -> {c}, …].`
- Target message key: `rule.COMP-002.error`
- Implemented by: `compostion_graph_validator.py::SpCompositionGraphValidator.validate_relations_hierarchy_with_graph` → `helpers/common/validation/graph_processing.py::GraphProcessing.detect_cycles`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_graph_processing.py`
- Notes / known defects: —

### COMP-003 · No disconnected indicator groups
- Severity: error
- NamesEnum: IR
- Protocol: §1 (single tree)
- Statement: the graph must have a single weakly connected component; every additional component (sorted by size) is reported with its edges.
- Current message (pt-BR): `{composicao}: Indicadores desconectados encontrados: [{a} -> {b}, …], [..].`
- Target message key: `rule.COMP-003.error`
- Implemented by: `compostion_graph_validator.py::SpCompositionGraphValidator.validate_relations_hierarchy_with_graph` → `GraphProcessing.detect_disconnected_components` / `generate_graph_report`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_graph_processing.py`
- Notes / known defects: `generate_graph_report` converts node ids through `float()`.

### COMP-004 · Titles must be unique inside each level-2 subtree
- Severity: warning (root missing → error)
- NamesEnum: UT (`verification_name_unique_titles`)
- Protocol: §2.3 p.6 ("Os nomes simples dentro de um mesmo risco não podem ser repetidos"; same for full names)
- Statement: preconditions — COMP-001, COMP-002, COMP-003 pass and node `"1"` exists (else error). For each child of the root, take the BFS subtree, slice `descricao` by its codes and report duplicated `nome_simples`/`nome_completo` (reported with the plural column names `nomes simples`/`nomes completos`).
- Current message (pt-BR): `{composicao}: Nó raiz '1' não encontrado.` (error) · `{descricao}: Existem nomes simples duplicados: [..].` / `… nomes completos duplicados: [..].` (warning)
- Target message key: `rule.COMP-004.warning`, `rule.COMP-004.root_missing.error`
- Implemented by: `compostion_graph_validator.py::SpCompositionGraphValidator.validate_unique_titles_with_graph` → `GraphProcessing.convert_to_tree`, `breadth_first_search_from_node`, `DataFrameProcessing.check_dataframe_titles_uniques`
- Covered by tests: helpers covered by `tests/unit/helpers/common/validation/test_graph_processing.py`, `test_column_validation.py`
- Notes / known defects: root `"1"` hard-coded; re-runs COMP-001/002/003 (BUG-019); protocol also wants global uniqueness (gap G-11).

### COMP-005 · Every leaf indicator must have a column in `valores`
- Severity: error
- NamesEnum: LEAF_NO_DATA (`verification_name_leaf_indicators_without_associated_data`)
- Protocol: §2.6 p.13 ("Para cada índice ou indicador descrito na Seção 2.3, deverá haver pelo menos uma coluna")
- Statement: for each node with out-degree 0, some `valores` column must start with `<code>-`. Skipped when `valores` is empty.
- Current message (pt-BR): `{valores}: Indicador folha '{leaf}' não possui dados associados.`
- Target message key: `rule.COMP-005.error`
- Implemented by: `compostion_graph_validator.py::SpCompositionGraphValidator.validate_associated_indicators_leafs` → `GraphProcessing.get_leaf_nodes`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_graph_processing.py`
- Notes / known defects: —

### COMP-006 · Every leaf indicator must appear in `proporcionalidades` (when delivered)
- Severity: error
- NamesEnum: LEAF_NO_DATA
- Protocol: §2.7 p.14 (children columns list every last-level indicator)
- Statement: when `proporcionalidades` was read and is non-empty, each leaf code must appear among the level-1 header names (prefix before `-`), excluding `id` and `Unnamed*`.
- Current message (pt-BR): `{proporcionalidades}: Indicador folha '{leaf}' não possui dados associados.`
- Target message key: `rule.COMP-006.error`
- Implemented by: `compostion_graph_validator.py::SpCompositionGraphValidator.validate_associated_indicators_leafs`
- Covered by tests: none — TST-001
- Notes / known defects: —

### COMP-007 · The tree built from edges must be acyclic (DFS)
- Severity: error
- NamesEnum: TH (`verification_name_tree_hierarchy`)
- Protocol: §1
- Statement: same property as COMP-002 checked with a DFS over an adjacency dict; reported as a node path.
- Current message (pt-BR): `{composicao}: Ciclo encontrado: [{a} -> {b} -> {a}].`
- Target message key: `rule.COMP-007.error`
- Implemented by: `validators/spreadsheets/composition/composition_tree_validator.py::SpCompositionTreeValidator.validate_hierarchy_with_tree` → `helpers/common/validation/tree_processing.py::TreeProcessing.detect_tree_cycles`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_tree_processing.py`
- Notes / known defects: duplicates COMP-002 under a different title; candidate for merging in the target registry.

### COMP-008 · A parent must have a lower level than its child
- Severity: error
- NamesEnum: TH
- Protocol: §2.4 p.10 ("O filho tem que sempre ter um nível maior do que o nível do pai", v1.9)
- Statement: using cleaned `descricao` (with a virtual row `codigo=0, nivel=0` appended when no code 0 exists), for every edge `level(parent) < level(child)`; codes missing from `descricao` are collected but only pairs where both codes exist are formatted.
- Current message (pt-BR): `{composicao}, linha {line_number}: O indicador {parent} (nível {parent_level}) não pode ser pai do indicador {child} (nível {child_level}). Atualize os níveis no arquivo de descrição.`
- Target message key: `rule.COMP-008.error`
- Implemented by: `composition_tree_validator.py::SpCompositionTreeValidator.validate_hierarchy_with_tree` + `_format_level_errors` → `TreeProcessing.validate_level_hierarchy`
- Covered by tests: helper covered by `tests/unit/helpers/common/validation/test_tree_processing.py`
- Notes / known defects: requires `relacao` column present (listed in `global_required_columns` although injected by the model); `iterrows` (PERF-001).

### COMP-009 · All children of a parent share the same level; codes must exist in `descricao`
- Severity: error
- NamesEnum: CHILD_LVL (`verification_name_child_indicator_levels`)
- Protocol: §2.4 p.10 ("Todos os filhos de um mesmo pai tem que estar em um mesmo nível", v1.9)
- Statement: group edges by `codigo_pai`; the parent and every child must exist in `descricao` (raw string comparison), and the set of child levels must have size 1.
- Current message (pt-BR): `{composicao}: Código pai {parent} não encontrado na descrição.` · `{composicao}: Código filho {child} não encontrado na descrição.` · `{descricao}: Indicadores filhos do pai {parent} não estão no mesmo nível: [indicador {child} possui nível '{level}', …].`
- Target message key: `rule.COMP-009.error`
- Implemented by: `composition_tree_validator.py::SpCompositionTreeValidator.validate_tree_levels_children`
- Covered by tests: none — TST-001
- Notes / known defects: uses raw (uncleaned) strings, so `"1"` vs `"1.0"` mismatch (BUG-014); parent `0` is always reported as missing unless present in `descricao`.

## Gaps (protocol ↔ code)

- **G-12 root semantics**: protocol says level-1 indicators have a parent of level 0; the graph validator instead requires node `"1"` to exist and be the root, while the tree validator fabricates code `0`. Unify in the `SheetSpec` (ADR-0003).
- COMP-002/COMP-007 duplicate the same check under two titles.

Last synced with code: 09279f4
