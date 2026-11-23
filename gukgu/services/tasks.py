from gukgu import models


def calculate_percent(done, total):
    """Whole-number percent, rounding half up; 0 when there is nothing to count."""
    if total <= 0:
        return 0
    # Integer math: round() would use banker's rounding (12.5 -> 12)
    return (done * 200 + total) // (total * 2)


def get_progress_by_project(projects):
    """Return {project id: (done, total, percent)} using a single query.

    Only active tasks count. Projects without tasks get (0, 0, 0). Nothing is
    stored; the numbers are recomputed on every call.
    """
    project_ids = [project.id for project in projects]
    counts = {project_id: [0, 0] for project_id in project_ids}
    if not project_ids:
        return {}

    rows = (
        models.Task.objects(project__in=project_ids, status="active")
        .only("project", "is_done")
        .as_pymongo()
    )
    for row in rows:
        count = counts.get(row["project"].id)
        if count is None:
            continue
        count[1] += 1
        if row.get("is_done"):
            count[0] += 1

    return {
        project_id: (done, total, calculate_percent(done, total))
        for project_id, (done, total) in counts.items()
    }


def get_progress(project):
    """Return (done, total, percent) of the active tasks of one project."""
    return get_progress_by_project([project])[project.id]
