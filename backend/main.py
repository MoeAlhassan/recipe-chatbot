from __future__ import annotations

"""FastAPI application entry-point for the recipe chatbot."""

import ast
import csv
import json
from pathlib import Path
from typing import Dict, Final, List

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from backend.utils import (get_agent_response, log_trace,
                           update_trace_annotation)

# -----------------------------------------------------------------------------
# Application setup
# -----------------------------------------------------------------------------

APP_TITLE: Final[str] = "Recipe Chatbot"
app = FastAPI(title=APP_TITLE)

# Serve static assets (currently just the HTML) under `/static/*`.
STATIC_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# -----------------------------------------------------------------------------
# Request / response models
# -----------------------------------------------------------------------------


class ChatMessage(BaseModel):
    """Schema for a single message in the chat history."""

    role: str = Field(
        ..., description="Role of the message sender (system, user, or assistant)."
    )
    content: str = Field(..., description="Content of the message.")


class ChatRequest(BaseModel):
    """Schema for incoming chat messages."""

    messages: List[ChatMessage] = Field(
        ..., description="The entire conversation history."
    )


class ChatResponse(BaseModel):
    """Schema for the assistant's reply returned to the front-end."""

    messages: List[ChatMessage] = Field(
        ..., description="The updated conversation history."
    )


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:  # noqa: WPS430
    """Main conversational endpoint.

    It proxies the user's message list to the underlying agent and returns the updated list.
    """
    # Convert Pydantic models to simple dicts for the agent
    request_messages: List[Dict[str, str]] = [
        msg.model_dump() for msg in payload.messages
    ]

    try:
        updated_messages_dicts = get_agent_response(request_messages)
        error = None
    except Exception as exc:  # noqa: BLE001 broad; surface as HTTP 500
        # In production you would log the traceback here.
        error = str(exc)
        # Log the trace with error info
        log_trace(
            user_query=str(request_messages),
            bot_response="",
            error=error,
            metadata=json.dumps({"model": "gpt-4o-mini"}),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    # Convert dicts back to Pydantic models for the response
    response_messages: List[ChatMessage] = [
        ChatMessage(**msg) for msg in updated_messages_dicts
    ]
    # Log the trace (success)
    log_trace(
        user_query=str(request_messages),
        bot_response=str([msg.model_dump() for msg in response_messages]),
        error=None,
        metadata=json.dumps({"model": "gpt-4o-mini"}),
    )
    return ChatResponse(messages=response_messages)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:  # noqa: WPS430
    """Serve the chat UI."""

    html_path = STATIC_DIR / "index.html"
    if not html_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Frontend not found. Did you forget to build it?",
        )

    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/traces")
def list_traces(request: Request):
    import sqlite3

    db_path = str(Path(__file__).parent / ".." / "data" / "traces.db")
    with sqlite3.connect(db_path) as conn:
        traces = conn.execute(
            "SELECT id, timestamp, user_query, bot_response, notes, failure_modes FROM traces ORDER BY id DESC"
        ).fetchall()
        # Compute error_stats for right panel
        error_counts = {}
        for t in traces:
            if t[5]:
                for mode in t[5].split(","):
                    mode = mode.strip()
                    if mode:
                        error_counts[mode] = error_counts.get(mode, 0) + 1
    return templates.TemplateResponse(
        "traces_list.html",
        {"request": request, "traces": traces, "error_stats": error_counts},
    )


@app.get("/traces/export_error_analysis")
def export_error_analysis():
    import csv
    import sqlite3

    from fastapi.responses import StreamingResponse

    db_path = str(Path(__file__).parent / ".." / "data" / "traces.db")
    with sqlite3.connect(db_path) as conn:
        traces = conn.execute(
            "SELECT id, user_query, bot_response, notes, failure_modes FROM traces ORDER BY id DESC"
        ).fetchall()
        # Collect all unique failure modes
        failure_mode_set = set()
        for t in traces:
            if t[4]:
                for mode in t[4].split(","):
                    mode = mode.strip()
                    if mode:
                        failure_mode_set.add(mode)
        failure_modes = sorted(failure_mode_set)
        # Prepare CSV columns
        columns = [
            "Trace_ID",
            "User_Query",
            "Dimension_Tuple_JSON",
            "Full_Bot_Trace_Summary",
            "Open_Code_Notes",
        ] + [f"Failure_Mode_{mode}" for mode in failure_modes]

    def iter_csv():
        yield ",".join(columns) + "\n"
        for t in traces:
            trace_id = f"TRA{t[0]}"
            user_query = t[1].replace("\n", " ").replace('"', '""') if t[1] else ""
            dimension_tuple = ""  # Not available
            bot_summary = t[2].replace("\n", " ").replace('"', '""') if t[2] else ""
            notes = t[3].replace("\n", " ").replace('"', '""') if t[3] else ""
            present_modes = set()
            if t[4]:
                for mode in t[4].split(","):
                    mode = mode.strip()
                    if mode:
                        present_modes.add(mode)
            row = [trace_id, user_query, dimension_tuple, bot_summary, notes] + [
                "1" if mode in present_modes else "0" for mode in failure_modes
            ]
            yield ",".join(
                f'"{v}"' if "," in v or '"' in v or "\n" in v else v for v in row
            ) + "\n"

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=error_analysis_export.csv"
        },
    )


@app.get("/traces/export")
def export_traces():
    import sqlite3

    db_path = str(Path(__file__).parent / ".." / "data" / "traces.db")
    with sqlite3.connect(db_path) as conn:
        traces = conn.execute("SELECT * FROM traces ORDER BY id DESC").fetchall()
        columns = [desc[0] for desc in conn.execute("PRAGMA table_info(traces)")]

    def iter_csv():
        yield ",".join(columns) + "\n"
        for row in traces:
            yield ",".join([str(x) if x is not None else "" for x in row]) + "\n"

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=traces.csv"},
    )


@app.get("/traces/{trace_id}")
def edit_trace(request: Request, trace_id: int):
    import json
    import sqlite3

    db_path = str(Path(__file__).parent / ".." / "data" / "traces.db")
    with sqlite3.connect(db_path) as conn:
        trace = conn.execute(
            "SELECT id, timestamp, user_query, bot_response, notes, failure_modes FROM traces WHERE id = ?",
            (trace_id,),
        ).fetchone()
        traces = conn.execute(
            "SELECT id, timestamp, user_query, bot_response, notes, failure_modes FROM traces ORDER BY id DESC"
        ).fetchall()
        # Compute error_stats for right panel
        error_counts = {}
        for t in traces:
            if t[5]:
                for mode in t[5].split(","):
                    mode = mode.strip()
                    if mode:
                        error_counts[mode] = error_counts.get(mode, 0) + 1
        # Find next trace id for navigation
        trace_ids = [t[0] for t in traces]
        try:
            idx = trace_ids.index(trace_id)
            next_trace_id = trace_ids[idx - 1] if idx > 0 else None
        except ValueError:
            next_trace_id = None

        # Parse user_query and bot_response as JSON or Python literal if possible
        def try_parse(val):
            try:
                return json.loads(val)
            except Exception:
                try:
                    obj = ast.literal_eval(val)
                    # Convert to JSON-compatible by dumping and loading
                    return json.loads(json.dumps(obj))
                except Exception:
                    return None

        user_query_parsed = try_parse(trace[2])
        bot_response_parsed = try_parse(trace[3])
    return templates.TemplateResponse(
        "trace_edit.html",
        {
            "request": request,
            "trace": trace,
            "traces": traces,
            "error_stats": error_counts,
            "next_trace_id": next_trace_id,
            "user_query_parsed": user_query_parsed,
            "bot_response_parsed": bot_response_parsed,
        },
    )


@app.post("/traces/{trace_id}")
def update_trace(
    request: Request,
    trace_id: int,
    notes: str = Form(...),
    failure_modes: str = Form(...),
):
    update_trace_annotation(trace_id, notes, failure_modes)
    return RedirectResponse(url=f"/traces/{trace_id}", status_code=303)
