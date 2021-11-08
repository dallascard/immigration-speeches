import os
import re
import json
from optparse import OptionParser
from collections import defaultdict, Counter

import numpy as np
from tqdm import tqdm

from analysis.group_terms import get_countries, get_nationalities, add_american


def main():
    usage = "%prog"
    parser = OptionParser(usage=usage)
    parser.add_option('--infile', type=str, default='data/speeches/Congress/imm_segments_with_tone_and_metadata.jsonlist',
                      help='infile: default=%default')
    parser.add_option('--outdir', type=str, default='data/speeches/Congress/country_mentions/',
                      help='outdir: default=%default')
    parser.add_option('--lower', action="store_true", default=False,
                      help='Lower case text: default=%default')

    (options, args) = parser.parse_args()

    infile = options.infile
    outdir = options.outdir
    lower = options.lower

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    american_terms, substitutions = add_american()

    countries = get_countries()
    nationalities = get_nationalities()

    if lower:
        countries = {country: [t.lower() for t in terms] for country, terms in countries.items()}
        nationalities = {country: [t.lower() for t in terms] for country, terms in nationalities.items()}
        american_terms = {country: [t.lower() for t in terms] for country, terms in american_terms.items()}

    nationality_terms = {}
    for country, terms in nationalities.items():
        nationality_terms[country] = set(terms).union(american_terms[country])

    combined_terms = {}
    for country, terms in countries.items():
        combined_terms[country] = set(terms).union(nationalities[country]).union(american_terms[country])

    country_counter_by_congress = defaultdict(Counter)
    nationality_counter_by_congress = defaultdict(Counter)
    combined_counter_by_congress = defaultdict(Counter)

    with open(infile) as f:
        lines = f.readlines()

    speech_ids_by_country = defaultdict(set)
    speech_ids_by_nationality = defaultdict(set)
    speech_ids_by_nationality_plus_country = defaultdict(set)

    for line in tqdm(lines):
        line = json.loads(line)
        speech_id = line['speech_id']
        congress = int(line['congress'])
        text = line['text']
        # remove spaces and dashes from <nationality>-American terms
        for query, replacement in substitutions.items():
            text = re.sub(query, replacement, text)
        if lower:
            text = text.lower()
        tokens = set(text.split())

        for country, terms in countries.items():
            if len(tokens.intersection(terms)) > 0:
                country_counter_by_congress[country][congress] += 1
                speech_ids_by_country[country].add(speech_id)
        for country, terms in nationality_terms.items():
            if len(tokens.intersection(terms)) > 0:
                nationality_counter_by_congress[country][congress] += 1
                speech_ids_by_nationality[country].add(speech_id)
        for country, terms in combined_terms.items():
            if len(tokens.intersection(terms)) > 0:
                combined_counter_by_congress[country][congress] += 1
                speech_ids_by_nationality_plus_country[country].add(speech_id)

    country_list = sorted(country_counter_by_congress)
    sums = [sum(country_counter_by_congress[country].values()) for country in country_list]

    with open(os.path.join(outdir, 'imm_country_counts_country_mentions.json'), 'w') as f:
        json.dump(dict(zip(country_list, sums)), f, indent=2)

    country_list = sorted(nationality_counter_by_congress)
    sums = [sum(nationality_counter_by_congress[country].values()) for country in country_list]
    order = np.argsort(sums)[::-1]
    print("Number of mentions per nationality:")
    for i in order:
        print(country_list[i], sums[i])

    with open(os.path.join(outdir, 'imm_country_counts_nationality_mentions.json'), 'w') as f:
        json.dump(dict(zip(country_list, sums)), f, indent=2)

    country_list = sorted(combined_counter_by_congress)
    sums = [sum(combined_counter_by_congress[country].values()) for country in country_list]

    with open(os.path.join(outdir, 'imm_country_counts_nationality_or_country_mentions.json'), 'w') as f:
        json.dump(dict(zip(country_list, sums)), f, indent=2)

    with open(os.path.join(outdir, 'imm_country_counts_nationality_mentions_by_congress.json'), 'w') as f:
        json.dump(combined_counter_by_congress, f, indent=2)

    with open(os.path.join(outdir, 'imm_country_counts_nationality_or_country_mentions_by_congress.json'), 'w') as f:
        json.dump(combined_counter_by_congress, f, indent=2)

    with open(os.path.join(outdir, 'imm_country_speech_ids_by_country_mentions.json'), 'w') as f:
        json.dump({country: sorted(ids) for country, ids in speech_ids_by_country.items()}, f, indent=2)

    with open(os.path.join(outdir, 'imm_country_speech_ids_by_nationality_mentions.json'), 'w') as f:
        json.dump({country: sorted(ids) for country, ids in speech_ids_by_nationality.items()}, f, indent=2)

    with open(os.path.join(outdir, 'imm_country_speech_ids_by_nationality_or_country_mentions.json'), 'w') as f:
        json.dump({country: sorted(ids) for country, ids in speech_ids_by_nationality_plus_country.items()}, f, indent=2)


if __name__ == '__main__':
    main()
