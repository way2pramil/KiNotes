# How to Capture Console Output from KiNotes

## Method 1: Using the Batch Script (EASIEST)

### Step 1: Run the Batch Script
```
Double-click: run_kicad_with_console.bat
```

This opens KiCad with a console window visible.

### Step 2: Test Open/Close Cycles
```
1. KiCad opens
2. Create or open a PCB file
3. Click: Tools → External Plugins → KiNotes
4. Use plugin for 5 seconds
5. Close plugin (X button)
   └─ Watch console for "[KiNotes] Cleanup complete"
6. Wait 2 seconds
7. Repeat steps 3-5 FIVE TIMES TOTAL
```

### Step 3: Capture Output
```
Right-click console window
Select: "Select All" (Ctrl+A)
Select: "Copy" (Ctrl+C)
Paste into text file or share
```

---

## Method 2: Redirect Output to File

### Using Command Line:
```cmd
"C:\Program Files\KiCad\9.0\bin\kicad.exe" > C:\kicad_output.txt 2>&1
```

This saves all output to `C:\kicad_output.txt`

---

## Method 3: Python Script (For Advanced Testing)

Create file: `test_memory_leaks.py`

```python
import subprocess
import time
import sys

print("=" * 60)
print("KiNotes Memory Leak Test")
print("=" * 60)

kicad_exe = r"C:\Program Files\KiCad\9.0\bin\kicad.exe"

# Start KiCad with output capture
print("\n[TEST] Starting KiCad with console output...")
print("Follow these steps in KiCad:")
print("1. Open or create a PCB file")
print("2. Click: Tools > External Plugins > KiNotes")
print("3. Close KiNotes")
print("4. Wait 2 seconds")
print("5. Repeat steps 2-4 FIVE TIMES")
print("6. Close KiCad\n")

try:
    # Run KiCad and capture output
    process = subprocess.Popen(
        [kicad_exe],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )
    
    # Print output in real-time
    for line in process.stdout:
        # Print all lines, highlight KiNotes messages
        if "[KiNotes]" in line:
            print(f">>> {line.rstrip()}")  # Highlight KiNotes output
        else:
            print(line.rstrip())
    
    # Wait for KiCad to close
    process.wait()
    
    print("\n" + "=" * 60)
    print("[TEST] KiCad closed")
    print("=" * 60)
    
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
```

### Run it:
```cmd
python test_memory_leaks.py > kicad_console_output.txt 2>&1
```

---

## What to Look For in Console Output

### ✅ GOOD OUTPUT (Successful Cleanup)

```
[KiNotes] Starting comprehensive cleanup...
[KiNotes] Task timer stopped
[KiNotes] Auto-save timer stopped
[KiNotes] Event handlers unbound
[KiNotes] Final data saved
[KiNotes] Visual editor cleaned up
[KiNotes] Markdown editor cleaned up
[KiNotes] Color pickers cleaned up
[KiNotes] Net linker cleaned up
[KiNotes] Designator linker cleaned up
[KiNotes] Notes manager cleaned up
[KiNotes] Debug logger cleaned up
[KiNotes] Crash safety marked clean shutdown
[KiNotes] Crash safety reference cleared
[KiNotes] Cleanup complete
[KiNotes] Frame destroyed successfully
```

### ❌ BAD OUTPUT (Missing Cleanup)

```
[KiNotes] Starting comprehensive cleanup...
[KiNotes] Task timer stopped
[KiNotes] Auto-save timer stopped
[KiNotes] Cleanup complete
[KiNotes] Frame destroyed successfully
```

Missing:
- Event handler unbinding
- Object cleanup
- Visual/Markdown editor cleanup

### ⚠️ ERROR OUTPUT

```
[KiNotes] XXX cleanup error: [exception message]
```

This shows which resource isn't cleaning up properly.

---

## Step-by-Step Console Capture

### Using Built-in Batch Script:

**1. Double-click this file:**
```
D:\AI_tools\PCBtools\KiNotes\KiNotes\run_kicad_with_console.bat
```

**2. You'll see:**
```
========================================
KiCad Console Output Capture
========================================

This will open KiCad with console visible.
All [KiNotes] debug messages will appear here.

[Steps listed...]

========================================
```

**3. Click OK, KiCad opens**

**4. In KiCad:**
```
- Open a PCB file (File > Open)
- Go to Tools > External Plugins > KiNotes
- Wait for plugin to load
- Note the console output
- Close the plugin
- Look for cleanup messages
```

**5. Repeat 5 times**

**6. When done:**
```
- Switch back to console window
- Select all text: Ctrl+A
- Copy: Ctrl+C
- Paste into notepad or email
```

---

## Console Window Tips

### To Scroll Back and See Earlier Output:
```
Right-click console → Scroll back with mouse wheel
Or use Up arrow key
```

### To Copy Multiple Lines:
```
1. Right-click → "Select All"
2. Right-click → "Copy"
3. Open Notepad, paste (Ctrl+V)
4. Save file
```

### To Keep Console Open After KiCad Closes:
```
Add "pause" to batch file
Then console waits for you to press a key
```

---

## Expected Console Output Timeline

### Open KiNotes First Time:
```
[KiNotes] KiNotesFrame created
[KiNotes] Run() called
[KiNotes] Crash safety initialized
[KiNotes] UI initialized
[KiNotes] Auto-save timer started
```

### Close KiNotes:
```
[KiNotes] Starting comprehensive cleanup...
[KiNotes] Task timer stopped
[KiNotes] Auto-save timer stopped
[KiNotes] Event handlers unbound
[KiNotes] Final data saved
[KiNotes] Visual editor cleaned up
... (all cleanup messages)
[KiNotes] Cleanup complete
[KiNotes] Frame destroyed successfully
```

### Open Again (2nd Time):
```
[KiNotes] KiNotesFrame created
[KiNotes] Run() called
... (same as first)
```

### Important:
- **Each open/close cycle** should show complete cleanup
- **No errors** between cycles
- **Memory stable** (Task Manager shows similar memory usage)

---

## Common Issues & Interpretation

### Issue: "Cleanup complete" not appearing
**Meaning:** cleanup() method not being called  
**Action:** Check if close event is firing

### Issue: "Frame destroyed successfully" not appearing  
**Meaning:** Frame.Destroy() failing  
**Action:** Check for exception message above it

### Issue: Cleanup messages disappear after 2 cycles
**Meaning:** Exception occurring, stopping cleanup  
**Action:** Look for "[KiNotes]" error messages

### Issue: "memory" or "out of memory" error
**Meaning:** Memory leak confirmed  
**Action:** Share console output with this message

---

## Sharing Console Output

Once captured, please share:

**1. Copy of console output** (full text)
**2. How many open/close cycles before crash**
**3. Any error messages** that appeared
**4. System info:**
   ```cmd
   systeminfo | find "Total Physical Memory"
   ```

---

## Quick Command (Direct)

Just run this in Command Prompt:
```cmd
cd D:\AI_tools\PCBtools\KiNotes\KiNotes
run_kicad_with_console.bat
```

Then follow the on-screen instructions.
