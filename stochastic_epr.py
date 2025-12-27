# stochastic_epr.py
# Standalone stochastic EPR timing model consistent with repeat-until-success.
# Paper model: success probability p = 2 * alpha * eta
# We model attempts ~ Geometric(p), total generation time scales with attempts.

from dataclasses import dataclass
import random
import math

@dataclass
class StochasticEPRConfig:
    enabled: bool = False

    # Paper parameters
    alpha: float = 0.5

    # Effective transmission rates (eta) for in-rack and cross-rack.
    # You can interpret these as "overall photon transmission rate" per the paper.
    eta_inter: float = 1e-2
    eta_exter: float = 1e-3

    # Time granularity: how much time each attempt costs (in your scheduler's unit time)
    # Often, you can set this to inter_time/exter_time, or 1, depending on calibration.
    attempt_time_inter: int = 1
    attempt_time_exter: int = 1

    # Optional cap to avoid extreme outliers in toy experiments
    max_attempts: int = None

class EPRSampler:
    """
    Generates stochastic EPR generation durations following repeat-until-success.
    """
    def __init__(self, cfg: StochasticEPRConfig, seed: int = None):
        self.cfg = cfg
        self.rng = random.Random(seed)

    def _p_success(self, eta: float) -> float:
        # p = 2 * alpha * eta
        p = 2.0 * float(self.cfg.alpha) * float(eta)
        # clamp into (0,1]
        if p <= 0.0:
            return 0.0
        if p > 1.0:
            return 1.0
        return p

    def geometric_attempts(self, p: float) -> int:
        """
        Attempts until first success.
        Geometric(p) over {1,2,3,...}.
        """
        if p <= 0.0:
            # effectively never succeeds; you can decide policy:
            # return a very large number to emulate "timeouts"
            return self.cfg.max_attempts if self.cfg.max_attempts is not None else 10**9

        # Inverse CDF for geometric:
        # P(N <= k) = 1 - (1-p)^k
        u = self.rng.random()
        n = math.ceil(math.log(1 - u) / math.log(1 - p))
        if n < 1:
            n = 1

        if self.cfg.max_attempts is not None:
            n = min(n, self.cfg.max_attempts)
        return n

    def sample_duration(self, is_inter: bool, base_switch_time: int, base_gen_time: int) -> int:
        """
        Returns end-to-end duration for an EPR generation event starting now:
        duration = switch_time + attempts * attempt_time
        where attempts ~ Geometric(p).
        base_gen_time is used only in deterministic mode, or as a default scaling anchor.
        """
        if not self.cfg.enabled:
            return int(base_switch_time + base_gen_time)

        if is_inter:
            p = self._p_success(self.cfg.eta_inter)
            attempts = self.geometric_attempts(p)
            attempt_time = int(self.cfg.attempt_time_inter)
        else:
            p = self._p_success(self.cfg.eta_exter)
            attempts = self.geometric_attempts(p)
            attempt_time = int(self.cfg.attempt_time_exter)

        return int(base_switch_time + attempts * attempt_time)
