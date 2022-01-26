import sys
import time
import logging
from datajoint_utilities.dj_worker import WorkerLog, DataJointWorker, parse_args

from workflow.pipeline import session, ephys, db_prefix


_logger = logging.getLogger(__name__)
_logger.setLevel('INFO')


def auto_generate_probe_insertions():
    for skey in (session.Session - ephys.ProbeInsertion).fetch('KEY', limit=10):
        try:
            ephys.ProbeInsertion.auto_generate_entries(skey)
        except FileNotFoundError as e:
            _logger.debug(str(e))
        except Exception as e:
            _logger.error(str(e))


def auto_generate_clustering_tasks():
    for rkey in (ephys.EphysRecording - ephys.ClusteringTask).fetch('KEY', limit=10):
        try:
            ephys.ClusteringTask.auto_generate_entries(rkey)
        except FileNotFoundError as e:
            _logger.debug(str(e))
        except Exception as e:
            _logger.error(str(e))


# -------- Define worker(s) --------
worker_schema_name = db_prefix + "workerlog"
autoclear_error_patterns = ['%FileNotFound%']

# standard worker for non-GPU jobs
standard_worker = DataJointWorker('standard_worker',
                                  worker_schema_name,
                                  db_prefix=db_prefix,
                                  run_duration=1,
                                  sleep_duration=10,
                                  autoclear_error_patterns=autoclear_error_patterns)

standard_worker(auto_generate_probe_insertions)
standard_worker(ephys.EphysRecording, max_calls=10)
standard_worker(auto_generate_clustering_tasks)
standard_worker(ephys.Clustering, max_calls=5)
standard_worker(ephys.CuratedClustering, max_calls=10)
standard_worker(ephys.LFP, max_calls=1)
standard_worker(ephys.WaveformSet, max_calls=1)

# spike_sorting worker for GPU required jobs

spike_sorting_worker = DataJointWorker('spike_sorting_worker',
                                       worker_schema_name,
                                       db_prefix=db_prefix,
                                       run_duration=1,
                                       sleep_duration=10,
                                       autoclear_error_patterns=autoclear_error_patterns)

spike_sorting_worker(ephys.Clustering, max_calls=5)


# -------- Run worker(s) --------
configured_workers = {
    'standard_worker': standard_worker,
    'spike_sorting_worker': spike_sorting_worker
}


def run(**kwargs):
    worker = configured_workers[kwargs["worker_name"]]
    worker._run_duration = kwargs["duration"]
    worker._sleep_duration = kwargs["sleep"]

    try:
        worker.run()
    except Exception:
        _logger.exception(
            "Worker '{}' encountered an exception:".format(kwargs["worker_name"])
        )


def cli():
    """
    Calls :func:`run` passing the CLI arguments extracted from `sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    args = parse_args(sys.argv[1:])
    run(
        priority=args.priority,
        duration=args.duration,
        sleep=args.sleep
    )


if __name__ == '__main__':
    cli()
