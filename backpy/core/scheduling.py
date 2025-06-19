import uuid

import crontab

COMMENT_SUFFIX = "(MANAGED BY BACKPY)"


def create_cronjob(
    unique_id: uuid.UUID, command: str, schedule: str
) -> crontab.CronItem:

    cron = crontab.CronTab(user=True)
    job = cron.new(command=command, comment=_get_comment(unique_id=unique_id))
    job.setall(schedule)
    cron.write()

    return job


def delete_cronjobs_by_uuid(unique_id: uuid.UUID):
    for job in get_cronjobs_by_uuid(unique_id=unique_id):
        job.delete()


def get_cronjobs_by_uuid(unique_id: uuid.UUID) -> list[crontab.CronItem]:
    cron = crontab.CronTab(user=True)
    return list(cron.find_comment(_get_comment(unique_id=unique_id)))


def _get_comment(unique_id: uuid.UUID) -> str:
    return str(unique_id) + " " + COMMENT_SUFFIX
