from dotenv import dotenv_values, find_dotenv

config = dotenv_values(find_dotenv())

agents_config = {
    'bootstrap_servers': f'{config.get("KAFKA_SERVER_IP")}:{config.get("KAFKA_AGENTS_PORT")}',
    'group_id': f'{config.get("KAFKA_GROUP_ID")}',
    # 'enable_auto_commit': False,
    # 'auto_offset_reset': 'latest'
}

webots_config = {
    'bootstrap_servers': f'{config.get("KAFKA_SERVER_IP")}:{config.get("KAFKA_WEBOTS_PORT")}',
    'group_id': f'{config.get("KAFKA_GROUP_ID")}',
    # 'enable_auto_commit': False,
    # 'auto_offset_reset': 'latest'
}

trainer_config = {
    'bootstrap_servers': f'{config.get("KAFKA_SERVER_IP")}:{config.get("KAFKA_TRAINER_PORT")}',
    'group_id': f'{config.get("KAFKA_GROUP_ID")}',
    # 'enable_auto_commit': False,
    # 'auto_offset_reset': 'latest'
}