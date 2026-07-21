"""Repositories: the only layer that touches SQLAlchemy queries.

Services depend on these classes, so swapping storage or mocking data access
in tests never touches business logic.
"""
