import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import "./Architecture.css";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  themeVariables: {
    primaryColor: "#646cff",
    primaryTextColor: "#fff",
    primaryBorderColor: "#444",
    lineColor: "#888",
    secondaryColor: "#1a1a2e",
    tertiaryColor: "#16213e",
    background: "#1a1a2e",
    mainBkg: "#1a1a2e",
    nodeBorder: "#444",
    clusterBkg: "#16213e",
    clusterBorder: "#333",
    titleColor: "#fff",
    edgeLabelBackground: "#1a1a2e",
  },
});

const CONTEXT_DIAGRAM = `C4Context
  title PAT — System Context Diagram

  Person(user, "Investor / Trader", "Manages portfolios, analyzes signals, trades options")

  System(pat, "PAT", "Portfolio tracking, signal generation, options analysis, paper trading")

  System_Ext(yahoo, "Yahoo Finance", "Market data, option chains")
  System_Ext(browser, "Web Browser", "React SPA")
  System_Ext(csv, "CSV Files", "Brokerage exports")

  Rel(user, browser, "Interacts via")
  Rel(browser, pat, "REST API", "HTTP/JSON")
  Rel(pat, yahoo, "Prices, OHLCV, chains", "yfinance")
  Rel(csv, pat, "Upload", "multipart")`;

const ARCHITECTURE_DIAGRAM = `graph TB
  subgraph Frontend ["Frontend — React + TypeScript + Recharts"]
    direction TB
    APP["App.tsx — Router & Nav"]
    APP --> DASH["Dashboard\\nSummary, P&L, Allocation"]
    APP --> ANAL["Analytics\\nPrice & Volume Charts, Risk Metrics"]
    APP --> SIG["Signals\\nComposite Score, Risk Context"]
    APP --> OPT["Options & LEAPS\\nIV, Skew, Term Structure, Greeks"]
    APP --> OPTIM["Optimize\\nEfficient Frontier, Weights"]
    APP --> ALERT["Alerts\\nCreate, Check, Manage"]
    APP --> PAPER["Paper Trading\\nOpen/Close Trades, P&L"]
    APP --> IMP["Import\\nCSV Upload"]
    AXIOS["Axios Client — baseURL: /api"]
  end

  subgraph Backend ["Backend — FastAPI + SQLAlchemy Async"]
    direction TB

    subgraph Routers ["API Routers"]
      R_PORT["/api/portfolio\\nAsset & Position CRUD"]
      R_ANAL["/api/analyze\\nSummary, Performance, Optimize"]
      R_SIG["/api/signals\\nComposite Scan"]
      R_OPT["/api/options\\nOverview, LEAPS"]
      R_ALERT["/api/alerts\\nCRUD + Check"]
      R_PAPER["/api/paper\\nTrades, Summary"]
      R_IMP["/api/portfolio/import\\nCSV Import"]
    end

    subgraph Analyzer ["Analyzer Module"]
      METRICS["metrics.py\\nSharpe, CAGR, Drawdown"]
      GREEKS["greeks.py\\nBlack-Scholes, Greeks, IV"]
      OPT_ANAL["options.py\\nIV Rank, Skew, Term Structure"]
      LEAPS["leaps.py\\nTheta Efficiency, Roll Timing"]
      OPTIMIZER["optimizer.py\\nMonte Carlo Frontier, Risk Parity"]
    end

    subgraph Signals ["Signal Engine"]
      TECH["technical.py\\nSMA, EMA, RSI, MACD, BB, ATR, OBV"]
      SCORE["scoring.py\\n7 Evaluators → [-1, +1]"]
      COMP["composite.py\\nWeighted Aggregate"]
      RISK["risk.py\\nATR Stop, Kelly, Position Sizing"]
    end

    subgraph Tracker ["Tracker Module"]
      MDATA["market_data.py\\nPrices, OHLCV, Option Chains"]
      CSV["csv_import.py\\nParse, Alias, Validate"]
    end

    subgraph DataLayer ["Data Layer"]
      DB[("SQLite — pat.db")]
      MODELS["Models\\nAsset, Position, Transaction\\nAlert, PaperTrade, PaperAccount"]
    end
  end

  subgraph External ["External"]
    YAHOO["Yahoo Finance\\n(yfinance)"]
  end

  AXIOS -->|"HTTP/JSON"| Routers
  R_PORT --> MODELS
  R_ANAL --> METRICS
  R_ANAL --> MDATA
  R_ANAL --> OPTIMIZER
  R_SIG --> COMP
  R_OPT --> GREEKS
  R_OPT --> OPT_ANAL
  R_OPT --> LEAPS
  R_OPT --> MDATA
  R_ALERT --> MODELS
  R_ALERT --> MDATA
  R_PAPER --> MODELS
  R_IMP --> CSV
  R_IMP --> MODELS
  TECH --> SCORE
  SCORE --> COMP
  COMP --> RISK
  MODELS --> DB
  MDATA -->|"asyncio.to_thread"| YAHOO`;

const DATA_FLOW_DIAGRAM = `graph LR
  subgraph Ingest ["1. Ingest"]
    CSV_FILE["CSV Upload"] --> PARSER["csv_import.py"]
    MANUAL["Manual Entry"] --> CRUD["Portfolio CRUD"]
    YAHOO["Yahoo Finance"] --> MDATA["market_data.py"]
  end

  subgraph Store ["2. Store"]
    PARSER --> DB[("SQLite")]
    CRUD --> DB
  end

  subgraph Compute ["3. Compute"]
    DB --> SUMMARY["Portfolio Summary\\n+ Live Prices"]
    MDATA --> INDICATORS["Technical Indicators"]
    INDICATORS --> SCORING["Signal Scoring"]
    SCORING --> COMPOSITE["Composite Signal"]
    COMPOSITE --> RISK_CTX["Risk Context"]
    MDATA --> IV_CALC["IV / Greeks"]
    MDATA --> FRONTIER["Efficient Frontier"]
    DB --> ALERT_CHK["Alert Check"]
    MDATA --> ALERT_CHK
  end

  subgraph Present ["4. Present"]
    SUMMARY --> DASH["Dashboard"]
    RISK_CTX --> SIG_PAGE["Signals Page"]
    IV_CALC --> OPT_PAGE["Options Page"]
    FRONTIER --> OPT_PGPG["Optimize Page"]
    ALERT_CHK --> ALERT_PG["Alerts Page"]
  end`;

const DB_DIAGRAM = `erDiagram
  Asset ||--o{ Position : has
  Position ||--o{ Transaction : records
  Asset {
    int id PK
    string symbol
    string name
    enum asset_type
    float strike
    date expiration
    string option_type
  }
  Position {
    int id PK
    int asset_id FK
    float quantity
    float avg_cost
    datetime opened_at
  }
  Transaction {
    int id PK
    int position_id FK
    enum transaction_type
    float quantity
    float price
    datetime timestamp
  }
  Alert {
    int id PK
    string symbol
    enum alert_type
    float threshold
    string message
    bool is_active
    bool is_triggered
    datetime triggered_at
  }
  PaperAccount {
    int id PK
    string name
    float initial_cash
    float current_cash
  }
  PaperTrade {
    int id PK
    string symbol
    string direction
    float quantity
    float entry_price
    float exit_price
    float pnl
    enum status
  }`;

const DIAGRAMS = [
  { id: "context", label: "Context", chart: CONTEXT_DIAGRAM },
  { id: "architecture", label: "Architecture", chart: ARCHITECTURE_DIAGRAM },
  { id: "dataflow", label: "Data Flow", chart: DATA_FLOW_DIAGRAM },
  { id: "database", label: "Database", chart: DB_DIAGRAM },
];

function MermaidChart({ chart, id }: { chart: string; id: string }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const render = async () => {
      if (!containerRef.current) return;
      containerRef.current.innerHTML = "";
      try {
        const { svg } = await mermaid.render(`mermaid-${id}-${Date.now()}`, chart);
        containerRef.current.innerHTML = svg;
      } catch {
        containerRef.current.innerHTML = `<pre class="mermaid-fallback">${chart}</pre>`;
      }
    };
    render();
  }, [chart, id]);

  return <div ref={containerRef} className="mermaid-container" />;
}

export default function Architecture() {
  const [tab, setTab] = useState("context");
  const current = DIAGRAMS.find((d) => d.id === tab)!;

  return (
    <div>
      <h1>Architecture</h1>
      <div className="arch-tabs">
        {DIAGRAMS.map((d) => (
          <button
            key={d.id}
            className={`arch-tab ${tab === d.id ? "active" : ""}`}
            onClick={() => setTab(d.id)}
          >
            {d.label}
          </button>
        ))}
      </div>
      <div className="arch-chart">
        <MermaidChart chart={current.chart} id={current.id} />
      </div>
    </div>
  );
}
