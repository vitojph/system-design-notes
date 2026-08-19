# Chapter 14: Design YouTube

## Listening overview

Separate video upload, metadata management, asynchronous transcoding, and global streaming. A DAG-driven workflow schedules specialized workers, while object storage and a CDN deliver multiple encoded renditions.

## Visual guide

The source text refers to the following diagrams. These descriptions retain the diagrams’ meaning when this note is uploaded without the image files.

### 1. dag config

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Video Transcoding Architecture**. It explains **dag config** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 2. dag scheduler

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Video Transcoding Architecture**. It explains **dag scheduler** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 3. dag video transcoding

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Directed Acyclic Graph (DAG) Model**. It explains **dag video transcoding** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 4. high level design

This component architecture diagram. It arranges client-facing entry points, service boxes, queues or caches, and durable stores as separate layers; arrows identify the request or event paths between them in **Components**. It explains **high level design** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 5. message queue1

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Speed Optimizations**. It explains **message queue1** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 6. message queue2

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Speed Optimizations**. It explains **message queue2** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 7. metadata upload

This step-by-step flow diagram. Its arrows and, where present, numbered stages follow one request or event from its initiator through processing and storage to the resulting response or downstream action in **1. Video Uploading Flow**. It explains **metadata upload** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 8. pres signed urls

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Safety Optimizations**. It explains **pres signed urls** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 9. resource manager

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Video Transcoding Architecture**. It explains **resource manager** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 10. task worker

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Video Transcoding Architecture**. It explains **task worker** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 11. video split

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Speed Optimizations**. It explains **video split** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 12. video streaming flow

This step-by-step flow diagram. Its arrows and, where present, numbered stages follow one request or event from its initiator through processing and storage to the resulting response or downstream action in **2. Video Streaming Flow**. It explains **video streaming flow** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 13. video transcoding architecture

This component architecture diagram. It arranges client-facing entry points, service boxes, queues or caches, and durable stores as separate layers; arrows identify the request or event paths between them in **Video Transcoding Architecture**. It explains **video transcoding architecture** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 14. video uploading flow

This step-by-step flow diagram. Its arrows and, where present, numbered stages follow one request or event from its initiator through processing and storage to the resulting response or downstream action in **1. Video Uploading Flow**. It explains **video uploading flow** as part of the youtube design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

## Source lesson text

_Source: `14. Youtube/Readme.md`. Embedded figures are replaced by the visual guide above; all written lesson content is retained below._

# Chapter 14: Design YouTube

## Introduction

YouTube is a massive video streaming platform supporting video uploads, playback, and various interactions. This chapter focuses on designing a scalable video streaming system with the following core features:

- **Fast video uploads**
- **Smooth video streaming**
- **Ability to change video quality**
- **Low infrastructure cost**
- **High availability and reliability**

### Key Statistics (2020)

- **2 billion monthly active users**
- **5 billion videos watched per day**
- **37% of mobile internet traffic comes from YouTube**
- Available in **80 languages**
- **$15.1 billion ad revenue** in 2019

---

## Step 1: Understand the Problem and Scope

### Core Functionalities

1. Upload videos
2. Watch videos

### Supported Platforms

- Mobile apps, web browsers, and smart TVs

### Assumptions

- **Daily Active Users (DAU):** 5 million
- **Average Video Size:** 300 MB
- **Upload Limits:** Max 1 GB per video
- **Daily Storage Need:** 150 TB
- **CDN Costs:** 5 million *5 videos* 0.3GB * $0.02 =  $150,000/day (using Amazon CloudFront)

---

## Step 2: High-Level Design

### Components

> _Diagram described in the visual guide above._

1. **Client:** Devices like smartphones, computers, and TVs.
2. **CDN (Content Delivery Network):** Stores and streams videos.
3. **API Servers:** Handles all user interactions except video streaming (e.g., uploads, metadata updates).
4. **Metadata Database:** Stores video metadata (e.g., title, description, size).
5. **Original Storage:** Blob storage for uploaded videos.
6. **Transcoding Servers:** Convert videos into multiple resolutions and formats.
7. **Transcoded Storage:** Blob storage for transcoded videos.

---

### Core Workflows

#### 1. Video Uploading Flow

- **Parallel Processes:**
  1. Upload video to original storage.
  2. Update video metadata in the database.

- **Video Upload (Steps):**

> _Diagram described in the visual guide above._

- [1] Videos are uploaded to blob storage.
  - [2] Transcoding servers convert videos to multiple formats.
  - [3] One trasncoding is complete, following two steps are exectued in parallel.
    - [3a] Transcoded videos are sent to transcoded storage.
    - [3b] Transcoding completion events are queued in the completion queue.
  - [3a.1] Videos are distributed to the CDN.
  - [3b.1] Completion handlers update metadata and inform users.

- **Metadata Upload (Steps):**

> _Diagram described in the visual guide above._

- The client in parallel sends a request to update the video metadata
  - The request contains video metadata, including file name, size, format, etc.

#### 2. Video Streaming Flow

> _Diagram described in the visual guide above._

- Videos are streamed directly from the CDN using edge servers to minimize latency.
- Some of te popular streaming protocols are MPEG_DASH, Apple HLS, Adobe HDS.
- _Different streaming protocols support different video encodings and playback players._

---

## Step 3: Design Deep Dive

### Video Transcoding

#### Importance

1. Raw video consumes large amounts of storage space. It Reduces storage space.
2. Ensures compatibility across devices and browsers.
3. Adapts video quality to network conditions.

#### Components

- **Container:** Encapsulates video, audio, and metadata (e.g., MP4, AVI).
- **Codecs:** Compression and Decompression algorithms (e.g., H.264, VP9).

#### Directed Acyclic Graph (DAG) Model

> _Diagram described in the visual guide above._

- Transcoding a video is computationally expensive and time-consuming.
- DAG Model defines tasks like encoding, thumbnail generation, and watermarking.
- Allows high parallelism in video processing.

- The original video is split into video, audio, and metadata.
  - Video encodings: Videos are converted to support different resolutions, codec, bitrates.
  - Thumbnail: It can either be uploaded by a user or automatically generated bythe system.
  - Watermark: Image overlay on top of your video contains identifying information about the video.

---

### Video Transcoding Architecture

> _Diagram described in the visual guide above._

1. **Preprocessor:** Splits videos into smaller chunks (GOP alignment). It has 4 responsibilities.

> _Diagram described in the visual guide above._

- Video splitting: Video stream is split or further split into smaller Group of Pictures (GOP) alignment.
  - It split videos by GOP alignment for old clients.
  - It generates DAG based on configuration files client programmers write.
  - It stores GOPs and metadata in temporary storage in case the encoding fails, the system could use persisted data for retry operations.

1. **DAG Scheduler:** Organizes tasks into sequential or parallel stages.

> _Diagram described in the visual guide above._

- It splits a DAG graph into stages of tasks and puts them in the task queue in the resource manager.
  - Stage 1: video, audio, and metadata.
  - The video file is further split into two tasks in stage 2: video encoding and thumbnail.

1. **Resource Manager:** Responsible for managing the efficiency of resource allocation.It
   contains 3 queues and a task scheduler.

> _Diagram described in the visual guide above._

- Task queue: priority queue that contains tasks to be executed.
  - Worker queue: priority queue that contains worker utilization info.
  - Running queue: contains currently running tasks and workers running the tasks.
  - Task scheduler: picks the optimal task/worker, and instructs the chosen task worker to execute the job.

1. **Task Workers:** Perform transcoding and other operations.

> _Diagram described in the visual guide above._

- Different task workers may run different tasks

1. **Temporary Storage:** Stores intermediate data for retries.
   - The choice of storage system depends on factors like data type, data size, access frequency, data life span, etc.
2. **Output:** Transcoded videos ready for distribution.

---

## System Optimizations

### Speed Optimizations

1. **Parallel Video Uploads:** Split videos into smaller chunks for faster, resumable uploads.

> _Diagram described in the visual guide above._

1. **Distributed Upload Centers:** Use CDNs as upload hubs close to users.
2. **Parallel Processing:** Decouple modules using message queues for high parallelism.

> _Diagram described in the visual guide above._

> _Diagram described in the visual guide above._

### Safety Optimizations

1. **Pre-Signed URLs:** Restrict video uploads to authorized users.

> _Diagram described in the visual guide above._

1. **Protect Videos:**
   - **DRM Systems** (e.g., Apple FairPlay, Google Widevine).
   - **AES Encryption.**
   - **Watermarking.**

### Cost-Saving Optimizations

1. Serve only popular videos via CDN; less popular ones from high-capacity servers.
2. Encode on-demand for rarely accessed videos.
3. Regionalize video distribution based on popularity.
4. Build custom CDNs and partner with ISPs to reduce bandwidth costs.

---

## Error Handling

### Recoverable Errors

- Retry failed uploads, transcoding, or resource allocation tasks.

### Non-Recoverable Errors

- Stop malformed video processing and return error codes.
