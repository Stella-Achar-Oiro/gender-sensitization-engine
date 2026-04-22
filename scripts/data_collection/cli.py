#!/usr/bin/env python3
"""
Unified CLI for JuaKazi Data Collection

Replaces 11 separate scripts with a single entry point.

Usage:
    python3 scripts/data_collection/cli.py collect wikipedia --language en --max-items 100
    python3 scripts/data_collection/cli.py collect news --language sw --max-items 500
    python3 scripts/data_collection/cli.py collect bible --language ki --max-items 200
    python3 scripts/data_collection/cli.py list-sources
    python3 scripts/data_collection/cli.py show-lineage data/raw/wiki_en.csv
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.data_collection.base_collector import CollectionConfig, DataCollector
from scripts.data_collection.wikipedia_collector import WikipediaCollector, GroundTruthCollector
from scripts.data_collection.news_collector import NewsCollector
from scripts.data_collection.bible_collector import BibleCollector


# Collector registry
COLLECTORS = {
    'wikipedia': {
        'class': WikipediaCollector,
        'languages': ['en', 'sw', 'fr', 'ki'],
        'description': 'Wikipedia articles with gender-relevant content'
    },
    'news': {
        'class': NewsCollector,
        'languages': ['sw'],
        'description': 'Swahili News Dataset (31K+ articles, 2015-2020)'
    },
    'bible': {
        'class': BibleCollector,
        'languages': ['ki'],
        'description': 'Kikuyu Bible verses with occupation terms'
    },
    'ground-truth': {
        'class': GroundTruthCollector,
        'languages': ['en', 'sw', 'fr', 'ki'],
        'description': 'Existing ground truth samples (for testing)'
    }
}


def print_header(title: str, width: int = 70):
    """Print formatted header."""
    print("=" * width)
    print(title.center(width))
    print("=" * width)


def print_success(message: str):
    """Print success message."""
    print(f"\n✅ {message}")


def print_error(message: str):
    """Print error message."""
    print(f"\n❌ ERROR: {message}", file=sys.stderr)


def print_info(message: str):
    """Print info message."""
    print(f"ℹ️  {message}")


def cmd_list_sources(args):
    """List all available data sources."""
    print_header("Available Data Sources")

    for name, info in COLLECTORS.items():
        print(f"\n{name}")
        print(f"  Description: {info['description']}")
        print(f"  Languages: {', '.join(info['languages'])}")
        print(f"  Class: {info['class'].__name__}")

    print("\n" + "=" * 70)
    print(f"Total sources: {len(COLLECTORS)}")


def cmd_show_lineage(args):
    """Show lineage information for collected data."""
    csv_file = Path(args.file)

    if not csv_file.exists():
        print_error(f"File not found: {csv_file}")
        return 1

    # Try to extract lineage from filename pattern
    # Format: {source}_{lang}_{version}.csv
    parts = csv_file.stem.split('_')

    print_header(f"Data Lineage: {csv_file.name}")
    print(f"\nFile: {csv_file}")
    print(f"Size: {csv_file.stat().st_size / 1024:.2f} KB")

    # Count lines in CSV
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f) - 1  # Exclude header
        print(f"Samples: {line_count:,}")
    except Exception:
        pass

    # Try to infer source and language
    if len(parts) >= 2:
        source = parts[0]
        language = parts[1]
        print(f"\nInferred metadata:")
        print(f"  Source: {source}")
        print(f"  Language: {language}")

        if source in COLLECTORS:
            info = COLLECTORS[source]
            print(f"  Collector: {info['class'].__name__}")
            print(f"  Description: {info['description']}")

    print("\n" + "=" * 70)
    return 0


def cmd_collect(args):
    """Collect data from specified source."""
    source = args.source

    if source not in COLLECTORS:
        print_error(f"Unknown source: {source}")
        print_info(f"Available sources: {', '.join(COLLECTORS.keys())}")
        return 1

    collector_info = COLLECTORS[source]

    # Validate language
    if args.language not in collector_info['languages']:
        print_error(f"Language '{args.language}' not supported for {source}")
        print_info(f"Supported languages: {', '.join(collector_info['languages'])}")
        return 1

    # Build output filename if not specified
    if args.output:
        output_file = Path(args.output)
    else:
        output_file = Path(f"data/raw/{source}_{args.language}.csv")

    # Create configuration
    config = CollectionConfig(
        language=args.language,
        max_items=args.max_items,
        output_file=output_file,
        cache_dir=Path(args.cache_dir) if args.cache_dir else Path("data/cache")
    )

    # Print configuration
    if not args.quiet:
        print_header(f"JuaKazi Data Collector: {source}")
        print(f"\nSource: {source}")
        print(f"Description: {collector_info['description']}")
        print(f"Language: {args.language}")
        print(f"Max items: {args.max_items}")
        print(f"Output: {output_file}")
        print("\n" + "=" * 70)

    # Initialize collector
    try:
        collector_class = collector_info['class']

        # Special handling for collectors with extra args
        if source == 'news' and args.lexicon:
            collector = collector_class(config, lexicon_path=args.lexicon)
        elif source == 'bible' and args.bible_dir:
            collector = collector_class(config, bible_dir=args.bible_dir)
        else:
            collector = collector_class(config)

        if not args.quiet:
            print(f"\n📥 Collecting data from {source}...")

        # Collect samples
        samples = collector.collect()

        if not samples:
            print_error("No samples collected")
            return 1

        if not args.quiet:
            print(f"✓ Collected {len(samples)} samples")

        # Save samples
        if not args.quiet:
            print(f"\n💾 Saving to {output_file}...")

        result = collector.save_samples(samples)

        if not result.success:
            print_error(f"Failed to save samples: {result.output_summary}")
            return 1

        # Print summary
        if not args.quiet:
            print_success("Collection complete!")
            print(f"\n📊 Summary:")
            print(f"  Source: {source}")
            print(f"  Language: {args.language}")
            print(f"  Samples collected: {result.samples_collected}")
            print(f"  Output file: {result.output_file}")
            print(f"  File size: {result.output_file.stat().st_size / 1024:.2f} KB")

            # Print lineage
            if args.verbose:
                lineage = collector.get_lineage()
                print(f"\n📋 Lineage:")
                for key, value in lineage.items():
                    print(f"  {key}: {value}")
        else:
            # Quiet mode: just print essential info
            print(f"{result.samples_collected} samples saved to {result.output_file}")

        return 0

    except Exception as e:
        print_error(f"Collection failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="JuaKazi Data Collection CLI - Unified data collection interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect from Wikipedia
  %(prog)s collect wikipedia --language en --max-items 100

  # Collect from Swahili News
  %(prog)s collect news --language sw --max-items 500

  # Collect from Kikuyu Bible
  %(prog)s collect bible --language ki --max-items 200

  # List available sources
  %(prog)s list-sources

  # Show lineage information
  %(prog)s show-lineage data/raw/wiki_en.csv
        """
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # list-sources command
    list_parser = subparsers.add_parser(
        'list-sources',
        help='List all available data sources'
    )
    list_parser.set_defaults(func=cmd_list_sources)

    # show-lineage command
    lineage_parser = subparsers.add_parser(
        'show-lineage',
        help='Show lineage information for a CSV file'
    )
    lineage_parser.add_argument(
        'file',
        help='Path to CSV file'
    )
    lineage_parser.set_defaults(func=cmd_show_lineage)

    # collect command
    collect_parser = subparsers.add_parser(
        'collect',
        help='Collect data from a source'
    )
    collect_parser.add_argument(
        'source',
        choices=list(COLLECTORS.keys()),
        help='Data source to collect from'
    )
    collect_parser.add_argument(
        '--language', '-l',
        required=True,
        choices=['en', 'sw', 'fr', 'ki'],
        help='Language code (en=English, sw=Swahili, fr=French, ki=Kikuyu)'
    )
    collect_parser.add_argument(
        '--max-items', '-n',
        type=int,
        default=100,
        help='Maximum number of items to collect (default: 100)'
    )
    collect_parser.add_argument(
        '--output', '-o',
        help='Output CSV file (default: data/raw/{source}_{lang}.csv)'
    )
    collect_parser.add_argument(
        '--cache-dir',
        help='Cache directory for downloads (default: data/cache)'
    )
    collect_parser.add_argument(
        '--lexicon',
        help='Path to lexicon file (for news collector)'
    )
    collect_parser.add_argument(
        '--bible-dir',
        help='Path to Bible directory (for bible collector)'
    )
    collect_parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Quiet mode (minimal output)'
    )
    collect_parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    collect_parser.set_defaults(func=cmd_collect)

    # Parse arguments
    args = parser.parse_args()

    # Validate verbose and quiet are mutually exclusive (if command supports them)
    if hasattr(args, 'verbose') and hasattr(args, 'quiet') and args.verbose and args.quiet:
        parser.error("--verbose and --quiet are mutually exclusive")

    # Run command
    if not hasattr(args, 'func'):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
