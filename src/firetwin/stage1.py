"""Run all stage-1 checks and print the results.

Usage (from the project root):  python -m firetwin.stage1
"""
from firetwin.kg import check_rules, load_graph, run_query


def show(title: str, rows: list[tuple]) -> None:
    print(f"\n== {title} ==")
    for row in rows or [("(none)",)]:
        print("  " + " | ".join(v.split("#")[-1] for v in row))


def main() -> None:
    plain = load_graph(reason=False)
    g = load_graph(reason=True)
    print(f"Triples before reasoning: {len(plain)}, after: {len(g)}")

    show("Rooms without a smoke detector", run_query(g, "rooms_without_smoke_detector"))
    show("Fire detectors per storey", run_query(g, "detectors_per_storey"))
    show("Spaces in compartment B", run_query(g, "spaces_in_compartment"))
    show("Evacuation exits", run_query(g, "exits"))
    show("Sensors WITHOUT reasoning", run_query(plain, "all_sensors"))
    show("Sensors WITH reasoning", run_query(g, "all_sensors"))

    conforms, problems = check_rules(g)
    print(f"\n== SHACL validation: {'conforms' if conforms else 'violations found'} ==")
    for p in problems:
        print("  " + p)


if __name__ == "__main__":
    main()
