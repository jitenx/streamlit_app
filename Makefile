.PHONY: sync run stop

PORT=8501

sync:
	@echo "📦 Syncing dependencies..."
	@uv sync

run: sync
	@echo "🌟 Starting Streamlit..."
	@uv run streamlit run app.py --server.port $(PORT)

stop:
	@pkill -f "streamlit" || true
	@echo "🛑 Streamlit stopped."