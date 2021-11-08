import os
import json
from optparse import OptionParser
from collections import defaultdict, Counter

import seaborn
import numpy as np
import matplotlib.pyplot as plt

from time_periods.common import congress_to_year


def main():
    usage = "%prog"
    parser = OptionParser(usage=usage)
    parser.add_option('--test-file', type=str, default='data/speeches/Congress/linear/test.tokenized.jsonlist',
                      help='Test file: default=%default')
    parser.add_option('--weight-file', type=str, default='data/speeches/Congress/linear/weights.nontest.npz',
                      help='Weight file: default=%default')
    parser.add_option('--outdir', type=str, default='plots/',
                      help='Weight file: default=%default')

    (options, args) = parser.parse_args()

    test_file = options.test_file
    weight_file = options.weight_file
    outdir = options.outdir
    add_labels = True

    if not os.path.exists(outdir):
        os.makedirs(outdir)

    stopwords = {}

    with open(test_file) as f:
        lines = f.readlines()
    lines = [json.loads(line) for line in lines]
    data = np.load(weight_file)

    pro_counters_by_congress = defaultdict(Counter)
    anti_counters_by_congress = defaultdict(Counter)
    tone_counters_by_congress = defaultdict(Counter)
    for line in lines:
        congress = int(line['congress'])
        tone = line['tone']
        for sent in line['tokens']:
            tokens = [t for t in sent if t == t.lower()]
            tone_counters_by_congress[congress].update(tokens)
            if tone == 'pro':
                pro_counters_by_congress[congress].update(tokens)
            elif tone == 'anti':
                anti_counters_by_congress[congress].update(tokens)

    print(list(data.keys()))
    vocab = data['vocab']
    weights = data['weights']
    vocab_size = len(vocab)
    n_congesses = len(pro_counters_by_congress)
    print(vocab_size, n_congesses)
    print(weights.shape)
    vocab_index = dict(zip(vocab, range(vocab_size)))

    pro_freq_by_congress = defaultdict(Counter)
    anti_freq_by_congress = defaultdict(Counter)
    tone_freq_by_congress = defaultdict(Counter)
    congresses = sorted(pro_counters_by_congress)
    pro_sum_by_congress = Counter()
    anti_sum_by_congress = Counter()
    tone_sum_by_congress = Counter()
    for congress in congresses:
        tone_sum = sum(tone_counters_by_congress[congress].values())
        tone_freq_by_congress[congress] = Counter({t: v / tone_sum for t, v in tone_counters_by_congress[congress].items()})
        tone_sum_by_congress[congress] = tone_sum
        pro_sum = sum(pro_counters_by_congress[congress].values())
        pro_freq_by_congress[congress] = Counter({t: v / pro_sum for t, v in pro_counters_by_congress[congress].items()})
        pro_sum_by_congress[congress] = pro_sum
        anti_sum = sum(anti_counters_by_congress[congress].values())
        anti_freq_by_congress[congress] = Counter({t: v / anti_sum for t, v in anti_counters_by_congress[congress].items()})
        anti_sum_by_congress[congress] = anti_sum

    pro_weights_by_congress = np.zeros([vocab_size, n_congesses])
    pro_freqs_by_congress_np = np.zeros([vocab_size, n_congesses])
    pro_impacts_by_congress = np.zeros([vocab_size, n_congesses])
    anti_weights_by_congress = np.zeros([vocab_size, n_congesses])
    anti_freqs_by_congress_np = np.zeros([vocab_size, n_congesses])
    anti_impacts_by_congress = np.zeros([vocab_size, n_congesses])
    n_found = 0
    for c_i, congress in enumerate(congresses):
        for t_i, term in enumerate(vocab):
            parts = term.split('__')
            if len(parts) == 1:
                pro_freq = pro_freq_by_congress[congress][term]
                anti_freq = anti_freq_by_congress[congress][term]
                weight = weights[0, t_i]
                decorated = term + '__' + str(congress)
                if decorated in vocab_index:
                    weight += weights[0, vocab_index[decorated]]
                    n_found += 1
                pro_weights_by_congress[t_i, c_i] = weight
                pro_freqs_by_congress_np[t_i, c_i] = pro_freq
                pro_impacts_by_congress[t_i, c_i] = weight * pro_freq
                anti_weights_by_congress[t_i, c_i] = -weight
                anti_freqs_by_congress_np[t_i, c_i] = anti_freq
                anti_impacts_by_congress[t_i, c_i] = -weight * anti_freq

    n_words, n_congresses = pro_impacts_by_congress.shape
    extended = np.zeros([n_words, n_congresses+4])
    extended_freq = np.zeros([n_words, n_congresses+4])
    totals = np.zeros(n_congresses+4)
    for i in range(5):
        extended[:, i:i+n_congresses] += pro_impacts_by_congress
        extended_freq[:, i:i+n_congresses] += pro_freqs_by_congress_np
        totals[i:i+n_congresses] += 1
    pro_impacts_by_congress_smoothed = extended[:, 2:-2] / totals[2:-2]

    n_words, n_congresses = anti_impacts_by_congress.shape
    extended = np.zeros([n_words, n_congresses+4])
    extended_freq = np.zeros([n_words, n_congresses+4])
    totals = np.zeros(n_congresses+4)
    for i in range(5):
        extended[:, i:i+n_congresses] += anti_impacts_by_congress
        extended_freq[:, i:i+n_congresses] += anti_freqs_by_congress_np
        totals[i:i+n_congresses] += 1
    anti_impacts_by_congress_smoothed = extended[:, 2:-2] / totals[2:-2]

    min_pro_impacts = np.min(pro_impacts_by_congress_smoothed, axis=1)
    median_pro_impacts = np.median(pro_impacts_by_congress_smoothed, axis=1)
    max_pro_impacts = np.max(pro_impacts_by_congress_smoothed, axis=1)
    median_pro_impacts = np.array([v if vocab[i] not in stopwords else 0 for i, v in enumerate(median_pro_impacts)])
    max_pro_impacts = np.array([v if vocab[i] not in stopwords else 0 for i, v in enumerate(max_pro_impacts)])

    min_anti_impacts = np.min(anti_impacts_by_congress, axis=1)
    median_anti_impacts = np.median(anti_impacts_by_congress_smoothed, axis=1)
    max_anti_impacts = np.max(anti_impacts_by_congress_smoothed, axis=1)
    median_anti_impacts = np.array([v if vocab[i] not in stopwords else 0 for i, v in enumerate(median_anti_impacts)])
    max_anti_impacts = np.array([v if vocab[i] not in stopwords else 0 for i, v in enumerate(max_anti_impacts)])

    seaborn.reset_orig()
    seaborn.set(font_scale=1.35)
    seaborn.set_palette('Paired')

    fig, ax = plt.subplots(nrows=2, figsize=(10, 7))
    plt.subplots_adjust(hspace=0.3)

    topn = 12
    years = [congress_to_year(c) for c in congresses]

    order = np.argsort(max_pro_impacts)[::-1]
    for i in order[:topn]:
        print(vocab[i], min_pro_impacts[i], median_pro_impacts[i], max_pro_impacts[i])

    indices = [i for i in order[:topn]]

    rows = [np.maximum(np.zeros_like(pro_impacts_by_congress_smoothed[i, :]), pro_impacts_by_congress_smoothed[i, :]) for i in indices]
    labels = [vocab[i] for i in indices]

    matrix = np.vstack(rows)
    sums = matrix.sum(0)
    matrix = matrix / sums

    ax[0].stackplot(years, matrix, labels=labels, alpha=0.8)

    if add_labels:
        ax[0].text(1943, 0.92, labels[11], color='white', fontsize=11)
        ax[0].text(2012, 0.87, labels[10], color='k', fontsize=7)
        ax[0].text(1892, 0.89, labels[9], color='white', fontsize=9)
        ax[0].text(1963, 0.78, labels[8], color='k', fontsize=11)
        ax[0].text(1915, 0.78, labels[7], color='white', fontsize=14)
        ax[0].text(1900, 0.59, labels[6], color='k', fontsize=14)
        ax[0].text(1935, 0.57, labels[5], color='white', fontsize=14)
        ax[0].text(1985, 0.7, labels[4], color='k', fontsize=12)
        ax[0].text(1988, 0.53, labels[3], color='white', fontsize=14)
        ax[0].text(1898, 0.11, labels[2], color='k', fontsize=13)
        ax[0].text(2005, 0.14, labels[1], color='white', fontsize=14)
        ax[0].text(1960, 0.1, labels[0], color='k', fontsize=16)
    else:
        ax[0].legend(loc='upper left', bbox_to_anchor=(1,1))
        handles, labels = ax[0].get_legend_handles_labels()
        ax[0].legend(handles[::-1], labels[::-1], loc='upper left', bbox_to_anchor=(1, 1))

    ax[0].set_title('Pro-immigration terms')
    ax[0].set_ylabel('Normalized impact')

    order = np.argsort(max_anti_impacts)[::-1]
    for i in order[:topn]:
        print(vocab[i], min_anti_impacts[i], median_anti_impacts[i], max_anti_impacts[i])

    indices = [i for i in order[:topn]]

    rows = [np.maximum(np.zeros_like(anti_impacts_by_congress_smoothed[i, :]), anti_impacts_by_congress_smoothed[i, :]) for i in indices]
    labels = [vocab[i] for i in indices]

    matrix = np.vstack(rows)
    sums = matrix.sum(0)
    matrix = matrix / sums

    ax[1].stackplot(years, matrix, labels=labels, alpha=0.8)

    if add_labels:
        ax[1].text(2007, 0.96, labels[11], color='white', fontsize=8)
        ax[1].text(1943, 0.93, labels[10], color='k', fontsize=12)
        ax[1].text(1959, 0.8, labels[9], color='white', fontsize=9)
        ax[1].text(2000, 0.87, labels[8], color='k', fontsize=8)
        ax[1].text(1921, 0.75, labels[7], color='white', fontsize=14)
        ax[1].text(1947, 0.73, labels[6], color='k', fontsize=9)
        ax[1].text(1943, 0.62, labels[5], color='white', fontsize=12)
        ax[1].text(1914, 0.58, labels[4], color='k', fontsize=11)
        ax[1].text(1882, 0.35, labels[3], color='white', fontsize=14)
        ax[1].text(1933, 0.23, labels[2], color='k', fontsize=16)
        ax[1].text(2005, 0.4, labels[1], color='white', fontsize=15)
        ax[1].text(1978, 0.13, labels[0], color='k', fontsize=16)
    else:
        ax[1].legend(loc='upper left', bbox_to_anchor=(1,1))
        handles, labels = ax[1].get_legend_handles_labels()
        ax[1].legend(handles[::-1], labels[::-1], loc='upper left', bbox_to_anchor=(1, 1))

    ax[1].set_title('Anti-immigration terms')
    ax[1].set_ylabel('Normalized impact')

    for k in range(2):
        ax[k].set_xlim(1880, 2020)
        ax[k].set_ylim(0, 1)

    if add_labels:
        plt.savefig(os.path.join(outdir, 'tone_linear_impact_with_labels.pdf'), bbox_inches='tight')
        plt.savefig(os.path.join(outdir, 'tone_linear_impact_with_labels.png'), bbox_inches='tight')
    else:
        plt.savefig(os.path.join(outdir, 'tone_linear_impact.pdf'), bbox_inches='tight')
        plt.savefig(os.path.join(outdir, 'tone_linear_impact.png'), bbox_inches='tight')


if __name__ == '__main__':
    main()
