from datetime import datetime, timezone
import asyncio

async def update_queue_length(params):
    while True:
        if params['queue'].empty():
            params['api'].update_profile(location='queue: empty')
        else:
            time_difference = str(datetime.now(timezone.utc) - params['last_time'])
            size = params['queue'].qsize()
            # We only need hour and minutes
            time_difference_formatted = time_difference[:time_difference.index(':', 3)]
            params['api'].update_profile(location=f'queue time: {time_difference_formatted}. length: {size}')
        await asyncio.sleep(60)
