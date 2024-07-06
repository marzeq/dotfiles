return {
	{
		"David-Kunz/gen.nvim",
		opts = {
			display_mode = "split",
      host = os.getenv("GEN_OLLAMA_HOST") or "localhost",
      port = os.getenv("GEN_OLLAMA_PORT") or "11434"
		},
	},
}
