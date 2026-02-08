import { useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import "./Architecture.css";

mermaid.initialize({
  startOnLoad: false,
  theme: "dark",
  fontSize: 14,
  flowchart: {
    nodeSpacing: 30,
    rankSpacing: 50,
    padding: 15,
    htmlLabels: true,
  },
  er: {
    fontSize: 14,
  },
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
    edgeLabelBackground: "#2a2a3e",
  },
});

const CONTEXT_DIAGRAM = `graph LR
  classDef person fill:#08427b,stroke:#052e56,color:#fff
  classDef system fill:#1168bd,stroke:#0b4884,color:#fff
  classDef external fill:#999,stroke:#666,color:#fff

  USER["👤 Investor / Trader\nManages portfolios,\nanalyzes signals"]:::person
  BROWSER["🌐 Web Browser\nReact SPA"]:::external
  PAT["🔷 PAT\nPortfolio tracking,\nsignal generation,\noptions analysis"]:::system
  YAHOO["📈 Yahoo Finance\nMarket data,\noption chains"]:::external
  CSV["📄 CSV Files\nBrokerage exports"]:::external

  USER -->|"Interacts via"| BROWSER
  BROWSER -->|"REST API\nHTTP/JSON"| PAT
  PAT -->|"Prices, OHLCV,\nchains via yfinance"| YAHOO
  CSV -->|"Upload\nmultipart"| PAT`;

const ARCHITECTURE_DIAGRAM = `graph TB
  classDef frontend fill:#264653,stroke:#2a9d8f,color:#fff
  classDef api fill:#1a3a5c,stroke:#4a9eff,color:#fff
  classDef module fill:#2d1b4e,stroke:#8b5cf6,color:#fff
  classDef storage fill:#1a1a2e,stroke:#646cff,color:#fff
  classDef external fill:#4a3728,stroke:#e67e22,color:#fff

  subgraph Frontend ["Frontend — React + TS"]
    PAGES["Dashboard · Analytics · Signals · Options<br/>Optimize · Alerts · Paper Trade · Import"]:::frontend
    AXIOS["Axios HTTP Client"]:::frontend
    PAGES --> AXIOS
  end

  subgraph API ["API Layer — FastAPI"]
    direction LR
    R_PORT["/portfolio"]:::api
    R_ANAL["/analyze"]:::api
    R_SIG["/signals"]:::api
    R_OPT["/options"]:::api
    R_ALERT["/alerts"]:::api
    R_PAPER["/paper"]:::api
    R_IMP["/import"]:::api
  end

  subgraph Modules ["Backend Modules"]
    direction LR
    ANALYZER["Analyzer<br/>Metrics · Greeks · IV<br/>LEAPS · Optimizer"]:::module
    SIGNALS["Signal Engine<br/>Technical → Scoring<br/>→ Composite → Risk"]:::module
    TRACKER["Tracker<br/>Market Data · CSV Import"]:::module
    MODELS["ORM Models<br/>Asset · Position · Transaction<br/>Alert · PaperTrade"]:::module
  end

  DB[("SQLite — pat.db")]:::storage
  YAHOO["Yahoo Finance — yfinance"]:::external

  AXIOS -->|"HTTP/JSON"| API

  R_PORT --> MODELS
  R_ANAL --> ANALYZER
  R_SIG --> SIGNALS
  R_OPT --> ANALYZER
  R_ALERT --> MODELS
  R_PAPER --> MODELS
  R_IMP --> TRACKER

  ANALYZER --> TRACKER
  SIGNALS --> TRACKER

  MODELS --> DB
  TRACKER --> YAHOO`;

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
