# Changelog

## 0.0.7

### Changed
- Migrate off `pkg_resources` (removed in setuptools 81) to `importlib.resources`
  for loading the bundled `sources.geojson`; removed unused `pkg_resources` imports
  in `__init__.py` and `connection.py`.

No other functional changes since 0.0.6.
