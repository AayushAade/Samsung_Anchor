# Memory API

## Overview

The Memory subsystem is responsible for persistent storage and retrieval of all long-term contextual information used by Samsung Anchor.

It acts as the project's central data layer and is responsible for maintaining:

- Person identities
- Face embeddings
- Object locations
- Audio-derived evidence
- Room state
- Recognition history

All persistent data is stored in an SQLite database.

---

# Architecture

```
Camera / Vision
        │
        ▼
Face Embedding
        │
        ▼
MemoraDatabase
        │
        ├── Identities
        ├── Face Embeddings
        ├── Evidence
        ├── Objects
        └── System State
```

---

# Public API

## register_anonymous(embedding)

### Purpose

Creates a new anonymous identity when no existing face match is found.

### Input

- embedding : Face embedding vector

### Returns

- identity_id : str

### Database Writes

- identities
- face_embeddings

---

## find_match(query_embedding, tolerance=None)

### Purpose

Searches all stored face embeddings and returns the closest matching identity.

### Input

- query_embedding
- tolerance (optional)

### Returns

(identity_id, identity_info, distance)

Returns `(None, None, None)` if no match exists.

---

## add_embedding_to_identity(identity_id, embedding)

### Purpose

Adds an additional face embedding to an existing identity.

---

## update_embedding_ema(embedding_id, new_embedding)

### Purpose

Updates an existing embedding using Exponential Moving Average (EMA).

---

## increment_times_seen(identity_id)

### Purpose

Updates recognition statistics whenever an identity is observed again.

---

## bind_name(identity_id, name, relationship=None)

### Purpose

Associates a human-readable identity with a previously anonymous profile.

---

## get_identity(identity_id)

Returns complete information for a single identity.

---

## get_all_identities()

Returns every stored identity.

---

## log_object(object_name, x, y, room)

Stores the latest known location of an object.

---

## get_last_known_location(object_name)

Returns the latest recorded location of an object.

---

## get_object_history(object_name)

Returns historical movement information for an object.

---

## set_current_room(room_name)

Updates the currently active room.

---

## get_current_room()

Returns the current room.

---

## add_evidence(identity_id, ...)

Stores audio-derived evidence and updates candidate confidence.

---

## get_candidates(identity_id)

Returns all candidate identities associated with a person.

---

# Current Status

| Component | Status |
|-----------|--------|
| Database Initialization | ✅ |
| Identity Management | ✅ |
| Face Matching | ✅ |
| Embedding Storage | ✅ |
| Object Memory | ✅ |
| Evidence Storage | ✅ |

---

# Future Improvements

- Automated unit tests
- Performance benchmarking
- Vector indexing for large embedding sets
- Database migration support
- Confidence calibration