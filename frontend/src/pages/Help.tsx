import "./Help.css";

export default function Help() {
  return (
    <div className="help-page">
      <h1>Reference Guide</h1>

      {/* Technical Indicators */}
      <section className="help-section">
        <h2>Technical Indicators</h2>
        <p className="help-desc">
          Computed from OHLCV data in <code>signals/technical.py</code>. These
          feed into the signal scoring engine.
        </p>

        <h3>Moving Averages</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">SMA</td><td>Simple Moving Average — equal-weighted mean over a rolling window</td><td>20 / 50 periods</td></tr>
            <tr><td className="mono">EMA</td><td>Exponential Moving Average — weights recent prices more heavily</td><td>20 / 50 / 200 periods</td></tr>
          </tbody>
        </table>

        <h3>Momentum</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">RSI</td><td>Relative Strength Index — ratio of average gains to losses, scaled 0-100. Below 30 = oversold, above 70 = overbought</td><td>14 periods</td></tr>
            <tr><td className="mono">MACD</td><td>Moving Average Convergence/Divergence — difference between fast and slow EMA, with a signal line and histogram</td><td>12 / 26 / 9</td></tr>
            <tr><td className="mono">ROC</td><td>Rate of Change — percentage price change over N periods</td><td>10 periods</td></tr>
          </tbody>
        </table>

        <h3>Volatility</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Bollinger Bands</td><td>Upper and lower bands at N standard deviations from SMA. Measures price volatility envelope</td><td>20-period, 2 std</td></tr>
            <tr><td className="mono">%B</td><td>Where price sits within Bollinger Bands (0 = lower band, 1 = upper band)</td><td>20-period, 2 std</td></tr>
            <tr><td className="mono">ATR</td><td>Average True Range — average of true ranges (max of high-low, high-prev close, low-prev close)</td><td>14 periods</td></tr>
          </tbody>
        </table>

        <h3>Volume</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">VWAP</td><td>Volume-Weighted Average Price — cumulative typical price weighted by volume</td><td>—</td></tr>
            <tr><td className="mono">OBV</td><td>On-Balance Volume — cumulative volume added on up days, subtracted on down days</td><td>—</td></tr>
            <tr><td className="mono">A/D Line</td><td>Accumulation/Distribution Line — cumulative money flow volume based on where close sits within the high-low range</td><td>—</td></tr>
            <tr><td className="mono">CMF</td><td>Chaikin Money Flow — rolling sum of money flow volume divided by rolling sum of volume, bounded [-1, +1]</td><td>20 periods</td></tr>
          </tbody>
        </table>

        <h3>Trend Strength</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">ADX</td><td>Average Directional Index — measures trend strength (not direction) on a 0-100 scale. &gt;25 = trending, &lt;20 = ranging. Uses +DI/-DI for direction</td><td>14 periods</td></tr>
            <tr><td className="mono">Stochastic</td><td>Stochastic Oscillator — %K measures where close sits relative to the high-low range over N periods. %D is SMA of %K. &lt;20 = oversold, &gt;80 = overbought</td><td>14 / 3 periods</td></tr>
          </tbody>
        </table>

        <h3>Sentiment</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Put/Call Ratio</td><td>Total put volume divided by total call volume from the nearest-expiry options chain. Used as a contrarian sentiment indicator</td><td>Nearest expiry</td></tr>
          </tbody>
        </table>
      </section>

      {/* Signal Engine */}
      <section className="help-section">
        <h2>Signal Scoring Engine</h2>
        <p className="help-desc">
          Twelve evaluators each produce a normalized score from <strong>-1</strong> (strong sell)
          to <strong>+1</strong> (strong buy). Scores are combined with weights into a composite signal.
        </p>
        <table>
          <thead>
            <tr><th>Signal</th><th>Weight</th><th>Logic</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">MA Crossover</td><td className="center">10%</td>
              <td>SMA 20 vs SMA 50 — bullish when fast &gt; slow, scaled by gap magnitude. A 2% gap = score of +1</td>
            </tr>
            <tr>
              <td className="mono">RSI</td><td className="center">10%</td>
              <td>Oversold (RSI &lt; 30) generates buy signal, overbought (RSI &gt; 70) generates sell. Linear scaling within zones</td>
            </tr>
            <tr>
              <td className="mono">MACD</td><td className="center">10%</td>
              <td>MACD histogram magnitude normalized by recent price standard deviation</td>
            </tr>
            <tr>
              <td className="mono">Bollinger %B</td><td className="center">7%</td>
              <td>Near lower band (0) = buy, near upper band (1) = sell, mid (0.5) = neutral</td>
            </tr>
            <tr>
              <td className="mono">Mean Reversion</td><td className="center">7%</td>
              <td>Z-score of price vs 20-period SMA. Z &gt; 2 = sell, Z &lt; -2 = buy</td>
            </tr>
            <tr>
              <td className="mono">Trend</td><td className="center">12%</td>
              <td>Multi-timeframe EMA alignment: EMA 20 &gt; 50 (+0.33), EMA 50 &gt; 200 (+0.33), price &gt; EMA 200 (+0.34). Reversed for bearish</td>
            </tr>
            <tr>
              <td className="mono">Volume Trend</td><td className="center">8%</td>
              <td>OBV trend confirms price direction. Signal fires when OBV deviation aligns with price vs SMA</td>
            </tr>
            <tr>
              <td className="mono">ADX</td><td className="center">10%</td>
              <td>ADX &gt; 25 with +DI &gt; -DI = bullish trend, -DI &gt; +DI = bearish. ADX &lt; 20 = no clear trend (neutral). Strength scaled by ADX magnitude</td>
            </tr>
            <tr>
              <td className="mono">Stochastic</td><td className="center">8%</td>
              <td>%K &lt; 20 = oversold (buy), %K &gt; 80 = overbought (sell). Bonus when %K crosses %D (momentum shift)</td>
            </tr>
            <tr>
              <td className="mono">A/D Line</td><td className="center">6%</td>
              <td>A/D line trend vs price trend — divergence signals reversal, confirmation signals trend continuation</td>
            </tr>
            <tr>
              <td className="mono">CMF</td><td className="center">7%</td>
              <td>Chaikin Money Flow &gt; 0 = buying pressure (bullish), &lt; 0 = selling pressure (bearish). Scaled by magnitude</td>
            </tr>
            <tr>
              <td className="mono">Put/Call Ratio</td><td className="center">5%</td>
              <td>Contrarian sentiment: ratio &gt; 1.2 = excessive fear (buy), ratio &lt; 0.5 = complacency (sell). Optional — weight redistributed if unavailable</td>
            </tr>
          </tbody>
        </table>

        <h3>Composite Output</h3>
        <div className="help-grid">
          <div className="help-card">
            <h4>Direction</h4>
            <ul>
              <li><span className="tag buy">BUY</span> Score &ge; +0.2</li>
              <li><span className="tag sell">SELL</span> Score &le; -0.2</li>
              <li><span className="tag hold">HOLD</span> Between -0.2 and +0.2</li>
            </ul>
          </div>
          <div className="help-card">
            <h4>Conviction</h4>
            <ul>
              <li><strong>High</strong> — |score| &ge; 0.6</li>
              <li><strong>Medium</strong> — |score| &ge; 0.3</li>
              <li><strong>Low</strong> — |score| &lt; 0.3</li>
            </ul>
          </div>
          <div className="help-card">
            <h4>Confidence (0-100)</h4>
            <p>Based on signal agreement: 70% weight on directional alignment among non-neutral signals, 30% weight on data quality (ratio of non-neutral to total signals).</p>
          </div>
        </div>
      </section>

      {/* Risk Management */}
      <section className="help-section">
        <h2>Risk Management</h2>
        <p className="help-desc">
          Risk context is computed alongside every signal scan to provide
          actionable position sizing and stop/target levels.
        </p>
        <table>
          <thead>
            <tr><th>Tool</th><th>Description</th><th>Parameters</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">ATR Stop-Loss</td>
              <td>Stop placed at N &times; ATR below entry price. Adapts to current volatility</td>
              <td>2&times; ATR multiplier</td>
            </tr>
            <tr>
              <td className="mono">Kelly Criterion</td>
              <td>Optimal fraction of portfolio to risk. Uses half-Kelly for safety</td>
              <td>Capped at 25% max</td>
            </tr>
            <tr>
              <td className="mono">Position Sizing</td>
              <td>Number of shares based on fixed risk % of portfolio value and ATR stop distance</td>
              <td>1-2% risk per trade</td>
            </tr>
            <tr>
              <td className="mono">Risk/Reward</td>
              <td>Ratio of potential profit (entry to target) vs potential loss (entry to stop)</td>
              <td>Target: 2:1 minimum</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* Analytics Metrics */}
      <section className="help-section">
        <h2>Analytics Metrics</h2>
        <p className="help-desc">
          Performance and risk metrics computed from historical price data on the Analytics page.
        </p>
        <table>
          <thead>
            <tr><th>Metric</th><th>Formula</th><th>Interpretation</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">Sharpe Ratio</td>
              <td>&radic;252 &times; mean(excess returns) / std(excess returns)</td>
              <td>&gt; 1.0 good, &gt; 2.0 very good, &lt; 0 losing money</td>
            </tr>
            <tr>
              <td className="mono">CAGR</td>
              <td>(end / start) ^ (252 / N) - 1</td>
              <td>Annualized compound growth rate. Comparable across time periods</td>
            </tr>
            <tr>
              <td className="mono">Max Drawdown</td>
              <td>Largest peak-to-trough decline in cumulative returns</td>
              <td>Worst-case loss from a peak. -20% means you'd have lost 20% at the worst point</td>
            </tr>
            <tr>
              <td className="mono">Volatility</td>
              <td>std(daily returns) &times; &radic;252</td>
              <td>Annualized price fluctuation. Higher = riskier. S&P 500 typically ~15-20%</td>
            </tr>
          </tbody>
        </table>
      </section>

      {/* Options & LEAPS */}
      <section className="help-section">
        <h2>Options Intelligence</h2>
        <p className="help-desc">
          Options analytics powered by Black-Scholes pricing and IV analysis.
        </p>

        <h3>Greeks</h3>
        <table>
          <thead>
            <tr><th>Greek</th><th>Measures</th><th>Key Insight</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Delta</td><td>Price sensitivity to $1 move in underlying</td><td>0.5 delta = option moves $0.50 per $1 stock move</td></tr>
            <tr><td className="mono">Gamma</td><td>Rate of change of delta</td><td>High gamma near ATM = delta changes rapidly</td></tr>
            <tr><td className="mono">Theta</td><td>Time decay per day</td><td>Negative for long options — loses value each day</td></tr>
            <tr><td className="mono">Vega</td><td>Sensitivity to 1% change in IV</td><td>Higher for longer-dated options (LEAPS)</td></tr>
            <tr><td className="mono">Rho</td><td>Sensitivity to 1% change in interest rates</td><td>More relevant for LEAPS due to longer duration</td></tr>
          </tbody>
        </table>

        <h3>IV Analysis</h3>
        <table>
          <thead>
            <tr><th>Metric</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">IV Rank</td><td>Where current IV sits relative to its 52-week range. 80% = IV is near the high end</td></tr>
            <tr><td className="mono">IV Percentile</td><td>% of days in the past year that IV was lower than today</td></tr>
            <tr><td className="mono">Volatility Skew</td><td>Ratio of put IV to call IV at same distance from ATM. Skew &gt; 1 = puts are more expensive</td></tr>
            <tr><td className="mono">Term Structure</td><td>ATM IV across expirations. Normal = upward slope. Inverted = near-term fear</td></tr>
          </tbody>
        </table>

        <h3>LEAPS Analysis</h3>
        <table>
          <thead>
            <tr><th>Metric</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Theta Efficiency</td><td>Daily theta decay relative to option price. Lower = less time decay drag</td></tr>
            <tr><td className="mono">Stock Replacement</td><td>Cost to control 100 shares via deep ITM LEAPS call vs buying stock outright</td></tr>
            <tr><td className="mono">Roll Timing</td><td><span className="tag hold">HOLD</span> DTE &gt; 180. <span className="tag monitor">MONITOR</span> DTE &lt; 180 &amp; extrinsic &lt; 15%. <span className="tag sell">ROLL NOW</span> DTE &lt; 90</td></tr>
          </tbody>
        </table>
      </section>

      {/* Portfolio Optimizer */}
      <section className="help-section">
        <h2>Portfolio Optimizer</h2>
        <p className="help-desc">
          Uses Monte Carlo simulation to find optimal portfolio allocations.
        </p>
        <table>
          <thead>
            <tr><th>Strategy</th><th>Objective</th><th>Method</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">Max Sharpe</td>
              <td>Best risk-adjusted return</td>
              <td>Portfolio with highest (return - risk_free) / volatility from 5,000 random allocations</td>
            </tr>
            <tr>
              <td className="mono">Min Variance</td>
              <td>Lowest possible risk</td>
              <td>Portfolio with smallest annualized volatility from simulated allocations</td>
            </tr>
            <tr>
              <td className="mono">Risk Parity</td>
              <td>Equal risk contribution</td>
              <td>Inverse-volatility weighting — higher vol assets get lower weight</td>
            </tr>
          </tbody>
        </table>
        <p className="help-note">
          The efficient frontier chart plots all simulated portfolios (volatility vs return).
          Points above and to the left are more efficient — better return for the same risk.
        </p>
      </section>

      {/* API Endpoints */}
      <section className="help-section">
        <h2>API Endpoints</h2>
        <table>
          <thead>
            <tr><th>Prefix</th><th>Endpoints</th><th>Purpose</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">/api/health</td><td>GET /</td><td>System health check</td></tr>
            <tr><td className="mono">/api/portfolio</td><td>GET/POST /assets, /positions, /transactions</td><td>Portfolio CRUD</td></tr>
            <tr><td className="mono">/api/portfolio/import</td><td>POST /</td><td>CSV file upload</td></tr>
            <tr><td className="mono">/api/analyze</td><td>GET /summary, /performance, /optimize</td><td>Analytics &amp; optimization</td></tr>
            <tr><td className="mono">/api/signals</td><td>GET /scan</td><td>Composite signal scan</td></tr>
            <tr><td className="mono">/api/options</td><td>GET /overview, /leaps</td><td>Options &amp; LEAPS analysis</td></tr>
            <tr><td className="mono">/api/alerts</td><td>GET, POST, DELETE /, POST /check</td><td>Alert management</td></tr>
            <tr><td className="mono">/api/paper</td><td>GET /summary, /trades; POST /trades, /trades/id/close</td><td>Paper trading</td></tr>
          </tbody>
        </table>
      </section>
    </div>
  );
}
