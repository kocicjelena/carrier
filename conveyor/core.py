from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import logging.config
import os
import time

import forklift
import redis
import requests
import xmlrpc2.client

from apscheduler.scheduler import Scheduler

from .config import Config, defaults
from .processor import Processor


logger = logging.getLogger(__name__)


class Conveyor(object):

    def __init__(self, *args, **kwargs):
        super(Conveyor, self).__init__(*args, **kwargs)

        # Get configuration
        self.config = Config(os.path.dirname(__file__))
        self.config.from_object(defaults)
        self.config.from_envvar("CONVEYOR_CONF")

        # Initalize app
        logging.config.dictConfig(self.config["LOGGING"])

        store = redis.StrictRedis(**dict([(k.lower, v) for k, v in self.config["REDIS"].items()]))

        wsession = requests.session(auth=(
                        self.config["WAREHOUSE_AUTH"]["USERNAME"],
                        self.config["WAREHOUSE_AUTH"]["PASSWORD"],
                    ))
        warehouse = forklift.Forklift(session=wsession)

        psession = requests.session(verify=self.config["PYPI_SSL_VERIFY"])
        pypi = xmlrpc2.client.Client(self.config["PYPI_URI"], session=psession)

        self.processor = Processor(warehouse, pypi, store)

    def run(self):
        scheduler = Scheduler()

        if self.config["SCHEDULE"].get("packages") is not None:
            scheduler.add_interval_job(self.processor.process, **self.config["SCHEDULE"]["packages"])

        scheduler.start()

        try:
            while True:
                time.sleep(999)
        except KeyboardInterrupt:
            logger.info("Shutting down Conveyor...")
            scheduler.shutdown(wait=False)
