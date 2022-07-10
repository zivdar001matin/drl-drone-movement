agents_config = {
    'bootstrap_servers': ['localhost:9093'],
    # 'acks': 'all',
    'retries': 100,
    # 'max_in_flight_requests_per_connection': 5,
    # 'compression_type': 'snappy',
    'linger_ms': 5,
    # 'batch_size': 1
}

webots_config = {
    'bootstrap_servers': ['localhost:9092'],
    # 'acks': 'all',
    'retries': 100,
    # 'max_in_flight_requests_per_connection': 5,
    # 'compression_type': 'snappy',
    'linger_ms': 5,
    # 'batch_size': 32
}