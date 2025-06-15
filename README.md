# dm-data-tokenization-replacer
Replaces sensitive data with unique, reversible tokens. Supports multiple tokenization methods (e.g., UUIDs, sequential IDs) and allows for the management of a token-to-value mapping for later de-tokenization. Takes CSV file as input. - Focused on Tools designed to generate or mask sensitive data with realistic-looking but meaningless values

## Install
`git clone https://github.com/ShadowStrikeHQ/dm-data-tokenization-replacer`

## Usage
`./dm-data-tokenization-replacer [params]`

## Parameters
- `-h`: Show help message and exit
- `--tokenize_columns`: A list of column names to tokenize.
- `--token_method`: No description provided
- `--token_map_file`: No description provided
- `--detokenize`: Detokenize the data using the token map file.

## License
Copyright (c) ShadowStrikeHQ
