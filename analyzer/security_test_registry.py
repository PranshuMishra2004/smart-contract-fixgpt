from collections.abc import Callable

from analyzer.foundry_verifier import (
    run_foundry_reentrancy_test,
    run_foundry_tx_origin_test,
)


SecurityTest = Callable[[str, str], dict]


SECURITY_TESTS: dict[str, SecurityTest] = {
    "reentrancy-eth": run_foundry_reentrancy_test,
    "tx-origin": run_foundry_tx_origin_test,
}


def get_security_test(
    detector_name: str,
) -> SecurityTest | None:
    """
    Return the vulnerability-specific security
    test registered for a Slither detector.
    """

    return SECURITY_TESTS.get(
        detector_name
    )