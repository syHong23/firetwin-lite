"""Question set for the evaluation.

Each question comes with a SPARQL query returning the IDs of a correct answer.
Trap questions ask about things that do not exist in the building; their
correct answer is an empty list of IDs.
"""
PREFIXES = """PREFIX bot: <https://w3id.org/bot#>
PREFIX ftl: <https://example.org/firetwin#>
PREFIX b:   <https://example.org/firetwin/building#>
"""

COMPARTMENTS = [("CompA0", "A0"), ("CompB0", "B0"), ("CompA1", "A1"), ("CompB1", "B1"),
                ("CompStair", "the protected stairwell compartment")]
STOREYS = [("S0", "ground floor"), ("S1", "first floor")]
DOORS = ["FD_002", "FD_101", "FD_S0", "FD_S1"]


def build_questions() -> list[dict]:
    q = []

    def add(category, text, sparql):
        q.append({"id": f"Q{len(q) + 1:02d}", "category": category, "question": text,
                  "sparql": PREFIXES + sparql if sparql else None})

    for comp, name in COMPARTMENTS:
        label = name if name.startswith("the ") else f"fire compartment {name}"
        add("compartment", f"Which spaces are in {label}?",
            f"SELECT ?id WHERE {{ ?id ftl:inCompartment b:{comp} . }}")
    for storey, name in STOREYS:
        add("storey", f"Which spaces are on the {name}?",
            f"SELECT ?id WHERE {{ b:{storey} bot:hasSpace ?id . }}")
        add("detector", f"Which rooms on the {name} have no smoke detector?",
            f"""SELECT ?id WHERE {{ b:{storey} bot:hasSpace ?id . ?id a ftl:Room .
               FILTER NOT EXISTS {{ ?id bot:containsElement ?d . ?d a ftl:SmokeDetector . }} }}""")
    add("detector", "Which rooms have no smoke detector?",
        """SELECT ?id WHERE { ?id a ftl:Room .
           FILTER NOT EXISTS { ?id bot:containsElement ?d . ?d a ftl:SmokeDetector . } }""")
    add("detector", "Which spaces contain a heat detector?",
        "SELECT DISTINCT ?id WHERE { ?id bot:containsElement ?d . ?d a ftl:HeatDetector . }")
    add("detector", "Which spaces contain a manual call point?",
        "SELECT DISTINCT ?id WHERE { ?id bot:containsElement ?d . ?d a ftl:ManualCallPoint . }")
    add("detector", "Which corridors contain a smoke detector?",
        "SELECT DISTINCT ?id WHERE { ?id a ftl:Corridor ; bot:containsElement ?d . ?d a ftl:SmokeDetector . }")
    add("detector", "Which stairwells contain a smoke detector?",
        "SELECT DISTINCT ?id WHERE { ?id a ftl:Stairwell ; bot:containsElement ?d . ?d a ftl:SmokeDetector . }")
    for door in DOORS:
        add("door", f"Which spaces does fire door {door} separate?",
            f"SELECT ?id WHERE {{ ?id bot:adjacentElement b:{door} . }}")
    for space, name in [("Corridor0", "Corridor 0"), ("Corridor1", "Corridor 1"), ("Stair1", "the first-floor stairwell")]:
        add("connection", f"Which spaces are directly connected to {name}?",
            f"SELECT DISTINCT ?id WHERE {{ {{ b:{space} ftl:connectsTo ?id }} UNION {{ ?id ftl:connectsTo b:{space} }} }}")
    add("exit", "Which evacuation exits does the building have?",
        "SELECT ?id WHERE { ?id a ftl:EvacuationExit . }")
    add("exit", "From which spaces can occupants leave the building directly through an exit?",
        "SELECT ?id WHERE { ?e a ftl:EvacuationExit ; ftl:exitFrom ?id . }")
    add("exit", "Which rooms contain an evacuation exit?",
        "SELECT ?id WHERE { ?id a ftl:Room ; bot:containsElement ?e . ?e a ftl:EvacuationExit . }")
    # Trap questions: the correct answer is an empty list
    for text in ["Can occupants use the elevator to evacuate?",
                 "Which rooms have a sprinkler?",
                 "Which spaces contain a fire extinguisher?",
                 "Which spaces are in fire compartment C1?",
                 "Which rooms on the second floor have no smoke detector?",
                 "Which smoke detector is installed in Room 104?"]:
        add("trap", text, None)
    return q
