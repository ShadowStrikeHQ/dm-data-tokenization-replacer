import argparse
import csv
import logging
import uuid
import os
from collections import defaultdict
from typing import Dict, Callable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="Replaces sensitive data in a CSV file with unique, reversible tokens."
    )
    parser.add_argument("input_file", help="The input CSV file.")
    parser.add_argument("output_file", help="The output CSV file with tokenized data.")
    parser.add_argument(
        "--tokenize_columns",
        nargs="+",
        required=True,
        help="A list of column names to tokenize."
    )
    parser.add_argument(
        "--token_method",
        choices=["uuid", "sequential"],
        default="uuid",
        help="The tokenization method to use (uuid or sequential). Defaults to uuid."
    )
    parser.add_argument(
        "--token_map_file",
        default="token_map.csv",
        help="The file to store the token-to-value mapping (CSV). Defaults to token_map.csv."
    )
    parser.add_argument(
        "--detokenize",
        action="store_true",
        help="Detokenize the data using the token map file."
    )
    return parser

def generate_uuid_token(value: str, token_map: Dict[str, str]) -> str:
    """
    Generates a UUID token for a given value, ensuring uniqueness.
    """
    # Attempt to retrieve existing token.
    for token, original_value in token_map.items():
        if original_value == value:
            return token

    token = str(uuid.uuid4())
    #Prevent collision, try again if needed
    while token in token_map:
        token = str(uuid.uuid4())

    return token
    

def generate_sequential_token(value: str, token_map: Dict[str, str]) -> str:
     """
     Generates a sequential token for a given value.
     This is more complex and needs to manage a counter.
     """

     # Attempt to retrieve existing token.
     for token, original_value in token_map.items():
         if original_value == value:
             return token

     # Find the next available sequential ID
     next_id = 1
     while str(next_id) in token_map:
         next_id += 1
     token = str(next_id)
     return token

def tokenize_data(
    input_file: str,
    output_file: str,
    tokenize_columns: list[str],
    token_method: str,
    token_map_file: str
) -> None:
    """
    Tokenizes specified columns in a CSV file and saves the result to a new file.
    """
    token_map: Dict[str, str] = {}

    # Read existing token map, if it exists
    if os.path.exists(token_map_file):
        try:
            with open(token_map_file, "r", newline="") as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if len(row) == 2:
                        token_map[row[0]] = row[1]
                    else:
                        logging.warning(f"Skipping malformed row in token map file: {row}")

        except Exception as e:
            logging.error(f"Error reading existing token map: {e}")
            raise

    if token_method == "uuid":
        token_generator: Callable[[str, Dict[str, str]], str] = generate_uuid_token
    elif token_method == "sequential":
        token_generator: Callable[[str, Dict[str, str]], str] = generate_sequential_token
    else:
        raise ValueError(f"Invalid token_method: {token_method}")


    try:
        with open(input_file, "r", newline="") as infile, open(
            output_file, "w", newline=""
        ) as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()

            for row in reader:
                for column in tokenize_columns:
                    if column in row:
                        original_value = row[column]
                        # Check if the value already has a token assigned
                        token = next((k for k, v in token_map.items() if v == original_value), None)
                        if token is None: #Create a new token if it does not exist
                            token = token_generator(original_value, token_map)
                            token_map[token] = original_value
                        row[column] = token
                    else:
                        logging.warning(f"Column '{column}' not found in input file.")

                writer.writerow(row)
    except FileNotFoundError:
        logging.error(f"Input file '{input_file}' not found.")
        raise
    except Exception as e:
        logging.error(f"An error occurred during tokenization: {e}")
        raise

    # Write token map to file
    try:
        with open(token_map_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            for token, value in token_map.items():
                writer.writerow([token, value])
    except Exception as e:
        logging.error(f"Error writing token map to file: {e}")
        raise


def detokenize_data(input_file: str, output_file: str, token_map_file: str) -> None:
    """
    Detokenizes specified columns in a CSV file using a token map and saves the result to a new file.
    """
    token_map: Dict[str, str] = {}
    try:
        with open(token_map_file, "r", newline="") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if len(row) == 2:
                    token_map[row[0]] = row[1]
                else:
                    logging.warning(f"Skipping malformed row in token map file: {row}")
    except FileNotFoundError:
        logging.error(f"Token map file '{token_map_file}' not found.")
        raise
    except Exception as e:
        logging.error(f"Error reading token map file: {e}")
        raise

    try:
        with open(input_file, "r", newline="") as infile, open(
            output_file, "w", newline=""
        ) as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()

            for row in reader:
                for column in reader.fieldnames:
                    if row[column] in token_map:
                        row[column] = token_map[row[column]]
                writer.writerow(row)
    except FileNotFoundError:
        logging.error(f"Input file '{input_file}' not found.")
        raise
    except Exception as e:
        logging.error(f"An error occurred during detokenization: {e}")
        raise


def main():
    """
    Main function to execute the data tokenization or detokenization process.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    try:
        if args.detokenize:
            detokenize_data(args.input_file, args.output_file, args.token_map_file)
            logging.info(f"Data detokenized successfully. Output saved to '{args.output_file}'.")
        else:
            tokenize_data(
                args.input_file,
                args.output_file,
                args.tokenize_columns,
                args.token_method,
                args.token_map_file,
            )
            logging.info(
                f"Data tokenized successfully. Output saved to '{args.output_file}'. Token map saved to '{args.token_map_file}'."
            )
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        exit(1)


if __name__ == "__main__":
    main()