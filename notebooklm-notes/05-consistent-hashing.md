# Chapter 5: Design Consistent Hashing

## Listening overview

Map both keys and servers onto a ring so adding or removing a server moves only a small subset of keys. Virtual nodes improve balance and smooth the impact of uneven server capacity.

## Visual guide

The source text refers to the following diagrams. These descriptions retain the diagrams’ meaning when this note is uploaded without the image files.

### 1. adding server

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Key Concepts**. It explains **adding server** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 2. hash ring

This spatial or partitioning illustration. It divides a map, hash ring, or key space into cells or ranges and highlights how a lookup crosses boundaries or selects an owner in **Key Concepts**. It explains **hash ring** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 3. removing server

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Key Concepts**. It explains **removing server** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 4. server addition

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Affected Keys**. It explains **server addition** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 5. server hashing miss

This spatial or partitioning illustration. It divides a map, hash ring, or key space into cells or ranges and highlights how a lookup crosses boundaries or selects an owner in **Explanation**. It explains **server hashing miss** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 6. server hashing

This spatial or partitioning illustration. It divides a map, hash ring, or key space into cells or ranges and highlights how a lookup crosses boundaries or selects an owner in **Explanation**. It explains **server hashing** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 7. server lookup

This step-by-step flow diagram. Its arrows and, where present, numbered stages follow one request or event from its initiator through processing and storage to the resulting response or downstream action in **Key Concepts**. It explains **server lookup** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 8. server removed

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Affected Keys**. It explains **server removed** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 9. server ring

This spatial or partitioning illustration. It divides a map, hash ring, or key space into cells or ranges and highlights how a lookup crosses boundaries or selects an owner in **Key Concepts**. It explains **server ring** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 10. virtual nodes

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Solution: Virtual Nodes**. It explains **virtual nodes** as part of the consistent hashing design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

## Source lesson text

_Source: `05. Consistent Hashing/Readme.md`. Embedded figures are replaced by the visual guide above; all written lesson content is retained below._

# Chapter 5: Design Consistent Hashing

## Introduction

This chapter explores consistent hashing, a technique essential for achieving horizontal scaling by efficiently distributing requests and data across servers. It minimizes data redistribution when servers are added or removed and ensures an even distribution of data to mitigate issues like server hotspots.

## The Rehashing Problem

### Explanation

In traditional hashing methods, such as `serverIndex = hash(key) % N`, data redistribution becomes problematic when the number of servers changes. For example:

- Removing a server causes most keys to be reassigned, leading to cache misses.
- Adding a server results in unnecessary key redistributions.

> _Diagram described in the visual guide above._

- This approach works well when the size of the server pool is fixed. However, problems arise when new servers are added, or existing servers are removed.

> _Diagram described in the visual guide above._

### Key Issue

Redistribution of most keys when server count changes causes inefficiency and overload.

## Consistent Hashing

### Definition

Consistent hashing ensures that only a fraction of keys are remapped when servers are added or removed. This minimizes disruptions and enhances scalability.

### Key Concepts

1. **Hash Space and Ring:** The hash space forms a continuous ring, with hash values distributed from `0` to `2^160-1` (e.g., using hash function like SHA-1). By connecting both ends we get a ring.
    <p align="center">

> _Diagram described in the visual guide above._

</p>

- Using the same hash function f, we map servers based on server IP or name onto the ring.

    <p align="center">

> _Diagram described in the visual guide above._

</p>

1. **Server Lookup**

- A key's server is determined by traversing clockwise on the ring until a server is found.

  <p align="center">

> _Diagram described in the visual guide above._

</p>

1. **Adding and Removing Servers**

- Adding a server redistributes only nearby keys. Only a fraction of keys are redistributed to the new server.

  <p align="center">

> _Diagram described in the visual guide above._

</p>

- Removing a server affects only the keys in its range. Only keys from the removed server are reassigned to the next server clockwise.

  <p align="center">

> _Diagram described in the visual guide above._

</p>

## Challenges and Solutions

### Two Issues in Basic Approach

1. **Uneven Partition Sizes:** Servers may have unequal data partitions.
2. **Non-uniform Key Distribution:** Some servers may receive significantly more keys than others.

### Solution: Virtual Nodes

- Each server is represented by multiple virtual nodes on the ring uniformly distrubuted on the ring.
- Virtual nodes improve key distribution and balance load. As the number of virtual nodes increases, the distribution of keys becomes more balanced. This is because the standard deviation gets smaller with more virtual nodes, leading to balanced data distribution.

  <p align="center">

> _Diagram described in the visual guide above._

</p>

## Affected Keys

When servers are added or removed:

- **Added Server:** Affected keys are those between the new server and its predecessor.
  In the following example server 4 is added onto the ring. The affected range starts from s4 (newly
  added node) and moves anticlockwise around the ring until a server is found (s3). Thus, keys
  located between s3 and s4 need to be redistributed to s4.

  <p align="center">

> _Diagram described in the visual guide above._

</p>

- **Removed Server:** Affected keys are those between the removed server and its predecessor. In the following example when a server (s1) is removed, the affected range starts from s1
  (removed node) and moves anticlockwise around the ring until a server is found (s0). Thus, keys located between s0 and s1 must be redistributed to s2.

  <p align="center">

> _Diagram described in the visual guide above._

</p>

## Benefits of Consistent Hashing

- **Minimized Redistribution:** Only a fraction of keys are reassigned.
- **Scalability:** Enables horizontal scaling.
- **Mitigates Hotspots:** Balances data distribution to avoid server overload.

## Real-World Applications

- Amazon Dynamo DB
- Apache Cassandra
- Discord
- Akamai CDN
- Maglev Load Balancer
