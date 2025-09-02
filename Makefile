.PHONY: help diagrams clean-diagrams

help:
	@echo "Targets:"
	@echo "  diagrams        Render PNG/SVG from Mermaid .mmd files via mermaid-cli (npx)"
	@echo "  clean-diagrams  Remove generated diagram artifacts"

diagrams:
	bash scripts/export_diagrams.sh

clean-diagrams:
	rm -rf AQ-NEW-NL2SQL/docs/diagrams/generated
