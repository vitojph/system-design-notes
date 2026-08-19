# Chapter 10: Design a Notification System

## Listening overview

Accept notification requests reliably, fan them out to channel-specific workers and third-party providers, and track delivery state. Queues, templates, user preferences, retries, rate limits, and analytics complete the design.

## Visual guide

The source text refers to the following diagrams. These descriptions retain the diagrams’ meaning when this note is uploaded without the image files.

### 1. contact info gathering

This spatial or partitioning illustration. It divides a map, hash ring, or key space into cells or ranges and highlights how a lookup crosses boundaries or selects an owner in **Components**. It explains **contact info gathering** as part of the notification system design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 2. data loss

This data-model or worked-example diagram. It uses rows, columns, record fields, or sample values to show exactly what is stored or how a result is calculated in **Reliability**. It explains **data loss** as part of the notification system design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 3. events tracking

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Additional Components**. It explains **events tracking** as part of the notification system design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 4. high level design

This component architecture diagram. It arranges client-facing entry points, service boxes, queues or caches, and durable stores as separate layers; arrows identify the request or event paths between them in **Components**. It explains **high level design** as part of the notification system design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 5. improved design

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Improved Design**. It explains **improved design** as part of the notification system design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

### 6. updated design

This labeled conceptual diagram. It uses simple boxes, arrows, or a focused before-and-after view to isolate the mechanism rather than the whole system in **Notification Flow**. It explains **updated design** as part of the notification system design, so read the connections, ordering, partitions, or fields as the concrete representation of the surrounding discussion.

## Source lesson text

_Source: `10. Notification System/Readme.md`. Embedded figures are replaced by the visual guide above; all written lesson content is retained below._

# Chapter 10: Design a Notification System

## Introduction

A **notification system** is essential for modern applications, providing timely updates like product notifications, events, offers, and alerts. Notifications can be sent through:

1. **Push notifications** (mobile or desktop),
2. **SMS messages**, and
3. **Emails**.

The chapter focuses on designing a scalable system capable of sending millions of notifications daily.

---

## Step 1: Understanding the Problem

### Requirements

- **Notification Types:** Push notifications, SMS, and Emails.
- **Delivery:** Soft real-time system with minimal delays.
- **Platforms:** iOS, Android, and desktop.
- **Triggers:** Notifications can be triggered by client applications or scheduled on servers.
- **Scale:**
  - **Push Notifications:** 10 million/day,
  - **SMS:** 1 million/day,
  - **Emails:** 5 million/day.
- **Opt-out Support:** Users can disable specific notification types.

---

## Step 2: High-Level Design

### Components

1. **Notification Types:**
   - **iOS Push Notifications:** Use **Apple Push Notification Service (APNS)**.
   - **Android Push Notifications:** Use **Firebase Cloud Messaging (FCM)**.
   - **SMS Messages:** Third-party services like Twilio or Nexmo.
   - **Emails:** Commercial email services like SendGrid or Mailchimp.

2. **Contact Info Gathering:**

> _Diagram described in the visual guide above._

- Collect device tokens, phone numbers, or email addresses during app installation or signup.
  - Store contact info in the database:
    - **Device Tokens Table:** For push notifications.
    - **User Table:** For emails and phone numbers.

1. **Notification Sending Flow:**

> _Diagram described in the visual guide above._

- **Trigger Services:** - Generate events to initiate notifications (e.g., billing reminders, shipping updates). - A service can be a micro-service, a cron job, or a distributed system that triggers notification sending events.
  - **Notification Server:**
    - Provide APIs for services to send notifications.
    - Carry out basic validations to verify emails, phone numbers.
    - Query the database or cache to fetch data needed to render a notification.
  - **Third-Party Services:** Deliver notifications to users.

### Challenges in Initial Design

- **Single Point of Failure (SPOF):** One notification server can crash the entire system.
- **Scalability Issues:** Hard to scale databases, caches, and processing components independently.
- **Performance Bottlenecks:** High resource demands for sending notifications.

### Improved Design

> _Diagram described in the visual guide above._

- Move databases and caches out of the notification server.
- Introduce **horizontal scaling** with multiple notification servers.
- Use **message queues** to decouple system components.
  - Message queues serve as buffers when high volumes of notifications are to be sent out.
- Add workers that pull notification events from message queues and send them to corresponding third party services.

---

## Step 3: Design Deep Dive

### Reliability

1. **Prevent Data Loss:**

> _Diagram described in the visual guide above._

- Persist notification data in a database and implement a retry mechanism.
  - The Notification log database is included for data persistence.

1. **Deduplication:**
   - Check event IDs to avoid sending duplicate notifications.
   - When a notification event first arrives, check if it is seen before by checking the event ID.
     If seen before discard it, otherwise send out the notification.

### Additional Components

> _Diagram described in the visual guide above._

1. **Notification Templates:** Preformatted templates for consistent and efficient notifications.
2. **Notification Settings:**
   - Users can opt-in or opt-out for specific channels (push, SMS, or email).
   - Stored in a dedicated notification settings table.
3. **Rate Limiting:** Cap the frequency of notifications sent to users.
4. **Retry Mechanism:** Retry sending notifications if third-party services fail.
5. **Monitoring Queues:** Track queued notifications to scale workers dynamically.
6. **Event Tracking:** Collect metrics like open rate, click rate, and engagement.

### Security

- Use **AppKey** and **AppSecret** to authenticate and secure APIs for push notifications.

### Notification Flow

> _Diagram described in the visual guide above._

1. Trigger services call APIs to send notifications.
2. Notification servers validate requests and fetch metadata from caches or databases.
3. Notification events are sent to message queues.
4. Workers process events and interact with third-party services.
5. Third-party services deliver notifications to users.

---

## Key Optimizations

1. **Horizontal Scaling:** Add more notification servers for load distribution.
2. **Message Queues:** Decouple processing to handle high volumes.
3. **Caching:** Reduce latency by caching frequently accessed data.
4. **Distributed Crawling:** Optimize message delivery geographically for better performance.
