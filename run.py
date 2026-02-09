#!/usr/bin/env python3
# ============================================
# PRICEPALLY OPERATIONS TRACKER
# Run Script
# ============================================

"""
Development run script with various options.

Usage:
    python run.py              # Run with defaults
    python run.py --reload     # Run with auto-reload
    python run.py --port 8080  # Run on different port
"""

import argparse
import uvicorn

from app.config import settings


def main():
    """Parse arguments and run the server."""
    
    parser = argparse.ArgumentParser(
        description="Run the Pricepally Operations Tracker API"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default=settings.host,
        help=f"Host to bind to (default: {settings.host})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help=f"Port to bind to (default: {settings.port})"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        default=settings.debug,
        help="Enable auto-reload (default: based on DEBUG setting)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="debug" if settings.debug else "info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print(f"🚀 Starting {settings.app_name}")
    print(f"📍 URL: http://{args.host}:{args.port}")
    print(f"📚 Docs: http://{args.host}:{args.port}/docs")
    print(f"🔄 Reload: {args.reload}")
    print(f"👷 Workers: {args.workers}")
    print("=" * 50)
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,  # Can't use workers with reload
        log_level=args.log_level,
        access_log=True,
    )


if __name__ == "__main__":
    main()