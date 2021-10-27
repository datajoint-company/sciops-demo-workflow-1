import time
import logging
from workflow.pipeline import session, ephys, db_prefix
from workflow.djworker import WorkerLog, DataJointWorker

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


def auto_generate_probe_insertions():
    for skey in (session.Session - ephys.ProbeInsertion).fetch('KEY', limit=10):
        try:
            ephys.ProbeInsertion.auto_generate_entries(skey)
        except FileNotFoundError as e:
            logger.debug(str(e))
        except Exception as e:
            logger.error(str(e))


def auto_generate_clustering_tasks():
    for rkey in (ephys.EphysRecording - ephys.ClusteringTask).fetch('KEY', limit=10):
        try:
            ephys.ClusteringTask.auto_generate_entries(rkey)
        except FileNotFoundError as e:
            logger.debug(str(e))
        except Exception as e:
            logger.error(str(e))


worker = DataJointWorker('sciops_worker', db_prefix + 'log',
                         db_prefix=db_prefix,
                         run_duration=3600*3,
                         sleep_duration=10)

worker(auto_generate_probe_insertions)
worker(ephys.EphysRecording, max_calls=10)
worker(auto_generate_clustering_tasks)
worker(ephys.Clustering, max_calls=5)
worker(ephys.CuratedClustering, max_calls=10)
worker(ephys.LFP, max_calls=1)
worker(ephys.WaveformSet, max_calls=1)


def run():
    worker.run()


if __name__ == '__main__':
    run()
