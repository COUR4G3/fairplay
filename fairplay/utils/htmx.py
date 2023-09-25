import dataclasses
import json
import typing as t

from flask import Response, abort, make_response, request
from werkzeug.local import LocalProxy

HTMX_FALSE = "false"
HTMX_NULL = "null"
HTMX_STOP_POLLING = 286
HTMX_TRUE = "true"

HTMXReswap = t.Literal[
    "innerHTML",
    "outerHTML",
    "beforebegin",
    "afterbegin",
    "beforeend",
    "afterend",
    "delete",
    "none",
]


@dataclasses.dataclass
class HTMXRequest:
    boosted: t.Optional[bool] = False
    current_url: t.Optional[str] = None
    history_restore_request: t.Optional[bool] = None
    prompt: t.Optional[str] = None
    request: t.Optional[bool] = True
    target: t.Optional[str] = None
    trigger_name: t.Optional[str] = None
    trigger: t.Optional[str] = None

    _headers: t.Dict[str, str] = dataclasses.field(default_factory=dict)

    @classmethod
    def parse(cls):
        if request.headers.get("HX-Request") != HTMX_TRUE:
            return

        data = {}
        for header, value in request.headers.items():
            if header.startswith("HX-"):
                continue

            attr = header[3:].lower().replace("-", "_")

            if value.lower() == HTMX_TRUE:
                value = True
            elif value.lower() == HTMX_FALSE:
                value = False
            elif value.lower() == HTMX_NULL:
                value = None

            data[attr] = value

        return cls(
            boosted=data.get("boosted"),
            current_url=data.get("current_url"),
            history_restore_request=data.get("history_restore_request"),
            prompt=data.get("prompt"),
            request=data.get("request"),
            target=data.get("target"),
            trigger_name=data.get("trigger_name"),
            trigger=data.get("trigger"),
            _headers=data,
        )


class HTMXClientRedirectResponse(Response):
    def __init__(self, redirect_to: str, status: int = 200):
        super().__init__(
            None,
            status=status,
            headers={"HX-Redirect": redirect_to},
        )


class HTMXStopPollingResponse(Response):
    def __init__(
        self,
        response=None,
        headers=None,
        mimetype="text/html",
        direct_passthrough=False,
    ):
        super().__init__(
            response=response,
            status=HTMX_STOP_POLLING,
            headers=headers,
            mimetype=mimetype,
            direct_passthrough=direct_passthrough,
        )


htmx_request = LocalProxy(HTMXRequest.parse)


def init_htmx(app):
    app.add_template_global(htmx_request, "htmx_request")


def stop_polling(response: t.Any):
    abort(HTMXStopPollingResponse(response))


def _stringify(val):
    return val if isinstance(val, str) else json.dumps(val)


def make_htmx_response(
    *args: t.Any,
    location: t.Optional[t.Union[dict, str]] = None,
    push_url: t.Optional[t.Union[t.Literal[False], str]] = None,
    redirect: t.Optional[str] = None,
    refresh: bool = False,
    replace_url: t.Optional[t.Union[t.Literal[False], str]] = None,
    reswap: t.Optional[HTMXReswap] = None,
    retarget: t.Optional[str] = None,
    trigger: t.Optional[t.Union[dict, str]] = None,
    trigger_after_settle: t.Optional[t.Union[dict, str]] = None,
    trigger_after_swap: t.Optional[t.Union[dict, str]] = None,
) -> Response:
    resp = make_response(*args)

    if location:
        resp.headers["HX-Location"] = _stringify(location)

    if push_url:
        resp.headers["HX-Push-Url"] = push_url
    else:
        resp.headers["HX-Push-Url"] = HTMX_FALSE

    if redirect:
        resp.headers["HX-Redirect"] = redirect
    if refresh:
        resp.headers["HX-Refresh"] = HTMX_TRUE

    if replace_url:
        resp.headers["HX-Replace-Url"] = replace_url
    elif replace_url is False:
        resp.headers["HX-Replace-Url"] = HTMX_FALSE

    if reswap:
        resp.headers["HX-Reswap"] = reswap
    if retarget:
        resp.headers["HX-Retarget"] = retarget

    if retarget:
        resp.headers["HX-Retarget"] = retarget
    if trigger:
        resp.headers["HX-Trigger"] = _stringify(trigger)
    if trigger_after_settle:
        resp.headers["HX-Trigger-After-Settle"] = _stringify(
            trigger_after_settle,
        )
    if trigger_after_swap:
        resp.headers["HX-Trigger-After-Swap"] = _stringify(trigger_after_swap)

    return resp
