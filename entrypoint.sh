#!/usr/bin/env sh
set -e

echo "[entrypoint] Python: $(python -V)"

# (opcjonalnie) szybki check env
if [ -f "CVgetData/test_env.py" ]; then
  echo "[entrypoint] Running test_env.py..."
  python CVgetData/test_env.py
fi

if [ -f "CVgetData/test_neo4j_connection.py" ]; then
  echo "[entrypoint] Running test_neo4j_connection.."
  python CVgetData/test_neo4j_connection.py
fi

# (opcjonalnie) inne skrypty startowe
# python CVgetData/build_graph_from_cvs.py || true

# Streamlit - podmień ścieżkę na swój plik
echo "[entrypoint] Starting Streamlit..."
exec streamlit run app.py --server.address=0.0.0.0 --server.port=8501
