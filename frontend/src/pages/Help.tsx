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
            <tr><th>Indicator</th><th>Description</th><th>Default</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">SMA</td><td>Simple Moving Average — equal-weighted mean over a rolling window</td><td>20 / 50 periods</td><td className="plain-english">Like checking the average temperature over the last few weeks — smooths out daily spikes so you can see if things are generally warming up or cooling down</td></tr>
            <tr><td className="mono">EMA</td><td>Exponential Moving Average — weights recent prices more heavily</td><td>20 / 50 / 200 periods</td><td className="plain-english">Same idea as SMA, but pays more attention to what happened recently — reacts faster to sudden changes</td></tr>
          </tbody>
        </table>

        <h3>Momentum</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">RSI</td><td>Relative Strength Index — ratio of average gains to losses, scaled 0-100. Below 30 = oversold, above 70 = overbought</td><td>14 periods</td><td className="plain-english">Think of it as a "how tired is this rally?" meter. A stock that's gone up a lot without pausing (above 70) may be due for a rest; one that's been beaten down (below 30) might be ready to bounce</td></tr>
            <tr><td className="mono">MACD</td><td>Moving Average Convergence/Divergence — difference between fast and slow EMA, with a signal line and histogram</td><td>12 / 26 / 9</td><td className="plain-english">Shows whether the stock's short-term momentum is speeding up or slowing down relative to its longer trend — like noticing a runner starting to slow before they actually stop</td></tr>
            <tr><td className="mono">ROC</td><td>Rate of Change — percentage price change over N periods</td><td>10 periods</td><td className="plain-english">Simply asks "how much has the price changed compared to N days ago?" — a quick pulse check on momentum</td></tr>
          </tbody>
        </table>

        <h3>Volatility</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Bollinger Bands</td><td>Upper and lower bands at N standard deviations from SMA. Measures price volatility envelope</td><td>20-period, 2 std</td><td className="plain-english">Imagine a rubber band around the price — when it stretches wide, the market is volatile and uncertain; when it's narrow, a big move may be brewing</td></tr>
            <tr><td className="mono">%B</td><td>Where price sits within Bollinger Bands (0 = lower band, 1 = upper band)</td><td>20-period, 2 std</td><td className="plain-english">Tells you where the current price sits inside that rubber band. Near 0 means the price is at the low end (potential bargain); near 1 means it's at the high end (potentially stretched)</td></tr>
            <tr><td className="mono">ATR</td><td>Average True Range — average of true ranges (max of high-low, high-prev close, low-prev close)</td><td>14 periods</td><td className="plain-english">Measures how much a stock typically moves in a day. A stock with an ATR of $5 swings a lot more than one with an ATR of $0.50 — useful for setting realistic stop losses</td></tr>
          </tbody>
        </table>

        <h3>Volume</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">VWAP</td><td>Volume-Weighted Average Price — cumulative typical price weighted by volume</td><td>—</td><td className="plain-english">The "fair price" for the day based on where most trading volume occurred. Institutional traders often use it as a benchmark — buying below VWAP feels like getting a deal</td></tr>
            <tr><td className="mono">OBV</td><td>On-Balance Volume — cumulative volume added on up days, subtracted on down days</td><td>—</td><td className="plain-english">Tracks whether volume is flowing into the stock (bullish) or out of it (bearish). If the price is rising but OBV is falling, the rally may lack real buying conviction</td></tr>
            <tr><td className="mono">A/D Line</td><td>Accumulation/Distribution Line — cumulative money flow volume based on where close sits within the high-low range</td><td>—</td><td className="plain-english">Similar to OBV but more nuanced — shows whether money is being quietly accumulated (bullish) or distributed (bearish), even if the price hasn't moved much yet</td></tr>
            <tr><td className="mono">CMF</td><td>Chaikin Money Flow — rolling sum of money flow volume divided by rolling sum of volume, bounded [-1, +1]</td><td>20 periods</td><td className="plain-english">A snapshot of buying vs selling pressure over the last 20 days. Positive = more buyers than sellers; negative = more sellers. Think of it as a tug-of-war score</td></tr>
          </tbody>
        </table>

        <h3>Trend Strength</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">ADX</td><td>Average Directional Index — measures trend strength (not direction) on a 0-100 scale. &gt;25 = trending, &lt;20 = ranging. Uses +DI/-DI for direction</td><td>14 periods</td><td className="plain-english">Answers "is this stock actually trending, or just going sideways?" It doesn't tell you which direction — just whether the move is strong. Above 25 means there's a real trend worth paying attention to</td></tr>
            <tr><td className="mono">Stochastic</td><td>Stochastic Oscillator — %K measures where close sits relative to the high-low range over N periods. %D is SMA of %K. &lt;20 = oversold, &gt;80 = overbought</td><td>14 / 3 periods</td><td className="plain-english">Like RSI but focused on where today's close sits relative to recent highs and lows. Below 20 = near the bottom of its recent range (potential bounce); above 80 = near the top (potential pullback)</td></tr>
          </tbody>
        </table>

        <h3>Sentiment</h3>
        <table>
          <thead>
            <tr><th>Indicator</th><th>Description</th><th>Default</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Put/Call Ratio</td><td>Total put volume divided by total call volume from the nearest-expiry options chain. Used as a contrarian sentiment indicator</td><td>Nearest expiry</td><td className="plain-english">A crowd psychology gauge. When everyone is buying puts (ratio &gt; 1.2), fear is high — contrarians see this as a buy signal. When few are buying puts (ratio &lt; 0.5), complacency is high — contrarians get cautious</td></tr>
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
            <tr><th>Signal</th><th>Weight</th><th>Logic</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">MA Crossover</td><td className="center">10%</td>
              <td>SMA 20 vs SMA 50 — bullish when fast &gt; slow, scaled by gap magnitude. A 2% gap = score of +1</td>
              <td className="plain-english">Are recent prices pulling ahead of (or falling behind) the longer-term trend? A widening gap means momentum is building</td>
            </tr>
            <tr>
              <td className="mono">RSI</td><td className="center">10%</td>
              <td>Oversold (RSI &lt; 30) generates buy signal, overbought (RSI &gt; 70) generates sell. Linear scaling within zones</td>
              <td className="plain-english">Has the stock been pushed too far in one direction without a breather?</td>
            </tr>
            <tr>
              <td className="mono">MACD</td><td className="center">10%</td>
              <td>MACD histogram magnitude normalized by recent price standard deviation</td>
              <td className="plain-english">Is the stock's momentum accelerating or fading?</td>
            </tr>
            <tr>
              <td className="mono">Bollinger %B</td><td className="center">7%</td>
              <td>Near lower band (0) = buy, near upper band (1) = sell, mid (0.5) = neutral</td>
              <td className="plain-english">Is the price near the top or bottom of its normal trading range?</td>
            </tr>
            <tr>
              <td className="mono">Mean Reversion</td><td className="center">7%</td>
              <td>Z-score of price vs 20-period SMA. Z &gt; 2 = sell, Z &lt; -2 = buy</td>
              <td className="plain-english">Has the price wandered unusually far from its average? Extreme moves tend to snap back</td>
            </tr>
            <tr>
              <td className="mono">Trend</td><td className="center">12%</td>
              <td>Multi-timeframe EMA alignment: EMA 20 &gt; 50 (+0.33), EMA 50 &gt; 200 (+0.33), price &gt; EMA 200 (+0.34). Reversed for bearish</td>
              <td className="plain-english">Are the short-, medium-, and long-term trends all pointing the same way? Alignment = stronger conviction</td>
            </tr>
            <tr>
              <td className="mono">Volume Trend</td><td className="center">8%</td>
              <td>OBV trend confirms price direction. Signal fires when OBV deviation aligns with price vs SMA</td>
              <td className="plain-english">Is trading volume confirming what the price is doing, or hinting at a divergence?</td>
            </tr>
            <tr>
              <td className="mono">ADX</td><td className="center">10%</td>
              <td>ADX &gt; 25 with +DI &gt; -DI = bullish trend, -DI &gt; +DI = bearish. ADX &lt; 20 = no clear trend (neutral). Strength scaled by ADX magnitude</td>
              <td className="plain-english">Is this a genuine trending market or just random noise?</td>
            </tr>
            <tr>
              <td className="mono">Stochastic</td><td className="center">8%</td>
              <td>%K &lt; 20 = oversold (buy), %K &gt; 80 = overbought (sell). Bonus when %K crosses %D (momentum shift)</td>
              <td className="plain-english">Is the stock near the top or bottom of its recent price range, and is momentum shifting?</td>
            </tr>
            <tr>
              <td className="mono">A/D Line</td><td className="center">6%</td>
              <td>A/D line trend vs price trend — divergence signals reversal, confirmation signals trend continuation</td>
              <td className="plain-english">Are institutional investors quietly accumulating shares (bullish) or distributing them (bearish)?</td>
            </tr>
            <tr>
              <td className="mono">CMF</td><td className="center">7%</td>
              <td>Chaikin Money Flow &gt; 0 = buying pressure (bullish), &lt; 0 = selling pressure (bearish). Scaled by magnitude</td>
              <td className="plain-english">Over the past month, has buying pressure or selling pressure dominated?</td>
            </tr>
            <tr>
              <td className="mono">Put/Call Ratio</td><td className="center">5%</td>
              <td>Contrarian sentiment: ratio &gt; 1.2 = excessive fear (buy), ratio &lt; 0.5 = complacency (sell). Optional — weight redistributed if unavailable</td>
              <td className="plain-english">Is the options market showing unusual fear or complacency?</td>
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

      {/* Elliott Wave Analysis */}
      <section className="help-section">
        <h2>Elliott Wave Analysis</h2>
        <p className="help-desc">
          Standalone wave structure analysis using zigzag pivot detection and Fibonacci ratio
          validation. This is separate from the composite signal engine — Elliott Wave is
          inherently more subjective and strategic than quantitative indicators.
        </p>

        <h3>Wave Detection Method</h3>
        <table>
          <thead>
            <tr><th>Step</th><th>Description</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">Zigzag Pivots</td>
              <td>ATR-filtered swing detection — walks through price data and marks reversals that exceed 1.5&times; median ATR. Filters out noise while preserving significant swings</td>
              <td className="plain-english">Finds the major turning points in price by ignoring small day-to-day wiggles — like stepping back from a chart to see the big swings</td>
            </tr>
            <tr>
              <td className="mono">Pattern Matching</td>
              <td>Matches recent pivots against impulse (5-wave) and corrective (A-B-C) templates. Validates that Wave 3 is not the shortest and Wave 4 does not overlap Wave 1</td>
              <td className="plain-english">Checks if those turning points form a recognizable wave pattern — either a 5-wave trending move or a 3-wave pullback</td>
            </tr>
            <tr>
              <td className="mono">Fibonacci Validation</td>
              <td>Scores how well wave ratios match Fibonacci levels — confidence is based on adherence to expected retracement and extension ratios</td>
              <td className="plain-english">Measures whether the waves relate to each other in the specific proportions that Elliott Wave theory predicts — higher match = higher confidence</td>
            </tr>
          </tbody>
        </table>

        <h3>Fibonacci Ratios</h3>
        <table>
          <thead>
            <tr><th>Wave</th><th>Expected Ratio</th><th>Description</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Wave 2</td><td>0.382 &ndash; 0.618</td><td>Retracement of Wave 1</td><td className="plain-english">The first pullback after an initial move — should give back roughly a third to two-thirds of Wave 1 before the trend resumes</td></tr>
            <tr><td className="mono">Wave 3</td><td>1.272 &ndash; 2.618</td><td>Extension of Wave 1 (typically the strongest wave)</td><td className="plain-english">Usually the strongest and longest wave — if it's not at least 1.27&times; Wave 1, the pattern may be weak</td></tr>
            <tr><td className="mono">Wave 4</td><td>0.236 &ndash; 0.500</td><td>Retracement of Wave 3</td><td className="plain-english">A shallower pullback than Wave 2 — gives back less than half of Wave 3's gains, showing the trend still has legs</td></tr>
            <tr><td className="mono">Wave 5</td><td>0.618 &ndash; 1.618</td><td>Extension of Wave 1</td><td className="plain-english">The final push — typically similar in size to Wave 1, after which the trend is likely to reverse</td></tr>
          </tbody>
        </table>

        <h3>Independent Signals</h3>
        <p className="help-desc">
          The Elliott Wave page displays three independent signals — not part of the composite engine:
        </p>
        <table>
          <thead>
            <tr><th>Signal</th><th>Logic</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">Elliott Wave</td>
              <td>Wave structure signal: bullish during impulse waves 1/3 (up to +1.0), weakening during wave 5, bearish during corrective patterns. Scaled by confidence</td>
              <td className="plain-english">What does the wave structure suggest? Bullish in early/middle waves, weakening near the end</td>
            </tr>
            <tr>
              <td className="mono">RSI</td>
              <td>Same RSI scorer as the composite engine — oversold (&lt;30) = buy, overbought (&gt;70) = sell</td>
              <td className="plain-english">Is the stock overbought or oversold right now, regardless of wave position?</td>
            </tr>
            <tr>
              <td className="mono">MACD</td>
              <td>Same MACD scorer as the composite engine — histogram magnitude normalized by price standard deviation</td>
              <td className="plain-english">Is short-term momentum supporting or contradicting the wave thesis?</td>
            </tr>
          </tbody>
        </table>
        <p className="help-note">
          Direction is derived from the simple average of all three scores using the same thresholds as the composite engine (&ge;0.2 buy, &le;-0.2 sell).
        </p>
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
            <tr><th>Tool</th><th>Description</th><th>Parameters</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">ATR Stop-Loss</td>
              <td>Stop placed at N &times; ATR below entry price. Adapts to current volatility</td>
              <td>2&times; ATR multiplier</td>
              <td className="plain-english">Sets your "bail out" price based on how much the stock normally moves — avoids getting stopped out by normal volatility</td>
            </tr>
            <tr>
              <td className="mono">Kelly Criterion</td>
              <td>Optimal fraction of portfolio to risk. Uses half-Kelly for safety</td>
              <td>Capped at 25% max</td>
              <td className="plain-english">A mathematical formula for "how much of your money should you bet?" — uses half the calculated amount for extra safety</td>
            </tr>
            <tr>
              <td className="mono">Position Sizing</td>
              <td>Number of shares based on fixed risk % of portfolio value and ATR stop distance</td>
              <td>1-2% risk per trade</td>
              <td className="plain-english">Calculates how many shares to buy so that if you hit your stop loss, you only lose 1-2% of your portfolio — not your shirt</td>
            </tr>
            <tr>
              <td className="mono">Risk/Reward</td>
              <td>Ratio of potential profit (entry to target) vs potential loss (entry to stop)</td>
              <td>Target: 2:1 minimum</td>
              <td className="plain-english">Before entering a trade, asks "is the potential upside at least 2&times; the potential downside?" If not, the trade may not be worth the risk</td>
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
            <tr><th>Metric</th><th>Formula</th><th>Interpretation</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">Sharpe Ratio</td>
              <td>&radic;252 &times; mean(excess returns) / std(excess returns)</td>
              <td>&gt; 1.0 good, &gt; 2.0 very good, &lt; 0 losing money</td>
              <td className="plain-english">"How much return am I getting for each unit of risk?" Above 1.0 means you're being reasonably compensated; below 0 means you're losing money on a risk-adjusted basis</td>
            </tr>
            <tr>
              <td className="mono">CAGR</td>
              <td>(end / start) ^ (252 / N) - 1</td>
              <td>Annualized compound growth rate. Comparable across time periods</td>
              <td className="plain-english">If your investment grew at a steady rate each year, what would that rate be? Lets you compare a 6-month trade to a 3-year hold on equal footing</td>
            </tr>
            <tr>
              <td className="mono">Max Drawdown</td>
              <td>Largest peak-to-trough decline in cumulative returns</td>
              <td>Worst-case loss from a peak. -20% means you'd have lost 20% at the worst point</td>
              <td className="plain-english">The worst peak-to-valley drop your investment experienced — answers "how much pain would I have endured if I bought at the worst time?"</td>
            </tr>
            <tr>
              <td className="mono">Volatility</td>
              <td>std(daily returns) &times; &radic;252</td>
              <td>Annualized price fluctuation. Higher = riskier. S&P 500 typically ~15-20%</td>
              <td className="plain-english">How much the price bounces around day-to-day, annualized. Higher volatility means more stomach-churning swings, even if the long-term direction is up</td>
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
            <tr><th>Greek</th><th>Measures</th><th>Key Insight</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Delta</td><td>Price sensitivity to $1 move in underlying</td><td>0.5 delta = option moves $0.50 per $1 stock move</td><td className="plain-english">If the stock moves $1, how much does your option move? A 0.50 delta means roughly 50 cents — also approximates the chance the option expires in the money</td></tr>
            <tr><td className="mono">Gamma</td><td>Rate of change of delta</td><td>High gamma near ATM = delta changes rapidly</td><td className="plain-english">How quickly does delta change? High gamma means your option's behavior can shift dramatically with small stock moves — exciting but risky</td></tr>
            <tr><td className="mono">Theta</td><td>Time decay per day</td><td>Negative for long options — loses value each day</td><td className="plain-english">Your option loses this much value every day just from time passing. It's the "cost of waiting" — accelerates as expiration approaches</td></tr>
            <tr><td className="mono">Vega</td><td>Sensitivity to 1% change in IV</td><td>Higher for longer-dated options (LEAPS)</td><td className="plain-english">If market uncertainty (IV) jumps by 1%, your option gains this much. LEAPS have higher vega, so they benefit more from volatility spikes</td></tr>
            <tr><td className="mono">Rho</td><td>Sensitivity to 1% change in interest rates</td><td>More relevant for LEAPS due to longer duration</td><td className="plain-english">How much an interest rate change affects your option. Usually small, but matters for LEAPS held over months or years</td></tr>
          </tbody>
        </table>

        <h3>IV Analysis</h3>
        <table>
          <thead>
            <tr><th>Metric</th><th>Description</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">IV Rank</td><td>Where current IV sits relative to its 52-week range. 80% = IV is near the high end</td><td className="plain-english">Is implied volatility high or low compared to the past year? High IV Rank = options are expensive (good for selling), low = cheap (good for buying)</td></tr>
            <tr><td className="mono">IV Percentile</td><td>% of days in the past year that IV was lower than today</td><td className="plain-english">What percentage of days in the past year had lower IV than today? 90th percentile means IV is higher than on 90% of recent days</td></tr>
            <tr><td className="mono">Volatility Skew</td><td>Ratio of put IV to call IV at same distance from ATM. Skew &gt; 1 = puts are more expensive</td><td className="plain-english">Are put options more expensive than calls? Often yes, because investors pay a premium for downside protection — a steep skew can signal market fear</td></tr>
            <tr><td className="mono">Term Structure</td><td>ATM IV across expirations. Normal = upward slope. Inverted = near-term fear</td><td className="plain-english">How does IV change across different expiration dates? If near-term IV is higher than long-term, the market expects turbulence soon</td></tr>
          </tbody>
        </table>

        <h3>LEAPS Analysis</h3>
        <table>
          <thead>
            <tr><th>Metric</th><th>Description</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr><td className="mono">Theta Efficiency</td><td>Daily theta decay relative to option price. Lower = less time decay drag</td><td className="plain-english">How much of your option's value melts away each day? Lower is better — you want time decay to be a small fraction of the option's price</td></tr>
            <tr><td className="mono">Stock Replacement</td><td>Cost to control 100 shares via deep ITM LEAPS call vs buying stock outright</td><td className="plain-english">How much cheaper is it to control 100 shares using a deep ITM LEAPS call instead of buying the stock? Shows the leverage advantage</td></tr>
            <tr><td className="mono">Roll Timing</td><td><span className="tag hold">HOLD</span> DTE &gt; 180. <span className="tag monitor">MONITOR</span> DTE &lt; 180 &amp; extrinsic &lt; 15%. <span className="tag sell">ROLL NOW</span> DTE &lt; 90</td><td className="plain-english">Should you roll your LEAPS to a later expiration? Tells you when time decay is starting to eat too much value and it's time to extend</td></tr>
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
            <tr><th>Strategy</th><th>Objective</th><th>Method</th><th>In Plain English</th></tr>
          </thead>
          <tbody>
            <tr>
              <td className="mono">Max Sharpe</td>
              <td>Best risk-adjusted return</td>
              <td>Portfolio with highest (return - risk_free) / volatility from 5,000 random allocations</td>
              <td className="plain-english">Finds the mix of stocks that historically delivered the best return for the amount of risk taken — the "sweet spot" portfolio</td>
            </tr>
            <tr>
              <td className="mono">Min Variance</td>
              <td>Lowest possible risk</td>
              <td>Portfolio with smallest annualized volatility from simulated allocations</td>
              <td className="plain-english">Finds the mix with the smallest price swings — for investors who prioritize sleeping well at night over maximum returns</td>
            </tr>
            <tr>
              <td className="mono">Risk Parity</td>
              <td>Equal risk contribution</td>
              <td>Inverse-volatility weighting — higher vol assets get lower weight</td>
              <td className="plain-english">Gives riskier stocks a smaller slice and calmer stocks a bigger slice, so each holding contributes roughly equal risk — a balanced approach</td>
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
            <tr><td className="mono">/api/elliott-wave</td><td>GET /analyze</td><td>Elliott Wave analysis</td></tr>
            <tr><td className="mono">/api/options</td><td>GET /overview, /leaps</td><td>Options &amp; LEAPS analysis</td></tr>
            <tr><td className="mono">/api/alerts</td><td>GET, POST, DELETE /, POST /check</td><td>Alert management</td></tr>
            <tr><td className="mono">/api/paper</td><td>GET /summary, /trades; POST /trades, /trades/id/close</td><td>Paper trading</td></tr>
          </tbody>
        </table>
      </section>
    </div>
  );
}
