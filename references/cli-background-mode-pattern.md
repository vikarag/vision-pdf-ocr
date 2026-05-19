# CLI Background Mode Pattern

Reusable pattern for adding `--background` execution to any long-running Python CLI tool. Extracted from the `batch_ocr.py` implementation.

## When to Use

- CLI tools that run for 10+ minutes (OCR, batch processing, data pipelines, model training)
- Tools invoked over SSH or via messaging platforms where the session may interrupt
- Any process where the user wants to "fire and forget" and check results later

## Implementation

### 1. Add CLI Arguments

```python
parser.add_argument(
    "--background",
    action="store_true",
    help="Run in background (detached from terminal). Use --log-file to capture output.",
)
parser.add_argument(
    "--log-file",
    default="",
    help="Log file path for background mode (default: <output_dir>/<name>.log)",
)
parser.add_argument(
    "--pid-file",
    default="",
    help="PID file path for background mode (default: <output_dir>/<name>.pid)",
)
```

### 2. Build Command Without Background Flags

Rebuild the command line, stripping `--background` and related flags so the child process runs in foreground mode:

```python
def _build_command(args: argparse.Namespace) -> list[str]:
    """Rebuild the command line without --background and related flags."""
    cmd = [sys.executable, __file__]
    cmd.append(args.input)  # or whatever positional arg
    if args.some_flag:
        cmd.extend(["--some-flag", args.some_flag])
    # ... add all other args EXCEPT --background, --log-file, --pid-file
    return cmd
```

### 3. Handle Background Mode in main()

```python
def main():
    args = parse_args()
    
    # Determine default paths
    log_file = Path(args.log_file) if args.log_file else output_dir / f"{name}.log"
    pid_file = Path(args.pid_file) if args.pid_file else output_dir / f"{name}.pid"
    
    if args.background:
        # Check for existing job
        if pid_file.exists():
            try:
                old_pid = int(pid_file.read_text().strip())
                os.kill(old_pid, 0)  # Check if process exists
                print(f"Background job already running (PID {old_pid}).")
                sys.exit(1)
            except (OSError, ValueError):
                pid_file.unlink(missing_ok=True)  # Stale PID file
        
        # Start detached process
        cmd = _build_command(args)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, "a") as log_fh:
            log_fh.write(f"\n{'='*60}\n")
            log_fh.write(f"Background job started at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_fh.write(f"Command: {' '.join(cmd)}\n")
            log_fh.write(f"{'='*60}\n\n")
            log_fh.flush()
            
            process = subprocess.Popen(
                cmd,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                close_fds=True,
                start_new_session=True,  # Detach from parent session
            )
        
        pid_file.write_text(str(process.pid))
        
        print(f"Background job started (PID {process.pid})")
        print(f"Log file: {log_file}")
        print(f"Monitor: tail -f {log_file}")
        print(f"Stop: kill {process.pid}")
        sys.exit(0)
    
    # ... normal foreground execution continues
```

### 4. Cleanup on Completion

```python
# At the end of normal execution, clean up PID file
pid_file.unlink(missing_ok=True)
```

## Key Design Decisions

**Use `subprocess.Popen` with `start_new_session=True` instead of `os.fork()` double-fork:**
- Simpler, more portable, and avoids issues with file descriptor inheritance
- `start_new_session=True` calls `setsid()` which creates a new session and detaches from the controlling terminal
- `close_fds=True` prevents file descriptor leaks to the child

**Write log header before starting the child:**
- Ensures the log file exists and is writable before detaching
- Captures the exact command that was run for debugging

**Check PID file before starting:**
- Prevents duplicate jobs that could waste resources or corrupt output
- Handles stale PID files gracefully (process no longer exists)

**Strip background flags when rebuilding command:**
- Prevents infinite recursion (child would also try to background itself)
- Keeps all other flags intact so behavior is identical

## Monitoring Commands

```bash
# Watch log in real-time
tail -f ./job.log

# Check if running
ps aux | grep script_name
# or
cat ./job.pid | xargs ps

# Stop gracefully
kill $(cat ./job.pid)

# Stop forcefully
kill -9 $(cat ./job.pid)
rm ./job.pid  # Clean up stale PID file
```

## Variations

### With Checkpoint/Resume Support

If your tool already has `--resume` and checkpoint files, background mode works seamlessly:
- The child process inherits `--resume` if specified
- Checkpoint files are written by the child, monitored independently
- If the parent disconnects, the child continues from the last checkpoint

### With Parallel Chunk Execution

Launch multiple background jobs with different page ranges:

```bash
python tool.py --pages 1-100 --output chunk1.md --background --log-file chunk1.log
python tool.py --pages 101-200 --output chunk2.md --background --log-file chunk2.log
```

Each gets its own PID file and log file. Monitor all with:

```bash
tail -f chunk1.log chunk2.log
```

## Platform Notes

- **Linux:** `start_new_session=True` works reliably
- **macOS:** Same as Linux
- **Windows:** Use `creationflags=subprocess.CREATE_NEW_PROCESS_GROUP` instead of `start_new_session`

## Full Example

See `scripts/batch_ocr.py` in this skill for the complete production implementation.
