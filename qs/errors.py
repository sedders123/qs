class Error(Exception):
    """Base Error Class"""
    pass


class NoStoriesError(Error):
    """Raised when an operation attempts to get a projects stories, however none
    have been created
    """
    def __init__(self):
        pass
