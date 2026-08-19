# Chapter 4: Design a Rate Limiter

## Listening overview

Protect services by deciding where to enforce limits, choosing a counter or bucket algorithm, and making the decision state scalable, observable, and correct across distributed instances.

## Visual guide

The source text refers to the following diagrams. These descriptions retain the diagrams’ meaning when this note is uploaded without the image files.

### 1. architecture

This component architecture diagram. It arranges client-facing entry points, service boxes, queues or caches, and durable stores as separate layers; arrows identify the request or event paths between them in **High-Level Architecture**. It explains **architecture** as part of the rate limiter design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 2. fixed window counter

This time-based comparison diagram. It uses a timeline, windows, axes, or side-by-side cases to expose the rate, capacity, latency, or scaling trade-off in **3. Fixed Window Counter**. It explains **fixed window counter** as part of the rate limiter design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 3. fixed window issue

This time-based comparison diagram. It uses a timeline, windows, axes, or side-by-side cases to expose the rate, capacity, latency, or scaling trade-off in **3. Fixed Window Counter**. It explains **fixed window issue** as part of the rate limiter design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 4. leaking bucket

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **2. Leaking Bucket**. It explains **leaking bucket** as part of the rate limiter design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 5. rate limiter architecture

This component architecture diagram. It arranges client-facing entry points, service boxes, queues or caches, and durable stores as separate layers; arrows identify the request or event paths between them in **Placement Options**. It explains **rate limiter architecture** as part of the rate limiter design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 6. sliding window counter

This time-based comparison diagram. It uses a timeline, windows, axes, or side-by-side cases to expose the rate, capacity, latency, or scaling trade-off in **5. Sliding Window Counter**. It explains **sliding window counter** as part of the rate limiter design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 7. sliding window log

This time-based comparison diagram. It uses a timeline, windows, axes, or side-by-side cases to expose the rate, capacity, latency, or scaling trade-off in **4. Sliding Window Log**. It explains **sliding window log** as part of the rate limiter design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 8. token bucket

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **1. Token Bucket**. It explains **token bucket** as part of the rate limiter design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

## Source lesson text

_Source: `04. Rate Limiter/Readme.md`. Embedded figures are replaced by the visual guide above; all written lesson content is retained below._

# Chapter 4: Design a Rate Limiter

## Introduction

This chapter explores the design and implementation of a rate limiter—a system component used to control traffic rates sent by clients or services. Rate limiters are crucial for preventing abuse, reducing costs, and ensuring the stability of server resources. Examples of their use include limiting posts, account creations, and reward claims.

## Benefits of Rate Limiting

- **Preventing DoS Attacks:** Blocking excess calls to avoid resource starvation.
- **Cost Reduction:** Limiting unnecessary requests to reduce server expenses.
- **Preventing Overloads:** Filtering out excessive requests to stabilize server performance.

## Step 1: Understanding the Problem

### Key Features

- Server-side API rate limiter.
- Support for multiple throttle rules.
- Handle large-scale systems in distributed environments.
- Option for a standalone service or application-level code.
- Inform users when throttled.

### Requirements

- Accurate request throttling.
- Minimal latency.
- Low memory usage.
- Distributed capability.
- Clear exception handling.
- High fault tolerance.

## Step 2: High-Level Design

### Placement Options

> _Diagram described in the visual guide above._

1. **Client-Side Implementation:** Unreliable due to potential misuse.
2. **Server-Side Implementation:** Preferred for control and reliability.
3. **Middleware (API Gateway):** A flexible option for integrated rate limiting.

### Guidelines for Placement

- Evaluate current tech stack and choose efficient options.
- Select appropriate algorithms based on business needs.
- Use an API gateway if microservices are employed.
- Opt for commercial solutions if resources are limited.

## Step 3: Rate Limiting Algorithms

### 1. Token Bucket

> _Diagram described in the visual guide above._

- **Description:** Tokens are added to a bucket at a fixed rate; each request consumes a token.
- **Parameters:** Bucket size and refill rate.
- **Pros:** Easy to implement, memory-efficient, supports traffic bursts.
- **Cons:** Requires careful parameter tuning.

### 2. Leaking Bucket

> _Diagram described in the visual guide above._

- **Description:** Processes requests at a fixed rate using a FIFO queue.
- **Pros:** Memory-efficient, stable outflow rate.
- **Cons:** Traffic bursts may delay recent requests.

  Example: <https://github.com/uber-go/ratelimit>

### 3. Fixed Window Counter

> _Diagram described in the visual guide above._

- **Description:** Divides time into fixed intervals and uses counters to limit requests.
- **Pros:** Simple, efficient for specific use cases.
- **Cons:** Traffic spikes at window edges can exceed limits.

- Sudden burst of traffic at the edges of time windows
  could cause more requests than allowed quota to go through.

> _Diagram described in the visual guide above._

### 4. Sliding Window Log

> _Diagram described in the visual guide above._

- **Description:** Tracks timestamps to allow a rolling time window.
- **Pros:** Accurate rate limiting.
- **Cons:** High memory consumption.

### 5. Sliding Window Counter

> _Diagram described in the visual guide above._

- **Description:** Combines fixed window and sliding log methods for smoothing spikes.
- **Pros:** Memory-efficient, handles traffic bursts.
- **Cons:** Approximation may not be perfectly strict.

## High-Level Architecture

> _Diagram described in the visual guide above._

- **Data Storage:** Use in-memory caching (e.g., Redis) for fast counter operations.
- **Steps:**
  1. Client sends request to middleware.
  2. Middleware checks counters in Redis.
  3. Request is processed or rejected based on limits.

## Advanced Considerations

### Distributed Environments

- **Challenges:** Race conditions, synchronization issues.
- **Solutions:** Use locks, Lua scripts, or sorted sets in Redis. Employ centralized data stores for synchronization.

### Performance Optimizations

- Multi-data center setups for reduced latency.
- Eventual consistency models for synchronization.

### Monitoring

- Regular analytics to ensure algorithm effectiveness and adjust rules as needed.
