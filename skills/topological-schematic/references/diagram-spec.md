# Diagram specification

- Use the target model's authoritative parameters and calculated coordinates. Keep the plotted geometry on equal aspect.
- Use one consistent visual grammar for phase A, phase B, domain boundaries, waveguides, and holes. Include a legend where colors alone are ambiguous.
- Distinguish internal routing nodes (`P01`, `P02`, …) from CST ports. Do not reuse a node number for a port.
- Label lengths with their parameter names and units. Dense paths should include a coordinate table keyed to visible node labels.
- Check phase labels at the lattice nodes, endpoint coordinates, crystal centrelines, and declared device dimensions against the source before export.
- For publication figures, retain vector SVG/PDF and a readable PNG preview. State that the figure is schematic unless it was generated from and compared with the actual geometry model.
