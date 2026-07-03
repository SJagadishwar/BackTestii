from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.services import strategy_service
from engine.data import data_loader
from engine.data.data_loader import load_index_data, get_available_indices
from datetime import date
from backend.db import engine, Base, get_db
from backend.models.user import User
from backend.security import hash_password, verify_password, create_access_token
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
import math
import logging

logger = logging.getLogger(__name__)

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
INTERNAL_CLIENT_KEY = os.getenv("INTERNAL_CLIENT_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}


@app.get("/db-status")
def db_status():
    """Return coverage statistics for the active data source."""
    source = os.getenv("DATA_SOURCE", "yahoo").strip().lower()
    if source == "own_db":
        try:
            from engine.data.own_db_loader import get_db_coverage
            coverage = get_db_coverage()
            return {"source": "own_db", "coverage": coverage}
        except Exception as e:
            return {"source": "own_db", "error": str(e)}
    else:
        return {
            "source": "yahoo",
            "status": "active",
            "info": "Using Yahoo Finance as data source. Own database is preserved but not active.",
        }


@app.get("/")
def root():
    return {"message": "Equity Strategy Backend Running"}


class BacktestRequest(BaseModel):
    ticker: str
    strategy_key: str
    strategy_params: Optional[Dict[str, Any]] = Field(default_factory=dict)
    start_date: date
    end_date: date
    capital: float
    asset_type: str = "stock"


class OptionsBacktestRequest(BaseModel):
    symbol: str
    strategy: str = "long_straddle"
    start_date: date
    end_date: date
    entry_price_type: str = "open"
    what_if_premium_target: Optional[float] = None
    what_if_spot_move_pct: Optional[float] = None


class RegisterRequest(BaseModel):
    email: str
    password: str


from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login", auto_error=False)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


def verify_internal_client(request: Request):
    """Validate the X-Internal-Client-Key header against INTERNAL_CLIENT_KEY."""
    key = request.headers.get("X-Internal-Client-Key")
    if not INTERNAL_CLIENT_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL_CLIENT_KEY is not configured on the server.",
        )
    if not key or key != INTERNAL_CLIENT_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal client key.",
        )
    return True


def require_auth(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Combined auth: allow access if EITHER:
      - Valid JWT bearer token (user auth)
      - Valid X-Internal-Client-Key header (internal client)
    """
    # Try internal client key first
    client_key = request.headers.get("X-Internal-Client-Key")
    if client_key:
        if INTERNAL_CLIENT_KEY and client_key == INTERNAL_CLIENT_KEY:
            return None  # Authenticated as internal client
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal client key.",
        )

    # Fall back to JWT user auth
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide a Bearer token or X-Internal-Client-Key header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return get_current_user(token=token, db=db)

@app.post("/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    hashed = hash_password(req.password)

    user = User(
        email=req.email,
        hashed_password=hashed,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully."}


@app.post("/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials.")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials.")

    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.post("/backtest")
def execute_backtest(
    req: BacktestRequest,
    _auth=Depends(require_auth),
):
    available_strategies = strategy_service.list_strategies()

    if req.strategy_key not in available_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy_key. Available: {list(available_strategies.keys())}"
        )

    if req.capital <= 0:
        raise HTTPException(
            status_code=400,
            detail="Capital must be greater than zero."
        )

    if req.start_date >= req.end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date must be earlier than end_date."
        )

    try:
        result = strategy_service.run_backtest(
            ticker=req.ticker,
            strategy_key=req.strategy_key,
            strategy_params=req.strategy_params or {},
            start_date=str(req.start_date),
            end_date=str(req.end_date),
            capital=req.capital,
            asset_type=req.asset_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Backtest execution failed: {str(e)}"
        )

    return result


@app.post("/options-backtest")
def execute_options_backtest(
    req: OptionsBacktestRequest,
    _auth=Depends(require_auth),
):
    if req.strategy != "long_straddle":
        raise HTTPException(status_code=400, detail="Only 'long_straddle' is currently supported.")
        
    try:
        from engine.options.data_provider import OptionsDataProvider
        from engine.options.engine import OptionsBacktester
        
        dp = OptionsDataProvider()
        tester = OptionsBacktester(data_provider=dp)
        
        trades = tester.run_weekly_long_straddle(
            symbol=req.symbol,
            start_date=req.start_date,
            end_date=req.end_date,
            entry_price_type=req.entry_price_type,
            what_if_premium_target=req.what_if_premium_target,
            what_if_spot_move_pct=req.what_if_spot_move_pct
        )
        
        total_pnl = sum(t["pnl"] for t in trades)
        win_trades = [t for t in trades if t["pnl"] > 0]
        loss_trades = [t for t in trades if t["pnl"] <= 0]
        
        return {
            "metrics": {
                "total_trades": len(trades),
                "total_pnl": total_pnl,
                "win_rate": (len(win_trades) / len(trades) * 100) if trades else 0,
                "avg_profit": (sum(t["pnl"] for t in win_trades) / len(win_trades)) if win_trades else 0,
                "avg_loss": (sum(t["pnl"] for t in loss_trades) / len(loss_trades)) if loss_trades else 0,
                "max_profit": max((t["pnl"] for t in trades), default=0),
                "max_loss": min((t["pnl"] for t in trades), default=0),
            },
            "trades": trades
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Options Backtest failed: {str(e)}"
        )


@app.get("/strategies")
def get_strategies():
    """Return the full strategy registry (JSON-safe, no lambdas)."""
    return strategy_service.list_strategies()


@app.get("/instruments")
def get_instruments(exchange: str | None = None):
    """Return sorted list of instrument display names, optionally filtered by exchange."""
    return strategy_service.list_instruments(exchange=exchange)


@app.get("/instruments/resolve")
def resolve_instrument(name: str, exchange: str | None = None):
    """Resolve an instrument display name to a Yahoo Finance ticker symbol."""
    try:
        symbol = strategy_service.resolve_symbol(name, exchange=exchange)
        return {"symbol": symbol}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/stock-data/{ticker}")
def get_stock_data(
    ticker: str,
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    """
    Fetch adjusted OHLCV data for a specific stock over a date range.
    Returns premium structured data for charting.
    """
    try:
        df = data_loader.load_price_data(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            timeframe="1D"
        )
        if df is None or df.empty:
            return {"data": []}
            
        # Convert DataFrame to list of dicts suitable for lightweight-charts
        df = df.reset_index()
        records = df.to_dict(orient="records")
        
        # Replace NaN with None
        clean_records = []
        for row in records:
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    clean_row[k] = None
                else:
                    if k == "date" and not isinstance(v, str):
                        clean_row[k] = v.strftime("%Y-%m-%d")
                    else:
                        clean_row[k] = v
            clean_records.append(clean_row)
            
        return {"data": clean_records}
    except ValueError as e:
        if "No data returned" in str(e):
            return {"data": []}
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch stock data: {str(e)}")


@app.get("/indices")
def list_indices():
    """Return all available NSE indices with their date ranges."""
    return {"data": get_available_indices()}


@app.get("/index-data/{index_name}")
def get_index_data(
    index_name: str,
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    """
    Fetch historical OHLCV data for an NSE index.
    index_name can use underscores or spaces, e.g. "NIFTY_50" or "NIFTY 50".
    """
    try:
        # Allow underscores as space replacement in URLs
        clean_name = index_name.replace("_", " ").strip().upper()
        df = load_index_data(clean_name, start_date, end_date)
        if df is None or df.empty:
            return {"data": []}

        df = df.reset_index()
        records = df.to_dict(orient="records")

        clean_records = []
        for row in records:
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float) and math.isnan(v):
                    clean_row[k] = None
                else:
                    if k == "date" and not isinstance(v, str):
                        clean_row[k] = v.strftime("%Y-%m-%d")
                    else:
                        clean_row[k] = v
            clean_records.append(clean_row)

        return {"data": clean_records}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch index data: {str(e)}")


@app.get("/corporate-actions/{ticker}")
def get_corporate_actions(ticker: str):
    """
    Fetch corporate actions (Splits, Dividends, etc.) for a specific stock.
    Routes to Yahoo Finance or own DB based on DATA_SOURCE.
    """
    source = os.getenv("DATA_SOURCE", "yahoo").strip().lower()

    if source == "own_db":
        return _get_corporate_actions_own_db(ticker)
    else:
        return _get_corporate_actions_yahoo(ticker)


def _get_corporate_actions_yahoo(ticker: str):
    """Fetch corporate actions from Yahoo Finance using yfinance."""
    try:
        import yfinance as yf

        # Ensure ticker has exchange suffix for Yahoo
        clean_ticker = ticker.strip()
        if not (".NS" in clean_ticker or ".BO" in clean_ticker):
            clean_ticker = f"{clean_ticker}.NS"

        stock = yf.Ticker(clean_ticker)
        actions = []

        # Splits
        try:
            splits = stock.splits
            if splits is not None and not splits.empty:
                for dt, ratio in splits.items():
                    if ratio != 0:
                        actions.append({
                            "exDate": dt.strftime("%Y-%m-%d"),
                            "actionType": "SPLIT",
                            "ratio": float(ratio),
                            "remarks": f"Stock split {ratio}:1",
                            "amount": None,
                        })
        except Exception:
            pass

        # Dividends
        try:
            dividends = stock.dividends
            if dividends is not None and not dividends.empty:
                for dt, amount in dividends.items():
                    if amount > 0:
                        actions.append({
                            "exDate": dt.strftime("%Y-%m-%d"),
                            "actionType": "DIVIDEND",
                            "ratio": None,
                            "remarks": f"Dividend Rs.{amount:.2f}",
                            "amount": float(amount),
                        })
        except Exception:
            pass

        # Sort newest first
        actions.sort(key=lambda x: x["exDate"] or "", reverse=True)
        return {"data": actions}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch corporate actions from Yahoo: {str(e)}",
        )


def _get_corporate_actions_own_db(ticker: str):
    """Fetch corporate actions from own PostgreSQL database."""
    try:
        import psycopg

        url = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")
        actions = []
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                # The frontend sends Yahoo-format symbols like 'RELIANCE.NS'.
                # Strip the '.NS' / '.BO' suffix to match the plain NSE symbol in the DB.
                clean_symbol = ticker.replace('.NS', '').replace('.BO', '').strip().upper()
                
                cur.execute('''
                    SELECT ex_date, action_type, ratio, remarks, amount 
                    FROM nse_corporate_actions 
                    WHERE symbol = %s 
                    ORDER BY ex_date DESC
                ''', (clean_symbol,))
                
                for row in cur.fetchall():
                    action_type = row[1]
                    ratio_val = float(row[2]) if row[2] is not None else None
                    if ratio_val is not None and math.isnan(ratio_val):
                        ratio_val = None
                    remarks = row[3] if row[3] else None
                    amount_val = float(row[4]) if row[4] is not None else None
                    if amount_val is not None and math.isnan(amount_val):
                        amount_val = None

                    # ── Noise filter for SPLIT rows ──
                    if action_type == 'SPLIT':
                        if ratio_val is not None and not remarks:
                            if 0.85 < ratio_val < 1.25:
                                continue  # noise — skip
                    
                    actions.append({
                        "exDate": row[0].strftime("%Y-%m-%d") if row[0] else None,
                        "actionType": action_type,
                        "ratio": ratio_val,
                        "remarks": remarks,
                        "amount": amount_val,
                    })
        return {"data": actions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch corporate actions: {str(e)}")


@app.get("/instruments/search")
def search_instruments(q: str, exchange: str | None = None):
    """Search for instruments. Routes enrichment through own DB or plain CSV based on DATA_SOURCE."""
    if not q or len(q.strip()) < 1:
        return []

    query = q.strip().upper()
    source = os.getenv("DATA_SOURCE", "yahoo").strip().lower()

    try:
        from engine.instruments.loader import load_instruments
        df = load_instruments()

        # Search by symbol prefix OR company name substring
        mask = (
            df["display_name"].str.upper().str.contains(query, na=False)
            | df.get("company_name", df["display_name"]).astype(str).str.upper().str.contains(query, na=False)
        )
        matches = df[mask].head(20)

        if matches.empty:
            return []

        if source == "own_db":
            return _search_instruments_own_db(matches, query)
        else:
            return _search_instruments_yahoo(matches, query)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


def _search_instruments_yahoo(matches, query: str) -> list:
    """Build search results without querying the own database."""
    results = []
    for _, row in matches.iterrows():
        symbol = row["display_name"].strip().upper()
        exchange = row.get("exchange", "NSE").upper()
        yahoo_symbol = row.get("yahoo_symbol", f"{symbol}.NS").strip()
        company_raw = row.get("company_name", "")
        company = "" if (company_raw is None or (isinstance(company_raw, float) and str(company_raw) == "nan")) else str(company_raw).strip()
        item = {
            "symbol": yahoo_symbol,
            "nse_symbol": symbol,
            "name": company if company else symbol,
            "exchange": exchange,
            "type": str(row.get("type", "equity")).upper(),
            "data_from": None,
            "data_to": None,
            "total_days": 0,
            "source": "yahoo",
        }
        results.append(item)

    # Sort: exact prefix matches first, then alphabetically
    results.sort(key=lambda x: (
        0 if x["nse_symbol"].startswith(query) else 1,
        x["nse_symbol"],
    ))
    return results


def _search_instruments_own_db(matches, query: str) -> list:
    """Enrich search results with data availability from own database."""
    import psycopg

    dsn = os.getenv("DATABASE_URL", "").replace("postgresql+psycopg://", "postgresql://")
    results = []

    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for _, row in matches.iterrows():
                symbol = row["display_name"].strip().upper()
                nse_symbol = symbol

                # Get data availability (including aliases for renamed stocks)
                cur.execute("""
                    SELECT old_symbol FROM symbol_aliases
                    WHERE current_symbol = %s
                """, (nse_symbol,))
                old_names = [r[0] for r in cur.fetchall()]
                all_syms = [nse_symbol] + old_names

                placeholders = ",".join(["%s"] * len(all_syms))
                cur.execute(f"""
                    SELECT MIN(date), MAX(date), COUNT(*)
                    FROM nse_price_data
                    WHERE symbol IN ({placeholders})
                """, all_syms)
                db_row = cur.fetchone()
                min_date, max_date, total_days = db_row if db_row else (None, None, 0)

                company_raw = row.get("company_name", "")
                company = "" if (company_raw is None or (isinstance(company_raw, float) and str(company_raw) == "nan")) else str(company_raw).strip()
                exchange = row.get("exchange", "NSE").upper()
                yahoo_symbol = row.get("yahoo_symbol", f"{symbol}.NS").strip()
                item = {
                    "symbol": yahoo_symbol,
                    "nse_symbol": nse_symbol,
                    "name": company if company else nse_symbol,
                    "exchange": exchange,
                    "type": str(row.get("type", "equity")).upper(),
                    "data_from": str(min_date) if min_date else None,
                    "data_to": str(max_date) if max_date else None,
                    "total_days": int(total_days) if total_days else 0,
                }
                results.append(item)

    # Sort: exact prefix matches first, then by total_days (most data first)
    results.sort(key=lambda x: (
        0 if x["nse_symbol"].startswith(query) else 1,
        -x["total_days"],
    ))
    return results


class ComparisonRequest(BaseModel):
    ticker: str
    start_date: date
    end_date: date
    capital: float = 100000
    asset_type: str = "stock"


class TunedComparisonRequest(BaseModel):
    ticker: str
    start_date: date
    end_date: date
    capital: float = 100000
    tuned_runs: dict = {}
    include_buy_hold: bool = False
    asset_type: str = "stock"


@app.post("/comparison")
def run_comparison(req: ComparisonRequest, _auth=Depends(require_auth)):
    """Run all strategies with default params and return comparison table + equity curves."""
    try:
        return strategy_service.run_comparison(
            ticker=req.ticker,
            start_date=str(req.start_date),
            end_date=str(req.end_date),
            capital=req.capital,
            asset_type=req.asset_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@app.post("/tuned-comparison")
def run_tuned_comparison(req: TunedComparisonRequest, _auth=Depends(require_auth)):
    """Run tuned strategy configs and return comparison table + equity curves."""
    try:
        return strategy_service.run_tuned_comparison(
            ticker=req.ticker,
            start_date=str(req.start_date),
            end_date=str(req.end_date),
            capital=req.capital,
            tuned_runs=req.tuned_runs,
            include_buy_hold=req.include_buy_hold,
            asset_type=req.asset_type,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tuned comparison failed: {str(e)}")
