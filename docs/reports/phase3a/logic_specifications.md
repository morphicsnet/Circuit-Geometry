# Phase 3A Logic Specifications

Gate formula:

`PASS = I AND C AND R AND L`

Where:
- `I` = mechanism identity stability and determinism
- `C` = cluster determinism and family assignment validity (including high-cardinality fixture)
- `R` = receipt schema/completeness/hash/linkage + immutability validity
- `L` = lane registry validity + immutability + deterministic policy action

Identity formula:

`mechanism_id = hash(mechanism_class_type, canonical_hyperpath_signature, normalized_causal_dependency_set, invariant_feature_signature)`

Cluster formula:

`cluster_id = hash(sorted(member_mechanism_ids))`
