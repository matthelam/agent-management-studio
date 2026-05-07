# Craft Standard

Apply when your output is code. Evaluate every change against these criteria.

**Single Responsibility** — Each function, class, and module does one thing. If you need the word "and" to describe what it does, split it.

**Dependency Inversion** — Depend on abstractions, not concretions. High-level modules must not import low-level modules directly. Inject dependencies.

**DRY** — Every piece of knowledge has a single, authoritative source. If you are copying logic, extract it. If two files define the same constant, consolidate.

**Shift-Left** — Catch problems at the earliest possible stage. Validate inputs at the boundary. Type-check at compile time. Test before merge. Lint before commit.

**Clarity** — Code is read more than it is written. Name things for what they represent, not what they do internally. Prefer explicit over clever. Comments explain why, never what.

**Single Source of Truth** — Configuration, constants, and business rules live in exactly one place. Everything else references that place. No shadow copies.
