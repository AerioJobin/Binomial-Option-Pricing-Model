"use strict";

const byId = (id) => document.getElementById(id);

function readInputs() {
  const S = parseFloat(byId("S").value);
  const K = parseFloat(byId("K").value);
  const T = parseFloat(byId("T").value);
  const r = parseFloat(byId("r").value);
  const sigma = parseFloat(byId("sigma").value);
  const q = parseFloat(byId("q").value);
  const n = parseInt(byId("n").value, 10);
  const option_type = byId("option_type").value;
  const exercise_type = byId("exercise_type").value;
  const target_price_raw = byId("target_price").value.trim();
  const target_price = target_price_raw === "" ? null : parseFloat(target_price_raw);
  return { S, K, T, r, sigma, q, n, option_type, exercise_type, target_price };
}

function validateInputs({ S, K, T, r, sigma, q, n, option_type, exercise_type }) {
  if (!(S > 0 && K > 0)) throw new Error("S and K must be positive.");
  if (!(T > 0)) throw new Error("T must be positive.");
  if (!(n > 0 && Number.isInteger(n))) throw new Error("n must be a positive integer.");
  if (sigma < 0) throw new Error("sigma must be non-negative.");
  if (q < 0) throw new Error("q must be non-negative.");
  if (!["call", "put"].includes(option_type)) throw new Error("Option type invalid.");
  if (!["european", "american"].includes(exercise_type)) throw new Error("Exercise type invalid.");
}

function riskNeutralProb(u, d, r, q, dt) {
  const p = (Math.exp((r - q) * dt) - d) / (u - d);
  if (p < 0 || p > 1) {
    throw new Error(`Risk-neutral probability out of bounds: p=${p.toFixed(6)}.`);
  }
  return p;
}

function binomialOptionPricing(S, K, T, r, sigma, n, optionType, exerciseType, q) {
  validateInputs({ S, K, T, r, sigma, q, n, option_type: optionType, exercise_type: exerciseType });
  const dt = T / n;
  const discount = Math.exp(-r * dt);
  const u = sigma > 0 ? Math.exp(sigma * Math.sqrt(dt)) : 1;
  const d = 1 / u;
  if (u === d) throw new Error("u and d are equal; increase n or sigma.");
  const p = riskNeutralProb(u, d, r, q, dt);

  const assetPrices = Array.from({ length: n + 1 }, (_, j) => S * (u ** j) * (d ** (n - j)));
  let optionValues = assetPrices.map((price) =>
    optionType === "call" ? Math.max(0, price - K) : Math.max(0, K - price)
  );

  for (let i = n - 1; i >= 0; i -= 1) {
    for (let j = 0; j <= i; j += 1) {
      const hold = discount * (p * optionValues[j + 1] + (1 - p) * optionValues[j]);
      if (exerciseType === "american") {
        const nodePrice = S * (u ** j) * (d ** (i - j));
        const exercise = optionType === "call" ? Math.max(0, nodePrice - K) : Math.max(0, K - nodePrice);
        optionValues[j] = Math.max(hold, exercise);
      } else {
        optionValues[j] = hold;
      }
    }
  }
  return optionValues[0];
}

function priceWithConvergence(params, nStart = 50, nMax = 2000, tol = 1e-4, step = 50) {
  let n = nStart;
  let prev = binomialOptionPricing(
    params.S,
    params.K,
    params.T,
    params.r,
    params.sigma,
    n,
    params.option_type,
    params.exercise_type,
    params.q
  );
  const trail = [{ n, price: prev }];
  n += step;
  while (n <= nMax) {
    const curr = binomialOptionPricing(
      params.S,
      params.K,
      params.T,
      params.r,
      params.sigma,
      n,
      params.option_type,
      params.exercise_type,
      params.q
    );
    trail.push({ n, price: curr });
    if (Math.abs(curr - prev) <= tol) {
      return { price: curr, n, trail };
    }
    prev = curr;
    n += step;
  }
  return { price: prev, n: nMax, trail };
}

function impliedVolatility(marketPrice, params, volLow = 1e-6, volHigh = 5, tol = 1e-6, maxIter = 100) {
  if (!(marketPrice > 0)) throw new Error("market_price must be positive.");
  let low = volLow;
  let high = volHigh;
  const priceLow = binomialOptionPricing(
    params.S,
    params.K,
    params.T,
    params.r,
    low,
    params.n,
    params.option_type,
    params.exercise_type,
    params.q
  );
  const priceHigh = binomialOptionPricing(
    params.S,
    params.K,
    params.T,
    params.r,
    high,
    params.n,
    params.option_type,
    params.exercise_type,
    params.q
  );
  if (!(priceLow <= marketPrice && marketPrice <= priceHigh)) {
    throw new Error("Target price not bracketed by vol_low and vol_high.");
  }

  for (let i = 0; i < maxIter; i += 1) {
    const mid = 0.5 * (low + high);
    const priceMid = binomialOptionPricing(
      params.S,
      params.K,
      params.T,
      params.r,
      mid,
      params.n,
      params.option_type,
      params.exercise_type,
      params.q
    );
    if (Math.abs(priceMid - marketPrice) <= tol) return mid;
    if (priceMid < marketPrice) low = mid;
    else high = mid;
  }
  return 0.5 * (low + high);
}

function greeks(params, dS = null, dT = null) {
  const stepS = dS ?? Math.max(0.01 * params.S, 1e-4);
  const stepT = dT ?? Math.max(1e-4, 1e-3 * params.T);
  const base = binomialOptionPricing(
    params.S,
    params.K,
    params.T,
    params.r,
    params.sigma,
    params.n,
    params.option_type,
    params.exercise_type,
    params.q
  );
  const up = binomialOptionPricing(
    params.S + stepS,
    params.K,
    params.T,
    params.r,
    params.sigma,
    params.n,
    params.option_type,
    params.exercise_type,
    params.q
  );
  const down = binomialOptionPricing(
    params.S - stepS,
    params.K,
    params.T,
    params.r,
    params.sigma,
    params.n,
    params.option_type,
    params.exercise_type,
    params.q
  );
  const delta = (up - down) / (2 * stepS);
  const gamma = (up - 2 * base + down) / (stepS ** 2);

  const upT = binomialOptionPricing(
    params.S,
    params.K,
    params.T + stepT,
    params.r,
    params.sigma,
    params.n,
    params.option_type,
    params.exercise_type,
    params.q
  );
  const downT = binomialOptionPricing(
    params.S,
    params.K,
    Math.max(params.T - stepT, 1e-8),
    params.r,
    params.sigma,
    params.n,
    params.option_type,
    params.exercise_type,
    params.q
  );
  const theta = (upT - downT) / (2 * stepT);

  return { price: base, delta, gamma, theta };
}

function drawConvergence(trail) {
  const canvas = byId("conv-chart");
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);

  if (!trail.length) return;
  const prices = trail.map((t) => t.price);
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  const padding = 20;
  const span = max - min || 1;

  ctx.strokeStyle = "rgba(109, 214, 199, 0.6)";
  ctx.lineWidth = 2;
  ctx.beginPath();
  trail.forEach((point, idx) => {
    const x = padding + (idx / (trail.length - 1 || 1)) * (width - padding * 2);
    const y = height - padding - ((point.price - min) / span) * (height - padding * 2);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.fillStyle = "rgba(244, 201, 93, 0.8)";
  const last = trail[trail.length - 1];
  const lastX = padding + ((trail.length - 1) / (trail.length - 1 || 1)) * (width - padding * 2);
  const lastY = height - padding - ((last.price - min) / span) * (height - padding * 2);
  ctx.beginPath();
  ctx.arc(lastX, lastY, 4, 0, Math.PI * 2);
  ctx.fill();
}

function formatNum(value, digits = 4) {
  if (!Number.isFinite(value)) return "-";
  return value.toFixed(digits);
}

function setError(message) {
  byId("error").textContent = message || "";
}

function run() {
  try {
    setError("");
    const params = readInputs();
    validateInputs(params);
    const price = binomialOptionPricing(
      params.S,
      params.K,
      params.T,
      params.r,
      params.sigma,
      params.n,
      params.option_type,
      params.exercise_type,
      params.q
    );
    const greek = greeks(params);
    const conv = priceWithConvergence(params);

    byId("price").textContent = formatNum(price);
    byId("delta").textContent = formatNum(greek.delta);
    byId("gamma").textContent = formatNum(greek.gamma, 6);
    byId("theta").textContent = formatNum(greek.theta);
    byId("conv").textContent = `${formatNum(conv.price)} @ n=${conv.n}`;
    drawConvergence(conv.trail);

    if (params.target_price !== null && Number.isFinite(params.target_price)) {
      const iv = impliedVolatility(params.target_price, params);
      byId("iv").textContent = formatNum(iv);
    } else {
      byId("iv").textContent = "-";
    }
  } catch (err) {
    setError(err.message || String(err));
  }
}

function resetDefaults() {
  byId("S").value = 100;
  byId("K").value = 100;
  byId("T").value = 1;
  byId("r").value = 0.05;
  byId("sigma").value = 0.2;
  byId("q").value = 0.02;
  byId("n").value = 200;
  byId("option_type").value = "call";
  byId("exercise_type").value = "european";
  byId("target_price").value = "";
  run();
}

byId("run").addEventListener("click", run);
byId("reset").addEventListener("click", resetDefaults);
byId("pricing-form").addEventListener("input", () => {
  window.clearTimeout(window._runTimer);
  window._runTimer = window.setTimeout(run, 200);
});

run();
