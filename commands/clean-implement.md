---
description: Minimal clean design, avoid unnecessary abstractions, prefer direct code, cleanup after changes.
---
The requirement is $REQ, please follow below principles during the implementation.
- Before editing, optimize for the simplest clean design, not defensive indirection. 
- Avoid unnecessary local aliases, wrapper helpers, and extra abstraction unless they clearly reduce complexity or are reused in multiple places. 
- Prefer direct code over “just in case” structure. 
- After making changes, do one cleanup pass specifically for code quality and remove any redundant variables, incidental complexity, or awkward scaffolding introduced during iteration.