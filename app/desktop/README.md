# Laptop operator app

Run the GUI from the repository root:

```powershell
$env:PYTHONPATH = 'src;app'
python -B app/desktop/operator.py --host 100.69.39.18 --port 8765
```

The map marker follows the map-frame pose and can be switched between a
robot-following view and a fixed whole-map view.
