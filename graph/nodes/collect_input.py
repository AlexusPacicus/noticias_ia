def collect_input(state: dict) -> dict:
    return {
        **state,
        "raw_input": state.copy()
    }
