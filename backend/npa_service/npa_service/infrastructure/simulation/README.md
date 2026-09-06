# simulation

`SimulationSource` returns three fixed snapshots for canonical URLs matching
`https://sozd.duma.gov.ru/bill/9999999-<number>`: initial draft, changed second-reading
draft, and published law. `SimulationChangeSummarizer` returns a deterministic
plain-language article and overall summary. They are composed only when
`NPA_SIMULATION_ENABLED=true`, so the UI can demonstrate polling without remote Duma or
OpenRouter calls.
