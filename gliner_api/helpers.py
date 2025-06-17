from gliner_api.datamodel import Entity


def merge_overlapping_entities(entities: list[Entity]) -> list[Entity]:
    """
    Merge overlapping entities, keeping larger entities and higher confidence scores.

    Rules:
    1. If entities have the same span, keep the one with higher confidence
    2. If entities overlap, keep the larger one
    3. If same size and overlap, keep the one with higher confidence
    """
    if not entities:
        return []

    # Sort by start position, then by length (descending), then by score (descending)
    sorted_entities = sorted(entities, key=lambda e: (e.start, -(e.end - e.start), -e.score))

    merged = []
    for entity in sorted_entities:
        # Check if this entity overlaps with any already merged entity
        should_add = True
        for i, merged_entity in enumerate(merged):
            # Check for overlap
            if entity.start < merged_entity.end and entity.end > merged_entity.start:
                # Entities overlap
                entity_length = entity.end - entity.start
                merged_length = merged_entity.end - merged_entity.start

                # If same span, keep higher confidence
                if entity.start == merged_entity.start and entity.end == merged_entity.end:
                    if entity.score > merged_entity.score:
                        merged[i] = entity
                    should_add = False
                    break
                # If current entity is larger, replace the merged one
                elif entity_length > merged_length:
                    merged[i] = entity
                    should_add = False
                    break
                # If merged entity is larger or same size with higher score, skip current
                elif merged_length > entity_length or merged_entity.score >= entity.score:
                    should_add = False
                    break

        if should_add:
            merged.append(entity)

    # Sort final result by start position
    return sorted(merged, key=lambda e: e.start)
