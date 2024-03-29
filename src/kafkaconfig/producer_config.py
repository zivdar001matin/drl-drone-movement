from dotenv import dotenv_values, find_dotenv

config = dotenv_values(find_dotenv())

agents_config = {
    'bootstrap_servers': [f'{config.get("KAFKA_SERVER_IP")}:{config.get("KAFKA_TRAINER_PORT")}'],
    # 'acks': 'all',
    'retries': 100,
    # 'max_in_flight_requests_per_connection': 5,
    # 'compression_type': 'snappy',
    'linger_ms': 5,
    # 'batch_size': 1
}

webots_config = {
    'bootstrap_servers': [f'{config.get("KAFKA_SERVER_IP")}:{config.get("KAFKA_TRAINER_PORT")}'],
    # 'acks': 'all',
    'retries': 100,
    # 'max_in_flight_requests_per_connection': 5,
    # 'compression_type': 'snappy',
    'linger_ms': 5,
    # 'batch_size': 32
}

trainer_to_agents_config = {
    'bootstrap_servers': [f'{config.get("KAFKA_SERVER_IP")}:{config.get("KAFKA_AGENTS_PORT")}'],
    # 'acks': 'all',
    'retries': 100,
    # 'max_in_flight_requests_per_connection': 5,
    # 'compression_type': 'snappy',
    'linger_ms': 5,
    # 'batch_size': 1
}

trainer_to_webots_config = {
    'bootstrap_servers': [f'{config.get("KAFKA_SERVER_IP")}:{config.get("KAFKA_WEBOTS_PORT")}'],
    # 'acks': 'all',
    'retries': 100,
    # 'max_in_flight_requests_per_connection': 5,
    # 'compression_type': 'snappy',
    'linger_ms': 5,
    # 'batch_size': 1
}