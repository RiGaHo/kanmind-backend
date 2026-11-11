"""Transactional membership changes keep task assignments consistent."""

from django.db import transaction


@transaction.atomic
def set_members(board, members):
    """Retain the owner and clear assignments of removed members."""
    board.members.set(set(members) | {board.owner})
    ids = board.members.values_list("pk", flat=True)
    board.tasks.exclude(assignee_id__in=ids).update(assignee=None)
    board.tasks.exclude(reviewer_id__in=ids).update(reviewer=None)
