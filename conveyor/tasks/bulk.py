import datetime
import time

import slumber

from conveyor.core import Conveyor
from conveyor.processor import get_key


# We ignore the last component as we cannot properly handle it
def get_jobs(last=0):
    current = time.mktime(datetime.datetime.utcnow().timetuple())

    app = Conveyor()

    warehouse = slumber.API(
                        app.config["conveyor"]["warehouse"]["url"],
                        auth=(
                            app.config["conveyor"]["warehouse"]["auth"]["username"],
                            app.config["conveyor"]["warehouse"]["auth"]["password"],
                        )
                    )
    processor_class = app.get_processor_class()
    processor = processor_class(
                    index=app.config["conveyor"]["index"],
                    warehouse=warehouse,
                    store=app.redis,
                    store_prefix=app.config.get("redis", {}).get("prefix", None)
                )

    names = set(processor.client.list_packages())

    for package in names:
        yield package

    processor.store.set(get_key(processor.store_prefix, "pypi:since"), current)


def handle_job(name):
    app = Conveyor()

    warehouse = slumber.API(
                        app.config["conveyor"]["warehouse"]["url"],
                        auth=(
                            app.config["conveyor"]["warehouse"]["auth"]["username"],
                            app.config["conveyor"]["warehouse"]["auth"]["password"],
                        )
                    )
    processor_class = app.get_processor_class()
    processor = processor_class(
                    index=app.config["conveyor"]["index"],
                    warehouse=warehouse,
                    store=app.redis,
                    store_prefix=app.config.get("redis", {}).get("prefix", None)
                )

    for release in processor.get_releases(name):
        processor.sync_release(release)
