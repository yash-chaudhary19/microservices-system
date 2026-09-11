"""NATS Subject and Stream naming constants.

Following the convention:
- Events: events.<domain>.<action>.<version> (Published to JetStream)
- Commands/RPC: service.<domain>.<action>.<version> (Direct Request/Reply)
"""

# JetStream Streams
STREAM_USER_EVENTS = "USER_EVENTS"
STREAM_USER_SUBJECT_FILTER = "events.user.>"

# JetStream Consumer Names
CONSUMER_NOTIFICATION_USER_EVENTS = "notification-service-user-created"

# Domain Events
EVENT_USER_CREATED_V1 = "events.user.created.v1"

# RPC Service Subjects
SUBJECT_USER_CREATE_V1 = "service.user.create.v1"
SUBJECT_USER_GET_V1 = "service.user.get.v1"
SUBJECT_USER_AUTHENTICATE_V1 = "service.user.authenticate.v1"

SUBJECT_NOTIFICATION_LIST_V1 = "service.notification.list.v1"
