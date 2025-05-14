from kubernetes import client, watch
from app.schemas.event import K8sEvent
from datetime import timezone, datetime
from typing import Iterator



def stream_events_sync_continuous() -> Iterator[K8sEvent]:
    v1 = client.CoreV1Api()
    w = watch.Watch()

    print(f"Watching events continuously inall namespaces")  # Debug log

    while True:
        try:
            event_found = False
            for event in w.stream(v1.list_event_for_all_namespaces, timeout_seconds=60):
                event_found = True
                obj = event["object"]
                timestamp = obj.last_timestamp or obj.event_time
                if timestamp:
                    timestamp = timestamp.replace(tzinfo=timezone.utc).isoformat()
                else:
                    timestamp = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

                yield K8sEvent(
                    type=event["type"],
                    reason=obj.reason,
                    message=obj.message,
                    involved_object=f"{obj.involved_object.kind}/{obj.involved_object.name}",
                    source=obj.source.component if obj.source else None,
                    timestamp=timestamp
                )
            if not event_found:
                print("No events during this watch window")
        except Exception as e:
            print(f"Error in event stream: {e}")
            time.sleep(1)  # retry delay
