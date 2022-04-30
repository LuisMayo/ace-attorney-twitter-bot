from datetime import datetime, timezone
from time import sleep

def update_queue_length(params):
    while True:
        if params['queue'].empty():
            params['mastodon'].account_update_credentials(fields=[("Queue time", "N/A"), ("Queue length", "Empty")])
        else:
            time_difference = str(datetime.now(timezone.utc) - params['last_time'])
            size = params['queue'].qsize()
            # We only need hour and minutes
            time_difference_formatted = time_difference[:time_difference.index(':', 3)]
            params['mastodon'].account_update_credentials(fields=[("Queue time", time_difference_formatted), ("Queue length", size)])
        sleep(60)
