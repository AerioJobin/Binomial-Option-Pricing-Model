Binomial Option Pricing Model
Made by Aerio

Overview
This project implements a binomial options pricing engine with an interactive UI. It prices European and American options using the Cox-Ross-Rubinstein tree, supports a continuous dividend yield, estimates Greeks via finite differences, and can solve for implied volatility from a target price.

Model Inputs
Underlying Price (S): The current price of the underlying asset.
Strike Price (K): The price at which the option can be exercised.
Time to Expiration (T): The time remaining until the option expires (in years).
Risk-Free Rate (r): The annualized risk-free interest rate.
Volatility (sigma): The annualized volatility of the underlying asset's returns.
Dividend Yield (q): Continuous dividend yield (annualized).
Number of Steps (n): The number of time steps in the binomial tree.
Option Type: Call or put.
Exercise Type: European or American.

Functionality
The model calculates theoretical prices for calls and puts under European and American exercise styles. It also provides:
- Greeks: Delta, Gamma, Theta (finite differences).
- Implied Volatility: Solves for sigma given a target price.
- Convergence Control: Increases step count until the price stabilizes.

UI (Web App)
Open index.html in a browser to use the interactive UI. It includes:
- Pricing for European and American options with dividend yield.
- Greeks (Delta, Gamma, Theta).
- Implied volatility solver from a target price.
- Convergence trail chart to see stabilization across step counts.

Files
- main.py: Core binomial pricing logic and example usage.
- index.html: UI shell.
- styles.css: Visual design.
- app.js: Client-side pricing engine and interactions.

Notes
The binomial model converges to Black-Scholes for European options as n increases. For American options, early exercise is handled at each node using the current underlying price.
