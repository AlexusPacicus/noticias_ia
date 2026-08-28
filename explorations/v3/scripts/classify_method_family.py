

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import matplotlib.pyplot as plt
    import pandas as pd
except ImportError as exc:
    missing = getattr(exc, "name", "dependency")
    print(
        f"Error: missing dependency '{missing}'. Install the required packages before running this script.",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


INPUT_CSV = Path("explorations/v3/data/curated/data_v0_curado.csv")
CLASSIFIED_CSV = Path("explorations/v3/data/interim/data_v0_classified.csv")
AGGREGATED_CSV = Path("explorations/v3/outputs/method_family_by_year.csv")
PLOT_PNG = Path("explorations/v3/outputs/method_family_by_year.png")

VALID_FAMILIES = [
    "gan",
    "autoregressive",
    "diffusion",
    "diffusion_transformer_or_hybrid",
    "other",
    "unknown",
]

KEYWORDS: Dict[str, List[str]] = {
    "gan": [
        "generative adversarial",
        "adversarial",
        "stackgan",
        "attngan",
        "cgan",
        "gan",
        "gans",
        "gan-based",
        "generative adversarial network",
    ],
    "autoregressive": [
        "discrete latent",
        "discrete token",
        "autoregressive",
        "vq-vae",
        "dall-e",
        "tokens",
        "token",
    ],
    "diffusion": [
        "classifier-free guidance",
        "latent diffusion",
        "score-based",
        "denoising",
        "diffusion",
        "imagen",
        "glide",
        "ddpm",
        "ldm",
    ],
    "diffusion_transformer_or_hybrid": [
        "multimodal diffusion transformer",
        "diffusion transformer",
        "rectified flow",
        "flow matching",
        "mmdit",
        "flux",
        "sd3",
    ],
}

EXPECTED_COLUMNS = [
    "paper_id",
    "title",
    "year",
    "source_url",
    "abstract",
    "problem",
    "method",
    "result",
    "method_family_seed",
    "method_family_final",
    "notes",
]


def ensure_parent_dirs() -> None:
    # Crea las carpetas de salida si todavía no existen.
    CLASSIFIED_CSV.parent.mkdir(parents=True, exist_ok=True)
    AGGREGATED_CSV.parent.mkdir(parents=True, exist_ok=True)
    PLOT_PNG.parent.mkdir(parents=True, exist_ok=True)


def load_input_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Input CSV not found: {path}")

    df = pd.read_csv(path)
    missing = [column for column in EXPECTED_COLUMNS if column not in df.columns]
    if missing:
        missing_text = ", ".join(missing)
        raise ValueError(f"Input CSV is missing required columns: {missing_text}")

    if df.empty:
        raise ValueError(f"Input CSV has no rows: {path}")

    return df


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().split())


def choose_text_source(row: pd.Series) -> Tuple[str, str]:
    # Prioriza `abstract`; si falta, cae a `method` y después a `title`.
    abstract = normalize_text(row.get("abstract", ""))
    method = normalize_text(row.get("method", ""))
    title = normalize_text(row.get("title", ""))

    if abstract:
        return abstract.lower(), "abstract"
    if method:
        return method.lower(), "method"
    if title:
        return title.lower(), "title"
    return "", "none"


def count_keyword_hits(text: str) -> Tuple[Dict[str, int], Dict[str, List[str]]]:
    # Cuenta coincidencias léxicas por familia y guarda qué señales exactas aparecieron.
    lowered = f" {text.lower()} "
    counts: Dict[str, int] = {}
    matched: Dict[str, List[str]] = {}

    for family, keywords in KEYWORDS.items():
        family_matches: List[str] = []
        for keyword in keywords:
            if keyword in lowered:
                family_matches.append(keyword)
        counts[family] = len(family_matches)
        matched[family] = family_matches

    return counts, matched


def classify_text(text: str) -> Tuple[str, List[str]]:
    if not text:
        return "unknown", []

    counts, matched = count_keyword_hits(text)

    signals: List[str] = []
    for family in VALID_FAMILIES:
        if family in matched:
            signals.extend([f"{family}:{keyword}" for keyword in matched[family]])

    ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    top_family, top_count = ordered[0]
    second_count = ordered[1][1] if len(ordered) > 1 else 0

    # Si no hay hits, devuelve `unknown`. Si hay empate arriba, devuelve `other`.
    if top_count == 0:
        return "unknown", signals
    if top_count > second_count:
        return top_family, signals
    return "other", signals


def classify_row(row: pd.Series) -> pd.Series:
    # Añade columnas nuevas sin tocar las etiquetas manuales existentes.
    text, source = choose_text_source(row)
    family, signals = classify_text(text)

    row = row.copy()
    row["method_family_lexical"] = family
    row["lexical_signals"] = "; ".join(signals)
    row["classification_source"] = source
    return row


def build_aggregated_table(df: pd.DataFrame) -> pd.DataFrame:
    # Resume el número de papers por año y familia léxica.
    agg = (
        df.groupby(["year", "method_family_lexical"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["year", "method_family_lexical"], ascending=[True, True])
    )
    return agg


def save_plot(agg_df: pd.DataFrame, output_path: Path) -> None:
    # Genera un gráfico de barras apiladas ordenado por año ascendente.
    plot_df = agg_df.pivot(
        index="year",
        columns="method_family_lexical",
        values="count",
    ).fillna(0)

    for family in VALID_FAMILIES:
        if family not in plot_df.columns:
            plot_df[family] = 0

    plot_df = plot_df[VALID_FAMILIES].sort_index()

    ax = plot_df.plot(
        kind="bar",
        stacked=True,
        figsize=(10, 6),
    )
    ax.set_title("Method Family by Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Count")
    ax.legend(title="Method Family")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def print_summary(df: pd.DataFrame) -> None:
    # Imprime un resumen mínimo útil para el smoke test.
    counts = df["method_family_lexical"].value_counts().reindex(VALID_FAMILIES, fill_value=0)
    print(f"Papers read: {len(df)}")
    for family, count in counts.items():
        print(f"{family}: {count}")


def main() -> int:
    try:
        ensure_parent_dirs()
        df = load_input_csv(INPUT_CSV)
        classified_df = df.apply(classify_row, axis=1)
        aggregated_df = build_aggregated_table(classified_df)

        classified_df.to_csv(CLASSIFIED_CSV, index=False)
        aggregated_df.to_csv(AGGREGATED_CSV, index=False)
        save_plot(aggregated_df, PLOT_PNG)
        print_summary(classified_df)
        return 0
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
