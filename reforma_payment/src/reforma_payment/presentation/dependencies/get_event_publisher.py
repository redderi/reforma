from reforma_payment.infrastructure.rabbitmq.publisher import EventPublisher


def get_event_publisher() -> EventPublisher:
    return EventPublisher()
