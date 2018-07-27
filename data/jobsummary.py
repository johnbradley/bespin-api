from models import Job
import datetime

SECONDS_IN_AN_HOUR = 3600.0


class JobSummary(object):
    def __init__(self, job):
        self.job = job

    @staticmethod
    def zip_job_activity_pairs(activities):
        """
        Return a list of (activity, next_activity) pairs based on this job's activities.
        Last next_activity value will be None.
        :param activities: [JobActivity]: activities to be zipped
        :return: [(JobActivity, JobActivity)]: pairs of job activities
        """
        return zip(activities, activities[1:] + [None])

    def filtered_activity_pairs(self, state, steps_to_include):
        """
        Return pairs(current_activity, next_activity) of this job's activities filtered by state and step data.
        :param state: str: the job state to include
        :param steps_to_include: [str]: list of job steps to include
        :return: [JobActivity]: pairs of job activities
        """
        filtered_activity_pairs = []
        activities = list(self.job.job_activities.all())
        for activity_pair in self.zip_job_activity_pairs(activities):
            activity, next_activity = activity_pair
            if activity.state == state and activity.step in steps_to_include:
                filtered_activity_pairs.append(activity_pair)
        return filtered_activity_pairs

    @staticmethod
    def calculate_elapsed_hours(activity, next_activity):
        """
        Return how long an activity took in hours.
        :param activity: JobActivity: activity to determine length of (starting time)
        :param next_activity: JobActivity: next activity (stopping time)
        :return: float: number of hours ellapsed in activity
        """
        if next_activity:
            end_datetime = next_activity.created
        else:
            end_datetime = datetime.datetime.now()
        time_delta = end_datetime - activity.created
        elapsed_seconds = time_delta.total_seconds()
        return elapsed_seconds / SECONDS_IN_AN_HOUR

    def calculate_vm_hours(self):
        """
        Calculate how long a job has run(or is currently running) on a VM.
        :return: float: number hours
        """
        hours = 0
        steps_to_include = [Job.JOB_STEP_STAGING, Job.JOB_STEP_RUNNING, Job.JOB_STEP_STORE_OUTPUT]
        vm_step_activity_pairs = self.filtered_activity_pairs(Job.JOB_STATE_RUNNING, steps_to_include)
        for activity, next_activity in vm_step_activity_pairs:
            hours += self.calculate_elapsed_hours(activity, next_activity)
        return hours
