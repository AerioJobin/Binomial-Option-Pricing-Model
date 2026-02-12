import math
from typing import Optional, Tuple


def _validate_inputs(S, K, T, r, sigma, n, option_type, exercise_type, q):
    if S <= 0 or K <= 0:
        raise ValueError("S and K must be positive.")
    if T <= 0:
        raise ValueError("T must be positive.")
    if n <= 0 or int(n) != n:
        raise ValueError("n must be a positive integer.")
    if sigma < 0:
        raise ValueError("sigma must be non-negative.")
    if option_type not in ("call", "put"):
        raise ValueError("Invalid option type. Use 'call' or 'put'.")
    if exercise_type not in ("european", "american"):
        raise ValueError("Invalid exercise type. Use 'european' or 'american'.")
    if q is not None and q < 0:
        raise ValueError("q (dividend yield) must be non-negative.")


def _risk_neutral_prob(u, d, r, q, dt):
    p = (math.exp((r - q) * dt) - d) / (u - d)
    if p < 0 or p > 1:
        raise ValueError(
            f"Risk-neutral probability out of bounds: p={p:.6f}. "
            "Try increasing n or checking inputs."
        )
    return p


def binomial_option_pricing(
    S,
    K,
    T,
    r,
    sigma,
    n,
    option_type="call",
    exercise_type="european",
    q: float = 0.0,
):
    """
    Binomial Option Pricing Model for European and American options.

    Parameters:
    S (float): Current price of the underlying asset.
    K (float): Strike price of the option.
    T (float): Time to expiration (in years).
    r (float): Risk-free interest rate (annualized).
    sigma (float): Volatility of the underlying asset (annualized).
    n (int): Number of time steps in the binomial tree.
    option_type (str): Type of option - 'call' or 'put'.
    exercise_type (str): Exercise type - 'european' or 'american'.
    q (float): Continuous dividend yield (annualized).

    Returns:
    float: The option price.
    """
    _validate_inputs(S, K, T, r, sigma, n, option_type, exercise_type, q)

    # Calculate time step and discount factor
    dt = T / n  # Time step
    discount = math.exp(-r * dt)  # Discount factor

    # Calculate up and down factors
    u = math.exp(sigma * math.sqrt(dt)) if sigma > 0 else 1.0
    d = 1 / u  # Down factor

    # Risk-neutral probability
    if u == d:
        raise ValueError("u and d are equal; increase n or sigma.")
    p = _risk_neutral_prob(u, d, r, q, dt)

    # Initialize asset prices at maturity
    asset_prices = [S * (u ** j) * (d ** (n - j)) for j in range(n + 1)]

    # Initialize option values at maturity
    if option_type == 'call':
        option_values = [max(0, price - K) for price in asset_prices]
    elif option_type == 'put':
        option_values = [max(0, K - price) for price in asset_prices]
    else:
        raise ValueError("Invalid option type. Use 'call' or 'put'.")

    # Step back through the tree
    for i in range(n - 1, -1, -1):
        for j in range(i + 1):
            # Calculate the option value at the current node
            option_values[j] = discount * (p * option_values[j + 1] + (1 - p) * option_values[j])

            # For American options, check for early exercise
            if exercise_type == 'american':
                # Use the current node's underlying price, not maturity prices
                node_price = S * (u ** j) * (d ** (i - j))
                if option_type == 'call':
                    option_values[j] = max(option_values[j], node_price - K)
                elif option_type == 'put':
                    option_values[j] = max(option_values[j], K - node_price)

    return option_values[0]


def price_with_convergence(
    S,
    K,
    T,
    r,
    sigma,
    option_type="call",
    exercise_type="european",
    q: float = 0.0,
    n_start: int = 50,
    n_max: int = 2000,
    tol: float = 1e-4,
    step: int = 50,
) -> Tuple[float, int]:
    """Increase n until price change is within tol or n_max is reached."""
    if n_start <= 0 or n_max <= 0 or step <= 0:
        raise ValueError("n_start, n_max, and step must be positive.")
    n = n_start
    prev = binomial_option_pricing(S, K, T, r, sigma, n, option_type, exercise_type, q)
    n += step
    while n <= n_max:
        curr = binomial_option_pricing(S, K, T, r, sigma, n, option_type, exercise_type, q)
        if abs(curr - prev) <= tol:
            return curr, n
        prev = curr
        n += step
    return prev, n_max


def implied_volatility(
    market_price,
    S,
    K,
    T,
    r,
    n,
    option_type="call",
    exercise_type="european",
    q: float = 0.0,
    vol_low: float = 1e-6,
    vol_high: float = 5.0,
    tol: float = 1e-6,
    max_iter: int = 100,
) -> float:
    """Implied volatility via bisection on binomial price."""
    if market_price <= 0:
        raise ValueError("market_price must be positive.")
    _validate_inputs(S, K, T, r, sigma=0.0, n=n, option_type=option_type, exercise_type=exercise_type, q=q)

    def price_at(vol):
        return binomial_option_pricing(S, K, T, r, vol, n, option_type, exercise_type, q)

    low = vol_low
    high = vol_high
    price_low = price_at(low)
    price_high = price_at(high)

    if not (price_low <= market_price <= price_high):
        raise ValueError(
            "market_price not bracketed by prices at vol_low and vol_high. "
            "Try wider vol bounds."
        )

    for _ in range(max_iter):
        mid = 0.5 * (low + high)
        price_mid = price_at(mid)
        if abs(price_mid - market_price) <= tol:
            return mid
        if price_mid < market_price:
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


def greeks(
    S,
    K,
    T,
    r,
    sigma,
    n,
    option_type="call",
    exercise_type="european",
    q: float = 0.0,
    dS: Optional[float] = None,
    dT: Optional[float] = None,
):
    """Finite-difference Greeks using the binomial pricer."""
    _validate_inputs(S, K, T, r, sigma, n, option_type, exercise_type, q)
    dS = dS if dS is not None else max(0.01 * S, 1e-4)
    dT = dT if dT is not None else max(1e-4, 1e-3 * T)

    base = binomial_option_pricing(S, K, T, r, sigma, n, option_type, exercise_type, q)
    up = binomial_option_pricing(S + dS, K, T, r, sigma, n, option_type, exercise_type, q)
    down = binomial_option_pricing(S - dS, K, T, r, sigma, n, option_type, exercise_type, q)
    delta = (up - down) / (2 * dS)
    gamma = (up - 2 * base + down) / (dS ** 2)

    # Theta as dPrice/dT (time decay, typically negative)
    upT = binomial_option_pricing(S, K, T + dT, r, sigma, n, option_type, exercise_type, q)
    downT = binomial_option_pricing(S, K, max(T - dT, 1e-8), r, sigma, n, option_type, exercise_type, q)
    theta = (upT - downT) / (2 * dT)

    return {
        "price": base,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
    }


# Example usage
S = 100  # Underlying price
K = 100  # Strike price
T = 1    # Time to expiration (1 year)
r = 0.05 # Risk-free rate (5%)
sigma = 0.2  # Volatility (20%)
n = 100  # Number of time steps
q = 0.02  # Dividend yield (2%)

# European Call Option (with dividend yield)
european_call_price = binomial_option_pricing(S, K, T, r, sigma, n, option_type='call', exercise_type='european', q=q)
print(f"European Call Option Price: {european_call_price:.2f}")

# American Put Option
american_put_price = binomial_option_pricing(S, K, T, r, sigma, n, option_type='put', exercise_type='american', q=q)
print(f"American Put Option Price: {american_put_price:.2f}")

# Convergence control
conv_price, conv_n = price_with_convergence(S, K, T, r, sigma, option_type='call', exercise_type='european', q=q)
print(f"Converged Price: {conv_price:.4f} with n={conv_n}")

# Implied volatility (example target price)
target_price = european_call_price
iv = implied_volatility(target_price, S, K, T, r, n, option_type='call', exercise_type='european', q=q)
print(f"Implied Volatility: {iv:.4f}")

# Greeks
g = greeks(S, K, T, r, sigma, n, option_type='call', exercise_type='european', q=q)
print(f"Greeks: price={g['price']:.4f}, delta={g['delta']:.4f}, gamma={g['gamma']:.6f}, theta={g['theta']:.4f}")
