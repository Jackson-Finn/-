PRAGMA foreign_keys = ON;

/* Core integrity rules are defined inline in tables.sql for SQLite compatibility. */
/* This file documents the expected state-machine constraints for future MySQL migration. */

/* Product audit status must stay in PENDING / APPROVED / REJECTED. */
/* Product runtime status must stay in DRAFT / ACTIVE / OFF_SHELF / BLOCKED. */
/* Order status must stay in CREATED / CANCELLED / COMPLETED. */
/* Appeal status must stay in PENDING / APPROVED / REJECTED. */
/* Report status must stay in PENDING / PROCESSED. */

