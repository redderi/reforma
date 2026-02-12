from reforma_authorization.infrastructure.rabbitmq.publisher import MailPublisher

def get_mail_publisher():
    return MailPublisher()