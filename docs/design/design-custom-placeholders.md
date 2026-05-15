# Design: Custom Placeholders CLI

**Issue:** [#479](https://github.com/conda/menuinst/issues/479)  
**Status:** In Review  
**Target:** Post-#477 (requires `menuinst.toml` infrastructure)  
**Author:** Robin Andersson  
**Date:** 2026-05-15

## Problem Statement

Installers need to set `DISTRIBUTION_NAME` dynamically at install time (derived from installation directory). This is particularly important for MSI installers on Windows, but the feature applies cross-platform to all installer types (shell scripts on Linux/macOS, PKG on macOS, NSIS/MSI on Windows).

The current implementation in PR #477 special-cases `distribution_name` as a root-level key in `menuinst.toml`. A general-purpose mechanism for custom placeholders would:

- Eliminate special-casing for `DISTRIBUTION_NAME`
- Enable future custom placeholders without code changes
- Provide a clean CLI interface for constructor and other installers

## Scope

### In Scope

- CLI flag to set global placeholders: `--set-global-placeholder KEY=value`
- Storage in `[placeholders]` section of `menuinst.toml`
- Resolution order: env var > local TOML > base TOML > built-in default
- Validation of placeholder names and reserved names

### Out of Scope

- `--set-local-placeholder` for per-environment placeholders (no use case identified)
- `--list-placeholders` / `--remove-placeholder` (can be added later if needed)
- Package author workflows (can be revisited if concrete use case emerges)

### Audience

**Installers only** (e.g., constructor). We considered also supporting package authors (e.g., Spyder setting `PKG_MAJOR_VER` in post-link scripts), but could not identify concrete use cases requiring install-time placeholders. Package-specific values like version numbers are known at build time and can be baked into the menu JSON during `conda-build`.

## Design

### Storage Format

**File:** `$BASE_PREFIX/Menu/menuinst.toml`

Placeholders are stored in a `[placeholders]` section:

```toml
schema_version = "1-0-0"

[placeholders]
DISTRIBUTION_NAME = "FooBar"

[[shortcuts]]
source = "app.json"
path = "/path/to/shortcut"  # Platform-specific: .lnk (Windows), .app (macOS), .desktop (Linux)
```

**Migration note:** The current PR #477 has `distribution_name` as a root-level key. This must be moved into `[placeholders]` as `DISTRIBUTION_NAME`. If this work is done before `menuinst.toml` ships in a release, no schema version bump is needed. If `menuinst.toml` is already in production, bump `schema_version` to `2-0-0` and add migration logic.

**Why `[placeholders]` section:**

- Clear separation from schema keys (`schema_version`, `shortcuts`)
- No collision risk with future schema additions
- Extensible for future placeholders

### Resolution Order

When resolving `{{ PLACEHOLDER_NAME }}` in a menu JSON:

| Priority | Source | Example |
|----------|--------|---------|
| 1 (highest) | `MENUINST_<NAME>` env var | `MENUINST_DISTRIBUTION_NAME=FooBar` |
| 2 | `$PREFIX/Menu/menuinst.toml` `[placeholders]` | Local environment override |
| 3 | `$BASE_PREFIX/Menu/menuinst.toml` `[placeholders]` | Global installer-set value |
| 4 (lowest) | Built-in defaults | `DISTRIBUTION_NAME` defaults to `base_prefix.name` |

**Notes:**

- Env var prefix `MENUINST_` is already established for `MENUINST_DISTRIBUTION_NAME`
- Priority 2 (local prefix) is included for forward compatibility if `--set-local-placeholder` is added later
- Built-in defaults only exist for specific placeholders; custom placeholders without a value are not substituted

### CLI Interface

**New flag:** `--set-global-placeholder KEY=value`

```bash
# Set a single placeholder
menuinst --set-global-placeholder DISTRIBUTION_NAME=FooBar --prefix /path/to/env

# Set multiple placeholders
menuinst --set-global-placeholder DISTRIBUTION_NAME=FooBar \
         --set-global-placeholder COMPANY_NAME=Acme \
         --prefix /path/to/env
```

**Typical invocations** from constructor installers:

```bash
# Linux/macOS shell installer
"$CONDA_EXEC" menuinst --set-global-placeholder DISTRIBUTION_NAME="$INSTALLER_NAME" --prefix "$PREFIX"
```

```batch
:: Windows batch (MSI/NSIS)
"%BASE_PATH%\_conda.exe" menuinst --set-global-placeholder DISTRIBUTION_NAME=%APPNAME% --prefix "%BASE_PATH%"
```

**Behavior:**

1. Parse `KEY=value` format (error if malformed)
2. Validate key name (see Validation Rules)
3. Read existing `menuinst.toml` from `$PREFIX/Menu/` (or create if missing)
4. Merge into `[placeholders]` section (existing keys are overwritten)
5. Write atomically

**Note:** For global placeholders, `--prefix` should point to the base prefix (installation root). No changes to conda-standalone are required since menuinst is already registered as a conda subcommand via the plugin system.

**Future extensions** (not in scope, design accommodates):

- `--list-placeholders` - show current placeholders
- `--remove-placeholder KEY` - remove a placeholder
- `--set-local-placeholder KEY=value` - if package author use case emerges

### Validation Rules

#### Naming Constraints

Error if key doesn't match `[A-Z_][A-Z0-9_]*`:

| Input | Result |
|-------|--------|
| `DISTRIBUTION_NAME` | Valid |
| `PKG_MAJOR_VER` | Valid |
| `MY_CUSTOM_123` | Valid |
| `foo-bar` | Error: invalid characters |
| `123_NAME` | Error: cannot start with digit |
| `my_name` | Error: lowercase not allowed |

**Rationale:** Ensures the `MENUINST_<NAME>` env var override mechanism always works. Environment variables cannot contain hyphens, and some platforms have case-sensitivity issues with lowercase names.

#### Reserved Names

Error if key is a built-in path placeholder:

- `PREFIX`, `BASE_PREFIX`
- `PYTHON`, `BASE_PYTHON`
- `BIN_DIR`, `MENU_DIR`
- `HOME`

**Rationale (security):** A malicious or misconfigured package could otherwise set `PREFIX=/tmp/evil`, causing `{{ PREFIX }}/bin/python` to resolve to an attacker-controlled path. Path placeholders must always reflect actual filesystem paths.

#### Value Constraints

Permissive - accept any value TOML can represent.

**Rationale:** Values undergo string replacement, not shell execution. Legitimate values may contain spaces, dots, or special characters. TOML handles escaping automatically.

### Error Messages

Clear, actionable error messages for validation failures:

| Condition | Message |
|-----------|---------|
| Malformed input (no `=`) | `Invalid placeholder format 'FOO': expected KEY=value` |
| Invalid name characters | `Invalid placeholder name 'foo-bar': must match [A-Z_][A-Z0-9_]*` |
| Reserved name | `Cannot override reserved placeholder 'PREFIX': path placeholders are read-only` |

## Open Questions

### Global vs Local Semantics

This design assumes "global" means base_prefix and "local" means current prefix (prefix-based semantics). Alternative interpretations exist:

| Option | Global | Local |
|--------|--------|-------|
| **A. Prefix-based (chosen)** | Stored in `$BASE_PREFIX`, inherited by all envs | Stored in `$PREFIX`, only affects that env |
| **B. Persistence-based** | Persisted to TOML file | Only set as env var for current operation |
| **C. Inheritance-based** | Written to base, auto-inherited by child envs | Written to env, overrides inherited value |

If alternative semantics are desired, this design should be revisited.

### Package Author Use Cases

If a concrete use case emerges where packages need to set placeholders at install time (not build time), `--set-local-placeholder` can be added. The storage format and resolution order already accommodate this.

## Success Criteria

**Functional:**

1. `menuinst --set-global-placeholder KEY=value --prefix <path>` writes to `[placeholders]` section
2. `{{ KEY }}` in menu JSON resolves to the stored value
3. `MENUINST_KEY` env var overrides the stored value
4. Invalid key names produce clear error messages
5. Reserved placeholder names produce clear error messages

**Integration:**

6. Constructor can set `DISTRIBUTION_NAME` via CLI instead of writing TOML directly
7. Shortcuts created after setting placeholders use the correct values

## Test Plan

- `--set-global-placeholder KEY=value` writes to `[placeholders]` section
- Multiple `--set-global-placeholder` flags in one command all persist
- Existing placeholders are overwritten, other keys preserved
- Invalid name format raises error with clear message
- Reserved names (`PREFIX`, `HOME`, etc.) raise error
- Malformed input (missing `=`) raises error
- `{{ KEY }}` resolves from TOML when env var not set
- `MENUINST_KEY` env var overrides TOML value
- Missing placeholder in TOML leaves `{{ KEY }}` unsubstituted

## Related

- [#477](https://github.com/conda/menuinst/pull/477) - TOML-based shortcut tracking (introduces `menuinst.toml`)
