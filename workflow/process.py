import time
import logging
from workflow.pipeline import session, ephys

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


_generic_errors = ["%Deadlock%", "%DuplicateError%", "%Lock wait timeout%",
                   "%MaxRetryError%", "%KeyboardInterrupt%",
                   "InternalError: (1205%", "%SIGTERM%"]


def _clean_up():
    (ephys.schema.jobs & 'status = "error"'
     & [f'error_message LIKE "{e}"'
        for e in _generic_errors + ['%FileNotFound%']]).delete()


_tables = ((ephys.EphysRecording, {'max_calls': 10}),
           (ephys.Clustering, {'max_calls': 5}),
           (ephys.CuratedClustering, {'max_calls': 10}),
           (ephys.LFP, {'max_calls': 1}),
           (ephys.WaveformSet, {'max_calls': 1}))

_default_settings = {
    'display_progress': True,
    'reserve_jobs': True,
    'suppress_errors': True}


def run(run_duration=3600*3, sleep_duration=10):

    start_time = time.time()
    while ((time.time() - start_time < run_duration)
           or (run_duration is None)
           or (run_duration < 0)):

        # auto-generate entries for ProbeInsertion
        for skey in (session.Session - ephys.ProbeInsertion).fetch('KEY', limit=10):
            try:
                ephys.ProbeInsertion.auto_generate_entries(skey)
            except FileNotFoundError as e:
                logger.debug(str(e))
            except Exception as e:
                logger.error(str(e))

        # auto-generate entries for ClusteringTask
        for rkey in (ephys.EphysRecording - ephys.ClusteringTask).fetch('KEY', limit=10):
            try:
                ephys.ClusteringTask.auto_generate_entries(rkey)
            except FileNotFoundError as e:
                logger.debug(str(e))
            except Exception as e:
                logger.error(str(e))

        # populate all ephys tables
        for table, populate_settings in _tables:
            logger.info(f'------------- {table.__name__} ---------------')
            table.populate(**{**_default_settings, **populate_settings})

        _clean_up()
        time.sleep(sleep_duration)


if __name__ == '__main__':
    run()
