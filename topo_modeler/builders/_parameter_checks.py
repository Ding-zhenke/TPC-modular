"""Parameter existence checks using cst-automation's public setup API."""

from typing import Iterable, List


def missing_parameters(app, names: Iterable[str]) -> List[str]:
    """Return missing names via ``setup.get_parameter`` when the app exposes it.

    Offline recorder objects often do not model a CST parameter table, so an
    app without the public getter is treated as unchecked. For a real setup
    instance, ``get_parameter`` raises ``KeyError`` for an undefined name.
    Other failures abort the build rather than allowing a possibly modal CST
    operation to continue with an unknown parameter state.
    """
    getter = getattr(app, "get_parameter", None)
    if not callable(getter):
        return []

    missing = []
    for name in names:
        try:
            getter(name)
        except KeyError:
            missing.append(name)
        except Exception as exc:
            raise RuntimeError(
                f"Unable to check whether CST parameter {name!r} exists via "
                "the public cst-automation setup.get_parameter() API; "
                "aborting to avoid an unverified parameter reference."
            ) from exc
    return missing
