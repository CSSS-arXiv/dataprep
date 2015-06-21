#!/usr/bin/env python
import argparse
import fnmatch
import re, string
import gzip

from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords
from os import path, walk


def interface():
    args = argparse.ArgumentParser()
    args.add_argument('-i', '--input-dir', help='Input directory')
    args.add_argument('-o', '--output-dir', help='Output directory')
    args.add_argument('-c', '--custom-stops', help='Custom stopwords file', default=None)
    args.add_argument('-f', '--file-list', help='List of files to process', default=None)
    args.add_argument('-s', '--file-suffix', default='.abs')
    args.add_argument('-n', '--min-wordcount', default=10, help='Minimum number of words')
    args.add_argument('--zip', dest='zipres', action='store_true', help='GZip output files')
    args = args.parse_args()
    return args


def word_filter(word, stop_list, lemmer):
    if 'cid:' in word or word.startswith("\\x") or word.startswith("arx"):
        return None
    w = lemmer.lemmatize(re.sub(r'[^a-zA-Z]+', '', word).lower())
    if w in stop_list:
        return None
    if len(w) < 3:
        return None
    return w


if __name__=="__main__":
    args = interface()

    if args.file_list:
        files_to_process = [path.basename(l.strip()) + args.file_suffix for l in open(args.file_list, 'rU')]
    else:
        files_to_process = []
    
    files = []
    for root, dirnames, filenames in walk(args.input_dir):
        for f in fnmatch.filter(filenames, '*'+args.file_suffix):
            file_path = path.join(root, f)
            if files_to_process:
                if f in files_to_process:
                    files.append(file_path)
            else:
                files.append(file_path)
    print "About to process %d files..." % len(files)

    lemmer = WordNetLemmatizer()
    title_pattern = re.compile(r'Title:(.+?)Authors:', flags=re.DOTALL)
    stop_list = stopwords.words('english')
    if args.custom_stops:
        custom_words = [word_filter(w.strip(), [], lemmer) for w in open(args.custom_stops, 'rU')]
        stop_list += custom_words
        print "Added %d words to the stopwords list." % (len(custom_words))

    out_dir = args.output_dir
    for f in files:
        try:
            filename = path.basename(f).replace(args.file_suffix, '')
            filename = path.join(args.output_dir, filename)
            text = open(f, 'r').read()
            title = title_pattern.findall(text)[0]
            text = text.split('\\\\')[2].strip() + ' ' + title.strip()
            words = []

            for word in text.split():
                w = word_filter(word, stop_list, lemmer)
                if w:
                    words.append(w)

            if len(words) >= args.min_wordcount:
                if args.zipres:
                    output = gzip.open(filename + '.abs.gz', 'w')
                else:
                    output = open(filename + '.abs', 'w')
                output.write(' '.join(words))
                output.close()
        except:
            print 'Failed to process %s' % f
