# Phase 3A Coverage Analysis

Fully exercised in gate path:
- mechanism ID determinism
- chart substitution and schema-compatible replay stability
- cluster ID determinism
- high-cardinality cluster determinism fixture
- lane registry loading/threshold/falsifier validity
- lane lock immutability check
- decision receipt schema + completeness + hash stability
- receipt persistence immutability (idempotent re-persist + mutation rejection)
- policy action determinism

Partially exercised:
- large-scale family clustering behavior under high cardinality
- multi-model cross-adapter mechanism identity stability
