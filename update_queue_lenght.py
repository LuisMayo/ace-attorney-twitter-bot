from datetime import datetime, timezone
from time import sleep

def update_queue_length(params):
    while True:
        if params['last_time'] is None:
            params['api'].update_profile(location='queue: empty')
        else:
            time_difference = datetime.now(timezone.utc) - params['last_time']
            params['last_time'] = None
            size = params['queue'].qsize()
            # We only need hour and minutes
            time_difference_formatted = time_difference[:time_difference.index(':', 3)]
            params['api'].update_profile(location=f'queue time: {time_difference_formatted}. length: {size}')
        sleep(10)