"""Authentication tweens."""
from pyramid.httpexceptions import HTTPFound
from pyramid.registry import Registry

from websauna.system.core import messages
from websauna.system.http import Request

from sqlalchemy import inspect


class SessionInvalidationTweenFactory:
    """Tween to detect invalidated sessions and redirect user back to home.

    This tween checks if the current session is logged in user and there has been authentication sensitive changes to this user. In this case all user sessions should be logged out.
    """

    def __init__(self, handler, registry:Registry):
        self.handler = handler
        self.registry = registry

    def __call__(self, request: Request):
        user = request.user

        if user:

            # TODO: Temporary workaround of error logs.
            # We simply discard user object in the case of transaction conflict,
            # Waiting for pyramid_tm 2.0 to handle this correctly
            # otherwise we get sqlalchemy.orm.exc.DetachedInstanceError: Instance in new few lines
            state = inspect(user)

            if state.detached or state.transient:
                # Do it here, because this is simply the point here this crap hits first
                request.user = None

            else:
                session_created_at = request.session["created_at"]
                if not user.is_valid_session(session_created_at):
                    request.session.invalidate()
                    messages.add(request, kind="error", msg="Your have been logged out due to authentication changes.   ", msg_id="msg-session-invalidated")
                    return HTTPFound(request.application_url)

        response = self.handler(request)
        return response