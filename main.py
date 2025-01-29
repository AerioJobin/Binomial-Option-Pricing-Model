import math

def binomial_option_pricing(S, K, T, r, sigma, n, option_type='call', exercise_type='european'):
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

    Returns:
    float: The option price.
    """
    # Calculate time step and discount factor
    dt = T / n  # Time step
    discount = math.exp(-r * dt)  # Discount factor

    # Calculate up and down factors
    u = math.exp(sigma * math.sqrt(dt))  # Up factor
    d = 1 / u  # Down factor

    # Risk-neutral probability
    p = (math.exp(r * dt) - d) / (u - d)

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
                if option_type == 'call':
                    option_values[j] = max(option_values[j], asset_prices[j] - K)
                elif option_type == 'put':
                    option_values[j] = max(option_values[j], K - asset_prices[j])

    return option_values[0]


# Example usage
S = 100  # Underlying price
K = 100  # Strike price
T = 1    # Time to expiration (1 year)
r = 0.05 # Risk-free rate (5%)
sigma = 0.2  # Volatility (20%)
n = 100  # Number of time steps

# European Call Option
european_call_price = binomial_option_pricing(S, K, T, r, sigma, n, option_type='call', exercise_type='european')
print(f"European Call Option Price: {european_call_price:.2f}")

# American Put Option
american_put_price = binomial_option_pricing(S, K, T, r, sigma, n, option_type='put', exercise_type='american')
print(f"American Put Option Price: {american_put_price:.2f}")