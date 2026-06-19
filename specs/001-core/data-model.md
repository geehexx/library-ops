# Data Model

## Canonical concepts

| Entity | Purpose | Key invariants |
|---|---|---|
| User | Authenticated actor with role. | Role checks are server-side. |
| Role/Profile | Admin, Librarian, Member capabilities. | Demo roles seeded idempotently. |
| BibliographicWork | Conceptual work/title. | Does not represent borrowable inventory. |
| BookEdition | Publication/edition metadata, ISBNs, publisher, language. | Belongs to one work; identifiers normalized. |
| Contributor | Author/editor/etc. | Many-to-many with works/editions through roles. |
| Subject | Search/facet subject. | Normalized and deduplicated. |
| BookCopy | Borrowable physical/logical item. | Barcode unique; availability derived from loan state/status. |
| Loan | Borrow/return event. | One active loan per copy; active loan has no returned timestamp. |
| AuditEvent | Append-only evidence for important actions. | Actor/action/target/timestamp immutable after write. |
| SearchDocument | Denormalized search projection. | Rebuildable from authoritative records. |
| ExternalSourceRecord | Seed import provenance. | Records source, license, target object, and import timestamps. |

## Boundary notes

- `catalog` owns works, editions, contributors, subjects, and external source
  records.
- `inventory` owns copies and availability projection.
- `circulation` owns loan transitions.
- `audit` owns append-only audit events.
- `search` owns projections/ranking, not authoritative state.
- `accounts` owns demo-user seeding.
- `catalog` owns public-domain import commands and provenance.
- `search` owns search-document rebuild workflows.

## Key constraints

- Unique normalized ISBN/external IDs where present.
- Unique copy barcode.
- Partial unique constraint for one active loan per copy.
- Foreign-key protection or explicit archive behavior for historical loans.
- Cover uploads constrained by size/type and decoded image validation.
