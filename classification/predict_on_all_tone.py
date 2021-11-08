import os
from optparse import OptionParser

from congress.make_predictions_tone import make_predictions


### Redundant with predict_on_all I think!


def main():
    usage = "%prog outdir"
    parser = OptionParser(usage=usage)
    parser.add_option('--indir', type=str, default='/u/scr/dcard/data/congress/segments/',
                      help='Base dir: default=%default')
    parser.add_option('--model-type', type=str, default='roberta',
                      help='Model type: default=%default')
    parser.add_option('--model_name_or_path', type=str, default=None,
                      help='Model dir: default=%default')
    parser.add_option('--first', type=int, default=43,
                      help='First congress: default=%default')
    parser.add_option('--last', type=int, default=114,
                      help='Last congress: default=%default')
    parser.add_option('--train-file', type=str, default=None,
                      help='Train file: default=%default')

    (options, args) = parser.parse_args()

    outdir = args[0]

    first = options.first
    last = options.last

    indir = options.indir
    model_type = options.model_type
    model = options.model_name_or_path
    train_file = options.train_file

    for congress in range(first, last+1):
        infile = os.path.join(indir, 'segments-' + str(congress).zfill(3) + '.jsonlist')
        outfile = os.path.join(outdir, 'pred.segments-' + str(congress).zfill(3) + '.tsv')
        make_predictions(infile,
                         outfile,
                         train_file,
                         model_type=model_type,
                         model_name_or_path=model,
                         overwrite_output_dir=False)

if __name__ == '__main__':
    main()
